# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dukungan deteksi dan pembacaan otomatis file `cookies.txt` di `main.py` untuk otentikasi YouTube pada IP data center/VPS.
- Endpoint `GET /health` untuk memantau status aplikasi dan status pemuatan cookies (`cookies_loaded`).
- Skrip utilitas `create_cookies.py` untuk mengonversi cookie mentah dari browser Inspect ke format Netscape `cookies.txt`.
- Panduan penanganan anti-bot YouTube dan ekspor cookies di `DEPLOYMENT_GUIDE.md`.
- Integrasi `yt-dlp-ejs`, `remote_components: ["ejs:github"]`, dan `js_runtimes: "node"` untuk memecahkan enkripsi YouTube signature/n-challenge modern via Node.js.

### Changed
- Konfigurasi `yt-dlp` menambahkan fallback `player_client` (`android`, `ios`, `web`) untuk menghindari deteksi bot.
- Penanganan error di `main.py` diperjelas dengan instruksi solusi ketika bot detection terpicu.
- Dependensi `requirements.txt` diperbarui untuk mendukung rilis terbaru `yt-dlp`.
- Workflow CI/CD deployment (`.github/workflows/deploy.yml`) kini menyertakan `--upgrade` pada pip install.

### Fixed
- Error HTTP 500 `Sign in to confirm you’re not a bot` pada endpoint download di server VPS.
- Error `Requested format is not available` pada resolusi 720p/1080p dengan beralih ke selektor modern `bv*+ba/b` dan pemilahan resolusi berbasis `format_sort`.

### Security
- Mengabaikan file `cookies.txt`, `*.cookie`, dan `*.cookies` di `.gitignore` untuk melindungi keamanan akun YouTube.
