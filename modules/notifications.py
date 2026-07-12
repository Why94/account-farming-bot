#!/usr/bin/env python3
"""
notifications.py - Multi-channel notification system.
Supports: Telegram Bot, Discord Webhook, generic HTTP Webhook.
"""

import json
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class Notifier:
    """Sends notifications via Telegram, Discord, and custom webhooks."""

    def __init__(self, config):
        self.config = config

    # ==================== TELEGRAM ====================

    def send_telegram(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message via Telegram Bot API."""
        if not self.config.telegram_enabled:
            return False

        if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
            logger.debug("Telegram not configured")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.config.telegram_chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.debug(f"✅ Telegram notification sent")
                return True
            else:
                logger.warning(f"❌ Telegram send failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.warning(f"Telegram error: {e}")
            return False

    # ==================== DISCORD ====================

    def send_discord(self, message: str, username: str = "Farming Bot") -> bool:
        """Send message via Discord Webhook."""
        if not self.config.discord_enabled:
            return False

        if not self.config.discord_webhook_url:
            logger.debug("Discord webhook not configured")
            return False

        try:
            payload = {
                "content": message,
                "username": username,
            }
            resp = requests.post(self.config.discord_webhook_url, json=payload, timeout=10)
            if resp.status_code == 204:
                logger.debug(f"✅ Discord notification sent")
                return True
            else:
                logger.warning(f"❌ Discord send failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.warning(f"Discord error: {e}")
            return False

    # ==================== GENERIC WEBHOOK (feature #30) ====================

    def send_webhook(self, data: dict) -> bool:
        """Send data to a generic webhook endpoint."""
        if not self.config.webhook_enabled:
            return False

        if not self.config.webhook_url:
            logger.debug("Webhook URL not configured")
            return False

        try:
            resp = requests.post(
                self.config.webhook_url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if resp.status_code in [200, 201, 204]:
                logger.debug(f"✅ Webhook sent successfully")
                return True
            else:
                logger.warning(f"❌ Webhook failed: {resp.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Webhook error: {e}")
            return False

    # ==================== NOTIFICATION FORMATTERS ====================

    def notify_account_created(self, email: str, status: str, proxy: str = "") -> None:
        """Notify when a new account is created."""
        emoji = "✅" if status in ("verified", "registered", "login_verified") else "❌"
        message = f"{emoji} <b>Account {status.upper()}</b>\n📧 {email}\n🌐 {proxy or 'No proxy'}"

        self.send_telegram(message)

        # Also send webhook if enabled
        if self.config.webhook_enabled:
            self.send_webhook({
                "event": "account_created",
                "email": email,
                "status": status,
                "proxy": proxy,
            })

    def notify_batch_complete(self, stats: dict) -> None:
        """Notify when a batch of accounts is completed."""
        msg = (
            f"📊 <b>Batch Complete</b>\n"
            f"Total: {stats.get('total', 0)}\n"
            f"Sukses: {stats.get('success', 0)}\n"
            f"Verified: {stats.get('verified', 0)}\n"
            f"Gagal: {stats.get('failed', 0)}\n"
            f"Success Rate: {stats.get('success_rate', 0)}%"
        )
        self.send_telegram(msg)
        self.send_discord(msg)

    def notify_full_run_complete(self, stats: dict) -> None:
        """Notify when all farming is complete."""
        msg = (
            f"🎉 <b>Farming Selesai!</b>\n"
            f"Total Akun: {stats.get('total', 0)}\n"
            f"✅ Sukses: {stats.get('success', 0)}\n"
            f"🔒 Verified: {stats.get('verified', 0)}\n"
            f"❌ Gagal: {stats.get('failed', 0)}\n"
            f"📈 Success Rate: {stats.get('success_rate', 0)}%\n"
            f"⏱️ Waktu: {stats.get('elapsed_minutes', 0)} menit"
        )
        self.send_telegram(msg)
        self.send_discord(msg)

        if self.config.webhook_enabled:
            self.send_webhook(stats)

    # ==================== BAN RATE ALERT (feature #20) ====================

    def check_ban_rate(self, total: int, failed: int) -> bool:
        """Check if ban rate exceeds threshold and send alert."""
        if total == 0:
            return False

        ban_rate = failed / total * 100
        threshold = self.config.ban_rate_threshold

        if ban_rate >= threshold:
            msg = (
                f"🚨 <b>PERINGATAN BAN RATE TINGGI!</b>\n"
                f"Ban Rate: {ban_rate:.1f}%\n"
                f"Threshold: {threshold}%\n"
                f"Gagal: {failed}/{total}\n"
                f"<i>Recommended: Switch proxy provider, increase delay, or review selectors</i>"
            )
            self.send_telegram(msg)
            self.send_discord(msg)

            if self.config.webhook_enabled:
                self.send_webhook({
                    "event": "ban_rate_alert",
                    "ban_rate": round(ban_rate, 1),
                    "threshold": threshold,
                    "failed": failed,
                    "total": total,
                })
            return True

        return False
