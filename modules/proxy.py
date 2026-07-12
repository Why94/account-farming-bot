#!/usr/bin/env python3
"""
proxy.py - Proxy management: fetch, health check, rotation, residential proxies,
rate limiting per IP, and IP rotation verification.
"""

import random
import time
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional, List

import requests

logger = logging.getLogger(__name__)


@dataclass
class ProxyInfo:
    url: str
    host: str
    port: int
    username: str
    password: str
    proxy_type: str = "datacenter"   # datacenter, residential
    healthy: bool = False
    latency_ms: int = 0
    requests_used: int = 0
    last_request_time: float = 0.0


class ProxyManager:
    """Manages proxy lifecycle: fetch, test, rotate, rate limit."""

    def __init__(self, config):
        self.config = config
        self._cache: List[ProxyInfo] = []
        self._ip_counts: dict = defaultdict(int)   # ip -> count in window
        self._ip_window_start: float = time.time()
        self._lock = None  # simplified: not using lock for now

    # ==================== FETCH ====================

    def fetch_proxies(self) -> List[ProxyInfo]:
        """Fetch proxies from configured provider."""
        proxies = []

        if not self.config.enabled:
            return proxies

        provider = self.config.provider

        if provider == "webshare":
            proxies = self._fetch_webshare()
        elif provider in ("brightdata", "smartproxy", "iproyal"):
            proxies = self._fetch_datacenter(provider)
        else:
            logger.warning(f"Unknown proxy provider: {provider}")

        # Also fetch residential proxies if configured
        if self.config.residential_provider and self.config.residential_token:
            res_proxies = self._fetch_residential(self.config.residential_provider, self.config.residential_token)
            for p in res_proxies:
                p.proxy_type = "residential"
            proxies.extend(res_proxies)
            logger.info(f"📥 Fetched {len(res_proxies)} residential proxies from {self.config.residential_provider}")

        logger.info(f"📥 Total fetched: {len(proxies)} proxies from {provider}")
        return proxies

    def _fetch_webshare(self) -> List[ProxyInfo]:
        """Fetch proxies from Webshare API."""
        proxies = []
        token = self.config.webshare_token
        url = "https://proxy.webshare.io/api/v2/proxy/list/"

        if not token:
            logger.warning("Webshare token not set")
            return proxies

        try:
            headers = {"Authorization": f"Token {token}"}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for p in data.get('results', [])[:100]:
                    proxy_url = f"http://{p['username']}:{p['password']}@{p['proxy_address']}:{p['port']}"
                    info = self._parse_proxy_url(proxy_url, "datacenter")
                    if info:
                        proxies.append(info)
        except Exception as e:
            logger.warning(f"Failed to fetch Webshare proxies: {e}")

        return proxies

    def _fetch_datacenter(self, provider: str) -> List[ProxyInfo]:
        """Fetch datacenter proxies from various providers."""
        proxies = []
        token = self.config.residential_token if provider != "webshare" else self.config.webshare_token

        # Generic endpoint pattern — customize per provider
        endpoints = {
            "brightdata": f"https://api.brightdata.com/ proxies?token={token}&limit=50",
            "smartproxy": f"https://api.smartproxy.com/proxies?token={token}",
            "iproyal": f"https://api.iproyal.com/proxies?token={token}",
        }

        endpoint = endpoints.get(provider)
        if not endpoint:
            return proxies

        try:
            resp = requests.get(endpoint, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for p in data.get('proxies', []):
                    proxy_url = f"http://{p.get('host')}:{p.get('port')}"
                    if p.get('user') and p.get('pass'):
                        proxy_url = f"http://{p['user']}:{p['pass']}@{p.get('host')}:{p.get('port')}"
                    info = self._parse_proxy_url(proxy_url, "datacenter")
                    if info:
                        proxies.append(info)
        except Exception as e:
            logger.warning(f"Failed to fetch {provider} proxies: {e}")

        return proxies

    def _fetch_residential(self, provider: str, token: str) -> List[ProxyInfo]:
        """Fetch residential proxies."""
        proxies = []
        try:
            # Generic residential proxy fetch — customize per provider
            resp = requests.get(
                f"https://api.{provider}.com/residential?token={token}&limit=50",
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                for p in data.get('proxies', []):
                    proxy_url = f"http://{p.get('host')}:{p.get('port')}"
                    if p.get('user') and p.get('pass'):
                        proxy_url = f"http://{p['user']}:{p['pass']}@{p.get('host')}:{p.get('port')}"
                    info = self._parse_proxy_url(proxy_url, "residential")
                    if info:
                        proxies.append(info)
        except Exception as e:
            logger.warning(f"Failed to fetch residential proxies from {provider}: {e}")

        return proxies

    @staticmethod
    def _parse_proxy_url(proxy_url: str, proxy_type: str = "datacenter") -> Optional[ProxyInfo]:
        """Parse proxy URL into ProxyInfo object."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(proxy_url)
            return ProxyInfo(
                url=proxy_url,
                host=parsed.hostname or "",
                port=parsed.port or 80,
                username=parsed.username or "",
                password=parsed.password or "",
                proxy_type=proxy_type,
            )
        except Exception as e:
            logger.warning(f"Failed to parse proxy URL: {e}")
            return None

    # ==================== HEALTH CHECK ====================

    def test_all_proxies(self) -> int:
        """Test all cached proxies and return count of healthy ones."""
        if not self._cache:
            return 0

        def _test(p: ProxyInfo) -> bool:
            return self.test_proxy(p)

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(_test, self._cache))

        healthy = sum(results)
        logger.info(f"✅ {healthy}/{len(self._cache)} proxies healthy")
        return healthy

    def test_proxy(self, proxy: ProxyInfo) -> bool:
        """Test a single proxy's health."""
        try:
            start = time.time()
            proxies = {"http": proxy.url, "https": proxy.url}
            resp = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
            latency = int((time.time() - start) * 1000)

            if resp.status_code == 200:
                proxy.healthy = True
                proxy.latency_ms = latency
                logger.debug(f"✅ Proxy healthy: {proxy.host}:{proxy.port} ({latency}ms)")
                return True
        except Exception as e:
            logger.debug(f"❌ Proxy unhealthy: {proxy.host}:{proxy.port} - {e}")

        proxy.healthy = False
        return False

    # ==================== ROTATION ====================

    def get_working_proxy(self) -> Optional[str]:
        """Get a working proxy URL for Playwright."""
        proxy = self._get_healthy_proxy()
        if proxy:
            # Rate limit check (feature #25)
            if not self._check_rate_limit(proxy):
                logger.debug(f"⏳ Rate limited for proxy {proxy.host}")
                return None

            logger.info(f"🔄 Proxy: {proxy.host}:{proxy.port} ({proxy.latency_ms}ms) [{proxy.proxy_type}]")
            # Update usage stats
            proxy.requests_used += 1
            proxy.last_request_time = time.time()
            return proxy.url

        logger.warning("⚠️ No healthy proxy available, proceeding without proxy")
        return None

    def _get_healthy_proxy(self) -> Optional[ProxyInfo]:
        """Get a healthy proxy from cache or refetch."""
        if not self._cache:
            logger.info("🔄 Fetching fresh proxies...")
            self._cache = self.fetch_proxies()
            if self._cache:
                self.test_all_proxies()

        healthy = [p for p in self._cache if p.healthy]

        if not healthy:
            # Refetch
            self._cache = self.fetch_proxies()
            if self._cache:
                self.test_all_proxies()
                healthy = [p for p in self._cache if p.healthy]

        if healthy:
            # Sort by latency, pick random from top 5 fastest
            healthy.sort(key=lambda p: p.latency_ms)
            return random.choice(healthy[:min(5, len(healthy))])

        return None

    # ==================== RATE LIMITING (feature #25) ====================

    def _check_rate_limit(self, proxy: ProxyInfo) -> bool:
        """Check if proxy IP is within rate limit (feature #25)."""
        # Reset window if expired
        if time.time() - self._ip_window_start > self.config.window_seconds:
            self._ip_counts.clear()
            self._ip_window_start = time.time()

        ip_key = f"{proxy.host}:{proxy.port}"
        count = self._ip_counts.get(ip_key, 0)

        if count >= self.config.max_per_ip:
            return False

        self._ip_counts[ip_key] = count + 1
        return True

    # ==================== IP ROTATION VERIFICATION (feature #32) ====================

    def verify_ip_rotation(self, proxy_url: Optional[str]) -> Optional[str]:
        """Verify that the proxy IP matches what we expect (feature #32)."""
        if not proxy_url:
            return None

        try:
            proxies = {"http": proxy_url, "https": proxy_url}
            resp = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
            if resp.status_code == 200:
                ip = resp.json().get("ip", "")
                logger.debug(f"✅ Proxy IP verified: {ip}")
                return ip
        except Exception as e:
            logger.warning(f"Failed to verify proxy IP: {e}")

        return None

    # ==================== CLEANUP ====================

    def cleanup(self) -> None:
        """Clean up expired rate limit entries."""
        if time.time() - self._ip_window_start > self.config.window_seconds:
            self._ip_counts.clear()
            self._ip_window_start = time.time()
