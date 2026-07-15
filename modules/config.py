#!/usr/bin/env python3
"""
config.py - Configuration management for Account Farming Bot.
Handles .env parsing, CLI argument overrides, batch config, and platform configs.
"""

import os
import json
import argparse
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# ==================== DATACLASSES ====================

@dataclass
class ProxyConfig:
    enabled: bool = True
    provider: str = "webshare"          # webshare, brightdata, smartproxy, iproyal
    webshare_token: str = ""
    residential_provider: str = ""      # brightdata, smartproxy, iproyal
    residential_token: str = ""
    max_per_ip: int = 3                 # rate limit per IP
    window_seconds: int = 3600          # rate limit window


@dataclass
class EmailConfig:
    use_mail_tm: bool = True
    use_1sec_mail: bool = True
    use_temp_mail: bool = False
    use_guerrilla_mail: bool = False
    default_password: str = "AmanJaya123!@#"
    fallback_domain: str = "domainkamu.my.id"


@dataclass
class BrowserConfig:
    headless: bool = True
    stealth: bool = True
    fingerprint_inject: bool = True
    mouse_simulation: bool = True
    keyboard_simulation: bool = True
    webrtc_block: bool = True
    permissions_random: bool = True
    geo_spoof: bool = True
    canvas_noise: bool = True


@dataclass
class CaptchaConfig:
    capsolver_api_key: str = ""
    enabled: bool = True
    max_solve_time: int = 90            # seconds
    max_poll_attempts: int = 30


@dataclass
class NotificationConfig:
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_enabled: bool = False
    discord_webhook_url: str = ""
    webhook_enabled: bool = False
    webhook_url: str = ""
    ban_rate_threshold: float = 50.0    # percent


@dataclass
class MonitoringConfig:
    screenshot_on_error: bool = True
    screenshot_dir: str = "./screenshots"
    enable_dashboard: bool = True
    dashboard_port: int = 8080
    log_rotation: str = "daily"         # daily, size (MB)
    enable_progress_bar: bool = True


@dataclass
class ExportConfig:
    csv_enabled: bool = True
    excel_enabled: bool = True
    export_dir: str = "./exports"


@dataclass
class BatchConfig:
    enabled: bool = True
    batch_size: int = 10
    batch_delay: int = 60               # seconds between batches


@dataclass
class PlatformConfig:
    name: str = ""
    register_url: str = ""
    category: str = "runway"
    email_selector: str = "input[type='email']"
    password_selector: str = "input[type='password']"
    submit_selector: str = "button[type='submit']"
    success_indicators: List[str] = field(default_factory=list)
    error_indicators: List[str] = field(default_factory=list)
    code_selector: str = ""          # where to type the verification code (code-based verify)
    code_submit_selector: str = ""   # button to confirm the code
    requires_verification: bool = True  # if False, skip email verification entirely


@dataclass
class Config:
    """Master configuration - merges .env, CLI args, and JSON configs."""

    # General
    password_default: str = "AmanJaya123!@#"
    max_workers: int = 5
    jumlah_akun: int = 20
    max_retries: int = 3
    base_retry_delay: float = 5.0
    max_retry_delay: float = 60.0

    # Proxy
    proxy: ProxyConfig = field(default_factory=ProxyConfig)

    # Email
    email: EmailConfig = field(default_factory=EmailConfig)

    # Browser
    browser: BrowserConfig = field(default_factory=BrowserConfig)

    # Captcha
    captcha: CaptchaConfig = field(default_factory=CaptchaConfig)

    # Notification
    notification: NotificationConfig = field(default_factory=NotificationConfig)

    # Monitoring
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Export
    export: ExportConfig = field(default_factory=ExportConfig)

    # Batch
    batch: BatchConfig = field(default_factory=BatchConfig)

    # Target
    target_url: str = "https://target-platform-ai.com/register"
    database_url: str = ""

    # Platform configs
    platforms: List[PlatformConfig] = field(default_factory=list)

    # Shutdown event
    shutdown: bool = False

    # ==================== INIT ====================

    def __post_init__(self):
        """Load .env, CLI overrides, and platform configs."""
        self._load_env()
        self._load_platforms()
        self._ensure_dirs()

    def _load_env(self) -> None:
        """Parse .env file and populate config."""
        load_dotenv()

        def env(key: str, default: str = "") -> str:
            return os.getenv(key, default)

        def env_bool(key: str, default: bool = False) -> bool:
            val = env(key, str(default)).lower()
            return val in ("true", "1", "yes", "y")

        # General
        self.password_default = env("PASSWORD_DEFAULT", self.password_default)
        self.max_workers = int(env("MAX_WORKERS", str(self.max_workers)))
        self.jumlah_akun = int(env("JUMLAH_AKUN", str(self.jumlah_akun)))
        self.max_retries = int(env("MAX_RETRIES", str(self.max_retries)))
        self.base_retry_delay = float(env("BASE_RETRY_DELAY", str(self.base_retry_delay)))
        self.max_retry_delay = float(env("MAX_RETRY_DELAY", str(self.max_retry_delay)))
        self.target_url = env("TARGET_URL", self.target_url)
        self.database_url = env("DATABASE_URL", self.database_url)

        # Proxy
        self.proxy.enabled = env_bool("USE_PROXY_API", self.proxy.enabled)
        self.proxy.provider = env("PROXY_PROVIDER", self.proxy.provider)
        self.proxy.webshare_token = env("WEBSHARE_TOKEN", self.proxy.webshare_token)
        self.proxy.residential_provider = env("RESIDENTIAL_PROXY_PROVIDER", self.proxy.residential_provider)
        self.proxy.residential_token = env("RESIDENTIAL_PROXY_TOKEN", self.proxy.residential_token)
        self.proxy.max_per_ip = int(env("RATE_LIMIT_PER_IP", str(self.proxy.max_per_ip)))
        self.proxy.window_seconds = int(env("RATE_LIMIT_WINDOW", str(self.proxy.window_seconds)))

        # Email
        self.email.use_mail_tm = env_bool("USE_MAIL_TM", self.email.use_mail_tm)
        self.email.use_1sec_mail = env_bool("USE_1SEC_MAIL", self.email.use_1sec_mail)
        self.email.use_temp_mail = env_bool("USE_TEMP_MAIL", self.email.use_temp_mail)
        self.email.use_guerrilla_mail = env_bool("USE_GUERRILLA_MAIL", self.email.use_guerrilla_mail)
        self.email.default_password = env("PASSWORD_DEFAULT", self.email.default_password)
        self.email.fallback_domain = env("FALLBACK_DOMAIN", self.email.fallback_domain)

        # Browser
        self.browser.headless = env_bool("HEADLESS", self.browser.headless)
        self.browser.stealth = env_bool("USE_STEALTH", self.browser.stealth)
        self.browser.fingerprint_inject = env_bool("INJECT_FINGERPRINT", self.browser.fingerprint_inject)
        self.browser.mouse_simulation = env_bool("MOUSE_SIMULATION", self.browser.mouse_simulation)
        self.browser.keyboard_simulation = env_bool("KEYBOARD_SIMULATION", self.browser.keyboard_simulation)
        self.browser.webrtc_block = env_bool("WEBRTC_BLOCK", self.browser.webrtc_block)
        self.browser.permissions_random = env_bool("PERMISSIONS_RANDOM", self.browser.permissions_random)
        self.browser.geo_spoof = env_bool("GEO_SPOOF", self.browser.geo_spoof)
        self.browser.canvas_noise = env_bool("CANVAS_NOISE", self.browser.canvas_noise)

        # Captcha
        self.captcha.capsolver_api_key = env("CAPSOLVER_API_KEY", self.captcha.capsolver_api_key)
        self.captcha.enabled = env_bool("USE_CAPTCHA", self.captcha.enabled)
        self.captcha.max_solve_time = int(env("CAPTCHA_MAX_TIME", str(self.captcha.max_solve_time)))

        # Notification
        self.notification.telegram_enabled = env_bool("NOTIFY_TELEGRAM", self.notification.telegram_enabled)
        self.notification.telegram_bot_token = env("TELEGRAM_BOT_TOKEN", self.notification.telegram_bot_token)
        self.notification.telegram_chat_id = env("TELEGRAM_CHAT_ID", self.notification.telegram_chat_id)
        self.notification.discord_enabled = env_bool("NOTIFY_DISCORD", self.notification.discord_enabled)
        self.notification.discord_webhook_url = env("DISCORD_WEBHOOK_URL", self.notification.discord_webhook_url)
        self.notification.webhook_enabled = env_bool("WEBHOOK_ENABLED", self.notification.webhook_enabled)
        self.notification.webhook_url = env("WEBHOOK_URL", self.notification.webhook_url)
        self.notification.ban_rate_threshold = float(env("BAN_RATE_THRESHOLD", str(self.notification.ban_rate_threshold)))

        # Monitoring
        self.monitoring.screenshot_on_error = env_bool("SCREENSHOT_ON_ERROR", self.monitoring.screenshot_on_error)
        self.monitoring.screenshot_dir = env("SCREENSHOT_DIR", self.monitoring.screenshot_dir)
        self.monitoring.enable_dashboard = env_bool("ENABLE_DASHBOARD", self.monitoring.enable_dashboard)
        self.monitoring.dashboard_port = int(env("DASHBOARD_PORT", str(self.monitoring.dashboard_port)))
        self.monitoring.log_rotation = env("LOG_ROTATION", self.monitoring.log_rotation)
        self.monitoring.enable_progress_bar = env_bool("ENABLE_PROGRESS_BAR", self.monitoring.enable_progress_bar)

        # Export
        self.export.csv_enabled = env_bool("EXPORT_CSV", self.export.csv_enabled)
        self.export.excel_enabled = env_bool("EXPORT_EXCEL", self.export.excel_enabled)
        self.export.export_dir = env("EXPORT_DIR", self.export.export_dir)

        # Batch
        self.batch.enabled = env_bool("ENABLE_BATCH", self.batch.enabled)
        self.batch.batch_size = int(env("BATCH_SIZE", str(self.batch.batch_size)))
        self.batch.batch_delay = int(env("BATCH_DELAY", str(self.batch.batch_delay)))

    def _load_platforms(self) -> None:
        """Load platform configs from JSON file."""
        platforms_path = Path(__file__).parent.parent / "config" / "platforms.json"
        if platforms_path.exists():
            try:
                with open(platforms_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for p in data.get("platforms", []):
                    platform = PlatformConfig(
                        name=p.get("name", ""),
                        register_url=p.get("register_url", ""),
                        category=p.get("category", "runway"),
                        email_selector=p.get("email_selector", "input[type='email']"),
                        password_selector=p.get("password_selector", "input[type='password']"),
                        submit_selector=p.get("submit_selector", "button[type='submit']"),
                        success_indicators=p.get("success_indicators", []),
                        error_indicators=p.get("error_indicators", []),
                        code_selector=p.get("code_selector", ""),
                        code_submit_selector=p.get("code_submit_selector", ""),
                        requires_verification=p.get("requires_verification", True),
                    )
                    self.platforms.append(platform)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to load platforms.json: {e}")

    def _ensure_dirs(self) -> None:
        """Create required directories."""
        for d in [
            self.monitoring.screenshot_dir,
            self.export.export_dir,
            Path("./config"),
        ]:
            Path(d).mkdir(parents=True, exist_ok=True)

    # ==================== VALIDATION ====================

    def validate(self, logger: logging.Logger) -> bool:
        """Validate critical config values at startup."""
        errors = []

        if not self.database_url:
            errors.append("DATABASE_URL is required")

        if not self.target_url:
            errors.append("TARGET_URL is required")

        if not self.target_url.startswith(("http://", "https://")):
            errors.append("TARGET_URL must be a valid URL")

        if self.proxy.enabled and not self.proxy.webshare_token:
            errors.append("WEBSHARE_TOKEN is required when proxy is enabled")

        if self.captcha.enabled and not self.captcha.capsolver_api_key:
            logger.warning("⚠️ CAPTCHA is enabled but CAPSOLVER_API_KEY is empty — CAPTCHA solving will be skipped")

        if errors:
            for err in errors:
                logger.error(f"❌ Config error: {err}")
            return False

        logger.info("✅ Config validation passed")
        return True

    # ==================== PLATFORM HELPER ====================

    def get_platform(self, name: str = "") -> Optional[PlatformConfig]:
        """Get platform config by name, or return the first one, or build from global config."""
        if not name:
            name = getattr(self, "active_platform_name", "")
        if self.platforms:
            if name:
                for p in self.platforms:
                    if p.name.lower() == name.lower():
                        return p
            return self.platforms[0]

        # Fallback: build from global config
        return PlatformConfig(
            name="default",
            register_url=self.target_url,
            category="runway",
            requires_verification=True,
            success_indicators=[
                "verify", "verifikasi", "confirm", "konfirmasi",
                "check your email", "cek email", "welcome", "selamat datang",
                "success", "berhasil", "registered", "terdaftar",
            ],
            error_indicators=[
                "already exists", "sudah terdaftar", "already registered",
                "email taken", "email digunakan", "duplicate",
                "captcha failed", "rate limit", "terlalu banyak",
                "invalid email", "email tidak valid", "blocked", "diblokir",
            ],
        )

    # ==================== CLI OVERRIDES ====================

    def apply_cli_overrides(self, args: argparse.Namespace) -> None:
        """Override config with CLI arguments."""
        if args.workers:
            self.max_workers = args.workers
        if args.jumlah:
            self.jumlah_akun = args.jumlah
        if args.retries:
            self.max_retries = args.retries
        if args.target:
            self.target_url = args.target
        if args.platform:
            # Switch to a different platform (uses its full config: selectors, verification, etc.)
            self.active_platform_name = args.platform
            platform = self.get_platform(args.platform)
            if platform and platform.register_url:
                self.target_url = platform.register_url
        if args.headless is not None:
            self.browser.headless = args.headless
        if args.no_dashboard:
            self.monitoring.enable_dashboard = False
        if args.batch_size:
            self.batch.batch_size = args.batch_size
        if args.batch_delay:
            self.batch.batch_delay = args.batch_delay

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        """Build CLI argument parser."""
        parser = argparse.ArgumentParser(description="Account Farming Bot - Automated Account Registration")
        parser.add_argument("-w", "--workers", type=int, help="Number of parallel workers")
        parser.add_argument("-n", "--jumlah", type=int, help="Number of accounts to create")
        parser.add_argument("-r", "--retries", type=int, help="Max retry attempts per account")
        parser.add_argument("-t", "--target", type=str, help="Target registration URL")
        parser.add_argument("-p", "--platform", type=str, help="Platform name from platforms.json")
        parser.add_argument("--headless/--no-headless", dest="headless", help="Run browser in headless mode")
        parser.add_argument("--no-dashboard", action="store_true", help="Disable web dashboard")
        parser.add_argument("--batch-size", type=int, help="Override batch size")
        parser.add_argument("--batch-delay", type=int, help="Override batch delay in seconds")
        parser.add_argument("--recovery", action="store_true", help="Run account recovery mode")
        parser.add_argument("--export-only", action="store_true", help="Only export existing accounts, don't farm")
        return parser
