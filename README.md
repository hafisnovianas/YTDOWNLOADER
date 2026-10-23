# YouTube Downloader API

A simple, local, self-hosted API for downloading YouTube videos using `yt-dlp` and `ffmpeg`. It allows you to fetch video metadata and download videos at specific resolutions with fully merged audio and video, with support for cutting/clipping specific segments.

## Features
- **Fetch Metadata**: Get details like title, duration, views, thumbnails, and available formats.
- **Download & Serve**: Download YouTube videos (video + audio merged automatically via ffmpeg) directly to your server and serve them via a temporary static link.
- **Video Clipping / Trimming**: Download specific segments (start & end timestamps) efficiently without having to download the full video first.
- **Auto Cleanup**: Downloaded files are automatically deleted after 30 minutes to save storage.

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3 and FFmpeg installed on your system.
For Ubuntu:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python-is-python3 ffmpeg
```

Install the Python dependencies:
```bash
pip install -r requirements.txt
```

### Starting the Server
Start the development server using uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```
The server will be running at `http://localhost:3000`.

### UI Tester
You can test the API easily using the provided beautiful UI tester:
Just open `test-ui.html` in your browser.

---

## 📖 API Documentation

### 1. Health Check
Check if the API is running and see available endpoints.

- **Endpoint**: `GET /health` (or `GET /` to open UI Tester)
- **Response**:
```json
{
  "status": "ok",
  "message": "YT Downloader API is running",
  "cookies_loaded": true,
  "endpoints": {
    "health": "GET /health — Server health check & cookies status",
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
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "api_key": "YOUR_API_KEY"
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
- **Body Parameters**:
  - `url` (*string*, required): YouTube video URL.
  - `quality` (*string*, optional, default: `"best"`): Desired video quality.
  - `start_time` (*string* | *number*, optional): Start time for video trimming (e.g. `"00:30"`, `"01:05:20"`, or `90`).
  - `end_time` (*string* | *number*, optional): End time for video trimming (e.g. `"02:15"` or `135`).
  - `api_key` (*string*, optional): Security API Key.

**Supported Qualities**:
- `"best"`: Highest possible quality (Auto)
- `"1080"`: 1080p
- `"720"`: 720p
- `"480"`: 480p
- `"360"`: 360p
- `"worst"`: Lowest available quality

#### Example 1: Full Video Download
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "quality": "720",
  "api_key": "YOUR_API_KEY"
}
```

#### Example 2: Segment Clipping / Trimming (e.g., from 00:30 to 02:15)
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "quality": "720",
  "start_time": "00:30",
  "end_time": "02:15",
  "api_key": "YOUR_API_KEY"
}
```

- **Success Response (Full Video)**:
```json
{
  "success": true,
  "data": {
    "downloadUrl": "http://localhost:3000/files/1694406540123.mp4",
    "title": "Rick Astley - Never Gonna Give You Up",
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "duration": 213,
    "duration_string": "3:33",
    "resolution": "720p",
    "filename": "1694406540123.mp4",
    "filesize": 15000000,
    "expiresIn": "30 minutes"
  }
}
```

- **Success Response (Clipped Segment)**:
```json
{
  "success": true,
  "data": {
    "downloadUrl": "http://localhost:3000/files/1694406540123.mp4",
    "title": "Rick Astley - Never Gonna Give You Up",
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "duration": 213,
    "duration_string": "3:33",
    "resolution": "720p",
    "filename": "1694406540123.mp4",
    "filesize": 4200000,
    "expiresIn": "30 minutes",
    "clip": {
      "is_clipped": true,
      "start_time": "00:30",
      "end_time": "02:15",
      "clip_duration": 105.0,
      "clip_duration_string": "01:45"
    }
  }
}
```

---

## 🛠 Integrating with Google Apps Script

Since this API returns JSON, it can be easily integrated with Google Apps Script using `UrlFetchApp`. 

```javascript
function downloadYouTubeClip() {
  var url = "https://yt.dijumper.web.id/file";
  var payload = {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "720",
    "start_time": "00:30",    // Unduh klip mulai detik ke-30 (opsional)
    "end_time": "02:15",      // Selesai pada 02:15 (opsional)
    "api_key": "YOUR_API_KEY"
  };
  
  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };
  
  try {
    var response = UrlFetchApp.fetch(url, options);
    var data = JSON.parse(response.getContentText());
    
    if (data.success) {
      Logger.log("Download URL: " + data.data.downloadUrl);
      Logger.log("File Name: " + data.data.filename);
      if (data.data.clip) {
        Logger.log("Klip: " + data.data.clip.start_time + " s/d " + data.data.clip.end_time);
      }
    } else {
      Logger.log("Error: " + (data.detail || data.error));
    }
  } catch (e) {
    Logger.log("Failed to call API: " + e.message);
  }
}
```
