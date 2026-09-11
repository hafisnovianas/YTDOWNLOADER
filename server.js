const express = require('express');
const cors = require('cors');
const ytdlp = require('yt-dlp-exec');
const ffmpeg = require('ffmpeg-static');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

// yt-dlp binary path (from yt-dlp-exec package)
const YT_DLP_PATH = require('yt-dlp-exec/src/constants').YOUTUBE_DL_PATH;

// Middleware
app.use(cors());
app.use(express.json());

// Directory untuk temporary downloads
const DOWNLOAD_DIR = path.join(__dirname, 'downloads');
if (!fs.existsSync(DOWNLOAD_DIR)) {
  fs.mkdirSync(DOWNLOAD_DIR, { recursive: true });
}

// Serve static files dari downloads folder
app.use('/files', express.static(DOWNLOAD_DIR));

// ============================================
// GET /
// Health check
// ============================================
app.get('/', (req, res) => {
  res.json({
    status: 'ok',
    message: 'YT Downloader API is running',
    endpoints: {
      info: 'POST /info — Get video info',
      file: 'POST /file — Download & serve video file',
    },
  });
});

// ============================================
// POST /info
// Get video metadata (title, thumbnail, formats)
// Body: { "url": "https://youtube.com/watch?v=..." }
// ============================================
app.post('/info', async (req, res) => {
  const { url } = req.body;

  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }

  if (!isValidYouTubeUrl(url)) {
    return res.status(400).json({ error: 'Invalid YouTube URL' });
  }

  try {
    const info = await ytdlp(url, {
      dumpSingleJson: true,
      noDownload: true,
      noWarnings: true,
      ffmpegLocation: ffmpeg,
    });

    res.json({
      success: true,
      data: {
        id: info.id,
        title: info.title,
        description: info.description?.substring(0, 200),
        duration: info.duration,
        duration_string: info.duration_string,
        thumbnail: info.thumbnail,
        uploader: info.uploader,
        view_count: info.view_count,
        upload_date: info.upload_date,
        formats: info.formats
          ?.filter((f) => f.vcodec !== 'none' && f.ext === 'mp4')
          .map((f) => ({
            format_id: f.format_id,
            ext: f.ext,
            resolution: f.resolution,
            filesize: f.filesize || f.filesize_approx,
            fps: f.fps,
            vcodec: f.vcodec,
            acodec: f.acodec,
          })),
      },
    });
  } catch (err) {
    console.error('Error getting info:', err.message);
    res.status(500).json({
      success: false,
      error: 'Failed to get video info',
      detail: err.message,
    });
  }
});



// ============================================
// POST /file
// Download video to server and return a servable link
// Body: { "url": "https://youtube.com/watch?v=...", "quality": "best" }
// Returns: { downloadUrl: "http://host/files/filename.mp4" }
// ============================================
app.post('/file', async (req, res) => {
  const { url, quality = 'best' } = req.body;

  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }

  if (!isValidYouTubeUrl(url)) {
    return res.status(400).json({ error: 'Invalid YouTube URL' });
  }

  try {
    const formatArg = getFormatArg(quality);
    const filename = `${Date.now()}`;
    const outputTemplate = path.join(DOWNLOAD_DIR, `${filename}.%(ext)s`);

    console.log(`Downloading: ${url}`);

    // Download using yt-dlp
    await ytdlp.exec(url, {
      format: formatArg,
      mergeOutputFormat: 'mp4',
      output: outputTemplate,
      noWarnings: true,
      ffmpegLocation: ffmpeg,
    });

    // Find the downloaded file
    const files = fs
      .readdirSync(DOWNLOAD_DIR)
      .filter((f) => f.startsWith(filename));

    if (files.length === 0) {
      throw new Error('Download completed but file not found');
    }

    const downloadedFile = files[0];
    const filePath = path.join(DOWNLOAD_DIR, downloadedFile);
    const stats = fs.statSync(filePath);

    // Get video title for metadata
    let title = 'Unknown';
    try {
      const info = await ytdlp(url, {
        dumpSingleJson: true,
        noDownload: true,
        noWarnings: true,
        ffmpegLocation: ffmpeg,
      });
      title = info.title;
    } catch (e) {
      // ignore
    }

    // Build the download URL
    const host = req.get('host');
    const protocol = req.protocol;
    const downloadUrl = `${protocol}://${host}/files/${downloadedFile}`;

    // Schedule cleanup after 30 minutes
    setTimeout(() => {
      try {
        if (fs.existsSync(filePath)) {
          fs.unlinkSync(filePath);
          console.log(`Cleaned up: ${downloadedFile}`);
        }
      } catch (e) {
        console.error(`Failed to clean up ${downloadedFile}:`, e.message);
      }
    }, 30 * 60 * 1000);

    res.json({
      success: true,
      data: {
        downloadUrl,
        title,
        filename: downloadedFile,
        filesize: stats.size,
        expiresIn: '30 minutes',
      },
    });
  } catch (err) {
    console.error('Error downloading file:', err.message);
    res.status(500).json({
      success: false,
      error: 'Failed to download video',
      detail: err.message,
    });
  }
});

// ============================================
// Helper Functions
// ============================================

function isValidYouTubeUrl(url) {
  const patterns = [
    /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
    /^https?:\/\/youtu\.be\/[\w-]+/,
    /^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+/,
  ];
  return patterns.some((p) => p.test(url));
}

function getFormatArg(quality) {
  // For /file downloads, we CAN merge them on the server using ffmpeg,
  // so we can use separated streams to get higher quality (like true 1080p).
  const qualityMap = {
    best: 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    worst: 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst',
    '1080':
      'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]',
    '720':
      'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
    '480':
      'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]',
    '360':
      'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]',
  };
  return qualityMap[quality] || qualityMap.best;
}

// ============================================
// Start Server
// ============================================
app.listen(PORT, () => {
  console.log(`\n🚀 YT Downloader API running on http://localhost:${PORT}`);
  console.log(`📦 yt-dlp binary: ${YT_DLP_PATH}`);
  console.log(`\nEndpoints:`);
  console.log(`  GET  /          — Health check`);
  console.log(`  POST /info      — Get video metadata`);
  console.log(`  POST /file      — Download & serve video file`);
  console.log('');
});
