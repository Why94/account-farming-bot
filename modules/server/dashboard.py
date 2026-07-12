#!/usr/bin/env python3
"""
dashboard.py - FastAPI web dashboard with HTMX for real-time monitoring.
"""

import asyncio
import json
import threading
import time
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import logging

logger = logging.getLogger(__name__)

# Global state shared with farming thread
_dashboard_state: Dict[str, Any] = {
    "running": False,
    "stats": {},
    "metrics": {},
    "db_stats": {},
    "accounts": [],
    "health": {},
}

# Lock for state updates
_state_lock = threading.Lock()


def set_dashboard_state(key: str, value: Any) -> None:
    """Update dashboard state from farming thread."""
    with _state_lock:
        _dashboard_state[key] = value


def get_dashboard_state() -> Dict[str, Any]:
    """Get current dashboard state."""
    with _state_lock:
        return dict(_dashboard_state)


# ==================== FASTAPP SETUP ====================

def create_dashboard(config, db_manager=None, metrics_collector=None, progress_tracker=None) -> FastAPI:
    """Create and configure the FastAPI dashboard app."""
    app = FastAPI(title="Account Farming Dashboard", version="2.0")

    # Templates
    templates = Jinja2Templates(directory="./modules/server/templates")

    # Mount static files
    import os
    os.makedirs("./modules/server/static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="./modules/server/static"), name="static")

    # Load template HTML content
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        TEMPLATE_HTML = f.read()

    # ==================== ROUTES ====================

    @app.get("/", response_class=HTMLResponse)
    async def dashboard_index(request: Request):
        """Main dashboard page — returns HTML directly."""
        return HTMLResponse(TEMPLATE_HTML)

    @app.get("/api/stats")
    async def api_stats():
        """Get current stats."""
        state = get_dashboard_state()
        return {
            "stats": state.get("stats", {}),
            "metrics": state.get("metrics", {}),
            "db_stats": state.get("db_stats", {}),
        }

    @app.get("/api/accounts")
    async def api_accounts(limit: int = 50):
        """Get recent accounts."""
        state = get_dashboard_state()
        accounts = state.get("accounts", [])[-limit:]
        return accounts

    @app.get("/api/health")
    async def api_health():
        """Health check endpoint."""
        health = await check_health(db_manager)
        return health

    @app.get("/api/accounts/export")
    async def api_export(format: str = "csv"):
        """Trigger export (placeholder — actual export handled by farming)."""
        return {"message": f"Export as {format} triggered", "note": "Check exports/ directory"}

    @app.post("/api/restart")
    async def api_restart():
        """Trigger restart (placeholder)."""
        return {"message": "Restart triggered"}

    @app.post("/api/stop")
    async def api_stop():
        """Trigger stop."""
        from modules.monitoring import trigger_shutdown
        trigger_shutdown()
        return {"message": "Shutdown signal sent"}

    # ==================== SSE (Server-Sent Events) ====================

    @app.get("/sse/stats")
    async def sse_stats():
        """Real-time stats via SSE."""
        async def event_generator():
            while True:
                state = get_dashboard_state()
                data = json.dumps({
                    "stats": state.get("stats", {}),
                    "metrics": state.get("metrics", {}),
                    "db_stats": state.get("db_stats", {}),
                })
                yield f"data: {data}\n\n"
                await asyncio.sleep(2)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # ==================== HEALTH CHECK ====================

    async def check_health(db) -> Dict[str, Any]:
        """Check health of all components."""
        health = {"status": "healthy", "components": {}}

        # Database
        if db:
            try:
                with db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                health["components"]["database"] = {"status": "healthy"}
            except Exception as e:
                health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
                health["status"] = "degraded"

        # Proxy
        health["components"]["proxy"] = {"status": "unknown"}

        # Email
        health["components"]["email"] = {"status": "unknown"}

        return health

    return app


# ==================== TEMPLATE CONTENT ====================

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farming Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; }
        .header { background: linear-gradient(135deg, #1e293b, #334155); padding: 20px 30px; border-bottom: 2px solid #3b82f6; }
        .header h1 { font-size: 24px; color: #60a5fa; }
        .header p { color: #94a3b8; font-size: 14px; margin-top: 4px; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px; }
        .card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        .card h3 { font-size: 14px; color: #94a3b8; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .card .value { font-size: 36px; font-weight: 700; color: #f1f5f9; }
        .card .value.success { color: #4ade80; }
        .card .value.danger { color: #f87171; }
        .card .value.warning { color: #fbbf24; }
        .card .value.info { color: #60a5fa; }
        .progress-bar { width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden; margin-top: 12px; }
        .progress-bar .fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #60a5fa); transition: width 0.5s; border-radius: 4px; }
        .table-container { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 12px 16px; color: #94a3b8; font-size: 12px; text-transform: uppercase; border-bottom: 1px solid #334155; }
        td { padding: 10px 16px; font-size: 14px; border-bottom: 1px solid #1a2332; }
        .status-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .status-verified { background: #064e3b; color: #4ade80; }
        .status-registered { background: #1e3a5f; color: #60a5fa; }
        .status-failed { background: #450a0a; color: #f87171; }
        .status-pending { background: #422006; color: #fbbf24; }
        .status-duplicate { background: #312e81; color: #a5b4fc; }
        .controls { display: flex; gap: 12px; margin-bottom: 20px; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }
        .btn-danger { background: #dc2626; color: white; }
        .btn-primary { background: #3b82f6; color: white; }
        .btn:hover { opacity: 0.85; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
        .metric-item { text-align: center; padding: 12px; background: #0f172a; border-radius: 8px; }
        .metric-item .label { font-size: 12px; color: #94a3b8; }
        .metric-item .val { font-size: 20px; font-weight: 700; color: #e2e8f0; margin-top: 4px; }
        .footer { text-align: center; color: #475569; font-size: 12px; margin-top: 30px; padding: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Account Farming Dashboard</h1>
        <p>Real-time monitoring &amp; control panel</p>
    </div>
    <div class="container">
        <div class="controls">
            <button class="btn btn-primary" hx-get="/api/stats" hx-target="#refresh-stats" hx-trigger="every 2s">🔄 Refresh</button>
            <button class="btn btn-danger" hx-post="/api/stop" hx-swap="none">⏹ Stop</button>
            <a class="btn btn-primary" href="/api/accounts/export?format=csv">📄 Export CSV</a>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Progress</h3>
                <div class="value info" id="progress-pct">0%</div>
                <div class="progress-bar"><div class="fill" id="progress-fill" style="width:0%"></div></div>
            </div>
            <div class="card">
                <h3>Total Akun</h3>
                <div class="value" id="total-count">0</div>
            </div>
            <div class="card">
                <h3>Sukses</h3>
                <div class="value success" id="success-count">0</div>
            </div>
            <div class="card">
                <h3>Verified</h3>
                <div class="value success" id="verified-count">0</div>
            </div>
            <div class="card">
                <h3>Gagal</h3>
                <div class="value danger" id="failed-count">0</div>
            </div>
            <div class="card">
                <h3>Success Rate</h3>
                <div class="value" id="success-rate">0%</div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 20px;">
            <h3>⚡ Performance Metrics</h3>
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="label">Avg Time/Acount</div>
                    <div class="val" id="avg-time">0s</div>
                </div>
                <div class="metric-item">
                    <div class="label">Rate/Hour</div>
                    <div class="val" id="rate-hour">0</div>
                </div>
                <div class="metric-item">
                    <div class="label">ETA</div>
                    <div class="val" id="eta">0 min</div>
                </div>
                <div class="metric-item">
                    <div class="label">Uptime</div>
                    <div class="val" id="uptime">0s</div>
                </div>
            </div>
        </div>

        <div class="table-container">
            <h3 style="margin-bottom: 12px;">📋 Recent Accounts</h3>
            <table>
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Proxy</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody id="accounts-table">
                </tbody>
            </table>
        </div>

        <div class="footer">
            Account Farming Bot v2.0 | FastAPI + HTMX Dashboard
        </div>
    </div>

    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script>
        // SSE connection for real-time updates
        const eventSource = new EventSource('/sse/stats');
        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            } catch(e) {}
        };

        function updateDashboard(data) {
            const stats = data.stats || {};
            const metrics = data.metrics || {};

            document.getElementById('progress-pct').textContent = (stats.progress_pct || 0) + '%';
            document.getElementById('progress-fill').style.width = (stats.progress_pct || 0) + '%';
            document.getElementById('total-count').textContent = stats.current || 0;
            document.getElementById('success-count').textContent = stats.success || 0;
            document.getElementById('verified-count').textContent = stats.verified || 0;
            document.getElementById('failed-count').textContent = stats.failed || 0;
            document.getElementById('success-rate').textContent = (stats.success_rate || 0) + '%';
            document.getElementById('avg-time').textContent = (metrics.avg_time_per_account || 0) + 's';
            document.getElementById('rate-hour').textContent = (stats.rate_per_hour || 0);
            document.getElementById('eta').textContent = (stats.eta_minutes || 0) + ' min';
            document.getElementById('uptime').textContent = formatUptime(metrics.uptime_seconds || 0);
        }

        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            if (h > 0) return h + 'h ' + m + 'm';
            if (m > 0) return m + 'm ' + s + 's';
            return s + 's';
        }
    </script>
</body>
</html>
"""
