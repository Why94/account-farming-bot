# 🤖 Account Farming Bot v2.0

**Bot Registrasi Akun Otomatis** dengan 32 fitur advanced: stealth, multi-provider email, dashboard real-time, notifikasi, dan masih banyak lagi.

---

## 📋 Fitur Lengkap

### 🔐 Keamanan (Anti-Detect)
| # | Fitur | Keterangan |
|---|-------|-----------|
| 1 | **Fingerprint Browser Unik** | Canvas/webgl/font random per session |
| 2 | **Residential Proxy** | Bright Data, Smartproxy, IPRoyal |
| 3 | **TLS Fingerprint** | playwright-stealth auto-handle JA3/TLS |
| 4 | **WebGL/Canvas Noise** | Noise injection per session |
| 5 | **Geo-Spoofing** | Timezone, locale, geolocation match proxy |
| 6 | **Mouse Movement** | Hover-then-click natural |
| 7 | **Keyboard Typing Pattern** | page.type() + random delay per karakter |
| 8 | **WebRTC Leak Protection** | RTCPeerConnection block |
| 9 | **Permissions Random** | Camera/mic/notification random per session |
| 10 | **Stealth Plugin** | playwright-stealth auto-apply |

### 📊 Monitoring & Dashboard
| # | Fitur | Keterangan |
|---|-------|-----------|
| 11 | **Real-time Dashboard** | FastAPI + HTMX + SSE |
| 12 | **Notifikasi** | Telegram Bot, Discord Webhook |
| 13-14 | **Screenshot Auto** | Error & per akun |
| 15 | **Progress Bar** | Console visual |
| 16 | **Export CSV/Excel** | Multi-sheet Excel |
| 17 | **Auto Log Rotation** | Size & daily rotation |
| 18 | **Health Check** | /health endpoint |
| 19 | **Performance Metrics** | Time/akun, throughput, success rate |
| 20 | **Ban Rate Alert** | Auto-alert jika > threshold |

### ⚙️ Fungsionalitas
| # | Fitur | Keterangan |
|---|-------|-----------|
| 21 | **Auto Login Verification** | Cek akun benar-benar aktif |
| 22 | **Profile Completion** | Auto-fill profil |
| 23 | **Session Save** | Cookie & token disimpan |
| 24 | **Multi-Platform** | Config JSON per platform |
| 25 | **Rate Limiter** | Throttle per IP proxy |
| 26 | **Queue System** | Batch queue dengan throttle |
| 27 | **Account Recovery** | Auto-retry akun stuck |
| 28 | **Incremental Farming** | Lanjut dari progress terakhir |
| 29 | **Batch Config** | CLI args + JSON config |
| 30 | **Webhook Support** | Kirim hasil ke endpoint eksternal |
| 31 | **Multi-Email Provider** | Mail.tm, 1sec-mail, temp-mail, guerrilla |
| 32 | **IP Rotation Verify** | Verifikasi IP baru setelah proxy switch |

---

## 🚀 Instalasi

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Konfigurasi `.env`

```bash
cp .env.example .env
```

Edit `.env` dan isi:
- `DATABASE_URL` — Koneksi PostgreSQL
- `WEBSHARE_TOKEN` — Token proxy Webshare
- `CAPSOLVER_API_KEY` — API key CapSolver
- `TARGET_URL` — URL platform target
- (Opsional) Telegram/Discord webhook untuk notifikasi

### 3. Setup Database

```sql
-- Jalankan schema.sql di PostgreSQL
psql -U user -d dbname -f schema.sql
```

Atau gunakan psql GUI (pgAdmin, DBeaver, dll).

### 4. Jalankan

```bash
# Run default
python farmer.py

# 50 accounts, 10 workers
python farmer.py -n 50 -w 10

# Recovery mode (retry stuck accounts)
python farmer.py --recovery

# Export only (no farming)
python farmer.py --export-only

# Disable dashboard
python farmer.py --no-dashboard
```

---

## 📁 Struktur File

```
farmer.py              → Main orchestrator
modules/
├── config.py          → Config parsing & validation
├── database.py        → DB pool & CRUD
├── proxy.py           → Proxy management
├── email_provider.py  → Multi-email providers
├── captcha.py         → CapSolver integration
├── browser.py         → Stealth & anti-detect
├── farming.py         → Core farming logic
├── monitoring.py      → Logging, metrics, screenshots
├── notifications.py   → Telegram, Discord, webhook
├── export.py          → CSV/Excel export
└── server/
    └── dashboard.py   → FastAPI + HTMX dashboard
config/
└── platforms.json     → Platform selectors
screenshots/           → Auto-screenshots
exports/               → CSV/Excel exports
logs/                  → Rotating log files
```

---

## 🖥️ Dashboard

Saat dashboard aktif, buka:
```
http://localhost:8080
```

Menampilkan:
- Real-time progress bar & statistik
- Performance metrics (time/akun, rate/jam)
- Recent accounts table
- Stop button

---

## 📝 CLI Options

| Option | Description |
|--------|-------------|
| `-w, --workers N` | Number of parallel workers |
| `-n, --jumlah N` | Number of accounts |
| `-r, --retries N` | Max retries per account |
| `-t, --target URL` | Override target URL |
| `-p, --platform NAME` | Use specific platform |
| `--headless` / `--no-headless` | Browser mode |
| `--no-dashboard` | Disable web dashboard |
| `--recovery` | Recover stuck accounts |
| `--export-only` | Only export existing accounts |
| `--batch-size N` | Override batch size |
| `--batch-delay N` | Override batch delay |

---

## ⚠️ Disclaimer

Script ini dibuat untuk **educational & authorized testing purposes only**.
Penggunaan untuk melanggar Terms of Service atau kegiatan ilegal merupakan tanggung jawab pengguna.

---

## 📬 Kontak

Dibuat untuk **Aysel** | 089698002242
