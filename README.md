# yt-mcp-server

YouTube and Podcast transcription and summarization server with AI-powered analysis.

## Features

- 🎥 YouTube video transcription and summarization
  - **Smart transcription**: Automatically uses subtitles when available, falls back to Whisper audio transcription when not
- 🎙️ Apple Podcast transcription and summarization
- 🤖 AI-powered content analysis using Claude
- 💾 Smart caching system
- 📊 Channel-level analysis

## API Endpoints

### YouTube Endpoints

#### 1. Get YouTube Video Subtitles
```bash
POST /yt
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "lang": "zh-TW"  // optional, defaults to zh-TW
}
```

**Note**: This endpoint now automatically falls back to Whisper transcription if subtitles are not available.


#### 2. Summarize Single YouTube Video (NEW!)
```bash
POST /youtube/summary
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "custom_prompt": "optional custom prompt for AI"  // optional
}
```

**Response:**
```json
{
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_id": "VIDEO_ID",
  "title": "Video Title",
  "summary": "AI-generated summary with timestamps and key points",
  "chunks": [],
  "generated_at": "2025-11-29T12:00:00",
  "raw": "Full transcript with timestamps",
  "view_url": "https://be.0xfanslab.com/youtube/channel/summary?id=CACHE_KEY"
}
```

#### 3. Summarize YouTube Channel
```bash
POST /youtube/channel/summary
Content-Type: application/json

{
  "url": "https://www.youtube.com/@CHANNEL_NAME",
  "max_videos": 5,  // optional, defaults to 5, max 10
  "custom_prompt": "optional custom prompt"  // optional
}
```

### Podcast Endpoints

#### 1. Get Apple Podcast Episode Subtitles
```bash
POST /apple_podcast
Content-Type: application/json

{
  "url": "https://podcasts.apple.com/...",
  "lang": "zh-TW"  // optional
}
```

#### 2. Get Latest Podcast Episode
```bash
POST /apple_podcast/latest
Content-Type: application/json

{
  "url": "https://podcasts.apple.com/SHOW_URL",
  "lang": "zh-TW"  // optional
}
```

#### 3. Summarize Podcast Channel
```bash
POST /apple_podcast/summary
Content-Type: application/json

{
  "url": "https://podcasts.apple.com/SHOW_URL",
  "max_episodes": 1,  // optional, defaults to 1, max 5
  "custom_prompt": "optional custom prompt"  // optional
}
```

### Cache Management

#### Get Cache Statistics
```bash
GET /cache/stats
```

#### Clear All Cache
```bash
DELETE /cache/clear
```

#### Get Cached Summary
```bash
GET /api/summary/{cache_key}
```

#### Get Cached Podcast Summary
```bash
GET /api/podcast/summary/{cache_key}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

3. Start the server:
```bash
./start_server.sh
```

The server will run on `http://0.0.0.0:8000`

## Docker Support

Build and run with Docker:
```bash
./docker-start.sh
```

Stop the Docker container:
```bash
./docker-stop.sh
```

## Requirements

- Python 3.12+
- CUDA-capable GPU (for faster_whisper transcription)
- Anthropic API key (for AI summarization)

## License

MIT
