#!/usr/bin/env python3
"""
generate_doc.py - Generate Account Farming Bot v2.0 PDF Documentation
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether, ListFlowable, ListItem
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.colors import HexColor

# ━━ Color Palette ━━
ACCENT       = HexColor('#4e2fae')
TEXT_PRIMARY  = HexColor('#1f1e1c')
TEXT_MUTED    = HexColor('#8d8a81')
BG_SURFACE   = HexColor('#e8e6df')
BG_PAGE      = HexColor('#eeedea')

W, H = A4
MARGIN = 2.2 * cm

OUTPUT = "Dokumentasi_Account_Farming_Bot_v2.pdf"

# ── Styles ──
styles = getSampleStyleSheet()

def S(name, **kw):
    base = kw.pop('parent', 'Normal')
    return ParagraphStyle(name, parent=styles[base], **kw)

cover_title  = S('CoverTitle',  fontName='Helvetica-Bold', fontSize=32, textColor=colors.white,
                  leading=38, spaceAfter=6, alignment=TA_CENTER)
cover_sub    = S('CoverSub',    fontName='Helvetica',     fontSize=14, textColor=colors.white,
                  leading=20, spaceAfter=4, alignment=TA_CENTER)
cover_meta   = S('CoverMeta',   fontName='Helvetica',      fontSize=10, textColor=colors.white,
                  leading=14, spaceAfter=3, alignment=TA_CENTER, opacity=0.8)
cover_contact= S('CoverContact',fontName='Helvetica',     fontSize=11, textColor=colors.white,
                  leading=16, spaceAfter=3, alignment=TA_CENTER)

h1 = S('H1', fontName='Helvetica-Bold', fontSize=18, textColor=ACCENT,
        leading=24, spaceBefore=20, spaceAfter=8)
h2 = S('H2', fontName='Helvetica-Bold', fontSize=13, textColor=ACCENT,
        leading=18, spaceBefore=14, spaceAfter=6)
h3 = S('H3', fontName='Helvetica-Bold', fontSize=11, textColor=TEXT_PRIMARY,
        leading=16, spaceBefore=10, spaceAfter=4)

body = S('Body', fontName='Helvetica', fontSize=10, textColor=TEXT_PRIMARY,
         leading=16, alignment=TA_JUSTIFY, spaceAfter=6)
body_left = S('BodyLeft', fontName='Helvetica', fontSize=10, textColor=TEXT_PRIMARY,
              leading=15, alignment=TA_LEFT, spaceAfter=4)
code = S('Code', fontName='Courier', fontSize=8.5, textColor=TEXT_PRIMARY,
         leading=13, backColor=BG_SURFACE, leftIndent=12, rightIndent=12,
         spaceBefore=4, spaceAfter=8, wordWrap='CJK')
caption = S('Caption', fontName='Helvetica-Oblique', fontSize=8.5, textColor=TEXT_MUTED,
            leading=12, alignment=TA_CENTER, spaceAfter=6)
bullet  = S('Bullet', fontName='Helvetica', fontSize=10, textColor=TEXT_PRIMARY,
            leading=15, leftIndent=16, spaceAfter=3, alignment=TA_LEFT)
label = S('Label', fontName='Helvetica-Bold', fontSize=9.5, textColor=ACCENT,
           leading=13, spaceAfter=2)
note = S('Note', fontName='Helvetica-Oblique', fontSize=9, textColor=TEXT_MUTED,
         leading=13, spaceAfter=4)
toc_entry = S('TOC', fontName='Helvetica', fontSize=11, textColor=TEXT_PRIMARY,
              leading=18, leftIndent=0, spaceAfter=2)

# ── Helpers ──
def rule(w=None, c=None, t=0.5):
    r = w or (W - 2*MARGIN)
    return HRFlowable(width=r, thickness=t, color=c or ACCENT, spaceAfter=6, spaceBefore=6)

def feature_table(data, col_widths=None):
    if col_widths is None:
        col_widths = [(W - 2*MARGIN) * p for p in [0.08, 0.22, 0.70]]
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_SURFACE]),
        ('GRID',       (0,0), (-1,-1), 0.3, HexColor('#d0cdc6')),
        ('VALIGN',     (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',(0,0), (-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
    ]))
    return tbl

def env_table(data, col_widths=None):
    if col_widths is None:
        col_widths = [(W - 2*MARGIN) * p for p in [0.30, 0.35, 0.35]]
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_SURFACE]),
        ('GRID',       (0,0), (-1,-1), 0.3, HexColor('#d0cdc6')),
        ('VALIGN',     (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',(0,0), (-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('FONTNAME',   (1,1), (-1,-1), 'Courier'),
        ('TEXTCOLOR',  (1,1), (-1,-1), TEXT_PRIMARY),
    ]))
    return tbl

def module_table(data, col_widths=None):
    if col_widths is None:
        col_widths = [(W - 2*MARGIN) * p for p in [0.28, 0.45, 0.27]]
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_SURFACE]),
        ('GRID',       (0,0), (-1,-1), 0.3, HexColor('#d0cdc6')),
        ('VALIGN',     (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',(0,0), (-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('FONTNAME',   (2,1), (-1,-1), 'Helvetica-Oblique'),
        ('TEXTCOLOR',  (2,1), (-1,-1), TEXT_MUTED),
    ]))
    return tbl

def cli_table(data):
    col_widths = [(W - 2*MARGIN) * p for p in [0.22, 0.28, 0.50]]
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_SURFACE]),
        ('GRID',       (0,0), (-1,-1), 0.3, HexColor('#d0cdc6')),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',(0,0), (-1,-1), 8),
        ('RIGHTPADDING',(0,0),(-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('FONTNAME',   (1,1), (-1,-1), 'Courier'),
    ]))
    return tbl

def section_header(text):
    return [Paragraph(text, h1), rule()]

def subsection(text):
    return Paragraph(text, h2)

# ═══════════════════════════════════════════════
#  DOCUMENT CONTENT
# ═══════════════════════════════════════════════

def build():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title="Account Farming Bot v2.0 - Dokumentasi Lengkap",
        author="Aysel | 089698002242",
        subject="Dokumentasi Teknis",
        creator="Account Farming Bot v2.0",
    )

    story = []

    # ───────────────────────────────
    # COVER
    # ───────────────────────────────
    story.append(Spacer(1, 2.5*cm))
    story.append(Paragraph("Account Farming Bot", cover_title))
    story.append(Spacer(1, 0.3*cm))
    story.append(rule(w=W - 2*MARGIN, c=colors.white, t=1))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("v2.0 — 32 Fitur Lengkap", cover_sub))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("Dokumentasi Teknis Lengkap", cover_meta))
    story.append(Paragraph("Modular Architecture | Stealth | Multi-Provider | Dashboard Real-Time", cover_meta))
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("Kontak: 089698002242", cover_contact))
    story.append(Paragraph("GitHub: github.com/Why94/account-farming-bot", cover_contact))
    story.append(Paragraph("Tanggal: Juli 2026", cover_contact))
    story.append(PageBreak())

    # ───────────────────────────────
    # TABLE OF CONTENTS
    # ───────────────────────────────
    story += section_header("Daftar Isi")
    toc_items = [
        ("1", "Ringkasan Proyek", "3"),
        ("2", "32 Fitur Lengkap", "3"),
        ("   2.1", "Keamanan (Fitur #1-10)", "3"),
        ("   2.2", "Monitoring (Fitur #11-20)", "4"),
        ("   2.3", "Fungsionalitas (Fitur #21-32)", "4"),
        ("3", "Instalasi", "5"),
        ("4", "Konfigurasi .env", "5"),
        ("5", "Arsitektur Modular", "8"),
        ("6", "Panduan Penggunaan", "9"),
        ("7", "Dashboard Real-Time", "11"),
        ("8", "Troubleshooting", "12"),
        ("9", "Disclaimer", "12"),
    ]
    toc_data = [[Paragraph(f"{n}.", toc_entry), Paragraph(t, toc_entry), Paragraph(h, toc_entry)]
                for n, t, h in toc_items]
    toc_tbl = Table(toc_data, colWidths=[0.8*cm, (W-2*MARGIN)*0.72, 1.5*cm])
    toc_tbl.setStyle(TableStyle([
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING',(0,0), (-1,-1), 0),
        ('TOPPADDING',  (0,0), (-1,-1), 2),
        ('BOTTOMPADDING',(0,0),(-1,-1), 2),
    ]))
    story.append(toc_tbl)
    story.append(PageBreak())

    # ───────────────────────────────
    # 1. RINGKASAN PROYEK
    # ───────────────────────────────
    story += section_header("1. Ringkasan Proyek")
    story.append(Paragraph(
        "Account Farming Bot v2.0 adalah script automasi Python untuk registrasi akun massal "
        "dengan 32 fitur advanced. Tool ini menggunakan arsitektur modular yang terpisah ke "
        "dalam 14 modul Python, mendukung parallel processing, proxy rotation, multi-email provider, "
        "real-time dashboard, dan notifikasi Telegram/Discord.", body))
    story.append(Paragraph(
        "Versi 2.0 merupakan upgrade besar dari versi sebelumnya (v1) dengan penambahan 32 fitur "
        "baru yang mencakup keamanan browser (stealth, fingerprint, anti-detection), monitoring "
        "(dashboard real-time, screenshot, metrics), dan fungsionalitas (auto-login, recovery, "
        "incremental farming).", body))

    story.append(Paragraph("Informasi Proyek:", h2))
    info_data = [
        [Paragraph("<b>Versi</b>", body_left), Paragraph("2.0", body_left)],
        [Paragraph("<b>Bahasa</b>", body_left), Paragraph("Python 3.11+", body_left)],
        [Paragraph("<b>Arsitektur</b>", body_left), Paragraph("Modular (14 modules)", body_left)],
        [Paragraph("<b>Database</b>", body_left), Paragraph("PostgreSQL", body_left)],
        [Paragraph("<b>Browser</b>", body_left), Paragraph("Playwright (Chromium)", body_left)],
        [Paragraph("<b>Author</b>", body_left), Paragraph("Aysel | 089698002242", body_left)],
        [Paragraph("<b>GitHub</b>", body_left), Paragraph("github.com/Why94/account-farming-bot", body_left)],
    ]
    story.append(env_table([["Properti", "Nilai"]] + info_data,
                           [(W-2*MARGIN)*0.35, (W-2*MARGIN)*0.65]))

    story.append(PageBreak())

    # ───────────────────────────────
    # 2. 32 FITUR LENGKAP
    # ───────────────────────────────
    story += section_header("2. 32 Fitur Lengkap")

    # 2.1 Keamanan
    story.append(subsection("2.1 Keamanan (#1-10)"))
    story.append(Paragraph(
        "Sepuluh fitur keamanan untuk menghindari deteksi oleh sistem anti-bot platform target:", body))
    story.append(Spacer(1, 4))

    sec_data = [["#", "Fitur", "Deskripsi"]]
    sec_data += [
        ["1", "Fingerprint Browser Unik",
         "Canvas/WebGL/font fingerprint random per session. Setiap browser context punya fingerprint unik untuk menghindari correlating."],
        ["2", "Residential Proxy",
         "Support Bright Data, Smartproxy, IPRoyal. Residential proxy lebih sulit dideteksi dibanding datacenter proxy."],
        ["3", "TLS Fingerprint",
         "playwright-stealth auto-handle JA3/TLS fingerprint randomization agar browser tidak terdeteksi sebagai automation tool."],
        ["4", "WebGL/Canvas Noise",
         "Inject noise pada Canvas dan WebGL rendering sehingga fingerprint selalu unik dan tidak konsisten antar request."],
        ["5", "Geo-Spoofing",
         "Set timezone, locale, dan geolocation sesuai IP proxy. Browser terlihat seperti user asli dari lokasi proxy."],
        ["6", "Mouse Movement Simulation",
         "Simulasi hover-then-click dengan delay acak per step. Bukan click langsung, tapi gerakan mouse natural."],
        ["7", "Keyboard Typing Pattern",
         "page.type() dengan random delay per karakter (20-150ms). Occasional longer pause 0.5-1.5s untuk simulasi thinking."],
        ["8", "WebRTC Leak Protection",
         "Blokir RTCPeerConnection untuk mencegah IP asli bocor lewat WebRTC. Ganti IP di SDP dengan 0.0.0.0."],
        ["9", "Permissions Randomization",
         "Randomize permissions (camera, mic, notification) per session. Tidak semua session punya permission yang sama."],
        ["10", "Stealth Plugin",
         "playwright-stealth auto-apply scripts: navigator.webdriver undefined, chrome runtime hide, permissions query override."],
    ]
    story.append(feature_table(sec_data, [(W-2*MARGIN)*0.06, (W-2*MARGIN)*0.25, (W-2*MARGIN)*0.69]))
    story.append(Spacer(1, 8))

    # 2.2 Monitoring
    story.append(subsection("2.2 Monitoring (#11-20)"))
    story.append(Paragraph(
        "Sepuluh fitur monitoring untuk tracking dan debugging proses farming:", body))
    story.append(Spacer(1, 4))
    mon_data = [["#", "Fitur", "Deskripsi"]]
    mon_data += [
        ["11", "Real-time Dashboard",
         "FastAPI + HTMX web dashboard dengan SSE (Server-Sent Events). Stats update setiap 2 detik."],
        ["12", "Notifikasi Telegram/Discord",
         "Bot API Telegram dan Discord Webhook. Kirim notifikasi saat akun berhasil, gagal, atau ban rate tinggi."],
        ["13", "Screenshot Auto-Save",
         "Screenshot otomatis saat error, CAPTCHA gagal, atau ban detected. Simpan ke folder screenshots/"],
        ["14", "Error Screenshot per Account",
         "Screenshot per akun dengan nama error_{email}_{timestamp}.png untuk debugging spesifik."],
        ["15", "Progress Bar Console",
         "tqdm progress bar visual di terminal. Tampilkan ETA, rate/jam, dan percentage real-time."],
        ["16", "Export CSV/Excel",
         "Export hasil ke CSV dan Excel (multi-sheet: All Accounts, Verified, Failed, Summary)."],
        ["17", "Auto Log Rotation",
         "RotatingFileHandler (10MB per file) dan TimedRotatingFileHandler (daily). Logs tersimpan di folder logs/"],
        ["18", "Health Monitoring Page",
         "Endpoint /health untuk cek status database, proxy, mail provider, dan CAPTCHA service."],
        ["19", "Performance Metrics",
         "Track avg time/akun, throughput, success rate per jam, median time. Export ke JSON."],
        ["20", "Ban Rate Alert",
         "Auto-alert jika ban rate melebihi threshold (default 50%). Notifikasi via Telegram/Discord."],
    ]
    story.append(feature_table(mon_data, [(W-2*MARGIN)*0.06, (W-2*MARGIN)*0.25, (W-2*MARGIN)*0.69]))
    story.append(Spacer(1, 8))

    # 2.3 Fungsionalitas
    story.append(subsection("2.3 Fungsionalitas (#21-32)"))
    story.append(Paragraph(
        "Dua belas fitur fungsionalitas untuk efisiensi dan reliability:", body))
    story.append(Spacer(1, 4))
    func_data = [["#", "Fitur", "Deskripsi"]]
    func_data += [
        ["21", "Auto Login Verification",
         "Setelah verifikasi email, auto-login dan cek apakah akun benar-benar aktif dengan redirect ke dashboard."],
        ["22", "Profile Completion",
         "Auto-fill profil (nama, bio) setelah login berhasil. Simulasi setup awal user."],
        ["23", "Token/Session Save",
         "Simpan cookie dan localStorage ke database. Session bisa di-reuse untuk login tanpa re-register."],
        ["24", "Multi-Platform Support",
         "config/platforms.json dengan selector dan endpoint berbeda per platform. Mudah tambah platform baru."],
        ["25", "Rate Limiter per IP",
         "Track jumlah request per proxy IP. Auto-throttle jika melebihi max_per_ip dalam window time."],
        ["26", "Queue System",
         "Priority queue dengan throttle per batch. Batch processing dengan delay antar batch untuk avoid detection."],
        ["27", "Account Recovery",
         "Auto-retry akun yang stuck di status pending/verification_timeout. Recovery mode terpisah."],
        ["28", "Incremental Farming",
         "Cek jumlah akun di DB, lanjut dari progress terakhir. Tidak perlu mulai dari awal saat restart."],
        ["29", "Batch Configuration",
         "CLI args dan JSON config per batch. Batch size dan delay bisa di-override saat runtime."],
        ["30", "API Webhook Support",
         "Kirim hasil farming ke endpoint webhook eksternal. Format JSON dengan stats lengkap."],
        ["31", "Multi-Email Provider",
         "Mail.tm, 1sec-mail (free no API key), temp-mail, guerrilla mail. Auto-fallback jika satu provider gagal."],
        ["32", "Auto IP Rotation Verification",
         "Setiap proxy switch, verify IP baru match dengan yang diharapkan. Deteksi proxy failure lebih cepat."],
    ]
    story.append(feature_table(func_data, [(W-2*MARGIN)*0.06, (W-2*MARGIN)*0.25, (W-2*MARGIN)*0.69]))
    story.append(PageBreak())

    # ───────────────────────────────
    # 3. INSTALASI
    # ───────────────────────────────
    story += section_header("3. Instalasi")
    story.append(Paragraph("3.1 Persyaratan Sistem", h2))
    req_data = [
        [Paragraph("<b>Komponen</b>", body_left), Paragraph("<b>Minimum</b>", body_left), Paragraph("<b>Recommended</b>", body_left)],
        [Paragraph("Python", body_left), Paragraph("3.10+", body_left), Paragraph("3.11+", body_left)],
        [Paragraph("RAM", body_left), Paragraph("4 GB", body_left), Paragraph("8 GB+", body_left)],
        [Paragraph("Storage", body_left), Paragraph("2 GB", body_left), Paragraph("10 GB+", body_left)],
        [Paragraph("OS", body_left), Paragraph("Windows 10/11", body_left), Paragraph("Windows 11 / Linux", body_left)],
        [Paragraph("PostgreSQL", body_left), Paragraph("13+", body_left), Paragraph("15+", body_left)],
    ]
    story.append(env_table(req_data, [(W-2*MARGIN)*0.40, (W-2*MARGIN)*0.30, (W-2*MARGIN)*0.30]))

    story.append(Paragraph("3.2 Langkah Instalasi", h2))
    steps = [
        ("Clone Repository", "git clone https://github.com/Why94/account-farming-bot.git && cd account-farming-bot"),
        ("Virtual Environment", "python -m venv venv && venv\\Scripts\\activate  (Windows)  atau  source venv/bin/activate  (Linux/Mac)"),
        ("Install Dependencies", "pip install -r requirements.txt"),
        ("Install Playwright Browser", "playwright install chromium"),
        ("Setup Database", "Buat PostgreSQL database, jalankan schema.sql:  psql -U user -d dbname -f schema.sql"),
        ("Konfigurasi .env", "cp .env.example .env  lalu edit .env dengan kredensial Anda"),
        ("Jalankan", "python farmer.py  atau  python farmer.py -n 50 -w 10"),
    ]
    for title, cmd in steps:
        story.append(Paragraph(f"<b>{title}:</b>", label))
        story.append(Paragraph(cmd, code))
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # ───────────────────────────────
    # 4. KONFIGURASI .ENV
    # ───────────────────────────────
    story += section_header("4. Konfigurasi .env")
    story.append(Paragraph(
        "Semua konfigurasi dilakukan melalui file .env. Berikut penjelasan lengkap semua variabel:", body))
    story.append(Spacer(1, 6))

    # General
    story.append(subsection("4.1 General"))
    gen_data = [["Variabel", "Default", "Deskripsi"]]
    gen_data += [
        ["PASSWORD_DEFAULT", "AmanJaya123!@#", "Password default untuk semua akun baru"],
        ["MAX_WORKERS", "5", "Jumlah parallel workers (thread)"],
        ["JUMLAH_AKUN", "20", "Total akun yang akan di-farming"],
        ["MAX_RETRIES", "3", "Max retry per akun sebelum declare failed"],
        ["BASE_RETRY_DELAY", "5.0", "Base delay exponential backoff (detik)"],
        ["MAX_RETRY_DELAY", "60.0", "Max delay exponential backoff (detik)"],
        ["TARGET_URL", "https://...", "URL register platform target"],
    ]
    story.append(env_table(gen_data))
    story.append(Spacer(1, 8))

    # Proxy
    story.append(subsection("4.2 Proxy"))
    proxy_data = [["Variabel", "Default", "Deskripsi"]]
    proxy_data += [
        ["USE_PROXY_API", "true", "Aktifkan proxy rotation (true/false)"],
        ["PROXY_PROVIDER", "webshare", "Provider: webshare, brightdata, smartproxy, iproyal"],
        ["WEBSHARE_TOKEN", "TOKEN_ANDA", "Token API Webshare"],
        ["RESIDENTIAL_PROXY_PROVIDER", "", "Provider residential (brightdata, smartproxy, iproyal)"],
        ["RESIDENTIAL_PROXY_TOKEN", "", "Token residential proxy"],
        ["RATE_LIMIT_PER_IP", "3", "Max request per IP dalam window time"],
        ["RATE_LIMIT_WINDOW", "3600", "Window time rate limiter (detik)"],
    ]
    story.append(env_table(proxy_data))
    story.append(Spacer(1, 8))

    # Email
    story.append(subsection("4.3 Email Provider"))
    email_data = [["Variabel", "Default", "Deskripsi"]]
    email_data += [
        ["USE_MAIL_TM", "true", "Aktifkan Mail.tm temporary email"],
        ["USE_1SEC_MAIL", "true", "Aktifkan 1sec-mail (free, no API key)"],
        ["USE_TEMP_MAIL", "false", "Aktifkan temp-mail.org"],
        ["USE_GUERRILLA_MAIL", "false", "Aktifkan guerrillamail.com"],
        ["FALLBACK_DOMAIN", "domainkamu.my.id", "Domain catch-all fallback"],
    ]
    story.append(env_table(email_data))
    story.append(Spacer(1, 8))

    # Browser
    story.append(subsection("4.4 Browser & Keamanan"))
    browser_data = [["Variabel", "Default", "Deskripsi"]]
    browser_data += [
        ["HEADLESS", "true", "Run browser tanpa GUI (true/false)"],
        ["USE_STEALTH", "true", "Aktifkan playwright-stealth scripts"],
        ["INJECT_FINGERPRINT", "true", "Randomize fingerprint per session"],
        ["MOUSE_SIMULATION", "true", "Natural mouse click (hover-then-click)"],
        ["KEYBOARD_SIMULATION", "true", "Natural keyboard typing dengan delay"],
        ["WEBRTC_BLOCK", "true", "Blokir WebRTC leak protection"],
        ["PERMISSIONS_RANDOM", "true", "Randomize browser permissions"],
        ["GEO_SPOOF", "true", "Set geo-location sesuai proxy IP"],
        ["CANVAS_NOISE", "true", "Inject noise pada canvas fingerprinting"],
        ["USE_CAPTCHA", "true", "Aktifkan CAPTCHA solving via CapSolver"],
        ["CAPSOLVER_API_KEY", "API_KEY", "API key CapSolver (wajib jika USE_CAPTCHA=true)"],
    ]
    story.append(env_table(browser_data))
    story.append(Spacer(1, 8))

    # Database
    story.append(subsection("4.5 Database"))
    db_data = [["Variabel", "Default", "Deskripsi"]]
    db_data += [
        ["DATABASE_URL", "", "Connection string PostgreSQL (wajib diisi)"],
    ]
    story.append(env_table(db_data))
    story.append(Paragraph(
        "Format DATABASE_URL: postgres://user:password@host:port/dbname", note))
    story.append(Spacer(1, 8))

    # Notification
    story.append(subsection("4.6 Notifikasi"))
    notif_data = [["Variabel", "Default", "Deskripsi"]]
    notif_data += [
        ["NOTIFY_TELEGRAM", "false", "Aktifkan notifikasi Telegram"],
        ["TELEGRAM_BOT_TOKEN", "", "Token Telegram Bot dari @BotFather"],
        ["TELEGRAM_CHAT_ID", "", "Chat ID target (dapatkan dari @userinfobot)"],
        ["NOTIFY_DISCORD", "false", "Aktifkan notifikasi Discord"],
        ["DISCORD_WEBHOOK_URL", "", "Discord Webhook URL dari Server Settings"],
        ["WEBHOOK_ENABLED", "false", "Aktifkan generic webhook endpoint"],
        ["WEBHOOK_URL", "", "URL endpoint webhook untuk kirim data"],
        ["BAN_RATE_THRESHOLD", "50", "Threshold ban rate untuk trigger alert (%)"],
    ]
    story.append(env_table(notif_data))
    story.append(Spacer(1, 8))

    # Monitoring
    story.append(subsection("4.7 Monitoring & Export"))
    mon_env_data = [["Variabel", "Default", "Deskripsi"]]
    mon_env_data += [
        ["SCREENSHOT_ON_ERROR", "true", "Auto screenshot saat error"],
        ["SCREENSHOT_DIR", "./screenshots", "Folder penyimpanan screenshot"],
        ["ENABLE_DASHBOARD", "true", "Aktifkan web dashboard di port 8080"],
        ["DASHBOARD_PORT", "8080", "Port untuk dashboard web"],
        ["LOG_ROTATION", "daily", "Log rotation: daily atau size-based"],
        ["ENABLE_PROGRESS_BAR", "true", "Tampilkan tqdm progress bar di console"],
        ["EXPORT_CSV", "true", "Export hasil ke CSV"],
        ["EXPORT_EXCEL", "true", "Export hasil ke Excel (multi-sheet)"],
        ["EXPORT_DIR", "./exports", "Folder penyimpanan export files"],
        ["ENABLE_BATCH", "true", "Aktifkan batch processing"],
        ["BATCH_SIZE", "10", "Jumlah akun per batch"],
        ["BATCH_DELAY", "60", "Delay antar batch (detik)"],
    ]
    story.append(env_table(mon_env_data))
    story.append(PageBreak())

    # ───────────────────────────────
    # 5. ARSITEKTUR MODULAR
    # ───────────────────────────────
    story += section_header("5. Arsitektur Modular")
    story.append(Paragraph(
        "Proyek menggunakan arsitektur modular dengan 14 modul Python terpisah untuk maintainability dan readability:", body))
    story.append(Spacer(1, 6))

    mod_data = [["Modul", "Deskripsi", "Fitur"]]

    story.append(Paragraph("Struktur Direktori:", h2))
    story.append(Paragraph(
        "farmer.py              -> Main orchestrator (~200 lines)\n"
        "modules/\n"
        "  __init__.py         -> Package exports\n"
        "  config.py           -> Config parsing, CLI args, batch config\n"
        "  database.py          -> DB pool, CRUD, session save, incremental\n"
        "  proxy.py             -> Proxy fetch, health check, rotation, rate limiter\n"
        "  email_provider.py    -> Mail.tm, 1sec-mail, temp-mail, guerrilla\n"
        "  captcha.py           -> CapSolver (reCAPTCHA, hCaptcha, Turnstile)\n"
        "  browser.py           -> Stealth, fingerprint, mouse/keyboard, WebRTC\n"
        "  farming.py           -> Core farming logic, retry, queue, recovery\n"
        "  monitoring.py        -> Logging, screenshot, progress bar, metrics\n"
        "  notifications.py     -> Telegram, Discord, webhook, ban alert\n"
        "  export.py            -> CSV/Excel export\n"
        "  server/\n"
        "    dashboard.py        -> FastAPI + HTMX real-time dashboard\n"
        "    stealth.js         -> Anti-detect JavaScript scripts\n"
        "    templates/index.html -> Dashboard HTML template\n"
        "config/\n"
        "  platforms.json       -> Multi-platform configuration\n"
        "schema.sql              -> PostgreSQL table schema",
        code))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Modul Utama:", h2))

    modules_desc = [
        ("config.py",
         "Config management terpusat",
         "Parsing .env, CLI argument overrides, platform configs, validation"),
        ("database.py",
         "Database connection pool dan operasi CRUD",
         "Thread-safe PostgreSQL pool, save/update/check session, incremental farming, stats"),
        ("proxy.py",
         "Proxy lifecycle management",
         "Fetch dari Webshare/residential, health check, rotation, rate limit per IP, IP verify"),
        ("email_provider.py",
         "Multi-email provider abstraction",
         "Mail.tm, 1sec-mail (free), temp-mail, guerrilla mail, auto fallback"),
        ("captcha.py",
         "CAPTCHA solving via CapSolver",
         "Auto-detect reCAPTCHA/hCaptcha/Turnstile, polling dengan timeout"),
        ("browser.py",
         "Advanced browser setup dan stealth",
         "Stealth scripts, fingerprint injection, canvas noise, WebRTC block, geo-spoof, mouse/keyboard simulation"),
        ("farming.py",
         "Core farming engine",
         "Retry logic, exponential backoff, auto-login verification, profile completion, queue system, recovery"),
        ("monitoring.py",
         "Observability dan logging",
         "Rotating logs, screenshot capture, tqdm progress bar, performance metrics collector"),
        ("notifications.py",
         "Multi-channel notifications",
         "Telegram Bot API, Discord Webhook, generic webhook, ban rate threshold alert"),
        ("export.py",
         "Data export ke file",
         "CSV (streaming), Excel multi-sheet (All, Verified, Failed, Summary), single-account export"),
        ("server/dashboard.py",
         "Real-time web monitoring",
         "FastAPI + HTMX + SSE, stats endpoint, health check, stop/restart API"),
    ]

    mod_table_data = [["Modul", "Tanggung Jawab", "Fitur Utama"]] + [
        [Paragraph(f"<b>{m}</b>", body_left),
         Paragraph(t, body_left),
         Paragraph(f, body_left)]
        for m, t, f in modules_desc
    ]
    story.append(module_table(mod_table_data,
                               [(W-2*MARGIN)*0.20, (W-2*MARGIN)*0.30, (W-2*MARGIN)*0.50]))
    story.append(PageBreak())

    # ───────────────────────────────
    # 6. PANDUAN PENGGUNAAN
    # ───────────────────────────────
    story += section_header("6. Panduan Penggunaan")

    story.append(subsection("6.1 Perintah Dasar"))
    story.append(Paragraph("Jalankan farming dengan konfigurasi default (.env):", body))
    story.append(Paragraph("python farmer.py", code))

    story.append(Paragraph("Custom jumlah akun dan workers:", body))
    story.append(Paragraph("python farmer.py -n 50 -w 10", code))

    story.append(Paragraph("Overridetarget URL:", body))
    story.append(Paragraph("python farmer.py -t https://example.com/register", code))

    story.append(Paragraph("Disable dashboard dan headless browser:", body))
    story.append(Paragraph("python farmer.py --no-dashboard --no-headless", code))

    story.append(Paragraph("Gunakan platform spesifik dari platforms.json:", body))
    story.append(Paragraph("python farmer.py -p runway", code))

    story.append(Paragraph("Batch mode dengan custom size dan delay:", body))
    story.append(Paragraph("python farmer.py -n 100 --batch-size 20 --batch-delay 120", code))

    story.append(subsection("6.2 Mode Spesial"))
    mode_data = [
        [Paragraph("<b>Mode</b>", body_left), Paragraph("<b>Perintah</b>", body_left), Paragraph("<b>Deskripsi</b>", body_left)],
        [Paragraph("Export saja", body_left), Paragraph("python farmer.py --export-only", body_left),
         Paragraph("Export semua akun di DB ke CSV/Excel tanpa farming baru", body_left)],
        [Paragraph("Recovery", body_left), Paragraph("python farmer.py --recovery", body_left),
         Paragraph("Retry akun yang stuck di status pending/verification_timeout", body_left)],
        [Paragraph("Help", body_left), Paragraph("python farmer.py --help", body_left),
         Paragraph("Tampilkan semua opsi CLI yang tersedia", body_left)],
    ]
    story.append(env_table(mode_data))

    story.append(Spacer(1, 8))
    story.append(subsection("6.3 CLI Options Lengkap"))
    cli_data = [["Option", "Argumen", "Deskripsi"]]
    cli_data += [
        ["-w, --workers", "N", "Jumlah parallel workers (default dari .env)"],
        ["-n, --jumlah", "N", "Jumlah akun yang akan di-farming"],
        ["-r, --retries", "N", "Max retry per akun"],
        ["-t, --target", "URL", "Override TARGET_URL dari .env"],
        ["-p, --platform", "NAME", "Gunakan platform dari platforms.json"],
        ["--headless", "bool", "Browser mode: headless atau visible"],
        ["--no-dashboard", "-", "Disable web dashboard"],
        ["--batch-size", "N", "Override jumlah akun per batch"],
        ["--batch-delay", "N", "Override delay antar batch (detik)"],
        ["--recovery", "-", "Run account recovery mode"],
        ["--export-only", "-", "Hanya export, tidak farming"],
    ]
    story.append(cli_table(cli_data))

    story.append(Spacer(1, 8))
    story.append(subsection("6.4 Setup Database"))
    story.append(Paragraph("Jalankan schema.sql di PostgreSQL untuk membuat tabel:", body))
    story.append(Paragraph(
        "psql -U postgres -d farming_db -f schema.sql\n"
        "# Atau via pgAdmin/DBeaver: buka schema.sql dan execute",
        code))
    story.append(Paragraph(
        "Tabel stok_akun otomatis dibuat dengan kolom: id, kategori, data_akun, status, "
        "session_data, created_at, updated_at. Trigger auto-update updated_at sudah dikonfigurasi.",
        note))

    story.append(PageBreak())

    # ───────────────────────────────
    # 7. DASHBOARD REAL-TIME
    # ───────────────────────────────
    story += section_header("7. Dashboard Real-Time")
    story.append(Paragraph(
        "Dashboard web menyediakan monitoring real-time dari proses farming. "
        "Dashboard otomatis aktif saat ENABLE_DASHBOARD=true di .env.", body))

    story.append(Paragraph("Akses Dashboard:", h2))
    story.append(Paragraph("Buka browser dan kunjungi: http://127.0.0.1:8080", code))

    story.append(Paragraph("Fitur Dashboard:", h2))
    dash_features = [
        "Progress bar real-time dengan percentage dan ETA",
        "Statistik: Total, Sukses, Verified, Gagal, Success Rate",
        "Performance metrics: Avg time/akun, rate/jam, uptime",
        "Tabel recent accounts dengan status badge",
        "Tombol Stop untuk trigger graceful shutdown",
        "Tombol Export CSV untuk download data",
        "Health check endpoint /api/health",
        "SSE (Server-Sent Events) untuk update real-time setiap 2 detik",
    ]
    for f in dash_features:
        story.append(Paragraph(f"  - {f}", bullet))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Screenshot Preview:", h2))
    story.append(Paragraph(
        "Dashboard menampilkan 6 metric cards (Progress, Total, Sukses, Verified, Gagal, "
        "Success Rate), performance metrics grid (6 metrik), recent accounts table, dan "
        "control buttons (Refresh, Stop, Export). Background gelap (#0f172a) dengan accent "
        "blue (#3b82f6) untuk visual modern.", caption))
    story.append(Paragraph(
        "Screenshot bisa dilihat setelah menjalankan: python farmer.py",
        note))

    story.append(PageBreak())

    # ───────────────────────────────
    # 8. TROUBLESHOOTING
    # ───────────────────────────────
    story += section_header("8. Troubleshooting")

    ts_data = [
        [Paragraph("<b>Masalah</b>", body_left), Paragraph("<b>Penyebab</b>", body_left), Paragraph("<b>Solusi</b>", body_left)],
        [Paragraph("Dashboard tidak bisa diakses", body_left), Paragraph("Port 8080 sudah digunakan atau uvicorn error", body_left),
         Paragraph("Cek logs/, restart, atau ubah DASHBOARD_PORT di .env", body_left)],
        [Paragraph("Proxy gagal fetch", body_left), Paragraph("Token invalid atau provider down", body_left),
         Paragraph("Set USE_PROXY_API=false untuk farming tanpa proxy", body_left)],
        [Paragraph("Email verification timeout", body_left), Paragraph("Platform lambat kirim email atau inbox penuh", body_left),
         Paragraph("Tambah EMAIL_VERIFICATION_TIMEOUT di .env", body_left)],
        [Paragraph("Ban rate tinggi", body_left), Paragraph("Proxy terlalu sering, fingerprint terdeteksi", body_left),
         Paragraph("Aktifkan residential proxy, naikkan RATE_LIMIT_PER_IP, disable fingerprint", body_left)],
        [Paragraph("CAPTCHA gagal solve", body_left), Paragraph("API key invalid atau website baru", body_left),
         Paragraph("Verifikasi CAPSOLVER_API_KEY, cek capsolver.com dashboard", body_left)],
        [Paragraph("Database connection error", body_left), Paragraph("DATABASE_URL salah atau PostgreSQL down", body_left),
         Paragraph("Verifikasi format DATABASE_URL, cek PostgreSQL service", body_left)],
        [Paragraph("Browser tidak launch", body_left), Paragraph("Playwright browser belum terinstall", body_left),
         Paragraph("Jalankan: playwright install chromium", body_left)],
        [Paragraph("Module import error", body_left), Paragraph("Dependencies belum terinstall", body_left),
         Paragraph("pip install -r requirements.txt", body_left)],
        [Paragraph("403/429 Rate Limited", body_left), Paragraph("Terlalu banyak request ke satu IP", body_left),
         Paragraph("Aktifkan proxy, turunkan MAX_WORKERS, naikkan delay", body_left)],
    ]
    story.append(env_table(ts_data, [(W-2*MARGIN)*0.20, (W-2*MARGIN)*0.28, (W-2*MARGIN)*0.52]))

    story.append(PageBreak())

    # ───────────────────────────────
    # 9. DISCLAIMER
    # ───────────────────────────────
    story += section_header("9. Disclaimer")
    story.append(Paragraph(
        "Account Farming Bot v2.0 dibuat untuk tujuan educational dan authorized testing purposes ONLY. "
        "Penggunaan script ini untuk melanggar Terms of Service platform manapun, atau untuk aktivitas ilegal "
        "seperti registrasi massal untuk spam, fraud, atau penyalahgunaan lainnya adalah TIDAK DIIZINKAN dan "
        "merupakan tanggung jawab penuh pengguna.", body))
    story.append(Paragraph(
        "Pengembang tidak bertanggung jawab atas任何 kerusakan, kehilangan akses, atau konsekuensi hukum "
        "yang timbul dari penggunaan script ini. Selalu gunakan secara bertanggung jawab dan patuhi semua "
        "hukum dan regulasi yang berlaku di yurisdiksi Anda.", body))
    story.append(Paragraph(
        "Sebelum menggunakan bot ini pada platform apapun, pastikan Anda telah membaca dan memahami "
        "Terms of Service platform tersebut. Beberapa platform mungkin melarang automated account creation "
        "dan dapat mengambil tindakan hukum atau memblokir akses Anda.", body))

    story.append(Spacer(1, 1*cm))
    story.append(rule())
    story.append(Paragraph("Account Farming Bot v2.0 | Author: Aysel | 089698002242", caption))
    story.append(Paragraph("github.com/Why94/account-farming-bot", caption))
    story.append(Paragraph("Dokumentasi ini dibuat Juli 2026", caption))

    # ── Build ──
    doc.build(story)
    print(f"PDF generated: {OUTPUT}")

if __name__ == "__main__":
    build()