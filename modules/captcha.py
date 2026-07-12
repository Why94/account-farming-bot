#!/usr/bin/env python3
"""
captcha.py - CAPTCHA solving via CapSolver API.
Supports: reCAPTCHA v2/v3, hCaptcha, Cloudflare Turnstile.
"""

import json
import time
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class CaptchaSolver:
    """Solves CAPTCHAs using CapSolver API service."""

    def __init__(self, config):
        self.config = config

    def solve(self, page, target_url: str = "") -> bool:
        """Detect and solve any CAPTCHA on the page. Returns True if solved or no CAPTCHA."""
        if not self.config.enabled:
            return True

        if not self.config.capsolver_api_key:
            logger.warning("⚠️ CAPSOLVER_API_KEY kosong, skip CAPTCHA solving")
            return False

        # Detect CAPTCHA presence
        has_captcha = page.evaluate(
            "() => !!document.querySelector('[data-sitekey], [data-turnstile], .g-recaptcha, .h-captcha, .cf-turnstile')"
        )

        if not has_captcha:
            return True  # No CAPTCHA to solve

        logger.info("🔄 CAPTCHA terdeteksi, menyelesaikan...")

        # Detect CAPTCHA type
        captcha_type = page.evaluate("""
            () => {
                const recaptcha = document.querySelector('.g-recaptcha, [data-sitekey]');
                const hcaptcha = document.querySelector('.h-captcha');
                const turnstile = document.querySelector('.cf-turnstile, [data-turnstile]');
                if (recaptcha) return 'recaptcha';
                if (hcaptcha) return 'hcaptcha';
                if (turnstile) return 'turnstile';
                return 'unknown';
            }
        """)

        # Map type to CapSolver task type
        task_types = {
            'recaptcha': 'ReCaptchaV2TaskProxyLess',
            'hcaptcha': 'HCaptchaTaskProxyLess',
            'turnstile': 'TurnstileTaskProxyLess',
        }

        task_type = task_types.get(captcha_type, 'ReCaptchaV2TaskProxyLess')
        logger.info(f"📋 CAPTCHA type: {captcha_type}")

        # Create task
        payload = {
            "clientKey": self.config.capsolver_api_key,
            "task": {
                "type": task_type,
                "websiteURL": target_url or page.url,
                "websiteKey": "auto_detect"
            }
        }

        try:
            res = requests.post(
                "https://api.capsolver.com/createTask",
                json=payload,
                timeout=20
            )
            task_id = res.json().get("taskId")
            if not task_id:
                logger.error(f"CapSolver createTask failed: {res.text}")
                return False

            logger.info(f"⏳ Waiting for CAPTCHA solution (task: {task_id[:8]}...)")

            # Poll for result
            for attempt in range(self.config.max_poll_attempts):
                if self._shutdown_requested():
                    return False

                time.sleep(3)

                result = requests.post(
                    "https://api.capsolver.com/getTaskResult",
                    json={"clientKey": self.config.capsolver_api_key, "taskId": task_id},
                    timeout=20
                ).json()

                status = result.get("status")
                if status == "ready":
                    solution = result.get("solution", {})
                    token = (
                        solution.get("token")
                        or solution.get("gRecaptchaResponse")
                        or solution.get("response")
                    )
                    if not token:
                        logger.error("CapSolver returned no token")
                        return False

                    # Inject token into page
                    self._inject_token(page, token)
                    logger.info(f"✅ {captcha_type} CAPTCHA berhasil diselesaikan")
                    return True

                elif status == "failed":
                    logger.error(f"CapSolver task failed: {result.get('error') or result}")
                    return False

            logger.error(f"⏰ CAPTCHA solve timeout after {self.config.max_poll_attempts} attempts")
            return False

        except Exception as e:
            logger.warning(f"CAPTCHA solving error: {e}")
            return False

    def _inject_token(self, page, token: str) -> None:
        """Inject CAPTCHA token into the appropriate form field."""
        token_js = json.dumps(token)  # Safe JS string escaping

        page.evaluate(f"""
            () => {{
                const selectors = [
                    'textarea[name="g-recaptcha-response"]',
                    'input[name="g-recaptcha-response"]',
                    'textarea[name="h-captcha-response"]',
                    'input[name="h-captcha-response"]',
                    'input[name="cf-turnstile-response"]',
                    'textarea[name="cf-turnstile-response"]'
                ];
                selectors.forEach(sel => {{
                    const el = document.querySelector(sel);
                    if (el) el.value = {token_js};
                }});
            }}
        """)

    @staticmethod
    def _shutdown_requested() -> bool:
        """Check if shutdown was requested (global check)."""
        try:
            import sys
            from modules.monitoring import _shutdown_event
            return _shutdown_event.is_set() if '_shutdown_event' in dir(sys.modules.get('modules.monitoring')) else False
        except Exception:
            return False
