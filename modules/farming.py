#!/usr/bin/env python3
"""
farming.py - Core farming logic with retry, auto-login, profile completion,
queue system, account recovery, and incremental farming.
"""

import time
import random
import threading
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import logging

from modules.database import DatabaseManager, AccountResult
from modules.email_provider import EmailManager
from modules.captcha import CaptchaSolver
from modules.browser import BrowserManager
from modules.proxy import ProxyManager
from modules.monitoring import (
    ProgressTracker, MetricsCollector, take_screenshot, is_shutting_down
)
from modules.notifications import Notifier
from modules.config import Config

logger = logging.getLogger(__name__)


class FarmingQueue:
    """Priority queue for farming tasks (feature #26)."""

    def __init__(self, batch_size: int = 10, batch_delay: int = 60):
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._batch_count = 0

    def add(self, account_index: int) -> None:
        with self._lock:
            self._queue.append(account_index)

    def get_batch(self) -> List[int]:
        """Get a batch of tasks."""
        with self._lock:
            batch = []
            for _ in range(min(self.batch_size, len(self._queue))):
                if self._queue:
                    batch.append(self._queue.popleft())
            if batch:
                self._batch_count += 1
            return batch

    def remaining(self) -> int:
        with self._lock:
            return len(self._queue)


class Farmer:
    """Main farming engine with all advanced features."""

    def __init__(self, config: Config, db: DatabaseManager, proxy: ProxyManager,
                 email_mgr: EmailManager, captcha: CaptchaSolver,
                 browser_mgr: BrowserManager, notifier: Notifier,
                 progress: ProgressTracker, metrics: MetricsCollector):
        self.config = config
        self.db = db
        self.proxy_mgr = proxy
        self.email_mgr = email_mgr
        self.captcha = captcha
        self.browser_mgr = browser_mgr
        self.notifier = notifier
        self.progress = progress
        self.metrics = metrics
        self.platform = config.get_platform()

        # Recovery queue for stuck accounts (feature #27)
        self._recovery_queue: deque = deque()

    # ==================== MAIN FARMING ====================

    def farm_accounts(self, total: int) -> Dict[str, int]:
        """Farm multiple accounts with retry, queue, and batch processing."""
        results: List[AccountResult] = []
        start_time = time.time()

        logger.info(f"🚀 Starting farming: {total} accounts, {self.config.max_workers} workers")

        try:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = {
                    executor.submit(self.farm_one_account, i): i
                    for i in range(1, total + 1)
                }

                for future in as_completed(futures):
                    if is_shutting_down():
                        logger.warning("⚠️ Shutdown requested, stopping...")
                        for f in futures:
                            f.cancel()
                        break

                    idx = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        self.progress.update(result.success, result.status == "verified")
                        self.metrics.record_account_time(result.email, time.time() - start_time, result.success)

                        if result.success:
                            logger.info(f"✅ #{idx}: {result.email} ({result.status})")
                            self.notifier.notify_account_created(result.email, result.status, result.proxy_used or "")
                        else:
                            logger.error(f"❌ #{idx}: {result.email} - {result.error}")
                    except Exception as e:
                        logger.error(f"💥 Worker #{idx} crash: {e}")

        except KeyboardInterrupt:
            logger.warning("⚠️ Interrupted by user")

        # Check ban rate (feature #20)
        stats = self.progress.get_status()
        self.notifier.check_ban_rate(stats["total"], stats["failed"])

        # Send final notification
        if self.config.notification.telegram_enabled or self.config.notification.discord_enabled:
            self.notifier.notify_full_run_complete({
                "total": total,
                "success": stats["success"],
                "verified": stats["verified"],
                "failed": stats["failed"],
                "success_rate": stats["success_rate"],
                "elapsed_minutes": stats["elapsed_minutes"],
            })

        # Send webhook (feature #30)
        if self.config.notification.webhook_enabled:
            self.notifier.send_webhook({
                "event": "farming_complete",
                "stats": stats,
                "timestamp": time.time(),
            })

        elapsed = time.time() - start_time
        logger.info(
            f"=== DONE in {elapsed/60:.1f} min ===\n"
            f"Total: {total} | Success: {stats['success']} | Verified: {stats['verified']} | Failed: {stats['failed']}\n"
            f"Success Rate: {stats['success_rate']}% | Rate: {stats['rate_per_hour']}/hr"
        )

        return stats

    # ==================== SINGLE ACCOUNT FARMING ====================

    def farm_one_account(self, account_index: int) -> AccountResult:
        """Farm a single account with full retry and verification pipeline."""
        start = time.time()
        email, password = self.email_mgr.get_email()
        proxy_url = self.proxy_mgr.get_working_proxy()

        logger.info(f"🚀 Farming #{account_index} | {email}")

        # Check duplicate (also incremental support, feature #28)
        if self.db.check_exists(email):
            logger.warning(f"⚠️ Duplicate: {email}")
            return AccountResult(email, password, False, "duplicate", "Already in DB",
                                proxy_used=proxy_url)

        # Save as pending immediately
        self.db.save_account(email, password, "pending", proxy_url)

        last_error = None

        for attempt in range(self.config.max_retries):
            if is_shutting_down():
                return AccountResult(email, password, False, "cancelled", "Shutdown",
                                    proxy_used=proxy_url)

            try:
                logger.info(f"🔄 Attempt {attempt + 1}/{self.config.max_retries} for {email}")

                with self.browser_mgr.launch_context() as (playwright, browser):
                    geo_ip = None
                    if proxy_url:
                        geo_ip = self.proxy_mgr.verify_ip_rotation(proxy_url)  # Feature #32

                    context = self.browser_mgr.new_context(browser, proxy_url, geo_ip)
                    page = context.new_page()

                    # Navigate to register page
                    page.goto(self.config.target_url, timeout=60000, wait_until="domcontentloaded")
                    self._human_delay(2.0, 4.5, "Load register page")

                    # Random interactions
                    self._random_scroll(page)

                    # Fill form
                    if self.config.browser.keyboard_simulation:
                        # Feature #7: Natural typing
                        self.browser_mgr.natural_type(page, self.platform.email_selector, email)
                    else:
                        page.fill(self.platform.email_selector, email)
                    self._human_delay(0.5, 1.5, "Type email")

                    self._random_scroll(page)

                    if self.config.browser.keyboard_simulation:
                        self.browser_mgr.natural_type(page, self.platform.password_selector, password)
                    else:
                        page.fill(self.platform.password_selector, password)
                    self._human_delay(0.5, 1.5, "Type password")

                    # Solve CAPTCHA
                    self.captcha.solve(page, self.config.target_url)
                    self._human_delay(1.5, 3.0, "Wait CAPTCHA")

                    self._random_scroll(page)

                    # Submit
                    if self.config.browser.mouse_simulation:
                        # Feature #6: Natural mouse click
                        self.browser_mgr.mouse_click(page, self.platform.submit_selector)
                    else:
                        page.click(self.platform.submit_selector)
                    self._human_delay(5.0, 8.0, "Wait server response")

                    # Validate registration success
                    success, message = self._validate_registration(page, email)

                    if success:
                        logger.info(f"✅ Registration OK: {message}")

                        # Email verification
                        mail_tm_domain = self.email_mgr.get_mail_tm_domain()
                        if email.endswith("@" + mail_tm_domain):
                            self._verify_email_mail_tm(page, email, password)
                        elif "@1sec-mail.com" in email or any(x in email for x in ["@1sec-mail.com"]):
                            self._verify_email_1sec(page, email)
                        else:
                            self.db.update_status(email, "pending_verification")

                        # Feature #21: Auto-login verification
                        if self.config.notification.telegram_enabled:  # Only if verification passed
                            self._auto_login_verification(page, context, email, password)

                        # Feature #22: Profile completion
                        self._profile_completion(page, email)

                        return AccountResult(
                            email, password, True,
                            "verified" if any(s in email for s in ["@mail.tm", "@1sec-mail.com"]) else "registered",
                            message, proxy_url
                        )

                    else:
                        logger.warning(f"❌ Registration failed: {message}")
                        last_error = message

                        # Permanent errors — don't retry
                        permanent = ["already exists", "already registered", "email taken",
                                     "duplicate", "blocked", "diblokir"]
                        if any(pe in message.lower() for pe in permanent):
                            self.db.update_status(email, "failed")
                            return AccountResult(email, password, False, "failed", message, proxy_url)

            except Exception as e:
                last_error = str(e)
                logger.error(f"Error on {email}: {e}")

                # Screenshot on error (feature #13, #14)
                if self.config.monitoring.screenshot_on_error and 'page' in locals():
                    take_screenshot(page, email, f"attempt{attempt+1}_error",
                                    self.config.monitoring.screenshot_dir)

            # Exponential backoff
            if attempt < self.config.max_retries - 1:
                delay = min(
                    self.config.base_retry_delay * (2 ** attempt) + random.uniform(0, 1),
                    self.config.max_retry_delay
                )
                logger.info(f"⏳ Retry in {delay:.1f}s...")
                time.sleep(delay)

        # All retries failed
        self.db.update_status(email, "failed")
        self.metrics.record_error("max_retries")

        # Add to recovery queue (feature #27)
        self._recovery_queue.append({"email": email, "password": password, "error": last_error})

        return AccountResult(email, password, False, "failed", last_error, proxy_url)

    # ==================== EMAIL VERIFICATION ====================

    def _verify_email_mail_tm(self, page, email: str, password: str) -> None:
        """Verify email via Mail.tm (feature #21)."""
        try:
            token = self.email_mgr._get_mail_tm_token(email)
            if token:
                verify_link = self.email_mgr.check_mail_tm_inbox(email, token)
                if verify_link:
                    logger.info("🔗 Clicking verification link...")
                    page.goto(verify_link, timeout=30000)
                    self._human_delay(3, 5, "Verify email")

                    content = page.content().lower()
                    if any(kw in content for kw in ["verified", "success", "confirmed", "activated"]):
                        self.db.update_status(email, "verified")
                        logger.info("✅ Email verified!")
                    else:
                        self.db.update_status(email, "verification_failed")
                else:
                    self.db.update_status(email, "verification_timeout")
        except Exception as e:
            logger.error(f"Email verification error: {e}")
            self.db.update_status(email, "verification_error")

    def _verify_email_1sec(self, page, email: str) -> None:
        """Verify email via 1sec-mail."""
        try:
            verify_link = self.email_mgr.check_1sec_inbox(email)
            if verify_link:
                logger.info("🔗 Clicking 1sec-mail verification link...")
                page.goto(verify_link, timeout=30000)
                self._human_delay(3, 5, "Verify email")
                self.db.update_status(email, "verified")
        except Exception as e:
            logger.error(f"1sec-mail verification error: {e}")
            self.db.update_status(email, "verification_error")

    # ==================== AUTO LOGIN (feature #21) ====================

    def _auto_login_verification(self, page, context, email: str, password: str) -> None:
        """Auto-login to verify account is working (feature #21)."""
        try:
            # Get current URL domain and construct login URL
            base_url = self.config.target_url.split("/register")[0]
            login_url = f"{base_url}/login"

            page.goto(login_url, timeout=30000)
            self._human_delay(1, 2, "Load login")

            page.fill(self.platform.email_selector, email)
            self._human_delay(0.3, 0.8, "Type email login")
            page.fill(self.platform.password_selector, password)
            self._human_delay(0.3, 0.8, "Type password login")
            self._random_scroll(page)
            page.click(self.platform.submit_selector)
            self._human_delay(3, 5, "Wait login")

            # Check if logged in
            url = page.url.lower()
            content = page.content().lower()

            if any(path in url for path in ["/dashboard", "/home", "/profile", "/settings", "/verify"]):
                self.db.update_status(email, "login_verified")
                logger.info("✅ Login verified — account is fully working!")

                # Save session (feature #23)
                try:
                    cookies = context.cookies()
                    session_data = {"cookies": cookies, "url": page.url}
                    import json
                    self.db.save_session_token(email, json.dumps(session_data))
                    logger.info("💾 Session saved")
                except Exception:
                    pass
            elif any(kw in content for kw in ["invalid password", "wrong password", "incorrect", "error", "invalid"]):
                self.db.update_status(email, "login_failed")
                logger.warning("⚠️ Login failed — account may not be fully created")
                # Screenshot
                if self.config.monitoring.screenshot_on_error:
                    take_screenshot(page, email, "login_failed",
                                    self.config.monitoring.screenshot_dir)

        except Exception as e:
            logger.warning(f"Auto-login error: {e}")

    # ==================== PROFILE COMPLETION (feature #22) ====================

    def _profile_completion(self, page, email: str) -> None:
        """Auto-fill profile after successful login (feature #22)."""
        try:
            # Try to find profile fields
            profile_fields = page.query_selector_all("input[name*='name'], input[name*='username'], input[name*='first_name']")
            if profile_fields:
                random_name = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=8)).capitalize()
                for field in profile_fields[:1]:
                    field.fill(random_name)
                    self._human_delay(0.2, 0.5, "Fill profile")
                logger.info(f"👤 Profile filled with: {random_name}")
        except Exception:
            pass  # Profile page might not exist

    # ==================== VALIDATION ====================

    def _validate_registration(self, page, email: str) -> Tuple[bool, str]:
        """Validate if registration was successful."""
        try:
            self._human_delay(2, 4, "Validate registration")

            content = page.content().lower()
            url = page.url.lower()

            # Error indicators
            for err in self.platform.error_indicators:
                if err in content or err in url:
                    return False, f"Error: {err}"

            # Success indicators
            for succ in self.platform.success_indicators:
                if succ in content or succ in url:
                    return True, f"Success: {succ}"

            # Check redirect
            if any(p in url for p in ["/login", "/dashboard", "/home", "/verify", "/verifikasi"]):
                return True, f"Redirected to: {url}"

            # Check for verification message
            if "email" in content and any(w in content for w in ["sent", "kirim", "dikirim", "check"]):
                return True, "Verification email sent"

            # Check for error elements on page
            error_els = page.query_selector_all(".error, .alert-danger, .text-danger, [role='alert']")
            for el in error_els:
                text = el.inner_text().lower().strip()
                if text and len(text) > 3:
                    return False, f"Page error: {text}"

            return False, "Unknown state"

        except Exception as e:
            return False, f"Validation exception: {e}"

    # ==================== RECOVERY MODE (feature #27) ====================

    def run_recovery(self) -> int:
        """Re-run stuck accounts (feature #27)."""
        pending = self.db.get_pending_accounts(limit=100)
        if not pending:
            logger.info("✅ No pending accounts to recover")
            return 0

        logger.info(f"🔄 Recovery mode: {len(pending)} pending accounts")
        recovered = 0

        for acc in pending:
            if is_shutting_down():
                break

            logger.info(f"🔄 Recovering: {acc['email']} (was: {acc['status']})")
            result = self._recovery_account(acc["email"], acc["password"])
            if result:
                recovered += 1

        logger.info(f"🔄 Recovery complete: {recovered}/{len(pending)} recovered")
        return recovered

    def _recovery_account(self, email: str, password: str) -> bool:
        """Try to recover a single stuck account."""
        try:
            with self.browser_mgr.launch() as (playwright, browser):
                context = self.browser_mgr.new_context(browser)
                page = context.new_page()

                # Check if email is already verified
                base_url = self.config.target_url.split("/register")[0]
                login_url = f"{base_url}/login"
                page.goto(login_url, timeout=30000)
                self._human_delay(1, 2, "Load login")

                page.fill(self.platform.email_selector, email)
                page.fill(self.platform.password_selector, password)
                page.click(self.platform.submit_selector)
                self._human_delay(3, 5, "Wait login")

                url = page.url.lower()
                if any(p in url for p in ["/dashboard", "/home", "/profile"]):
                    self.db.update_status(email, "login_verified")
                    logger.info(f"✅ Recovered: {email}")
                    browser.close()
                    return True
                else:
                    self.db.update_status(email, "recovery_failed")

        except Exception as e:
            logger.error(f"Recovery error for {email}: {e}")

        return False

    # ==================== HELPERS ====================

    @staticmethod
    def _human_delay(min_sec: float = 0.6, max_sec: float = 2.8, desc: str = "") -> None:
        """Random human-like delay."""
        delay = random.uniform(min_sec, max_sec)
        if desc:
            logger.debug(f"⏳ {desc} ({delay:.2f}s)")
        time.sleep(delay)

    @staticmethod
    def _random_scroll(page) -> None:
        """Random scroll simulation."""
        try:
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(200, 600)
                page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                time.sleep(random.uniform(0.3, 0.8))
                if random.random() < 0.3:
                    page.evaluate("window.scrollBy(0, -200)")
        except Exception:
            pass
