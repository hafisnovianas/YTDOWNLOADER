# YouTube Downloader API

A simple, local, self-hosted API for downloading YouTube videos using `yt-dlp` and `ffmpeg`. It allows you to fetch video metadata and download videos at specific resolutions with fully merged audio and video.

## Features
- **Fetch Metadata**: Get details like title, duration, views, thumbnails, and available formats.
- **Download & Serve**: Download YouTube videos (video + audio merged automatically via ffmpeg) directly to your server and serve them via a temporary static link.
- **Auto Cleanup**: Downloaded files are automatically deleted after 30 minutes to save storage.

---

## 🚀 Getting Started

### Prerequisites
Make sure you have run the installation (if you haven't already):
```bash
npm install
```

### Starting the Server
Start the development server:
```bash
npm run dev
```
The server will be running at `http://localhost:3000`.

### UI Tester
You can test the API easily using the provided beautiful UI tester:
Just open `test-ui.html` in your browser.

---

## 📖 API Documentation

### 1. Health Check
Check if the API is running and see available endpoints.

- **Endpoint**: `GET /`
- **Response**:
```json
{
  "status": "ok",
  "message": "YT Downloader API is running",
  "endpoints": {
    "info": "POST /info — Get video info",
    "file": "POST /file — Download & serve video file"
  }
}
```

---

### 2. Get Video Info
Retrieve metadata about a YouTube video without downloading it.

- **Endpoint**: `POST /info`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

- **Success Response**:
```json
{
  "success": true,
  "data": {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration": 213,
    "duration_string": "3:33",
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "uploader": "Rick Astley",
    "view_count": 1400000000,
    "formats": [ ... array of available formats ... ]
  }
}
```

---

### 3. Download & Serve Video (`/file`)
Downloads the video to the server, merges the highest quality video and audio using `ffmpeg`, and returns a temporary URL where the file can be downloaded or streamed by the user.

> **Note:** The generated file link will expire and be deleted from the server after 30 minutes.

- **Endpoint**: `POST /file`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "quality": "720"
}
```
**Supported Qualities**:
- `"best"`: Highest possible quality (Auto)
- `"1080"`: 1080p
- `"720"`: 720p
- `"480"`: 480p
- `"360"`: 360p

- **Success Response**:
```json
{
  "success": true,
  "data": {
    "downloadUrl": "http://localhost:3000/files/1694406540123.mp4",
    "title": "Rick Astley - Never Gonna Give You Up",
    "filename": "1694406540123.mp4",
    "filesize": 15000000,
    "expiresIn": "30 minutes"
  }
}
```

---

## 🛠 Integrating with Google Apps Script

Since this API returns JSON, it can be easily integrated with Google Apps Script using `UrlFetchApp`. 
*(Make sure your API server is deployed online or accessible via a tool like ngrok/localtunnel if you want to call it from Apps Script)*.

```javascript
function downloadYouTubeVideo() {
  var url = "YOUR_API_URL/file";
  var payload = {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "720"
  };
  
  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload)
  };
  
  try {
    var response = UrlFetchApp.fetch(url, options);
    var data = JSON.parse(response.getContentText());
    
    if (data.success) {
      Logger.log("Download URL: " + data.data.downloadUrl);
    } else {
      Logger.log("Error: " + data.error);
    }
  } catch (e) {
    Logger.log("Failed to call API: " + e.message);
  }
}
```
