#!/usr/bin/env python3
"""
monitoring.py - Logging setup, screenshot management, progress bar,
performance metrics, and log rotation.
"""

import os
import io
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any, Optional, List
from collections import deque

logger = logging.getLogger(__name__)

# Global shutdown event shared across modules
_shutdown_event = threading.Event()


# ==================== LOGGING SETUP ====================

def setup_logging(config) -> logging.Logger:
    """Setup comprehensive logging with rotation."""
    main_logger = logging.getLogger()
    main_logger.setLevel(logging.INFO)

    # Remove existing handlers
    main_logger.handlers = []

    fmt = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    main_logger.addHandler(console_handler)

    # File handler with rotation
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "farming.log")

    if config.monitoring.log_rotation == "size":
        # Rotate by size (10MB)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
    else:
        # Rotate daily
        file_handler = TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, backupCount=30, encoding="utf-8"
        )
    file_handler.setFormatter(fmt)
    main_logger.addHandler(file_handler)

    logger.info("📝 Logging initialized")
    return main_logger


# ==================== SCREENSHOT MANAGEMENT ====================

def take_screenshot(page, email: str = "", label: str = "", dir_path: str = "./screenshots") -> Optional[str]:
    """Take and save a screenshot. Returns file path."""
    os.makedirs(dir_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_email = email.replace("@", "_at_").replace(".", "_").replace("?", "_") if email else "unknown"
    filename = f"{timestamp}_{safe_email}_{label}.png" if label else f"{timestamp}_{safe_email}.png"
    filepath = os.path.join(dir_path, filename)

    try:
        page.screenshot(path=filepath, full_page=True, timeout=10000)
        logger.debug(f"📸 Screenshot saved: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"Failed to save screenshot: {e}")
        return None


# ==================== PROGRESS BAR ====================

class ProgressTracker:
    """Thread-safe progress tracker with console progress bar."""

    def __init__(self, total: int, enable_bar: bool = True):
        self.total = total
        self.current = 0
        self.success = 0
        self.failed = 0
        self.verified = 0
        self.enable_bar = enable_bar
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._timestamps: deque = deque(maxlen=1000)

    def update(self, success: bool, verified: bool = False) -> None:
        """Update progress counter."""
        with self._lock:
            self.current += 1
            if success:
                self.success += 1
                if verified:
                    self.verified += 1
            else:
                self.failed += 1
            self._timestamps.append((time.time(), success, verified))

    def get_status(self) -> Dict[str, Any]:
        """Get current status dict for dashboard."""
        with self._lock:
            elapsed = time.time() - self._start_time
            rate = self.current / elapsed * 3600 if elapsed > 0 else 0  # per hour

            # Calculate recent throughput (last 5 minutes)
            five_min_ago = time.time() - 300
            recent = [(t, s, v) for t, s, v in self._timestamps if t > five_min_ago]
            recent_rate = len(recent) / 300 if recent else 0

            return {
                "current": self.current,
                "total": self.total,
                "success": self.success,
                "failed": self.failed,
                "verified": self.verified,
                "progress_pct": round(self.current / self.total * 100, 1) if self.total > 0 else 0,
                "elapsed_seconds": round(elapsed, 1),
                "elapsed_minutes": round(elapsed / 60, 1),
                "rate_per_hour": round(rate, 1),
                "recent_rate_per_min": round(recent_rate, 2),
                "eta_minutes": round((self.total - self.current) / (recent_rate * 60), 1) if recent_rate > 0 else 0,
                "success_rate": round(self.success / self.current * 100, 1) if self.current > 0 else 0,
                "ban_rate": round(self.failed / self.current * 100, 1) if self.current > 0 else 0,
            }

    def is_done(self) -> bool:
        return self.current >= self.total


# ==================== PERFORMANCE METRICS ====================

class MetricsCollector:
    """Collects and exports performance metrics."""

    def __init__(self):
        self._lock = threading.Lock()
        self._account_times: deque = deque(maxlen=10000)
        self._errors_by_type: Dict[str, int] = {}
        self._start_time = time.time()

    def record_account_time(self, email: str, duration: float, success: bool) -> None:
        """Record time taken for one account."""
        with self._lock:
            self._account_times.append({
                "email": email,
                "duration": duration,
                "success": success,
                "timestamp": time.time(),
            })

    def record_error(self, error_type: str) -> None:
        """Record an error occurrence."""
        with self._lock:
            self._errors_by_type[error_type] = self._errors_by_type.get(error_type, 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        with self._lock:
            times = [a["duration"] for a in self._account_times]
            successful = [a for a in self._account_times if a["success"]]
            success_times = [a["duration"] for a in successful]

            return {
                "total_accounts": len(self._account_times),
                "avg_time_per_account": round(sum(times) / len(times), 2) if times else 0,
                "min_time": round(min(times), 2) if times else 0,
                "max_time": round(max(times), 2) if times else 0,
                "median_time": round(sorted(times)[len(times) // 2], 2) if times else 0,
                "avg_success_time": round(sum(success_times) / len(success_times), 2) if success_times else 0,
                "errors": dict(self._errors_by_type),
                "uptime_seconds": round(time.time() - self._start_time, 1),
            }

    def export_metrics(self, filepath: str = "./exports/metrics.json") -> str:
        """Export metrics to JSON file."""
        metrics = {
            "collected_at": datetime.now().isoformat(),
            "metrics": self.get_metrics(),
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"📊 Metrics exported to {filepath}")
        return filepath


# ==================== SHUTDOWN ====================

def trigger_shutdown() -> None:
    """Signal all threads to shut down gracefully."""
    _shutdown_event.set()
    logger.warning("⚠️ Shutdown signal sent")

def is_shutting_down() -> bool:
    return _shutdown_event.is_set()
