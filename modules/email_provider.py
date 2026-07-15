#!/usr/bin/env python3
"""
email_provider.py - Multi-email provider management.
Supports: Mail.tm, 1sec-mail (free, no API key), temp-mail, guerrilla mail.
"""

import random
import string
import time
import logging
import re
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class EmailManager:
    """Manages temporary email account creation and verification across multiple providers."""

    def __init__(self, config):
        self.config = config
        self._mail_tm_domain = None

    # ==================== CREATE ====================

    def get_mail_tm_domain(self) -> str:
        """Return an active Mail.tm domain (fetched from API, cached).

        Mail.tm rotates its free domains, so hardcoding @mail.tm breaks
        account creation. We fetch the currently active domain instead.
        """
        if self._mail_tm_domain:
            return self._mail_tm_domain
        try:
            resp = requests.get("https://api.mail.tm/domains", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("hydra:member", data.get("member", []))
                for d in items:
                    if d.get("isActive"):
                        self._mail_tm_domain = d.get("domain")
                        return self._mail_tm_domain
        except Exception as e:
            logger.debug(f"Mail.tm domain fetch failed: {e}")
        self._mail_tm_domain = "mail.tm"
        return self._mail_tm_domain

    def get_email(self) -> Tuple[Optional[str], Optional[str]]:
        """Get a temporary email: tries providers in priority order. Returns (email, password)."""
        # 1. Mail.tm
        if self.config.use_mail_tm:
            email, password = self._create_mail_tm()
            if email:
                return email, password

        # 2. 1sec-mail (no API key needed)
        if self.config.use_1sec_mail:
            email, password = self._create_1sec_mail()
            if email:
                return email, password

        # 3. Temp-mail
        if self.config.use_temp_mail:
            email, password = self._create_temp_mail()
            if email:
                return email, password

        # 4. Guerrilla mail
        if self.config.use_guerrilla_mail:
            email, password = self._create_guerrilla_mail()
            if email:
                return email, password

        # Fallback to catch-all domain
        return self._generate_fallback_email(), self.config.default_password

    def _generate_fallback_email(self) -> str:
        """Generate fallback email from catch-all domain."""
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return f"ai_user_{random_str}@{self.config.fallback_domain}"

    # ==================== MAIL.TM ====================

    def _create_mail_tm(self) -> Tuple[Optional[str], Optional[str]]:
        """Create temporary email via Mail.tm API."""
        try:
            domain = self.get_mail_tm_domain()
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            email = f"farm{random_str}@{domain}"
            resp = requests.post(
                "https://api.mail.tm/accounts",
                json={"address": email, "password": self.config.default_password},
                timeout=10
            )
            if resp.status_code in [201, 200]:
                logger.info(f"✅ Mail.tm created: {email}")
                return email, self.config.default_password
            else:
                logger.debug(f"Mail.tm creation returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.debug(f"Mail.tm creation failed: {e}")
        return None, None

    def _get_mail_tm_token(self, email: str) -> Optional[str]:
        """Get auth token for Mail.tm account."""
        try:
            resp = requests.post(
                "https://api.mail.tm/token",
                json={"address": email, "password": self.config.default_password},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json().get("token")
        except Exception as e:
            logger.debug(f"Mail.tm token error: {e}")
        return None

    def check_mail_tm_inbox(self, email: str, token: str, timeout: int = 120,
                            poll_interval: int = 5) -> Optional[str]:
        """Check Mail.tm inbox for verification link."""
        headers = {"Authorization": f"Bearer {token}"}
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                resp = requests.get("https://api.mail.tm/messages", headers=headers, timeout=10)
                if resp.status_code == 200:
                    messages = resp.json().get("hydra:member", [])
                    for msg in messages:
                        subject = msg.get("subject", "").lower()
                        text = msg.get("text", "").lower()
                        html = msg.get("html", "").lower()

                        if any(kw in subject or kw in text or kw in html for kw in
                               ["verify", "verifikasi", "confirm", "konfirmasi", "activate", "aktivasi"]):
                            links = re.findall(r'https?://[^\s"\'<>]+',
                                               msg.get("html", "") + " " + msg.get("text", ""))
                            for link in links:
                                if any(kw in link.lower() for kw in
                                       ["verify", "confirm", "activate", "verifikasi", "konfirmasi"]):
                                    logger.info(f"✅ Verification link found for {email}")
                                    return link
            except Exception as e:
                logger.debug(f"Inbox check error: {e}")

            from time import sleep
            sleep(poll_interval)

        logger.warning(f"⏰ Verification email timeout for {email}")
        return None

    # ==================== 1SEC-MAIL (feature #31, free no API key) ====================

    def _create_1sec_mail(self) -> Tuple[Optional[str], Optional[str]]:
        """Create temporary email via 1sec-mail API (no API key needed)."""
        try:
            # Get available domains
            resp = requests.get("https://www.1sec-mail.com/api/v1/?action=getDomainList", timeout=10)
            if resp.status_code == 200:
                domains = resp.json()
                if domains:
                    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                    domain = random.choice(domains)
                    email = f"{random_str}@{domain}"
                    password = self.config.default_password
                    logger.info(f"✅ 1sec-mail created: {email}")
                    return email, password
        except Exception as e:
            logger.debug(f"1sec-mail creation failed: {e}")
        return None, None

    def check_1sec_inbox(self, email: str, timeout: int = 120, poll_interval: int = 5) -> Optional[str]:
        """Check 1sec-mail inbox for verification link."""
        parts = email.split("@")
        if len(parts) != 2:
            return None

        login, domain = parts
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                resp = requests.get(
                    f"https://www.1sec-mail.com/api/v1/?action=getMessages&login={login}&domain={domain}",
                    timeout=10
                )
                if resp.status_code == 200:
                    messages = resp.json()
                    for msg in messages:
                        text = msg.get("textBody", "") + msg.get("htmlBody", "")
                        if any(kw in text.lower() for kw in ["verify", "confirm", "activate"]):
                            links = re.findall(r'https?://[^\s"\'<>]+', text)
                            for link in links:
                                if any(kw in link.lower() for kw in ["verify", "confirm", "activate"]):
                                    logger.info(f"✅ Verification link found (1sec-mail) for {email}")
                                    return link
            except Exception as e:
                logger.debug(f"1sec-mail inbox check error: {e}")

            time.sleep(poll_interval)

        logger.warning(f"⏰ 1sec-mail verification timeout for {email}")
        return None

    # ==================== TEMP-MAIL ====================

    def _create_temp_mail(self) -> Tuple[Optional[str], Optional[str]]:
        """Create temporary email via temp-mail.org API."""
        try:
            resp = requests.get("https://www.temp-mail.org/api/v3/email/", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("email", "")
                if email:
                    password = self.config.default_password
                    logger.info(f"✅ Temp-mail created: {email}")
                    return email, password
        except Exception as e:
            logger.debug(f"Temp-mail creation failed: {e}")
        return None, None

    def check_temp_mail_inbox(self, email: str, timeout: int = 120, poll_interval: int = 5) -> Optional[str]:
        """Check temp-mail.org inbox for verification link."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                resp = requests.get(
                    f"https://www.temp-mail.org/api/v3/email/{email}/inbox/",
                    timeout=10
                )
                if resp.status_code == 200:
                    messages = resp.json()
                    for msg in messages:
                        text = msg.get("body", "")
                        if any(kw in text.lower() for kw in ["verify", "confirm", "activate"]):
                            links = re.findall(r'https?://[^\s"\'<>]+', text)
                            for link in links:
                                if any(kw in link.lower() for kw in ["verify", "confirm", "activate"]):
                                    logger.info(f"✅ Verification link found (temp-mail) for {email}")
                                    return link
            except Exception as e:
                logger.debug(f"temp-mail inbox check error: {e}")
            time.sleep(poll_interval)

        logger.warning(f"⏰ temp-mail verification timeout for {email}")
        return None

    # ==================== GUERRILLA MAIL ====================

    def _create_guerrilla_mail(self) -> Tuple[Optional[str], Optional[str]]:
        """Create temporary email via guerrillamail.com API."""
        try:
            random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
            domains = ["guerrillamail.com", "guerrillamail.net", "guerrillamail.biz"]
            domain = random.choice(domains)
            email = f"{random_str}@{domain}"

            # Guerrilla mail doesn't need password
            logger.info(f"✅ Guerrilla mail created: {email}")
            return email, ""
        except Exception as e:
            logger.debug(f"Guerrilla mail creation failed: {e}")
        return None, None

    def check_guerrilla_inbox(self, email: str, timeout: int = 120, poll_interval: int = 5) -> Optional[str]:
        """Check guerrilla mail inbox for verification link."""
        import urllib.request

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                req = urllib.request.Request(
                    f"http://www.guerrillamail.com/email/inbox.json?q={email}"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    import json
                    data = json.loads(resp.read().decode())
                    for msg in data:
                        body = msg.get("email_text", "") + msg.get("email_html", "")
                        if any(kw in body.lower() for kw in ["verify", "confirm", "activate"]):
                            import re
                            links = re.findall(r'https?://[^\s"\'<>]+', body)
                            for link in links:
                                if any(kw in link.lower() for kw in ["verify", "confirm", "activate"]):
                                    logger.info(f"✅ Verification link found (guerrilla) for {email}")
                                    return link
            except Exception as e:
                logger.debug(f"Guerrilla inbox check error: {e}")
            time.sleep(poll_interval)

        logger.warning(f"⏰ Guerrilla mail verification timeout for {email}")
        return None

    # ==================== DISPATCHER ====================

    def check_inbox(self, email: str, password: str, timeout: int = 120,
                    poll_interval: int = 5) -> Optional[str]:
        """Auto-detect provider and check inbox for verification link."""
        if email.endswith("@" + self.get_mail_tm_domain()):
            token = self._get_mail_tm_token(email)
            if token:
                return self.check_mail_tm_inbox(email, token, timeout, poll_interval)
        elif "@1sec-mail.com" in email or any(x in email for x in ["@1sec-mail.com"]):
            return self.check_1sec_inbox(email, timeout, poll_interval)
        else:
            # Try 1sec-mail first for any domain
            return self.check_1sec_inbox(email, timeout, poll_interval)

        # Fallback: also try mail.tm
        if self.config.use_mail_tm:
            token = self._get_mail_tm_token(email)
            if token:
                return self.check_mail_tm_inbox(email, token, timeout, poll_interval)

        return None

    # ==================== CODE EXTRACTION (code-based verify) ====================

    @staticmethod
    def _extract_code(text: str) -> Optional[str]:
        """Extract a numeric verification code from email text.

        Prefers a code that appears right after keywords like 'code'/'kode'/
        'verification', then falls back to a standalone 6-digit / 4-8-digit number.
        """
        if not text:
            return None
        low = text.lower()
        patterns = [
            r'(?:code|kode|verification|verifikasi|pin|otp)[^\d\n]{0,25}?(\d{4,8})',
            r'(\d{6})',
            r'(\d{4,8})',
        ]
        for pat in patterns:
            m = re.search(pat, low, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    def get_verification_code(self, email: str, password: str,
                              timeout: int = 120, poll_interval: int = 5) -> Optional[str]:
        """Poll inbox and return a numeric verification code (Kling-style).

        Code-based verification: the platform emails a code that the user must
        type into a field on the registration page (instead of clicking a link).
        """
        domain = email.split("@")[-1]
        if domain == self.get_mail_tm_domain():
            token = self._get_mail_tm_token(email)
            if token:
                return self._poll_mail_tm_code(email, token, timeout, poll_interval)
        elif "1sec-mail" in domain:
            return self._poll_1sec_code(email, timeout, poll_interval)
        return None

    def _poll_mail_tm_code(self, email: str, token: str, timeout: int, poll_interval: int) -> Optional[str]:
        headers = {"Authorization": f"Bearer {token}"}
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get("https://api.mail.tm/messages", headers=headers, timeout=10)
                if resp.status_code == 200:
                    for msg in resp.json().get("hydra:member", []):
                        blob = (msg.get("subject", "") + " " +
                                msg.get("text", "") + " " + msg.get("html", ""))
                        code = self._extract_code(blob)
                        if code:
                            logger.info(f"✅ Verification code found for {email}: {code}")
                            return code
            except Exception as e:
                logger.debug(f"Mail.tm code poll error: {e}")
            time.sleep(poll_interval)
        logger.warning(f"⏰ Verification code timeout for {email}")
        return None

    def _poll_1sec_code(self, email: str, timeout: int, poll_interval: int) -> Optional[str]:
        parts = email.split("@")
        if len(parts) != 2:
            return None
        login, domain = parts
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(
                    f"https://www.1sec-mail.com/api/v1/?action=getMessages&login={login}&domain={domain}",
                    timeout=10)
                if resp.status_code == 200:
                    for msg in resp.json():
                        blob = msg.get("textBody", "") + " " + msg.get("htmlBody", "")
                        code = self._extract_code(blob)
                        if code:
                            logger.info(f"✅ Verification code found (1sec-mail) for {email}: {code}")
                            return code
            except Exception as e:
                logger.debug(f"1sec-mail code poll error: {e}")
            time.sleep(poll_interval)
        logger.warning(f"⏰ 1sec-mail verification code timeout for {email}")
        return None
