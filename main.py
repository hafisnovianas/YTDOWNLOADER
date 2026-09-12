import os
import time
import asyncio
import re
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI(title="YT Downloader API", version="1.0.0")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for temporary downloads
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Serve static files from downloads folder
app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

@app.get("/")
async def root():
    ui_path = os.path.join(os.path.dirname(__file__), "test-ui.html")
    if os.path.exists(ui_path):
        return FileResponse(ui_path)
    return {"message": "Welcome to YT Downloader API"}


# Models for Request Bodies
class InfoRequest(BaseModel):
    url: str

class FileRequest(BaseModel):
    url: str
    quality: str = "best"


# Helper Functions
def is_valid_youtube_url(url: str) -> bool:
    patterns = [
        r"^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+",
        r"^https?:\/\/youtu\.be\/[\w-]+",
        r"^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+",
    ]
    return any(re.match(p, url) for p in patterns)

def get_format_arg(quality: str) -> str:
    quality_map = {
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "worst": "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst",
        "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
        "720": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
        "480": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
        "360": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]",
    }
    return quality_map.get(quality, quality_map["best"])

async def cleanup_file(filepath: str, delay_seconds: int = 1800):
    """Wait for 'delay_seconds' and then delete the file."""
    await asyncio.sleep(delay_seconds)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Cleaned up: {filepath}")
    except Exception as e:
        print(f"Failed to clean up {filepath}: {str(e)}")


# ============================================
# GET /
# Health check
# ============================================
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "YT Downloader API is running",
        "endpoints": {
            "info": "POST /info — Get video info",
            "file": "POST /file — Download & serve video file",
        },
    }

# ============================================
# POST /info
# Get video metadata (title, thumbnail, formats)
# ============================================
@app.post("/info")
async def get_video_info(req: InfoRequest):
    if not is_valid_youtube_url(req.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    ydl_opts = {
        "dump_single_json": True,
        "extract_flat": False,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        # Run synchronous yt-dlp call in a thread
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(req.url, download=False)

        info = await asyncio.to_thread(extract)

        formats = []
        if "formats" in info:
            for f in info["formats"]:
                if f.get("vcodec") != "none" and f.get("ext") == "mp4":
                    formats.append({
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "resolution": f.get("resolution"),
                        "filesize": f.get("filesize") or f.get("filesize_approx"),
                        "fps": f.get("fps"),
                        "vcodec": f.get("vcodec"),
                        "acodec": f.get("acodec"),
                    })

        return {
            "success": True,
            "data": {
                "id": info.get("id"),
                "title": info.get("title"),
                "description": info.get("description", "")[:200] if info.get("description") else None,
                "duration": info.get("duration"),
                "duration_string": info.get("duration_string"),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
                "upload_date": info.get("upload_date"),
                "formats": formats
            },
        }

    except Exception as e:
        print(f"Error getting info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# POST /file
# Download video to server and return a servable link
# ============================================
@app.post("/file")
async def download_video_file(req: FileRequest, request: Request, background_tasks: BackgroundTasks):
    if not is_valid_youtube_url(req.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    format_arg = get_format_arg(req.quality)
    filename = str(int(time.time()))
    output_template = os.path.join(DOWNLOAD_DIR, f"{filename}.%(ext)s")

    ydl_opts = {
        "format": format_arg,
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }

    print(f"Downloading: {req.url}")

    try:
        def extract_and_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(req.url, download=True)
                return info

        info = await asyncio.to_thread(extract_and_download)

        # Find the downloaded file
        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith(filename)]
        if not files:
            raise Exception("Download completed but file not found")

        downloaded_file = files[0]
        filepath = os.path.join(DOWNLOAD_DIR, downloaded_file)
        filesize = os.path.getsize(filepath)

        # Build download URL
        host = request.headers.get("host")
        protocol = request.url.scheme
        
        # When behind a proxy (like Nginx), request.url.scheme might be http
        # while the actual request is https. Trust X-Forwarded-Proto if available.
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto:
            protocol = forwarded_proto

        download_url = f"{protocol}://{host}/files/{downloaded_file}"

        # Schedule cleanup in background after 30 minutes
        background_tasks.add_task(cleanup_file, filepath, 1800)

        return {
            "success": True,
            "data": {
                "downloadUrl": download_url,
                "title": info.get("title", "Unknown"),
                "filename": downloaded_file,
                "filesize": filesize,
                "expiresIn": "30 minutes",
            }
        }

    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Make sure this matches the port you expect to run on locally. 
    # Usually you start it via `uvicorn main:app --host 0.0.0.0 --port 8000`
    uvicorn.run(app, host="0.0.0.0", port=8000)
