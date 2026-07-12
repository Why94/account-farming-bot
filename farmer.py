#!/usr/bin/env python3
"""
farmer.py - Account Farming Bot v2.0
Main entry point & orchestrator. All logic is in modules/.

Usage:
    python farmer.py                        # Default run
    python farmer.py -n 50 -w 10            # 50 accounts, 10 workers
    python farmer.py --recovery              # Recover stuck accounts
    python farmer.py --export-only           # Only export existing accounts
    python farmer.py --no-dashboard          # Disable web dashboard
    python farmer.py -p runway               # Use specific platform
"""

import os
import sys
import time
import signal
import logging
import argparse
import threading
from typing import Optional

# ==================== IMPORTS ====================
from modules.config import Config
from modules.database import DatabaseManager
from modules.proxy import ProxyManager
from modules.email_provider import EmailManager
from modules.captcha import CaptchaSolver
from modules.browser import BrowserManager
from modules.farming import Farmer, FarmingQueue
from modules.monitoring import (
    setup_logging, ProgressTracker, MetricsCollector, take_screenshot,
    is_shutting_down, trigger_shutdown
)
from modules.notifications import Notifier
from modules.export import ExportManager
from modules.server.dashboard import create_dashboard, set_dashboard_state

# ==================== GLOBALS ====================
_shutdown_event = threading.Event()
_dashboard_task: Optional[threading.Thread] = None


def signal_handler(signum, frame):
    """Graceful shutdown on SIGINT/SIGTERM."""
    logging.getLogger(__name__).warning(f"⚠️ Signal {signum} received, shutting down...")
    trigger_shutdown()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ==================== MAIN ====================

def main():
    """Main orchestrator."""
    # 1. Parse config
    config = Config()
    parser = Config.build_parser()
    args = parser.parse_args()
    config.apply_cli_overrides(args)

    # 2. Setup logging
    logger = setup_logging(config)
    logger.info("=" * 60)
    logger.info("  ACCOUNT FARMING BOT v2.0")
    logger.info("=" * 60)
    logger.info(f"Workers: {config.max_workers} | Accounts: {config.jumlah_akun} | Retries: {config.max_retries}")

    # 3. Validate config
    if not config.validate(logger):
        logger.error("❌ Config validation failed, exiting")
        sys.exit(1)

    # 4. Determine mode
    if args.export_only:
        run_export_only(config, logger)
        return

    if args.recovery:
        run_recovery(config, logger)
        return

    # 5. Check incremental farming (feature #28)
    existing = 0
    db = DatabaseManager(config.database_url, config.max_workers)
    if db.init_pool():
        existing = db.get_incremental_start()
        if existing > 0:
            logger.info(f"📊 Found {existing} existing accounts — incremental farming mode")
            remaining = config.jumlah_akun - existing
            if remaining > 0:
                config.jumlah_akun = remaining
                logger.info(f"   Adjusting: farming {remaining} more accounts")
            else:
                logger.info("   All accounts already exist — nothing to farm")
                run_export_only(config, logger)
                db.close()
                return
    else:
        logger.error("❌ Database connection failed. Check DATABASE_URL in .env")
        sys.exit(1)

    # 6. Initialize all modules
    proxy_mgr = ProxyManager(config.proxy)
    email_mgr = EmailManager(config.email)
    captcha_solver = CaptchaSolver(config.captcha)
    browser_mgr = BrowserManager(config)
    progress = ProgressTracker(config.jumlah_akun, config.monitoring.enable_progress_bar)
    metrics = MetricsCollector()
    notifier = Notifier(config.notification)
    export_mgr = ExportManager(config.export)

    # 7. Pre-fetch proxies
    if config.proxy.enabled:
        logger.info("🔄 Fetching and testing proxies...")
        healthy = proxy_mgr.fetch_proxies()
        if healthy:
            proxy_mgr.test_all_proxies()
            healthy_count = sum(1 for p in proxy_mgr._cache if p.healthy)
            logger.info(f"✅ {healthy_count}/{len(proxy_mgr._cache)} proxies healthy")
        else:
            logger.warning("⚠️ No proxies available, will proceed without proxy")

    # 8. Start dashboard (feature #11)
    dashboard_thread = None
    if config.monitoring.enable_dashboard:
        dashboard_thread = start_dashboard(config, db, metrics, progress, logger)

    # 9. Start farming
    farmer = Farmer(
        config=config,
        db=db,
        proxy=proxy_mgr,
        email_mgr=email_mgr,
        captcha=captcha_solver,
        browser_mgr=browser_mgr,
        notifier=notifier,
        progress=progress,
        metrics=metrics,
    )

    start_time = time.time()
    stats = farmer.farm_accounts(config.jumlah_akun)
    total_time = time.time() - start_time

    # 10. Update dashboard with final stats
    final_stats = {**stats, "elapsed_minutes": round(total_time / 60, 1)}
    set_dashboard_state("stats", final_stats)
    set_dashboard_state("running", False)

    # 11. Export results (feature #16)
    if config.export.csv_enabled or config.export.excel_enabled:
        export_accounts_to_file(config, db, export_mgr, logger)

    # 12. Export metrics (feature #19)
    metrics_file = metrics.export_metrics()

    # 13. Shutdown dashboard
    if dashboard_thread and dashboard_thread.is_alive():
        dashboard_thread.join(timeout=3)

    # 14. Cleanup
    db.close()

    # 15. Final report
    logger.info("=" * 60)
    logger.info("  📊 FINAL REPORT")
    logger.info("=" * 60)
    logger.info(f"Total Time:     {total_time/60:.1f} minutes")
    logger.info(f"Total Accounts: {config.jumlah_akun}")
    logger.info(f"Success:        {stats.get('success', 0)}")
    logger.info(f"Verified:       {stats.get('verified', 0)}")
    logger.info(f"Failed:         {stats.get('failed', 0)}")
    logger.info(f"Success Rate:   {stats.get('success_rate', 0)}%")
    logger.info(f"Ban Rate:       {stats.get('ban_rate', 0)}%")
    logger.info(f"Rate/Hour:      {stats.get('rate_per_hour', 0)}")
    if metrics_file:
        logger.info(f"Metrics:        {metrics_file}")
    logger.info("=" * 60)

    # 16. Trigger ban rate alert
    notifier.check_ban_rate(config.jumlah_akun, stats.get("failed", 0))


# ==================== MODES ====================

def run_export_only(config: Config, logger: logging.Logger) -> None:
    """Only export existing accounts to CSV/Excel."""
    db = DatabaseManager(config.database_url, config.max_workers)
    if not db.init_pool():
        logger.error("❌ Database connection failed")
        sys.exit(1)

    export_mgr = ExportManager(config.export)
    export_accounts_to_file(config, db, export_mgr, logger)
    db.close()


def run_recovery(config: Config, logger: logging.Logger) -> None:
    """Recovery mode — retry stuck accounts."""
    db = DatabaseManager(config.database_url, config.max_workers)
    if not db.init_pool():
        logger.error("❌ Database connection failed")
        sys.exit(1)

    proxy_mgr = ProxyManager(config.proxy)
    email_mgr = EmailManager(config.email)
    captcha_solver = CaptchaSolver(config.captcha)
    browser_mgr = BrowserManager(config)
    notifier = Notifier(config.notification)
    progress = ProgressTracker(0)
    metrics = MetricsCollector()

    farmer = Farmer(
        config=config, db=db, proxy=proxy_mgr, email_mgr=email_mgr,
        captcha=captcha_solver, browser_mgr=browser_mgr, notifier=notifier,
        progress=progress, metrics=metrics,
    )

    recovered = farmer.run_recovery()
    db.close()


# ==================== HELPERS ====================

def start_dashboard(config, db, metrics, progress, logger) -> Optional[threading.Thread]:
    """Start dashboard in a background thread."""
    try:
        import uvicorn
        from modules.server.dashboard import create_dashboard, set_dashboard_state

        app = create_dashboard(config, db, metrics, progress)

        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=config.monitoring.dashboard_port,
                        log_level="error", use_colors=False)

        thread = threading.Thread(target=run_server, daemon=True, name="dashboard")
        thread.start()
        time.sleep(0.5)  # Wait for server to start
        logger.info(f"🌐 Dashboard: http://127.0.0.1:{config.monitoring.dashboard_port}")
        return thread
    except ImportError:
        logger.debug("Dashboard skipped (uvicorn/fastapi not installed)")
        return None
    except Exception as e:
        logger.warning(f"Dashboard failed to start: {e}")
        return None


def export_accounts_to_file(config, db, export_mgr, logger):
    """Export all accounts from DB to CSV/Excel."""
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data_akun, status, created_at, session_data FROM stok_akun ORDER BY created_at DESC")
                rows = cur.fetchall()

        accounts = []
        for row in rows:
            parts = row[0].split("|")
            accounts.append({
                "email": parts[0] if len(parts) > 0 else "",
                "password": parts[1] if len(parts) > 1 else "",
                "status": row[1] or "",
                "created_at": row[2].isoformat() if row[2] else "",
                "session_token": row[3] or "",
            })

        if accounts:
            paths = export_mgr.export_accounts(accounts, format="both")
            for p in paths:
                if p:
                    logger.info(f"📄 Exported: {p}")
        else:
            logger.info("No accounts to export")
    except Exception as e:
        logger.error(f"Export failed: {e}")


# ==================== ENTRY ====================

if __name__ == "__main__":
    main()
