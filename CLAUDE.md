# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

yt-mcp-server is a YouTube and Apple Podcast transcription and summarization server. The project consists of:

1. **Main FastAPI Backend** (`ubuntu_backend.py`) - Production server with full features
2. **Simple Backend** (`backend.py`) - Lightweight version with basic transcription
3. **MCP Server** (`main.py`) - Model Context Protocol server for YouTube subtitles
4. **Proxy Component** (`mcp-n8n-proxy/`) - Separate FastMCP-based n8n proxy server

The server automatically chooses between subtitles (when available) and Whisper audio transcription (when not) for YouTube videos, and uses Whisper for Apple Podcasts.

## Architecture

### Core Components

**ubuntu_backend.py** - Primary production server
- FastAPI application with AI-powered summarization
- Dual transcription strategy: subtitles first, Whisper fallback
- Cache system using `.cache/` directory with MD5-based keys
- Claude AI integration for intelligent summarization with Map-Reduce for long content
- Preloads `faster_whisper` model at startup for performance
- Handles both YouTube videos and Apple Podcasts

**backend.py** - Simplified alternative server
- Uses `mlx_whisper` instead of `faster_whisper`
- Supports async podcast transcription with task management
- No AI summarization features
- Suitable for macOS/MLX environments

**main.py** - MCP server implementation
- Exposes `get_subtitles` tool via FastMCP
- Runs on streamable-http transport
- Subtitle-only (no Whisper fallback)

### Key Design Patterns

**Smart Transcription Strategy**
1. Try to fetch subtitles via `yt-dlp`
2. If subtitles unavailable, download audio and use Whisper
3. Return results in consistent format with `transcription_method` field

**Caching System**
- Cache key generation: `hashlib.md5(url.encode()).hexdigest()`
- Cached data includes: original URL, timestamp, and complete result
- Separate caches for different custom prompts (via URL modification)
- Cache files stored as JSON in `.cache/` directory

**AI Summarization (ubuntu_backend.py only)**
- Uses Claude API (`anthropic` client) for content analysis
- Map-Reduce strategy for long content (chunks of ~25000 chars)
- Supports custom prompts per request
- Default prompt optimized for Traditional Chinese investment content

## Development Commands

### Start the Server

Main production server:
```bash
./start_server.sh
# Runs ubuntu_backend.py with proper LD_LIBRARY_PATH for CUDA libraries
# Uses uv to run Python
```

Alternative simplified server:
```bash
# For backend.py (mlx_whisper version)
python backend.py
```

Docker deployment:
```bash
./docker-start.sh  # Build and run
./docker-stop.sh   # Stop container
```

### Environment Setup

Required environment variables:
```bash
ANTHROPIC_API_KEY=your_api_key_here  # For AI summarization features
```

Install dependencies:
```bash
pip install -r requirements.txt
# or use uv
```

### Testing

The repository includes multiple test scripts:
- `test_subtitle_fallback.py` - Tests subtitle fallback functionality
- `test_channel_summary.py` - Tests channel summarization
- `test_podcast_summary.py` - Tests podcast summarization
- `example_youtube_summary.py` - Example usage of summary endpoint

Run tests directly:
```bash
python test_subtitle_fallback.py
```

## Important Implementation Details

### Transcription Methods

**Subtitles (Fast)**
- VTT format parsing with timestamp extraction
- Merges cues within 5 seconds into single entries
- Returns dict with `{timestamp_seconds: "text"}`

**Whisper (Slower but Universal)**
- `ubuntu_backend.py`: Uses `faster_whisper` with CUDA acceleration
- `backend.py`: Uses `mlx_whisper` for macOS/MLX
- Model preloading at startup to avoid first-request delay
- Returns same format as subtitles for consistency

### API Response Format

All transcription endpoints return:
```json
{
  "video_id": "string",
  "title": "string",
  "page": 1,
  "total_pages": 1,
  "transcribed_part": {
    "0": "text at 0 seconds",
    "3": "text at 3 seconds"
  },
  "transcription_method": "subtitles" | "whisper"  // ubuntu_backend.py only
}
```

Summary endpoints additionally include:
```json
{
  "video_url": "string",
  "summary": "AI-generated summary",
  "chunks": [],
  "generated_at": "ISO timestamp",
  "raw": "full transcript",
  "view_url": "cache view URL"
}
```

### Temporary Files and Cleanup

- Each request creates unique temp directory: `/tmp/{uuid}`
- Audio files downloaded to temp directory for Whisper processing
- Cleanup happens in `finally` blocks using `shutil.rmtree(temp_dir)`
- Subtitle files cleaned up with `os.remove()` after reading

### Concurrent Request Handling

- UUID-based temp directories prevent filename collisions
- Each request isolated in its own temp directory
- `backend.py` includes async task management for long-running jobs

## File Structure Notes

**Core Backend Files**
- `ubuntu_backend.py` - Production backend (faster_whisper + Claude AI)
- `backend.py` - Alternative backend (mlx_whisper, no AI)
- `main.py` - MCP server for subtitle extraction

**Test Files**
- `test_*.py` - Various test scripts for different features
- `example_youtube_summary.py` - Usage example

**Documentation**
- `YOUTUBE_SUMMARY_IMPLEMENTATION.md` - Details on summary feature
- `UPDATE_WHISPER_FALLBACK.md` - Whisper fallback implementation guide
- `CHANNEL_SUMMARY_GUIDE.md` - Channel summarization documentation

**Scripts**
- `start_server.sh` - Starts ubuntu_backend.py with CUDA libraries
- `docker-start.sh` / `docker-stop.sh` - Docker management
- `install-service.sh` / `uninstall-service.sh` - Systemd service setup
- `simple-start.sh` / `simple-stop.sh` - Basic server management

## Dependencies Notes

**GPU Libraries**
- `faster_whisper` requires CUDA-capable GPU
- CUDA libraries path set in `start_server.sh`: `.venv/lib/python3.12/site-packages/nvidia/{cudnn,cublas}/lib`

**Key Python Packages**
- `fastapi` - Web framework
- `yt-dlp` - YouTube/media download
- `faster_whisper` / `mlx_whisper` - Transcription
- `anthropic` - Claude AI client
- `beautifulsoup4` - HTML parsing for podcast pages
- `mcp` - Model Context Protocol

## Cache Management

View cache stats:
```bash
curl http://localhost:8000/cache/stats
```

Clear cache:
```bash
curl -X DELETE http://localhost:8000/cache/clear
```

Retrieve cached summary:
```bash
curl http://localhost:8000/api/summary/{cache_key}
```

## Notes for Development

- Server runs on port 8000 by default
- Preloading phase occurs on startup (watch for "✅ Model preloaded successfully!")
- Whisper fallback is transparent to clients - same response format
- Custom prompts create separate cache entries
- Long videos use chunked processing with Map-Reduce strategy
- Apple Podcast episode discovery via BeautifulSoup scraping of podcast page
