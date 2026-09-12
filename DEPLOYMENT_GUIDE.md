# Panduan Hosting & CI/CD dari GitHub ke VPS 

Karena aplikasi ini membutuhkan **Node.js**, **FFmpeg**, dan **yt-dlp**, panduan ini difokuskan pada penggunaan VPS (misalnya DigitalOcean, AWS, Hostinger, atau server lokal dengan Ubuntu/Debian) yang dikombinasikan dengan otomatisasi **GitHub Actions**.

Dengan cara ini, setiap kali kamu melakukan `git push` ke GitHub, GitHub Actions akan masuk (SSH) ke VPS kamu secara otomatis, menarik update terbaru, dan me-restart server.

---

## Prasyarat di VPS
Sebelum menyiapkan CI/CD, pastikan VPS kamu sudah siap:
1. **Akses SSH** ke VPS kamu berfungsi.
2. **Python 3, pip, dan FFmpeg** sudah terinstall:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv python-is-python3 ffmpeg
   ```
3. **PM2** terinstall (digunakan untuk menjaga aplikasi tetap berjalan di background). Kamu bisa menginstalnya via npm (jika ada Node.js) atau menggunakan alternatif lain, namun panduan ini mengasumsikan kamu memakai PM2:
   ```bash
   sudo apt install npm -y
   sudo npm install -g pm2
   ```
2. **Git** sudah terinstall.
3. (Opsional tapi disarankan) Install **Nginx** sebagai Reverse Proxy untuk meneruskan trafik HTTP port 80/443 ke port 3000 lokal.

### 1. Setup Awal Virtual Environment (Lakukan sekali di VPS)
Sebelum GitHub Actions bisa men-deploy aplikasi secara otomatis, kamu perlu menyiapkan folder target dan membuat Virtual Environment (venv) di VPS kamu secara manual *satu kali*:
```bash
mkdir -p ~/ytdownloader
cd ~/ytdownloader
python3 -m venv venv
```

---

## Langkah-langkah Setup CI/CD

### 2. Siapkan SSH Key di GitHub
Agar GitHub Actions bisa me-remote VPS kamu secara otomatis dan aman, kita perlu memasukkan rahasia koneksi (Secrets) ke repository GitHub.

- Masuk ke repository GitHub kamu.
- Pergi ke tab **Settings** -> **Secrets and variables** -> **Actions**.
- Klik **New repository secret** untuk masing-masing variabel berikut:
  - `HOST`: Isi dengan IP Address publik VPS kamu (contoh: `123.45.67.89`).
  - `USERNAME`: Username untuk login ke VPS (biasanya `root` atau `ubuntu`).
  - `SSH_KEY`: Isi dengan **Private Key SSH** dari VPS kamu.
    *(Cara mendapatkannya: di VPS kamu jalankan `cat ~/.ssh/id_rsa`, salin semua text dari `-----BEGIN RSA PRIVATE KEY-----` sampai `-----END RSA PRIVATE KEY-----`. Jika belum punya, buat dulu dengan `ssh-keygen -t rsa` di VPS).*

### 3. Buat File Workflow GitHub Actions
Langkah ini dilakukan di kode lokal kamu:

1. Buat folder bernama `.github` di root direktori project kamu.
2. Di dalamnya buat folder `workflows`.
3. Di dalam folder `workflows`, buat file bernama `deploy.yml`. 
   Struktur foldernya: `.github/workflows/deploy.yml`
4. Isi file `deploy.yml` tersebut dengan kode berikut:

```yaml
name: Deploy to VPS

on:
  push:
    branches:
      - main # Workflow akan berjalan otomatis setiap ada push ke branch main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Copy files to VPS (Auto create folder)
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          source: "."
          target: "/home/${{ secrets.USERNAME }}/ytdownloader"
          strip_components: 0

      - name: Install & Restart Server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            # Masuk ke folder yang baru saja dibuat & dicopy oleh langkah sebelumnya
            cd /home/${{ secrets.USERNAME }}/ytdownloader
            
            # Install dependensi (sangat aman dijalankan tiap deploy)
            venv/bin/pip install -r requirements.txt
            
            # Restart aplikasi menggunakan PM2 (restart gracefully)
            pm2 restart ytdownloader || pm2 start "venv/bin/python main.py" --name "ytdownloader"
            pm2 save
```

### 4. Push ke GitHub
Simpan file `deploy.yml` tadi. Lakukan *commit* dan *push* perubahan tersebut ke GitHub:

```bash
git add .
git commit -m "Menambahkan script CI/CD GitHub Actions"
git push origin main
```

Setelah push berhasil, kamu bisa membuka tab **Actions** di halaman repository GitHub kamu. Di sana kamu akan melihat proses *deploy* sedang berjalan otomatis. Jika statusnya *green/success*, artinya kodemu sudah berhasil terkirim dan server berhasil di-restart!

---

## Catatan Penting
- **Penyimpanan (Storage):** Endpoint `/file` akan menyimpan file sementara di folder `downloads/`. Aplikasi ini sudah diatur agar otomatis menghapusnya setelah 30 menit. Pastikan kapasitas disk VPS kamu cukup (minimal 10GB+) jika aplikasi ini mendownload file video besar secara rutin.
- **Batasan IP (Rate Limiting):** YouTube terkadang mendeteksi dan memblokir IP dari data center besar (seperti AWS atau DigitalOcean) jika terlalu sering mendownload video dalam waktu singkat. Jika API kamu nanti mulai memunculkan pesan error seperti `Sign in to confirm you're not a bot` atau error 403, kamu perlu menggunakan metode *Cookies* di yt-dlp, menggunakan proxy rotasi, atau mencari VPS provider yang *residential IP*.
