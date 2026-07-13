#!/usr/bin/env python3
"""
generate_handbook.py - Panduan Cetak Biru Account Farming Bot v2.0 (REVISI)
Dokumen handbook untuk pemilik toko Telegram, sudah disesuaikan dengan
struktur kode modular terbaru (config via .env, 14 modul, dashboard, dll).
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, ListFlowable, ListItem, Preformatted
)
from reportlab.lib.colors import HexColor

# ---- Palette (blueprint) ----
NAVY     = HexColor('#0f172a')
ACCENT   = HexColor('#3b82f6')
TEXT     = HexColor('#1f2937')
MUTED    = HexColor('#6b7280')
WATER    = HexColor('#9ca3af')

W, H = A4
MARGIN = 2.0 * cm
OUTPUT = "Panduan_Account_Farming_Otomatis_v2_Revisi.pdf"

styles = getSampleStyleSheet()

def S(name, **kw):
    base = kw.pop('parent', 'Normal')
    return ParagraphStyle(name, parent=styles[base], **kw)

cover_title = S('CT', fontName='Helvetica-Bold', fontSize=26, textColor=colors.white,
                 leading=32, alignment=TA_CENTER, spaceAfter=4)
cover_sub   = S('CS', fontName='Helvetica', fontSize=13, textColor=colors.white,
                 leading=18, alignment=TA_CENTER, spaceAfter=3)
cover_meta  = S('CM', fontName='Helvetica', fontSize=10, textColor=HexColor('#cbd5e1'),
                 leading=14, alignment=TA_CENTER, spaceAfter=2)
warn        = S('Warn', fontName='Helvetica-Oblique', fontSize=9, textColor=HexColor('#fcd34d'),
                 leading=13, alignment=TA_CENTER, spaceAfter=2)

h1 = S('H1', fontName='Helvetica-Bold', fontSize=16, textColor=ACCENT,
        leading=22, spaceBefore=16, spaceAfter=6)
h2 = S('H2', fontName='Helvetica-Bold', fontSize=12, textColor=NAVY,
        leading=16, spaceBefore=10, spaceAfter=4)
body = S('Body', fontName='Helvetica', fontSize=10, textColor=TEXT,
          leading=15, alignment=TA_JUSTIFY, spaceAfter=6)
body_l = S('BodyL', fontName='Helvetica', fontSize=10, textColor=TEXT,
            leading=15, alignment=TA_LEFT, spaceAfter=4)
label = S('Label', fontName='Helvetica-Bold', fontSize=10, textColor=ACCENT,
           leading=14, spaceAfter=2)
code = S('Code', fontName='Courier', fontSize=8.5, textColor=HexColor('#111827'),
          leading=12, backColor=HexColor('#f1f5f9'), leftIndent=10, rightIndent=10,
          spaceBefore=4, spaceAfter=8)
note = S('Note', fontName='Helvetica-Oblique', fontSize=9, textColor=MUTED,
          leading=12, spaceAfter=4)
toc = S('TOC', fontName='Helvetica', fontSize=11, textColor=TEXT, leading=18)

def rule(c=ACCENT, t=1, sb=4, sa=6):
    return HRFlowable(width=W - 2*MARGIN, thickness=t, color=c, spaceBefore=sb, spaceAfter=sa)

def bullets(items, style=body_l):
    return ListFlowable(
        [ListItem(Paragraph(t, style), leftIndent=14, value='\u2022') for t in items],
        bulletType='bullet', start='\u2022', leftIndent=14, spaceAfter=6)

def table(data, widths, header=True, font=8.5):
    tbl = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), font),
        ('GRID', (0,0), (-1,-1), 0.3, HexColor('#d1d5db')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('TOPPADDING',(0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HexColor('#f8fafc')]),
    ]
    if header:
        style += [
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]
    tbl.setStyle(TableStyle(style))
    return tbl


def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN,
        title="Panduan Account Farming Otomatis v2.0 (Revisi)",
        author="Aysel | 089698002242",
    )
    story = []

    # ===================== COVER =====================
    story.append(Spacer(1, 2.2*cm))
    story.append(Paragraph("PANDUAN CETAK BIRU", cover_title))
    story.append(Paragraph("SISTEM ACCOUNT FARMING OTOMATIS", cover_title))
    story.append(Spacer(1, 0.3*cm))
    story.append(rule(colors.white, 1, 2, 6))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Produksi Akun Image-to-Video Massal untuk Toko Telegram", cover_sub))
    story.append(Paragraph("Versi 2.0 (Revisi) - Modular + Proxy Rotator + Mail.tm + Stealth + Dashboard", cover_sub))
    story.append(Paragraph("Update CAPTCHA Advanced, Turnstile, Mouse/Scroll Simulation, Real-time Dashboard", cover_sub))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("Kontak: 089698002242", cover_meta))
    story.append(Paragraph("GitHub: github.com/Why94/account-farming-bot", cover_meta))
    story.append(Spacer(1, 1.0*cm))
    story.append(Paragraph("PERINGATAN: Panduan ini untuk edukasi. Farming akun biasanya melanggar ToS platform AI. Gunakan dengan risiko sendiri.", warn))
    story.append(PageBreak())

    # ===================== DAFTAR ISI =====================
    story.append(Paragraph("DAFTAR ISI", h1))
    story.append(rule())
    toc_items = [
        "1.  Pendahuluan",
        "2.  Arsitektur & Tools",
        "3.  Persiapan Proxy (Webshare)",
        "4.  Konfigurasi (.env)  <- PALING PENTING",
        "5.  Setup Database (PostgreSQL)",
        "6.  Cara Menjalankan",
        "7.  CAPTCHA & Stealth",
        "8.  Dashboard Real-time",
        "9.  Multi-Platform (platforms.json)",
        "10. Tips & Disclaimer",
    ]
    for t in toc_items:
        story.append(Paragraph(t, toc))
    story.append(PageBreak())

    # ===================== 1. PENDAHULUAN =====================
    story.append(Paragraph("1. PENDAHULUAN", h1))
    story.append(rule())
    story.append(Paragraph(
        "Panduan ini membantu Anda menjalankan sistem otomatis untuk memproduksi akun pada platform "
        "AI Image-to-Video (Runway, Luma, Kling, dll) secara massal dan aman. Cocok untuk pemilik toko "
        "bot Telegram yang ingin mengontrol sendiri supply akun tanpa bergantung pihak ketiga.", body))
    story.append(Paragraph("Keunggulan Sistem Ini (32 Fitur):", h2))
    story.append(bullets([
        "Parallel farming (5-10 akun bersamaan via ThreadPoolExecutor)",
        "Proxy rotator otomatis + health check + rate limiter per IP",
        "Integrasi Mail.tm / 1sec-mail (gratis) atau Catch-All domain",
        "Stealth tinggi + human behavior simulation (mouse, keyboard, scroll)",
        "Support reCAPTCHA + hCaptcha + Cloudflare Turnstile via CapSolver",
        "Real-time Dashboard (FastAPI + HTMX) di port 8080",
        "Logging lengkap + screenshot otomatis + error handling",
        "Multi-platform via config JSON, recovery mode, incremental farming",
    ]))
    story.append(Paragraph(
        "PENTING: Versi ini menggunakan struktur MODULAR. Semua konfigurasi dilakukan lewat file "
        "<b>.env</b>, BUKAN dengan mengedit farmer.py seperti versi lama. Ikuti panduan bagian 4 dengan teliti.",
        note))
    story.append(PageBreak())

    # ===================== 2. ARSITEKTUR & TOOLS =====================
    story.append(Paragraph("2. ARSITEKTUR & TOOLS", h1))
    story.append(rule())
    story.append(Paragraph("Flow Kerja:", h2))
    story.append(Paragraph(
        "Python Parallel  &#8594;  Proxy Rotator (Webshare)  &#8594;  Stealth Playwright  &#8594;  "
        "Mail.tm / Catch-All  &#8594;  Daftar Akun  &#8594;  Solve CAPTCHA (CapSolver)  &#8594;  "
        "Simpan ke PostgreSQL  &#8594;  Export &amp; Notifikasi", body))

    story.append(Paragraph("Tools Wajib:", h2))
    story.append(bullets([
        "Python 3.10+ (direkomendasikan 3.11+)",
        "playwright + playwright-stealth (browser automation & anti-detect)",
        "psycopg2-binary (koneksi PostgreSQL)",
        "fastapi + uvicorn + jinja2 + pydantic (dashboard real-time)",
        "tqdm + pandas + openpyxl (progress & export)",
        "CapSolver API Key (untuk CAPTCHA)",
        "Webshare Residential Proxy (WAJIB untuk anti-ban)",
        "Mail.tm (gratis) atau domain sendiri + Cloudflare Catch-All",
        "PostgreSQL 13+ (database penyimpanan akun)",
    ]))

    story.append(Paragraph("Struktur Modular (14 modul):", h2))
    mod_data = [
        ["File", "Fungsi"],
        ["farmer.py", "Entry point / orchestrator utama"],
        ["modules/config.py", "Parse .env, CLI args, validasi konfigurasi"],
        ["modules/database.py", "Connection pool & CRUD PostgreSQL"],
        ["modules/proxy.py", "Fetch, health check, rotasi, rate limiter proxy"],
        ["modules/email_provider.py", "Mail.tm, 1sec-mail, temp-mail, guerrilla"],
        ["modules/captcha.py", "Solve CAPTCHA via CapSolver"],
        ["modules/browser.py", "Stealth, fingerprint, mouse/keyboard, WebRTC"],
        ["modules/farming.py", "Core logic: retry, queue, recovery, auto-login"],
        ["modules/monitoring.py", "Log, screenshot, progress bar, metrics"],
        ["modules/notifications.py", "Telegram, Discord, webhook, ban alert"],
        ["modules/export.py", "Export CSV / Excel"],
        ["modules/server/dashboard.py", "FastAPI + HTMX real-time dashboard"],
        ["config/platforms.json", "Selector & URL per platform"],
        ["schema.sql", "Schema tabel stok_akun PostgreSQL"],
    ]
    story.append(table(mod_data, [(W-2*MARGIN)*0.34, (W-2*MARGIN)*0.66]))
    story.append(PageBreak())

    # ===================== 3. PROXY =====================
    story.append(Paragraph("3. PERSIAPAN PROXY (WEBSHARE) - PALING PENTING", h1))
    story.append(rule())
    story.append(Paragraph(
        "JANGAN pakai proxy datacenter! Sangat mudah kena deteksi. Gunakan Residential Proxy.", body))
    story.append(Paragraph("Langkah Webshare:", h2))
    story.append(bullets([
        "Daftar di webshare.io",
        "Beli Residential Rotating (mulai 10-25 proxy)",
        "Settings &#8594; API &#8594; Copy Token",
        "Paste token ke file <b>.env</b> pada baris WEBSHARE_TOKEN=... (lihat bagian 4)",
        "Script otomatis ambil proxy baru + test koneksi setiap akun",
    ]))
    story.append(Paragraph(
        "Rekomendasi: Mulai dengan 10-25 proxy. Untuk 20 akun/hari cukup. Naikkan sesuai kebutuhan. "
        "Aktifkan juga residential proxy (Bright Data / Smartproxy / IPRoyal) untuk stealth maksimal.", note))
    story.append(PageBreak())

    # ===================== 4. KONFIGURASI .ENV (REVISI) =====================
    story.append(Paragraph("4. KONFIGURASI (.env)  -  PALING PENTING", h1))
    story.append(rule())
    story.append(Paragraph(
        "<b>PERBEDAAN DENGAN VERSI LAMA:</b> Di versi lama Anda mengedit variabel langsung di farmer.py "
        "(PROXY_CONFIG, CAPSOLVER_API_KEY, HEADLESS, dll). Di versi 2.0 SEMUA itu dipindah ke file "
        "<b>.env</b>. Anda TIDAK perlu menyentuh farmer.py sama sekali.", body))

    story.append(Paragraph("Langkah Konfigurasi:", h2))
    story.append(Paragraph("1. Copy template .env:", label))
    story.append(Preformatted("cp .env.example .env", code))
    story.append(Paragraph("2. Edit file .env, isi bagian WAJIB berikut:", label))
    story.append(Preformatted(
        "DATABASE_URL=postgres://user:pass@host:port/dbname\n"
        "TARGET_URL=https://www.runwayml.com/register\n"
        "WEBSHARE_TOKEN=isi_token_webshare_anda\n"
        "CAPSOLVER_API_KEY=isi_api_key_capsolver_anda", code))

    story.append(Paragraph("Variabel Penting (ringkasan):", h2))
    env_data = [
        ["Variabel .env", "Default", "Keterangan"],
        ["DATABASE_URL", "(kosong)", "WAJIB - koneksi PostgreSQL"],
        ["TARGET_URL", "example.com", "URL halaman register platform"],
        ["WEBSHARE_TOKEN", "(kosong)", "WAJIB jika proxy aktif"],
        ["CAPSOLVER_API_KEY", "(kosong)", "WAJIB jika CAPTCHA aktif"],
        ["MAX_WORKERS", "5", "Jumlah akun paralel"],
        ["JUMLAH_AKUN", "20", "Total akun yang dibuat"],
        ["HEADLESS", "true", "false = tampilkan browser (debug)"],
        ["USE_PROXY_API", "true", "false = jalan tanpa proxy"],
        ["USE_CAPTCHA", "true", "false = lewati CAPTCHA"],
    ]
    story.append(table(env_data, [(W-2*MARGIN)*0.34, (W-2*MARGIN)*0.18, (W-2*MARGIN)*0.48]))
    story.append(Paragraph(
        "Penjelasan lengkap semua variabel ada di file .env.example (terdapat komentar per baris). "
        "Untuk daftar 32 fitur & konfigurasi lanjutan, lihat Dokumentasi_Teknis yang dihasilkan generate_doc.py.", note))
    story.append(PageBreak())

    # ===================== 5. DATABASE =====================
    story.append(Paragraph("5. SETUP DATABASE (PostgreSQL)", h1))
    story.append(rule())
    story.append(Paragraph(
        "Bot menyimpan akun ke PostgreSQL. Anda butuh server PostgreSQL (bisa Railway, Neon, atau lokal). "
        "Jalankan schema.sql sekali saja untuk membuat tabel stok_akun:", body))
    story.append(Preformatted(
        "# Via psql CLI:\n"
        "psql -U user -d dbname -f schema.sql\n\n"
        "# Atau buka schema.sql di pgAdmin / DBeaver lalu Execute", code))
    story.append(Paragraph(
        "Tabel stok_akun berisi kolom: id, kategori, data_akun, status, session_data, created_at, "
        "updated_at. Pastikan DATABASE_URL di .env menunjuk ke database yang sudah di-setup.", note))
    story.append(PageBreak())

    # ===================== 6. CARA MENJALANKAN =====================
    story.append(Paragraph("6. CARA MENJALANKAN", h1))
    story.append(rule())
    story.append(Paragraph("Langkah Testing (Paling Aman):", h2))
    story.append(bullets([
        "Install dependencies: <font name='Courier'>pip install -r requirements.txt</font>",
        "Install browser: <font name='Courier'>playwright install chromium</font>",
        "Setup database (bagian 5) &amp; isi .env (bagian 4)",
        "Set HEADLESS=false di .env (biar kelihatan browser)",
        "Set JUMLAH_AKUN=3 &amp; MAX_WORKERS=2 dulu (testing kecil)",
        "Jalankan: <font name='Courier'>python farmer.py</font>",
        "Cek hasil di terminal, folder exports/, dan logs/",
        "Kalau berhasil, naikkan jumlahnya bertahap",
    ]))

    story.append(Paragraph("Perintah CLI Berguna:", h2))
    cli_data = [
        ["Perintah", "Fungsi"],
        ["python farmer.py", "Jalankan dengan config dari .env"],
        ["python farmer.py -n 50 -w 10", "50 akun, 10 worker paralel"],
        ["python farmer.py -p runway", "Gunakan platform 'runway' dari platforms.json"],
        ["python farmer.py --no-headless", "Tampilkan browser (debugging)"],
        ["python farmer.py --recovery", "Ulangi akun yang stuck (pending/timeout)"],
        ["python farmer.py --export-only", "Hanya export akun yg sudah ada ke CSV/Excel"],
        ["python farmer.py --no-dashboard", "Matikan web dashboard"],
        ["python test_dashboard.py", "Test dashboard saja tanpa farming"],
    ]
    story.append(table(cli_data, [(W-2*MARGIN)*0.45, (W-2*MARGIN)*0.55]))
    story.append(Paragraph(
        "Tips: Selalu test dulu dengan jumlah kecil. Pantau logs/ setiap hari untuk melihat error. "
        "Naikkan MAX_WORKERS & JUMLAH_AKUN secara bertahap setelah sukses.", note))
    story.append(PageBreak())

    # ===================== 7. CAPTCHA & STEALTH =====================
    story.append(Paragraph("7. CAPTCHA & STEALTH", h1))
    story.append(rule())
    story.append(Paragraph(
        "Script sudah support reCAPTCHA v2/v3 dan Cloudflare Turnstile via CapSolver. Jika sering gagal, coba: "
        "tambah delay, ganti task type di CapSolver, atau pakai proxy negara yang sama dengan target platform.", body))
    story.append(Paragraph("Stealth yang Sudah Ada:", h2))
    story.append(bullets([
        "Random User-Agent & Viewport per session",
        "Fingerprint Canvas/WebGL unik + noise injection",
        "Random delay + human typing/scroll",
        "Residential proxy berganti otomatis (IP rotation)",
        "WebRTC leak protection (blokir IP asli bocor)",
        "Geo-spoofing (timezone/locale ikut proxy)",
        "playwright-stealth untuk sembunyikan navigator.webdriver",
    ]))
    story.append(Paragraph(
        "Semua fitur stealth diatur lewat .env (USE_STEALTH, INJECT_FINGERPRINT, MOUSE_SIMULATION, "
        "KEYBOARD_SIMULATION, WEBRTC_BLOCK, GEO_SPOOF, CANVAS_NOISE). Default semuanya true.", note))
    story.append(PageBreak())

    # ===================== 8. DASHBOARD =====================
    story.append(Paragraph("8. DASHBOARD REAL-TIME", h1))
    story.append(rule())
    story.append(Paragraph(
        "Bot menyediakan dashboard web real-time (FastAPI + HTMX + SSE). Otomatis aktif saat ENABLE_DASHBOARD=true "
        "(default). Buka di browser:", body))
    story.append(Preformatted("http://localhost:8080", code))
    story.append(Paragraph("Fitur Dashboard:", h2))
    story.append(bullets([
        "6 metric card: Progress %, Total, Sukses, Verified, Gagal, Success Rate",
        "Performance metrics: Avg time/akun, Rate/hour, ETA, Uptime",
        "Tabel recent accounts dengan status badge",
        "Tombol Refresh, Stop, dan Export CSV",
        "Health check endpoint /api/health",
        "Update real-time tiap 2 detik via Server-Sent Events",
    ]))
    story.append(Paragraph(
        "Untuk mencoba dashboard TANPA farming (tanpa DB/proxy), jalankan: "
        "<font name='Courier'>python test_dashboard.py</font> lalu buka http://localhost:8080.", note))
    story.append(PageBreak())

    # ===================== 9. MULTI-PLATFORM =====================
    story.append(Paragraph("9. MULTI-PLATFORM (platforms.json)", h1))
    story.append(rule())
    story.append(Paragraph(
        "Anda bisa mendaftar ke banyak platform berbeda cukup dengan mengubah config platforms.json. "
        "Setiap platform punya selector CSS, URL register, dan indikator sukses/error sendiri.", body))
    story.append(Paragraph("Contoh isi platforms.json:", h2))
    story.append(Preformatted(
        '{\n'
        '  "platforms": [\n'
        '    {\n'
        '      "name": "runway",\n'
        '      "register_url": "https://www.runwayml.com/register",\n'
        '      "category": "ai",\n'
        '      "email_selector": "input[name=\'email\']",\n'
        '      "password_selector": "input[name=\'password\']",\n'
        '      "submit_selector": "button[type=\'submit\']",\n'
        '      "success_indicators": ["verify","welcome","success"],\n'
        '      "error_indicators": ["already exists","rate limit","blocked"]\n'
        '    }\n'
        '  ]\n'
        '}', code))
    story.append(Paragraph(
        "Jalankan dengan: <font name='Courier'>python farmer.py -p runway</font>. "
        "Jika tidak ada -p, bot pakai platform pertama atau TARGET_URL dari .env.", note))
    story.append(PageBreak())

    # ===================== 10. TIPS & DISCLAIMER =====================
    story.append(Paragraph("10. TIPS & DISCLAIMER", h1))
    story.append(rule())
    story.append(Paragraph("Produksi yang Bijak:", h2))
    story.append(bullets([
        "Jangan stok ribuan akun sekaligus (Just-In-Time production)",
        "Produksi sesuai volume penjualan toko Anda",
        "Monitor success rate proxy & ganti yang sering gagal",
        "Update script jika platform ubah sistem keamanan",
        "Gunakan residential proxy + stealth untuk hindari ban massal",
    ]))
    story.append(Paragraph(
        "DISCLAIMER: Panduan ini hanya untuk edukasi. Membuat akun massal di platform AI biasanya melanggar "
        "Terms of Service. Anda bertanggung jawab penuh atas semua risiko (ban, kerugian, hukum). Gunakan dengan "
        "bijak dan etis.", body))
    story.append(Spacer(1, 0.6*cm))
    story.append(rule(WATER, 0.5, 2, 4))
    story.append(Paragraph("Account Farming Bot v2.0 (Revisi) | Author: Aysel | 089698002242", note))
    story.append(Paragraph("github.com/Why94/account-farming-bot", note))

    doc.build(story)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build()
