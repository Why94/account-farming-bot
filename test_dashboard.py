#!/usr/bin/env python3
"""
test_dashboard.py - Standalone test untuk dashboard tanpa farming.
"""

import threading
import time
import logging
from modules.server.dashboard import create_dashboard, set_dashboard_state
from modules.monitoring import ProgressTracker, MetricsCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting dashboard standalone test...")
    
    class FakeConfig:
        class monitoring:
            dashboard_port = 8080
    
    class FakeDB:
        def get_connection(self):
            raise Exception("Fake")
    
    progress = ProgressTracker(50)
    metrics = MetricsCollector()
    
    app = create_dashboard(FakeConfig, FakeDB(), metrics, progress)
    
    # Test langsung via uvicorn
    import uvicorn
    
    def run():
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
    
    logger.info("Dashboard di http://localhost:8080")
    logger.info("Tekan Ctrl+C untuk stop")
    run()
