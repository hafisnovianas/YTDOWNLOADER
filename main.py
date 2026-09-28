import os
import time
import asyncio
import re
import shutil
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
    allow_origins=[
        "https://yt.dijumper.web.id",
        "https://script.google.com",
        "https://script.googleusercontent.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for temporary downloads
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Cookie file path (used to authenticate requests and bypass YouTube bot detection)
COOKIE_FILE = os.getenv("YTDL_COOKIES_PATH", os.path.join(os.path.dirname(__file__), "cookies.txt"))

# Serve static files from downloads folder
app.mount("/files", StaticFiles(directory=DOWNLOAD_DIR), name="files")

# ============================================
# Security: API Key & Rate Limiting
# ============================================
from datetime import datetime, timedelta
from collections import defaultdict

API_KEY = os.getenv("YTDL_API_KEY", "ganti-key-ini-di-production")
request_counts = defaultdict(list)
RATE_LIMIT = 5
RATE_LIMIT_PERIOD = timedelta(hours=1)

def check_security(api_key: str, request: Request):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key. You are not authorized.")
        
    client_ip = request.client.host
    if request.headers.get("x-forwarded-for"):
        client_ip = request.headers.get("x-forwarded-for").split(",")[0]
        
    now = datetime.now()
    request_counts[client_ip] = [t for t in request_counts[client_ip] if now - t < RATE_LIMIT_PERIOD]
    
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail=f"Too Many Requests. Limit is {RATE_LIMIT} videos per hour.")
        
    request_counts[client_ip].append(now)

@app.get("/")
async def root():
    ui_path = os.path.join(os.path.dirname(__file__), "test-ui.html")
    if os.path.exists(ui_path):
        return FileResponse(ui_path)
    return {"message": "Welcome to YT Downloader API"}


# Models for Request Bodies
class InfoRequest(BaseModel):
    url: str
    api_key: str = ""

class FileRequest(BaseModel):
    url: str
    quality: str = "best"
    api_key: str = ""


# Helper Functions
def is_valid_youtube_url(url: str) -> bool:
    patterns = [
        r"^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+",
        r"^https?:\/\/youtu\.be\/[\w-]+",
        r"^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+",
    ]
    return any(re.match(p, url) for p in patterns)

def get_format_opts(quality: str) -> dict:
    """Mengembalikan opsi format dan format_sort modern untuk yt-dlp."""
    sort_rules = ["ext:mp4:m4a"]
    if quality in ["1080", "720", "480", "360"]:
        sort_rules = [f"res:{quality}", "ext:mp4:m4a"]
    elif quality == "worst":
        sort_rules = ["+res", "ext:mp4:m4a"]

    return {
        "format": "bv*+ba/b",
        "format_sort": sort_rules,
    }

async def cleanup_file(filepath: str, delay_seconds: int = 1800):
    """Wait for 'delay_seconds' and then delete the file."""
    await asyncio.sleep(delay_seconds)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Cleaned up: {filepath}")
    except Exception as e:
        print(f"Failed to clean up {filepath}: {str(e)}")


DENO_BIN = shutil.which("deno") or "/usr/local/bin/deno"

def get_base_ydl_opts() -> dict:
    """Konfigurasi dasar yt-dlp dengan dukungan cookies dan EJS challenge solver via Deno."""
    opts = {
        "js_runtimes": {
            "deno": {"path": DENO_BIN}
        },
        "remote_components": ["ejs:github"],
    }
    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0:
        opts["cookiefile"] = COOKIE_FILE
    return opts

# ============================================
# GET /health
# Health check & Cookie status
# ============================================
@app.get("/health")
def health_check():
    cookies_present = os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0
    return {
        "status": "ok",
        "message": "YT Downloader API is running",
        "cookies_loaded": cookies_present,
        "endpoints": {
            "health": "GET /health — Server health check & cookies status",
            "info": "POST /info — Get video info",
            "file": "POST /file — Download & serve video file",
        },
    }

# ============================================
# POST /info
# Get video metadata (title, thumbnail, formats)
# ============================================
@app.post("/info")
async def get_video_info(req: InfoRequest, request: Request):
    check_security(req.api_key, request)

    if not is_valid_youtube_url(req.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        "dump_single_json": True,
        "extract_flat": False,
    })

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
        err_msg = str(e)
        print(f"Error getting info: {err_msg}")
        if "Sign in to confirm you’re not a bot" in err_msg or "Sign in to confirm you're not a bot" in err_msg:
            err_msg = "YouTube bot detection triggered: Sign in to confirm you're not a bot. Silakan pasang cookies.txt di server atau update yt-dlp."
        raise HTTPException(status_code=500, detail=err_msg)

# ============================================
# POST /file
# Download video to server and return a servable link
# ============================================
@app.post("/file")
async def download_video_file(req: FileRequest, request: Request, background_tasks: BackgroundTasks):
    check_security(req.api_key, request)

    if not is_valid_youtube_url(req.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    format_opts = get_format_opts(req.quality)
    filename = str(int(time.time()))
    output_template = os.path.join(DOWNLOAD_DIR, f"{filename}.%(ext)s")

    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        **format_opts,
    })

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
        elif "localhost" not in host and "127.0.0.1" not in host:
            protocol = "https"

        download_url = f"{protocol}://{host}/files/{downloaded_file}"

        # Schedule cleanup in background after 30 minutes
        background_tasks.add_task(cleanup_file, filepath, 1800)

        return {
            "success": True,
            "data": {
                "downloadUrl": download_url,
                "title": info.get("title", "Unknown"),
                "thumbnail": info.get("thumbnail"),
                "filename": downloaded_file,
                "filesize": filesize,
                "expiresIn": "30 minutes",
            }
        }

    except Exception as e:
        err_msg = str(e)
        print(f"Error downloading file: {err_msg}")
        if "Sign in to confirm you’re not a bot" in err_msg or "Sign in to confirm you're not a bot" in err_msg:
            err_msg = "YouTube bot detection triggered: Sign in to confirm you're not a bot. Silakan pasang cookies.txt di server atau update yt-dlp."
        raise HTTPException(status_code=500, detail=err_msg)

if __name__ == "__main__":
    import uvicorn
    # Make sure this matches the port you expect to run on locally. 
    # Usually you start it via `uvicorn main:app --host 0.0.0.0 --port 8000`
    uvicorn.run(app, host="0.0.0.0", port=8000)
