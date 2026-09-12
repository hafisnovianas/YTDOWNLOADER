/**
 * =========================================================
 * YT DOWNLOADER API - GOOGLE APPS SCRIPT CLIENT
 * =========================================================
 * 
 * Cara Penggunaan:
 * 1. Copy seluruh kode di file ini.
 * 2. Paste ke editor Google Apps Script (extensions > Apps Script).
 * 3. Ganti nilai "API_KEY" di bawah dengan API Key rahasia Anda.
 * 4. Jalankan fungsi runTest() untuk mencoba API.
 */

const API_BASE_URL = "https://yt.dijumper.web.id";
const API_KEY = "<MASUKKAN_API_KEY_ANDA_DISINI>"; // JANGAN COMMIT KEY ASLI KE GITHUB!

/**
 * 1. Fungsi untuk mendapatkan Info Video (Judul, Thumbnail, dll)
 * @param {string} youtubeUrl - Link YouTube
 * @returns {object|null} JSON Response dari API
 */
function getVideoInfo(youtubeUrl) {
  const endpoint = API_BASE_URL + "/info";
  
  const payload = {
    url: youtubeUrl,
    api_key: API_KEY
  };
  
  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true // Wajib agar script tidak crash jika kena Error 401/429
  };
  
  try {
    const response = UrlFetchApp.fetch(endpoint, options);
    const responseCode = response.getResponseCode();
    const json = JSON.parse(response.getContentText());
    
    if (responseCode === 200) {
      Logger.log("✅ Berhasil! Judul: " + json.data.title);
      return json;
    } else {
      Logger.log("❌ Error (" + responseCode + "): " + json.detail);
      return null;
    }
  } catch (e) {
    Logger.log("💥 Koneksi gagal: " + e.message);
    return null;
  }
}

/**
 * 2. Fungsi untuk Mendownload Video dan Mendapatkan Link Streaming
 * @param {string} youtubeUrl - Link YouTube
 * @param {string} quality - Resolusi (best, 1080, 720, 480, 360)
 * @returns {string|null} URL untuk mendownload/stream video
 */
function downloadVideo(youtubeUrl, quality = "720") {
  const endpoint = API_BASE_URL + "/file";
  
  const payload = {
    url: youtubeUrl,
    quality: quality,
    api_key: API_KEY
  };
  
  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(endpoint, options);
    const responseCode = response.getResponseCode();
    const json = JSON.parse(response.getContentText());
    
    if (responseCode === 200 && json.success) {
      Logger.log("✅ Video siap di server!");
      Logger.log("🎥 Link Video: " + json.data.downloadUrl);
      Logger.log("⚠️ File ini akan kedaluwarsa dalam: " + json.data.expiresIn);
      return json.data.downloadUrl;
    } else {
      Logger.log("❌ Error (" + responseCode + "): " + (json.detail || json.error));
      return null;
    }
  } catch (e) {
    Logger.log("💥 Koneksi gagal: " + e.message);
    return null;
  }
}

/**
 * ==========================================
 * CARA TESTING:
 * Pilih fungsi 'runTest' di dropdown menu atas, lalu klik "Run" (Jalankan)
 * ==========================================
 */
function runTest() {
  const testUrl = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
  
  Logger.log("--- MENGAMBIL INFO VIDEO ---");
  const info = getVideoInfo(testUrl);
  
  if (info) {
    Logger.log("\n--- MEMPROSES DOWNLOAD (720p) ---");
    const downloadUrl = downloadVideo(testUrl, "720");
    
    if (downloadUrl) {
      Logger.log("\n🎉 SELAMAT! API berjalan lancar dari Google Apps Script!");
    }
  }
}
