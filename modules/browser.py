#!/usr/bin/env python3
# browser.py - Advanced browser management with stealth, fingerprint randomization,
# mouse/keyboard simulation, WebRTC protection, geo-spoofing, and canvas noise.
import json
import os
import random
import time
import logging
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

LOCALES = ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "ja-JP", "ko-KR", "pt-BR", "nl-NL"]

TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "Europe/London", "Europe/Berlin", "Europe/Paris", "Europe/Madrid",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Singapore", "Asia/Kolkata",
    "Australia/Sydney", "Pacific/Auckland",
]


class BrowserManager:
    def __init__(self, config):
        self.config = config

    def launch(self, headless=None):
        hl = headless if headless is not None else self.config.browser.headless
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=hl,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080",
            ],
        )
        logger.info("[INFO] Browser launched")
        return playwright, browser

    def launch_context(self, headless=None):
        return _LaunchContext(self, headless)

    def new_context(self, browser, proxy=None, geo_ip=None):
        ua = random.choice(USER_AGENTS)
        locale = random.choice(LOCALES)
        timezone = random.choice(TIMEZONES)
        viewport = {
            "width": random.randint(1280, 1920),
            "height": random.randint(720, 1080),
        }
        context_args = {
            "user_agent": ua,
            "viewport": viewport,
            "locale": locale,
            "timezone_id": timezone,
            "proxy": {"server": proxy} if proxy else None,
            "color_scheme": "light",
            "device_scale_factor": random.choice([1.0, 1.25, 1.5, 2.0]),
            "has_touch": random.choice([True, False]),
        }
        context = browser.new_context(**context_args)

        if self.config.browser.stealth:
            self._inject_stealth_scripts(context)
        if self.config.browser.fingerprint_inject:
            self._inject_fingerprint(context)
        if self.config.browser.canvas_noise:
            self._inject_canvas_noise(context)
        if self.config.browser.webrtc_block:
            self._block_webrtc(context)
        if self.config.browser.permissions_random:
            self._randomize_permissions(context)
        if self.config.browser.geo_spoof and geo_ip:
            self._geo_spoof(context, geo_ip)

        logger.debug("[CTX] Context created — UA: %s... | Locale: %s | TZ: %s", ua[:30], locale, timezone)
        return context

    def _inject_stealth_scripts(self, context):
        stealth_js_path = os.path.join(os.path.dirname(__file__), "server", "stealth.js")
        if os.path.exists(stealth_js_path):
            with open(stealth_js_path, "r", encoding="utf-8") as f:
                script = f.read()
        else:
            script = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                      "window.chrome={runtime:{}};")
        context.add_init_script(script)
        logger.debug("[STEALTH] Stealth scripts injected")

    def _inject_fingerprint(self, context):
        fonts = ["Arial","Helvetica","Times New Roman","Courier New",
                 "Georgia","Verdana","Impact","Comic Sans MS",
                 "Trebuchet MS","Palatino","Lucida Console"]
        random_fonts = random.sample(fonts, k=random.randint(5, 10))
        js = 'const fontList=' + json.dumps(random_fonts) + ';'
        js += 'Object.defineProperty(navigator,"fonts",{get:()=>[1,2,3]});'
        context.add_init_script(js)
        logger.debug("[NOISE] Fingerprint injection done")

    def _inject_canvas_noise(self, context):
        noise_seed = random.randint(1, 1000000)
        lines = []
        lines.append("const originalToDataURL=HTMLCanvasElement.prototype.toDataURL;")
        lines.append("HTMLCanvasElement.prototype.toDataURL=function(type,...args){")
        lines.append("if(this.width>100&&this.height>100){")
        lines.append("var ctx=this.getContext('2d');")
        lines.append("if(ctx){")
        lines.append("ctx.fillStyle='rgba(%d,%d,%d,0.01)';" % (noise_seed%256, noise_seed%128, noise_seed%64))
        lines.append("ctx.fillRect(0,0,this.width,this.height);")
        lines.append("}}")
        lines.append("return originalToDataURL.call(this,type,...args);")
        lines.append("};")
        context.add_init_script("\n".join(lines))
        logger.debug("[NOISE] Canvas/WebGL noise injection done")

    def _block_webrtc(self, context):
        lines = []
        lines.append("const originalRTC=window.RTCPeerConnection;")
        lines.append("window.RTCPeerConnection=function(){")
        lines.append("var conn=originalRTC.apply(this,arguments);")
        lines.append("Object.defineProperty(conn,'localDescription',{")
        lines.append("get(){")
        lines.append("if(this&&this.sdp){")
        lines.append("this.sdp=this.sdp.replace(/(c=IN IPv4\\\\s+)(\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\.\\\\d+)/,'$10.0.0.0');")
        lines.append("}")
        lines.append("return this;")
        lines.append("}});")
        lines.append("return conn;")
        lines.append("};")
        lines.append("window.RTCPeerConnection.prototype=originalRTC.prototype;")
        context.add_init_script("\n".join(lines))
        logger.debug("[WEBRTC] WebRTC blocked")

    def _randomize_permissions(self, context):
        permissions = ["geolocation","notifications","camera","microphone","clipboard-read"]
        granted = random.sample(permissions, k=random.randint(0, 2))
        if granted:
            try:
                context.grant_permissions(granted)
                logger.debug("[PERMS] Permissions granted: %s", granted)
            except Exception:
                pass

    def _geo_spoof(self, context, ip):
        ip_prefix = ip.split(".")[:2] if "." in ip else ["", ""]
        geo_mappings = {
            ("104","162"): {"lat": 37.7749, "lon": -122.4194, "tz": "America/Los_Angeles"},
            ("104","21"): {"lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
            ("45","33"): {"lat": 48.8566, "lon": 2.3522, "tz": "Europe/Paris"},
            ("51","35"): {"lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
            ("103","2"): {"lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore"},
        }
        key = tuple(ip_prefix)
        geo = geo_mappings.get(key)
        if geo:
            try:
                context.set_geolocation({"latitude": geo["lat"], "longitude": geo["lon"]})
                logger.debug("[GEO] Geo-spoof: lat=%s, lon=%s", geo["lat"], geo["lon"])
            except Exception:
                pass

    @staticmethod
    def mouse_click(page, selector, clicks=1):
        try:
            element = page.query_selector(selector)
            if element:
                box = element.bounding_box()
                if box:
                    x = box["x"] + box["width"] / 2
                    y = box["y"] + box["height"] / 2
                    page.mouse.move(x + random.randint(-50, 50), y + random.randint(-30, 30))
                    time.sleep(random.uniform(0.1, 0.3))
                    page.mouse.move(x, y)
                    time.sleep(random.uniform(0.05, 0.15))
                    page.mouse.click(x, y, clicks=clicks)
                    logger.debug("[MOUSE] Natural click on %s", selector)
                else:
                    page.click(selector)
            else:
                page.click(selector)
        except Exception:
            page.click(selector)

    @staticmethod
    def mouse_scroll(page, direction="down", amount=300):
        try:
            scroll_amount = random.randint(amount // 2, amount * 2)
            if direction == "up":
                scroll_amount = -scroll_amount
            page.mouse.wheel(random.randint(-30, 30), scroll_amount)
            time.sleep(random.uniform(0.2, 0.8))
        except Exception:
            pass

    @staticmethod
    def natural_type(page, selector, text, min_delay=0.02, max_delay=0.15):
        try:
            page.focus(selector)
            time.sleep(random.uniform(0.1, 0.3))
            for char in text:
                delay = random.uniform(min_delay, max_delay)
                if random.random() < 0.05:
                    delay = random.uniform(0.5, 1.5)
                page.keyboard.press(char)
                time.sleep(delay)
            logger.debug("[KBD] Natural typing: %d chars", len(text))
        except Exception:
            page.fill(selector, text)


class _LaunchContext:
    """Context manager for browser launch — auto closes on exit."""
    def __init__(self, mgr, hl):
        self._mgr = mgr
        self._hl = hl
        self.playwright = None
        self.browser = None

    def __enter__(self):
        self.playwright, self.browser = self._mgr.launch(self._hl)
        return self.playwright, self.browser

    def __exit__(self, *args):
        try:
            self.browser.close()
        except Exception:
            pass
        try:
            self.playwright.stop()
        except Exception:
            pass
