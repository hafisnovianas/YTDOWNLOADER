# Panduan Lengkap: Setup Nginx, Custom Domain, & SSL (HTTPS) di VPS

**Tags:** `Nodejs`, `Nginx`, `SSL`, `VPS`, `Tutorial Pemula`, `BestPractice`

---

## 🌟 Pendahuluan: Mengapa Kita Membutuhkan Nginx?

Bayangkan Anda memiliki sebuah restoran (Aplikasi Anda yang berjalan di port 8000). Saat ini, pelanggan yang ingin makan harus masuk lewat pintu belakang dan menyebutkan nomor ruangan secara spesifik (contoh: `http://123.45.67.89:8000`). Tentu ini kurang bagus dan kurang aman.

Di sinilah **Nginx** berperan. Nginx bertindak seperti **Resepsionis** di pintu depan utama (Port 80/HTTP dan 443/HTTPS). 
Ketika ada pelanggan (user) yang datang mengunjungi website Anda, Resepsionis (Nginx) akan menyambut mereka dan secara diam-diam mengambilkan makanan dari pintu belakang (Port 8000) lalu menyajikannya ke pelanggan.

**Keuntungan menggunakan Nginx:**
1. **Lebih Profesional:** User tidak perlu mengetikkan port `:8000` lagi.
2. **Keamanan Ekstra:** Pintu belakang (Port 8000) bisa kita kunci rapat dari publik, sehingga hacker tidak bisa langsung menyerang aplikasi Anda.
3. **Mendukung SSL/HTTPS:** Nginx memungkinkan kita memasang "gembok hijau" (sertifikat keamanan SSL) dengan mudah.

Mari kita mulai langkah demi langkah! Asumsinya, aplikasi Anda saat ini sedang menyala di Port `8000` menggunakan PM2 atau sejenisnya.

---

## Langkah 1: Install Nginx di VPS

Buka terminal SSH VPS Anda (Ubuntu/Debian), lalu jalankan perintah berikut untuk memperbarui daftar paket dan menginstal Nginx:

```bash
sudo apt update
sudo apt install -y nginx
```

---

## Langkah 2: Setup Nginx sebagai *Reverse Proxy*

Sekarang kita akan mengajari "Resepsionis" kita cara meneruskan permintaan pengunjung ke port 8000.

1. **Buat file konfigurasi baru:**
   Kita akan membuat file bernama `aplikasi-kita` (Anda bisa menggantinya dengan nama project Anda).
   ```bash
   sudo nano /etc/nginx/sites-available/aplikasi-kita
   ```

2. **Isi Konfigurasi:**
   *Copy* dan *Paste* kode di bawah ini ke dalam terminal Anda:
   ```nginx
   server {
       # Nginx mendengarkan di pintu utama (Port 80)
       listen 80;
       listen [::]:80;
   
       # Jika Anda belum punya domain, gunakan garis bawah (_)
       # Jika sudah punya domain, ganti dengan: server_name domainanda.com;
       server_name _;
   
       # Meneruskan traffic ke port 8000 (Aplikasi Anda)
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```
   *(Cara Simpan di Nano: Tekan `Ctrl + X`, ketik `Y`, lalu tekan `Enter`)*

3. **Aktifkan Konfigurasi & Restart Nginx:**
   Jalankan baris perintah ini satu per satu:
   ```bash
   # 1. Mengaktifkan konfigurasi yang baru dibuat
   sudo ln -s /etc/nginx/sites-available/aplikasi-kita /etc/nginx/sites-enabled/
   
   # 2. Menghapus konfigurasi default bawaan (agar tidak bentrok)
   # ⚠️ CATATAN: Jika server ini sudah menjalankan aplikasi Nginx lain di konfigurasi 'default', JANGAN jalankan perintah ini agar aplikasi lama tidak mati!
   sudo unlink /etc/nginx/sites-enabled/default
   
   # 3. Mengecek apakah ada typo/salah ketik (pastikan outputnya "syntax is ok")
   sudo nginx -t
   
   # 4. Me-reload Nginx agar aturan baru mulai berlaku
   # Kita menggunakan 'reload' (bukan restart) agar koneksi di aplikasi Nginx Anda yang lain tidak terputus (zero downtime).
   sudo systemctl reload nginx
   ```

🎉 **Testing Langkah 2:** Buka browser dan ketikkan IP VPS Anda (contoh: `http://123.45.67.89`) tanpa `:8000`. Jika aplikasi Anda muncul, berarti Nginx sudah sukses bekerja!

---

## Langkah 3: Kunci Pintu Belakang (Tutup Port 8000)

Ini langkah keamanan yang sangat penting. Karena Nginx sudah menangani pengunjung di pintu depan (Port 80), kita harus menutup port 8000 dari akses publik.

1. Pergi ke *dashboard* penyedia VPS Anda (AWS, DigitalOcean, Hostinger, dll).
2. Cari menu **Firewall** atau **Security Groups**.
3. **Hapus** aturan yang mengizinkan lalu lintas masuk (Inbound) ke port `8000`.
4. Pastikan hanya port **80 (HTTP)**, **443 (HTTPS)**, dan **22 (SSH)** yang dibiarkan terbuka.

🎉 **Testing Langkah 3:** Coba akses `http://123.45.67.89:8000` di browser. Halaman seharusnya *loading* terus dan akhirnya *error*. Ini berarti port sudah berhasil dikunci dari luar.

---

## Langkah 4: Menghubungkan Custom Domain (Opsional)

Jika Anda ingin aplikasi Anda diakses melalui alamat seperti `namaproject.domainanda.com`, ikuti langkah ini. Jika Anda hanya ingin menggunakan IP Address saja, Anda bisa berhenti di sini.

1. **Setting DNS (A Record):**
   Masuk ke tempat Anda membeli domain (Niagahoster, Rumahweb, dll). Tambahkan **A Record** baru:
   - **Name:** isi dengan nama awalan (misal: `api`, `app`, atau `@` untuk domain utama).
   - **Target/IP:** isi dengan alamat IP VPS Anda.

2. **Beritahu Nginx tentang Domain Anda:**
   Buka kembali file konfigurasi Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/aplikasi-kita
   ```
   Ubah baris `server_name _;` menjadi nama domain Anda:
   ```nginx
   server_name namaproject.domainanda.com;
   ```
   Simpan, lalu reload Nginx:
   ```bash
   sudo systemctl reload nginx
   ```

🎉 **Testing Langkah 4:** Akses `http://namaproject.domainanda.com` di browser Anda. Aplikasi Anda seharusnya muncul! 
*(Note: Jika Anda iseng menambahkan `https://` dan terjadi error, itu wajar karena gembok keamanannya belum kita pasang di Langkah 5).*

---

## Langkah 5: Instalasi SSL/HTTPS (Gembok Keamanan)

Sertifikat SSL membuat koneksi antara pengunjung dan server Anda menjadi terenkripsi (aman). Kita akan menggunakan **Certbot** dari Let's Encrypt, yang 100% gratis.

1. **Install Certbot:**
   Jalankan perintah ini di terminal:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   ```

2. **Pasang SSL Secara Otomatis:**
   Jalankan perintah ini (jangan lupa ganti dengan domain Anda yang sesungguhnya):
   ```bash
   sudo certbot --nginx -d namaproject.domainanda.com
   ```
   - Certbot akan meminta alamat email Anda (untuk notifikasi perpanjangan SSL).
   - Akan ada pertanyaan konfirmasi Terms of Service (Ketik `Y`).
   - Ketika ditanya apakah ingin me-*redirect* otomatis pengunjung HTTP ke HTTPS, **sangat disarankan untuk memilih opsi Redirect**.

🎉 **Selesai!** Coba buka lagi domain Anda di browser. Anda sekarang akan melihat ikon **Gembok (Secure)** di sebelah alamat website Anda.

---

### 🎊 Kesimpulan
Selamat! Anda telah belajar men-deploy aplikasi secara profesional. Aplikasi Anda kini tersembunyi dengan aman di belakang Nginx, bisa diakses menggunakan nama domain yang cantik, dan lalu lintas datanya sudah terenkripsi secara otomatis menggunakan HTTPS!