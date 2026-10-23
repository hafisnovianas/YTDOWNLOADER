# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Fitur pemotongan cuplikan video (*video clipping/trimming*) berdasarkan rentang waktu (`start_time` & `end_time`) pada endpoint `POST /file`.
- Dukungan parser timestamp fleksibel yang menerima detik numerik (`90`), menit-detik (`MM:SS`), dan jam-menit-detik (`HH:MM:SS`).
- Integrasi callback native `download_ranges` dan `force_keyframes_at_cuts: True` pada `yt-dlp` untuk pemotongan stream yang akurat dan hemat bandwidth VPS.
- Metadata respon `clip` pada `POST /file` (`start_time`, `end_time`, `clip_duration`, `clip_duration_string`).
- Kolom input waktu mulai & selesai pada UI tester `test-ui.html` beserta tampilan rincian durasi klip pada kartu video.
- Dokumentasi parameter pemotongan cuplikan dan contoh integrasi Google Apps Script di `README.md`.

## [1.0.0] - 2026-10-23

### Added
- Dukungan deteksi dan pembacaan otomatis file `cookies.txt` di `main.py` untuk otentikasi YouTube pada IP data center/VPS.
- Endpoint `GET /health` untuk memantau status aplikasi dan status pemuatan cookies (`cookies_loaded`).
- Skrip utilitas `create_cookies.py` untuk mengonversi cookie mentah dari browser Inspect ke format Netscape `cookies.txt`.
- Panduan penanganan anti-bot YouTube dan ekspor cookies di `DEPLOYMENT_GUIDE.md`.
- Integrasi `yt-dlp-ejs`, `remote_components: ["ejs:github"]`, dan `js_runtimes: "deno"` untuk memecahkan enkripsi YouTube signature/n-challenge modern secara ringan via Deno.
- Metadata resolusi riil (`resolution`), durasi (`duration`), dan teks durasi (`duration_string`) pada respon data endpoint `POST /file`.

### Changed
- Konfigurasi `yt-dlp` menambahkan fallback `player_client` (`android`, `ios`, `web`) untuk menghindari deteksi bot.
- Penanganan error di `main.py` diperjelas dengan instruksi solusi ketika bot detection terpicu.
- Dependensi `requirements.txt` diperbarui untuk mendukung rilis terbaru `yt-dlp`.
- Workflow CI/CD deployment (`.github/workflows/deploy.yml`) kini menyertakan `--upgrade` pada pip install.
- Workflow CI/CD deployment (`.github/workflows/deploy.yml`) kini mendukung pembuatan otomatis virtual environment (`venv`) jika belum ada serta dukungan port kustom SSH (`PORT`).
- Dokumentasi `DEPLOYMENT_GUIDE.md` diperbarui dengan penambahan variabel secret `PORT` dan `YTDL_API_KEY` serta penyelarasan kode workflow.

### Fixed
- Error HTTP 500 `Sign in to confirm you’re not a bot` pada endpoint download di server VPS.
- Error `Requested format is not available` pada resolusi 720p/1080p dengan beralih ke selektor modern `bv*+ba/b` dan pemilahan resolusi berbasis `format_sort`.
- Error Deno crash `Failed to open IPC channel from NODE_CHANNEL_FD` saat berjalan di dalam proses PM2.
- Tampilan `Quality: -` pada kartu hasil download tester UI (`test-ui.html`) menjadi resolusi riil serta menampilkan info durasi dan masa berlaku file.

### Security
- Mengabaikan file `cookies.txt`, `*.cookie`, dan `*.cookies` di `.gitignore` untuk melindungi keamanan akun YouTube.
