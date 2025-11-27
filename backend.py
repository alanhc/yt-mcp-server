import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import glob
import uuid
import shutil
import yt_dlp
import re
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Dict, Optional
from datetime import datetime
import asyncio
import mlx_whisper

# Global variable to store the preloaded model path
WHISPER_MODEL_PATH = "mlx-community/whisper-base-mlx"

# Task storage
tasks: Dict[str, dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up server...")
    print(f"📥 Preloading mlx_whisper model: {WHISPER_MODEL_PATH}")
    try:
        import tempfile
        import numpy as np
        import wave
        
        # Create a minimal audio file to trigger model loading
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            with wave.open(tmp.name, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(np.zeros(16000, dtype=np.int16).tobytes())
            
            print("Loading model...")
            _ = mlx_whisper.transcribe(tmp.name, path_or_hf_repo=WHISPER_MODEL_PATH)
            os.unlink(tmp.name)
            
        print("✅ Model preloaded successfully!")
    except Exception as e:
        print(f"⚠️  Could not preload model: {e}")
        print("Model will be downloaded on first request instead.")
    
    yield
    print("👋 Shutting down server...")

app = FastAPI(
    title="yt-mcp-server",
    lifespan=lifespan,
    servers=[
        {
            "url": "https://dam-bell-dive-compared.trycloudflare.com",  # 例如 ngrok / cloudflare tunnel 網址
            "description": "Public HTTPS endpoint"
        }
    ],
)

class VideoRequest(BaseModel):
    url: str
    lang: str | None = None

def parse_vtt(vtt_content):
    lines = vtt_content.split('\n')
    cues = []
    
    # Regex for timestamp: 00:00:22.633 or 00:22.633
    time_pattern = re.compile(r'(\d{2}:)?(\d{2}):(\d{2})\.(\d{3})')
    
    current_start = None
    current_lines = []
    
    for line in lines:
        line = line.strip()
        if '-->' in line:
            # Save previous cue if exists
            if current_start is not None and current_lines:
                cues.append({'start': current_start, 'text': ' '.join(current_lines)})
            
            # New cue
            parts = line.split(' --> ')
            start_str = parts[0]
            match = time_pattern.match(start_str)
            if match:
                groups = match.groups()
                h = int(groups[0].replace(':', '')) if groups[0] else 0
                m = int(groups[1])
                s = int(groups[2])
                current_start = h * 3600 + m * 60 + s
                current_lines = []
            else:
                current_start = None 
        elif line and not line.isdigit() and not line.startswith('WEBVTT') and not line.startswith('Kind:') and not line.startswith('Language:') and not line.startswith('NOTE'):
             clean = re.sub(r'<[^>]+>', '', line)
             current_lines.append(clean)
             
    # Append last cue
    if current_start is not None and current_lines:
        cues.append({'start': current_start, 'text': ' '.join(current_lines)})
        
    # Merge cues close in time (e.g. within 5 seconds)
    merged = {}
    if not cues:
        return merged
        
    last_key = cues[0]['start']
    merged[last_key] = cues[0]['text']
    
    for cue in cues[1:]:
        if cue['start'] - last_key < 5:
            merged[last_key] += ' ' + cue['text']
        else:
            last_key = cue['start']
            merged[last_key] = cue['text']
            
    return merged

@app.post("/yt")
def get_subtitles(request: VideoRequest):
    """
    Accepts a YouTube URL and returns the subtitles.
    """
    print(f"Processing request for URL: {request.url} with lang: {request.lang}")
    url = request.url
    lang = request.lang
    
    # Create a unique temporary directory for this request to avoid collisions
    request_id = str(uuid.uuid4())
    temp_dir = f"/tmp/{request_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'outtmpl': f'{temp_dir}/%(id)s',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    if lang:
        ydl_opts['subtitleslangs'] = [lang]
    else:
        # If no language specified, limit to common languages to avoid 429 (Too Many Requests)
        # from fetching all available auto-generated captions.
        ydl_opts['subtitleslangs'] = ['en', 'zh-Hant', 'zh-TW', 'ja']

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to fetch video info: {str(e)}")

            video_id = info.get('id')
            title = info.get('title', 'Untitled Video')
            
            # Find the subtitle file
            # Since we use a unique temp dir, we can just look for any file starting with video_id
            # This handles cases where requested 'zh' results in 'zh-TW' file
            pattern = f"{temp_dir}/{video_id}.*"
            files = glob.glob(pattern)
            
            if not files:
                raise HTTPException(status_code=404, detail=f"No subtitles found.")
            
            # Use the first matching file (usually .vtt)
            subtitle_file = files[0]
            
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            transcribed_part = parse_vtt(content)

            return {
                "video_id": video_id,
                "title": title,
                "page": 1,
                "total_pages": 1,
                "transcribed_part": transcribed_part
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.post("/apple_podcast")
def get_apple_podcast_subtitles(request: VideoRequest):
    """
    Accepts an Apple Podcast URL and returns the subtitles using mlx-whisper.
    """
    print(f"Processing Apple Podcast request for URL: {request.url}")
    url = request.url
    
    # Create a unique temporary directory
    request_id = str(uuid.uuid4())
    temp_dir = f"/tmp/{request_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{temp_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to fetch podcast info: {str(e)}")

            video_id = info.get('id')
            title = info.get('title', 'Untitled Podcast')
            
            # Find the downloaded file
            files = glob.glob(f"{temp_dir}/{video_id}.*")
            if not files:
                raise HTTPException(status_code=404, detail="Failed to download audio file.")
            
            audio_file = files[0]
            file_size = os.path.getsize(audio_file)
            print(f"Downloaded audio file: {audio_file}, size: {file_size} bytes")
            
            if file_size == 0:
                 raise HTTPException(status_code=500, detail="Downloaded audio file is empty.")


            # Transcribe using mlx_whisper
            try:
                import time
                file_size_mb = file_size / (1024 * 1024)
                estimated_time = int(file_size_mb * 2)
                print(f"Starting transcription with mlx_whisper...")
                print(f"File size: {file_size_mb:.1f}MB, estimated time: ~{estimated_time}s")
                
                start_time = time.time()
                result = mlx_whisper.transcribe(audio_file, path_or_hf_repo=WHISPER_MODEL_PATH)
                elapsed_time = time.time() - start_time
                print(f"✅ Transcription completed in {elapsed_time:.1f}s")
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Whisper transcription failed: {str(e)}")
            
            # Format results
            transcribed_part = {}
            for segment in result['segments']:
                start = int(segment['start'])
                text = segment['text'].strip()
                transcribed_part[start] = text
                
            return {
                "video_id": video_id,
                "title": title,
                "page": 1,
                "total_pages": 1,
                "transcribed_part": transcribed_part
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


# Background task function for async transcription
def process_podcast_transcription(task_id: str, url: str):
    """Background task to process podcast transcription"""
    try:
        # Update task status
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = "Downloading audio..."
        
        # Create a unique temporary directory
        request_id = str(uuid.uuid4())
        temp_dir = f"/tmp/{request_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{temp_dir}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        # Download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            title = info.get('title', 'Untitled Podcast')
            
            tasks[task_id]["title"] = title
            tasks[task_id]["video_id"] = video_id
            
            # Find the downloaded file
            files = glob.glob(f"{temp_dir}/{video_id}.*")
            if not files:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = "Failed to download audio file"
                return
            
            audio_file = files[0]
            file_size = os.path.getsize(audio_file)
            
            if file_size == 0:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = "Downloaded audio file is empty"
                return
            
            # Update progress
            file_size_mb = file_size / (1024 * 1024)
            estimated_time = int(file_size_mb * 2)
            tasks[task_id]["progress"] = f"Transcribing... (File: {file_size_mb:.1f}MB, Est: ~{estimated_time}s)"
            
            # Transcribe with mlx_whisper
            import time
            start_time = time.time()
            result = mlx_whisper.transcribe(audio_file, path_or_hf_repo=WHISPER_MODEL_PATH)
            elapsed_time = time.time() - start_time
            
            # Format results
            transcribed_part = {}
            for segment in result['segments']:
                start = int(segment['start'])
                text = segment['text'].strip()
                transcribed_part[start] = text
            
            # Update task with results
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = f"Completed in {elapsed_time:.1f}s"
            tasks[task_id]["result"] = {
                "video_id": video_id,
                "title": title,
                "page": 1,
                "total_pages": 1,
                "transcribed_part": transcribed_part,
                "processing_time": elapsed_time
            }
            tasks[task_id]["completed_at"] = datetime.now().isoformat()
            
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        import traceback
        traceback.print_exc()


@app.post("/apple_podcast/async")
def submit_podcast_transcription(request: VideoRequest, background_tasks: BackgroundTasks):
    """
    Submit a podcast transcription task and get a task ID.
    Use /apple_podcast/status/{task_id} to check progress.
    """
    task_id = str(uuid.uuid4())
    
    # Initialize task
    tasks[task_id] = {
        "task_id": task_id,
        "url": request.url,
        "status": "queued",
        "progress": "Task queued",
        "created_at": datetime.now().isoformat(),
        "result": None,
        "error": None
    }
    
    # Add background task
    background_tasks.add_task(process_podcast_transcription, task_id, request.url)
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Task submitted. Use /apple_podcast/status/{task_id} to check progress."
    }


@app.get("/apple_podcast/status/{task_id}")
def get_task_status(task_id: str):
    """
    Get the status of a transcription task.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    response = {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "created_at": task["created_at"]
    }
    
    if task.get("title"):
        response["title"] = task["title"]
    
    if task.get("completed_at"):
        response["completed_at"] = task["completed_at"]
    
    if task["status"] == "completed":
        response["result"] = task["result"]
    elif task["status"] == "failed":
        response["error"] = task["error"]
    
    return response


@app.get("/apple_podcast/tasks")
def list_tasks():
    """
    List all transcription tasks.
    """
    return {
        "total": len(tasks),
        "tasks": [
            {
                "task_id": task_id,
                "status": task["status"],
                "title": task.get("title", "N/A"),
                "created_at": task["created_at"]
            }
            for task_id, task in tasks.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    # Run the server with increased timeout for long transcription tasks
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=60*20,  
        timeout_graceful_shutdown=60*20
    )
