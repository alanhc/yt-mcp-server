import os
from dotenv import load_dotenv
load_dotenv()

import glob
import uuid
import shutil
import yt_dlp
import re
import json
import hashlib
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from faster_whisper import WhisperModel

# Anthropic client
try:
    from anthropic import Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if ANTHROPIC_API_KEY:
        anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        print("✅ Anthropic API initialized")
    else:
        anthropic_client = None
        print("⚠️  ANTHROPIC_API_KEY not found")
except Exception as e:
    anthropic_client = None
    print(f"⚠️ Anthropic initialization failed: {e}")

# Global Whisper model (will be preloaded at startup)
WHISPER_MODEL = None
WHISPER_MODEL_SIZE = "base"

# Cache directory
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_key(url: str) -> str:
    """Generate cache key from URL"""
    return hashlib.md5(url.encode()).hexdigest()

def get_cached_result(url: str) -> Optional[dict]:
    """Retrieve cached result if exists"""
    cache_key = get_cache_key(url)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                print(f"✅ Cache HIT for URL: {url[:50]}...")
                return cached_data
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            return None
    
    print(f"❌ Cache MISS for URL: {url[:50]}...")
    return None

def save_to_cache(url: str, result: dict):
    """Save result to cache"""
    cache_key = get_cache_key(url)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    try:
        cache_data = {
            "url": url,
            "cached_at": datetime.now().isoformat(),
            "result": result
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved to cache: {cache_file.name}")
    except Exception as e:
        print(f"⚠️ Cache write error: {e}")

def get_latest_episode_url(podcast_url: str) -> str:
    """Get the latest episode URL from an Apple Podcasts show page"""
    try:
        print(f"🔍 Fetching latest episode from: {podcast_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(podcast_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'  # Force UTF-8 encoding
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        episode_links = soup.find_all('a', href=re.compile(r'/podcast/[^/]+/id\d+\?i=\d+'))
        
        if not episode_links:
            raise ValueError("No episodes found on the podcast page")
        
        latest_episode_url = episode_links[0]['href']
        if not latest_episode_url.startswith('http'):
            latest_episode_url = 'https://podcasts.apple.com' + latest_episode_url
            
        print(f"✅ Found latest episode: {latest_episode_url}")
        return latest_episode_url
        
    except Exception as e:
        print(f"❌ Error fetching latest episode: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch latest episode: {str(e)}"
        )

def get_podcast_episodes(podcast_url: str, max_episodes: int = 5) -> List[dict]:
    """Get recent episodes from an Apple Podcasts show page"""
    try:
        print(f"🔍 Fetching episodes from: {podcast_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(podcast_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'  # Force UTF-8 encoding
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        episode_links = soup.find_all('a', href=re.compile(r'/podcast/[^/]+/id\d+\?i=\d+'))
        
        if not episode_links:
            raise ValueError("No episodes found on the podcast page")
            
        episodes = []
        seen_urls = set()
        
        for link in episode_links:
            url = link['href']
            if not url.startswith('http'):
                url = 'https://podcasts.apple.com' + url
            
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = link.get_text(strip=True)
            episodes.append({
                'title': title,
                'url': url
            })
            
            if len(episodes) >= max_episodes:
                break
                
        print(f"✅ Found {len(episodes)} episodes")
        return episodes
        
    except Exception as e:
        print(f"❌ Error fetching podcast episodes: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch episodes: {str(e)}")

def get_channel_videos(channel_url: str, max_videos: int = 5) -> List[dict]:
    """Get recent videos from a YouTube channel"""
    try:
        print(f"🔍 Fetching videos from channel: {channel_url}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': max_videos,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            
            if 'entries' not in info:
                raise ValueError("No videos found in channel")
            
            videos = []
            for entry in info['entries'][:max_videos]:
                if entry:
                    videos.append({
                        'title': entry.get('title', 'Untitled'),
                        'url': f"https://www.youtube.com/watch?v={entry['id']}"
                    })
            
            print(f"✅ Found {len(videos)} videos")
            return videos
            
    except Exception as e:
        print(f"❌ Error fetching channel videos: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch channel videos: {str(e)}"
        )

def split_text(text: str, max_chunk_size: int = 25000) -> List[str]:
    """Split text into chunks respecting line breaks"""
    chunks = []
    current_chunk = []
    current_length = 0
    
    lines = text.split('\n')
    for line in lines:
        line_len = len(line) + 1  # +1 for newline
        
        if current_length + line_len > max_chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0
            
        current_chunk.append(line)
        current_length += line_len
        
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    return chunks

def summarize_with_claude(content: str, prompt: str = None) -> str:
    """
    Summarize content using Claude AI with Map-Reduce support for long content.
    """
    if not anthropic_client:
        raise HTTPException(
            status_code=503,
            detail="AI summarization not available - ANTHROPIC_API_KEY not configured"
        )
    
    default_prompt = """你是一個專門將 Podcast / YouTube 逐字稿轉成「投資整理＋重點摘要」的助手。  
請全程使用 **繁體中文** 回覆。

────────────────────────
【輸入格式】
────────────────────────
我會傳給你一個 JSON 物件，結構大致如下：

{
  "url": "...",
  "cached_at": "...",
  "result": {
    "video_id": "...",
    "title": "...",
    "page": 1,
    "total_pages": 1,
    "transcribed_part": {
      "0": "…",
      "3": "…",
      "6": "…",
      "...": "…"
    }
  }
}

其中：
- `transcribed_part` 的 key 是「秒數（string）」，value 是該時間點的中文逐字稿片段。
- 可能只有一頁（page=1, total_pages=1）。

你需要先把 `transcribed_part` 依照 key（秒數）由小到大排序，串成一份完整逐字稿，再進行後續分析。

────────────────────────
【任務】
────────────────────────
請針對整段內容產出一份「投資向」摘要與標的整理，並 **保留關鍵句的時間標記**。  
時間請把秒數轉成 `mm:ss` 格式（例如 "17" → "00:17"）。

輸出結構請固定為以下 5 個區塊：

1️⃣ 節目總結（高層摘要）
- 用 3–7 點條列說明這集在講什麼，主要脈絡是什麼。
- 先簡單提到一開始的置入（例如 Sony WH-1000XM6 耳機），再說明後面主線：  
  - 遊戲投資 / 小男資本與屋山資本  
  - 台灣遊戲團隊與新創遊戲  
  - Google / TPU / Broadcom / MediaTek / TSMC 等 AI 供應鏈及投資觀點  
  - 投資心態、槓桿、風險與資金控管  
  - QA 段落中與投資、工作、家庭相關的重點想法

2️⃣ 投資主題與關鍵論點
用小標＋條列整理，舉例：

- 🎮 遊戲投資與小男資本
  - 說明小男資本、屋山資本在做什麼（募資、投資對象、Evergreen Fund 概念）。
  - 台灣遊戲團隊目前面臨的成本、發行、創意與生存問題。
  - 主持人在 NMEA 亞洲新媒體高峰會上主張的核心理念（遊戲性 > 畫面、不要教育玩家等）。

- 🤖 Google TPU / Broadcom / MediaTek / NVIDIA / TSMC 供應鏈
  - 整理主持人對 Google TPU、Broadcom、MediaTek（聯發科）、TSMC 的角色與營收結構描述。
  - 說明「ASIC vs GPU」的對比觀點：為何不能簡單解讀成「ASIC 贏、GPU 死」。
  - 說明 TPU 代數（如 V7）與產能 / CoWoS / HBM / 封測廠相關的供應鏈延伸。
  - 整理主持人對 NVIDIA 股價、拉回、長期配置的看法。

- 📈 投資心態與操作原則
  - 對「不要當嘴砲宅，要真的拿錢出來投資」的觀點。
  - 對「不要把投資當球賽、不要非 A 死 B 的二元思維」的批評。
  - 怎麼看待槓桿、回檔、追高、消息面交易、小作文、X（Twitter）資訊。
  - 對散戶容易出現的心態錯誤與建議（切帳戶、資金分層、不要自視甚高等）。

3️⃣ 投資標的清單（標的 x 狀況）
請做成 Markdown 表格，整理節目中 **與投資相關的標的**，包含但不限於：

- 個股／公司：Google、NVIDIA、Broadcom、MediaTek（聯發科）、TSMC、AWS、Microsoft、Meta…  
- 類別／產品：TPU、GPU、HBM、CoWoS、封測廠（例如 Amkor、SPIL 等如果有提）、Google 供應鏈、AI 伺服器、遊戲股/遊戲團隊  
- 其他：Sony WH-1000XM6（雖然是廣告產品，但也可簡列於「產品」類）

表格欄位請如下：

| 類型 | 名稱 / 代號 | 在節目中的角色 / 定位 | 主持人觀點（偏多 / 偏空 / 中性） | 關鍵論點摘要 | 相關時間（mm:ss, 可多個） |
| ---- | ---------- | ---------------------- | ---------------------------------- | ------------ | -------------------------- |

規則：
- 只列出逐字稿中真的有提到、且與「投資 / 產業」有關的標的。  
- 若節目對某標的沒有明顯多空傾向，就寫「中性」或「描述為主」即可。  
- `相關時間` 欄：填入 1~3 個最關鍵的時間點（從 transcribed_part 對應的 key 換算成 mm:ss）。

4️⃣ 投資心態與操作建議（從節目萃取）
- 不是要你給我自己的投顧意見，而是 **整理主持人自己講的操作心法**。
- 用條列方式，分成：
  - 「資金與槓桿」：例如三倍槓桿、回檔承受度、不要以為自己能買在主力前面等。
  - 「產業與題材」：例如 Google 之亂、TPU vs GPU、不要過度解讀短期利多/利空。
  - 「散戶常見陷阱」：追高、亂下單、情緒化交易、小作文、對降息／宏觀事件的錯誤想像。
- 每點盡量附上 **對應的大致時間**（mm:ss）方便回聽。

5️⃣ 精選金句（含時間）
- 篩選 5–10 句最值得記下來的句子，可以是：
  - 對投資心態很有幫助的話
  - 對產業 / TPU / GPU / Google 供應鏈有洞見的評論
  - 對家庭、孩子、人生、工作等很有感觸的話
- 每一條格式如下：
  - `mm:ss – 「原文金句」`  
- 不需要逐字完全一致，但要接近日常口語，不要亂改意思。

────────────────────────
【風格與限制】
────────────────────────
- 全程使用 **繁體中文**。
- 不要自己創造逐字稿裡不存在的標的或數字；無法確定就寫「未明確說明」。
- 可以適度簡化口語，但保留原本語氣與立場。
- 你是「節目整理者」，不是投顧，**請不要對標的下買進/賣出指令**，只需忠實整理節目內容與觀點。

────────────────────────
【實際輸入】
────────────────────────
以下是本次要處理的 JSON 輸入：



"""
    base_prompt = prompt or default_prompt

    def call_claude(text_chunk):
        full_prompt = base_prompt + "\n\n" + text_chunk
        try:
            message = anthropic_client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=8192,  # Max allowed for Haiku
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"⚠️ Claude API error for chunk: {e}")
            return f"[Error summarizing this chunk: {str(e)}]"

    # Check if content needs splitting (approx 30k chars)
    if len(content) > 30000:
        print(f"📦 Content length {len(content)} exceeds limit, using Map-Reduce summarization...")
        chunks = split_text(content)
        chunk_summaries = []
        chunks_metadata = []
        
        # Map Phase: Summarize each chunk (with caching)
        for i, chunk in enumerate(chunks):
            # Generate cache key for this chunk
            chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
            chunk_cache_file = CACHE_DIR / f"chunk_{chunk_hash}.json"
            
            chunk_data = None
            
            # Check chunk cache
            if chunk_cache_file.exists():
                try:
                    with open(chunk_cache_file, 'r', encoding='utf-8') as f:
                        cached_chunk = json.load(f)
                        chunk_summary = cached_chunk['summary']
                        chunk_data = cached_chunk
                        print(f"✅ [Map] Chunk {i+1}/{len(chunks)} cache HIT")
                except Exception as e:
                    print(f"⚠️ Chunk cache read error: {e}")
            
            if not chunk_data:
                print(f"🔄 [Map] Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
                chunk_summary = call_claude(chunk)
                
                # Save chunk summary to cache
                try:
                    chunk_data = {
                        'chunk_hash': chunk_hash,
                        'cached_at': datetime.now().isoformat(),
                        'summary': chunk_summary,
                        'chunk_length': len(chunk)
                    }
                    with open(chunk_cache_file, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                    print(f"💾 Saved chunk {i+1} to cache")
                except Exception as e:
                    print(f"⚠️ Failed to cache chunk: {e}")
                    # Create temporary chunk data even if cache failed
                    chunk_data = {
                        'chunk_hash': chunk_hash,
                        'cached_at': datetime.now().isoformat(),
                        'summary': chunk_summary,
                        'chunk_length': len(chunk)
                    }
            
            chunk_summaries.append(chunk_summary)
            chunks_metadata.append(chunk_data)
            
        # Reduce Phase: Concatenate summaries + Generate final overview
        if len(chunk_summaries) > 1:
            print("🔄 [Reduce] Concatenating chunk summaries...")
            # Step 1: Direct concatenation
            concatenated_summaries = "\n\n---\n\n".join([
                f"### 第 {i+1} 部分\n{summary}" 
                for i, summary in enumerate(chunk_summaries)
            ])
            
            # Step 2: Generate final overview based on concatenated content
            print("🔄 [Reduce] Generating final overview summary...")
            overview_prompt = f"""請基於全部 chunk，產生一份 **投資向、可回聽、可做筆記** 的高品質總結，包含：

1️⃣ 節目總結（3–7 句，抓出主軸）  
2️⃣ 深度投資重點整理（條列＋小標題）  
   - 遊戲投資、台灣團隊、基金理念  
   - AI/TPU/GPU/ASIC、供應鏈（Broadcom / MTK / NVIDIA / TSMC 等）  
   - 投資心態、散戶錯誤、槓桿與風險  
3️⃣ 投資標的表（從所有 chunks 的 entities 彙總）  
   - 類型（公司 / 產品 / 概念）  
   - 名稱  
   - 節目中的定位  
   - 主持人態度（偏多 / 偏空 / 中性）  
   - 對應 chunk 的 timestamps（mm:ss 格式即可）  
4️⃣ 投資心態與操作建議（主持人觀點，不是你的建議）  
5️⃣ 精選金句（從 raw_sentences 中挑最有力的 5–10 句）

【規則】
- 若多個 chunk 重複內容，要「整併」而不是重複貼上。
- 若觀點有矛盾，請做「整合性解釋」。
- 全程使用繁體中文。

以下是分段摘要內容：

{concatenated_summaries}
"""
            
            final_output = call_claude(overview_prompt)
            return final_output, chunks_metadata
        else:
            return chunk_summaries[0], chunks_metadata
    else:
        # Single chunk processing
        summary = call_claude(content)
        return summary, []
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    global WHISPER_MODEL
    print("🚀 Starting up server...")
    print(f"📥 Preloading faster_whisper model: {WHISPER_MODEL_SIZE}")
    print("⚡ GPU-ONLY MODE: CPU fallback disabled")
    try:
        print("Loading model on CUDA...")
        WHISPER_MODEL = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cuda",
            compute_type="float16"
        )
        print("✅ Model preloaded successfully on GPU!")
    except Exception as e:
        print(f"❌ FATAL: Could not load model on GPU: {e}")
        print("💡 Ensure CUDA and cuDNN are properly installed")
        raise RuntimeError(f"GPU initialization failed: {e}")
    
    yield
    print("👋 Shutting down server...")

app = FastAPI(
    title="yt-mcp-server",
    lifespan=lifespan,
    servers=[
        {
            "url": "https://be.0xfanslab.com",
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
    
    time_pattern = re.compile(r'(\d{2}:)?(\d{2}):(\d{2})\.(\d{3})')
    
    current_start = None
    buffer = []
    
    for line in lines:
        line = line.strip()
        
        if '-->' in line:
            match = time_pattern.search(line)
            if match:
                groups = match.groups()
                hours = int(groups[0][:-1]) if groups[0] else 0
                minutes = int(groups[1])
                seconds = int(groups[2])
                timestamp = hours * 3600 + minutes * 60 + seconds
                
                if buffer and current_start is not None:
                    cues.append({'start': current_start, 'text': ' '.join(buffer)})
                    buffer = []
                
                current_start = timestamp
        
        elif line and not line.startswith('WEBVTT') and not line.isdigit() and current_start is not None:
            buffer.append(line)
    
    if buffer and current_start is not None:
        cues.append({'start': current_start, 'text': ' '.join(buffer)})
    
    return cues

@app.post("/yt")
def get_subtitles(request: VideoRequest):
    print(f"Processing request for URL: {request.url} with lang: {request.lang}")
    url = request.url
    lang = request.lang or "zh-TW"
    
    cached_result = get_cached_result(url)
    if cached_result:
        return cached_result["result"]
    
    # First, try to get subtitles
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang],
        'skip_download': True,
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            title = info.get('title')
            
            pattern = f"/tmp/{video_id}.{lang}.vtt"
            vtt_files = glob.glob(pattern)
            
            if not vtt_files:
                pattern = f"/tmp/{video_id}.*.vtt"
                vtt_files = glob.glob(pattern)
            
            if vtt_files:
                # Subtitles found, use them
                print(f"✅ Found subtitles for {video_id}")
                vtt_file = vtt_files[0]
                
                with open(vtt_file, 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                
                cues = parse_vtt(vtt_content)
                
                transcribed_part = {}
                for cue in cues:
                    transcribed_part[cue['start']] = cue['text']
                
                result = {
                    "video_id": video_id,
                    "title": title,
                    "page": 1,
                    "total_pages": 1,
                    "transcribed_part": transcribed_part,
                    "transcription_method": "subtitles"
                }
                
                save_to_cache(url, result)
                
                for f in glob.glob(f"/tmp/{video_id}.*"):
                    try:
                        os.remove(f)
                    except:
                        pass
                
                return result
            else:
                # No subtitles found, fallback to audio transcription
                print(f"⚠️ No subtitles found for {video_id}, falling back to audio transcription...")
                
    except Exception as e:
        print(f"⚠️ Error getting subtitles: {e}, falling back to audio transcription...")
    
    # Fallback: Download audio and transcribe with Whisper
    print(f"🎵 Downloading audio for transcription: {url}")
    request_id = str(uuid.uuid4())
    temp_dir = f"/tmp/{request_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    ydl_opts_audio = {
        'format': 'bestaudio/best',
        'outtmpl': f'{temp_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            title = info.get('title', 'Untitled Video')
            
            files = glob.glob(f"{temp_dir}/{video_id}.*")
            if not files:
                raise HTTPException(status_code=404, detail="Failed to download audio file.")
            
            audio_file = files[0]
            file_size = os.path.getsize(audio_file)
            print(f"📥 Downloaded audio file: {audio_file}, size: {file_size} bytes")
            
            if file_size == 0:
                raise HTTPException(status_code=500, detail="Downloaded audio file is empty.")
            
            try:
                import time
                file_size_mb = file_size / (1024 * 1024)
                estimated_time = int(file_size_mb * 2)
                print(f"🎙️ Starting transcription with faster_whisper (GPU)...")
                print(f"File size: {file_size_mb:.1f}MB, estimated time: ~{estimated_time}s")
                
                global WHISPER_MODEL
                if WHISPER_MODEL is None:
                    raise RuntimeError("GPU model not loaded. Server startup may have failed.")
                
                start_time = time.time()
                segments, info = WHISPER_MODEL.transcribe(audio_file, beam_size=5)
                elapsed_time = time.time() - start_time
                print(f"✅ Transcription completed in {elapsed_time:.1f}s")
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Whisper transcription failed: {str(e)}")
            
            transcribed_part = {}
            for segment in segments:
                start = int(segment.start)
                text = segment.text.strip()
                transcribed_part[start] = text
            
            result = {
                "video_id": video_id,
                "title": title,
                "page": 1,
                "total_pages": 1,
                "transcribed_part": transcribed_part,
                "transcription_method": "whisper"
            }
            
            save_to_cache(url, result)
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

class PodcastRequest(BaseModel):
    url: str
    lang: str | None = None

@app.post("/apple_podcast/latest")
def get_latest_podcast_episode(request: PodcastRequest):
    """Accepts a podcast show URL and returns the subtitles for the latest episode"""
    podcast_url = request.url
    print(f"Processing latest episode request for podcast: {podcast_url}")

    try:
        latest_episode_url = get_latest_episode_url(podcast_url)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching latest episode info: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to find latest episode: {str(e)}"
        )
    
    episode_request = VideoRequest(url=latest_episode_url, lang=request.lang)
    result = get_apple_podcast_subtitles(episode_request)
    
    result["podcast_show_url"] = podcast_url
    result["episode_url"] = latest_episode_url
    result["is_latest_episode"] = True
    
    # Ensure view_url is present
    if "view_url" not in result:
        view_base_url = "https://be.0xfanslab.com/youtube/channel/summary"
        cache_key = get_cache_key(latest_episode_url)
        result["view_url"] = f"{view_base_url}?id={cache_key}&type=podcast"
    
    return result

@app.get("/api/podcast/summary/{cache_key}")
def get_podcast_cache(cache_key: str):
    """Retrieve cached podcast summary by cache key"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if not cache_file.exists():
        raise HTTPException(status_code=404, detail="Cache not found")
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            return cache_data.get("result", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read cache: {str(e)}")

@app.post("/apple_podcast")
def get_apple_podcast_subtitles(request: VideoRequest):
    """Accepts an Apple Podcast URL and returns the subtitles using faster_whisper"""
    print(f"Processing Apple Podcast request for URL: {request.url}")
    url = request.url
    
    view_base_url = "https://be.0xfanslab.com/youtube/channel/summary"
    
    cached_result = get_cached_result(url)
    if cached_result:
        result = cached_result["result"]
        cache_key = get_cache_key(url)
        result["view_url"] = f"{view_base_url}?id={cache_key}&type=podcast"
        return result
    
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
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            title = info.get('title', 'Untitled Podcast')
            
            files = glob.glob(f"{temp_dir}/{video_id}.*")
            if not files:
                raise HTTPException(status_code=404, detail="Failed to download audio file.")
            
            audio_file = files[0]
            file_size = os.path.getsize(audio_file)
            print(f"Downloaded audio file: {audio_file}, size: {file_size} bytes")
            
            if file_size == 0:
                 raise HTTPException(status_code=500, detail="Downloaded audio file is empty.")

            try:
                import time
                file_size_mb = file_size / (1024 * 1024)
                estimated_time = int(file_size_mb * 2)
                print(f"Starting transcription with faster_whisper (GPU)...")
                print(f"File size: {file_size_mb:.1f}MB, estimated time: ~{estimated_time}s")
                
                global WHISPER_MODEL
                if WHISPER_MODEL is None:
                    raise RuntimeError("GPU model not loaded. Server startup may have failed.")
                
                start_time = time.time()
                segments, info = WHISPER_MODEL.transcribe(audio_file, beam_size=5)
                elapsed_time = time.time() - start_time
                print(f"✅ Transcription completed in {elapsed_time:.1f}s")
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Whisper transcription failed: {str(e)}")
            
            transcribed_part = {}
            for segment in segments:
                start = int(segment.start)
                text = segment.text.strip()
                transcribed_part[start] = text
                
            result = {
                "video_id": video_id,
                "title": title,
                "page": 1,
                "total_pages": 1,
                "transcribed_part": transcribed_part
            }
            
            save_to_cache(url, result)
            
            cache_key = get_cache_key(url)
            result["view_url"] = f"{view_base_url}?id={cache_key}&type=podcast"
            
            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

class VideoSummaryRequest(BaseModel):
    url: str
    custom_prompt: Optional[str] = None

@app.post("/youtube/summary")
def summarize_youtube_video(request: VideoSummaryRequest):
    """Summarize a single YouTube video"""
    print(f"📺 Processing video summary request: {request.url}")
    
    # Generate cache key
    cache_key_data = f"{request.url}|{request.custom_prompt or 'default'}"
    cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()
    cache_file = CACHE_DIR / f"summary_{cache_key}.json"
    
    view_base_url = "https://be.0xfanslab.com/youtube/channel/summary"
    
    # Check cache
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                print(f"✅ Summary cache HIT for video: {request.url[:50]}...")
                result = cached_data["result"]
                result["view_url"] = f"{view_base_url}?id={cache_key}"
                return result
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
    
    print(f"❌ Summary cache MISS for video: {request.url[:50]}...")
    
    try:
        # Get video subtitles
        print(f"📝 Fetching subtitles for: {request.url}")
        video_request = VideoRequest(url=request.url)
        subtitle_result = get_subtitles(video_request)
        
        # Format subtitle text with timestamps
        subtitle_text = " ".join([f"[{ts}] {text}" for ts, text in subtitle_result['transcribed_part'].items()])
        
        # Prepare content for summarization
        video_content = f"影片: {subtitle_result['title']}\n內容: {subtitle_text}"
        
        # Generate AI summary
        print("🤖 Generating AI summary...")
        summary, chunks = summarize_with_claude(video_content, request.custom_prompt)
        
        # Prepare result
        result = {
            "video_url": request.url,
            "video_id": subtitle_result['video_id'],
            "title": subtitle_result['title'],
            "summary": summary,
            "chunks": chunks,
            "generated_at": datetime.now().isoformat(),
            "raw": video_content,
            "view_url": f"{view_base_url}?id={cache_key}"
        }
        
        # Save to cache
        try:
            cache_data = {
                "request": {
                    "url": request.url,
                    "custom_prompt": request.custom_prompt
                },
                "cached_at": datetime.now().isoformat(),
                "result": result
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved summary to cache: {cache_file.name}")
            
            # Save chunk list separately if chunks exist
            if chunks:
                chunk_list_file = CACHE_DIR / f"chunk_list_{cache_key}.json"
                with open(chunk_list_file, 'w', encoding='utf-8') as f:
                    json.dump({"chunks": chunks}, f, ensure_ascii=False, indent=2)
                print(f"💾 Saved chunk list to cache: {chunk_list_file.name}")
                
        except Exception as e:
            print(f"⚠️ Failed to save summary cache: {e}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in video summarization: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Video summarization failed: {str(e)}"
        )

class ChannelSummaryRequest(BaseModel):
    url: str
    max_videos: int = 5
    custom_prompt: Optional[str] = None

@app.post("/youtube/channel/summary")
def summarize_youtube_channel(request: ChannelSummaryRequest):
    """Summarize recent videos from a YouTube channel"""
    print(f"📺 Processing channel summary request: {request.url}")
    
    max_videos = min(request.max_videos, 10)
    
    cache_key_data = f"{request.url}|{max_videos}|{request.custom_prompt or 'default'}"
    cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()
    cache_file = CACHE_DIR / f"summary_{cache_key}.json"
    
    view_base_url = "https://be.0xfanslab.com/youtube/channel/summary"
    
    # Get current latest videos to check if cache is still valid
    try:
        current_videos = get_channel_videos(request.url, max_videos)
        latest_video_urls = [video['url'] for video in current_videos]
        print(f"📡 Current latest video(s): {len(latest_video_urls)} found")
    except Exception as e:
        print(f"⚠️ Failed to fetch current videos: {e}")
        current_videos = None
        latest_video_urls = None
    
    # Check cache with freshness validation
    if cache_file.exists() and latest_video_urls:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
                cached_video_urls = cached_data.get("latest_video_urls", [])
                
                if cached_video_urls == latest_video_urls:
                    print(f"✅ Summary cache HIT for channel: {request.url[:50]}...")
                    print(f"✅ Cache is fresh (latest video unchanged)")
                    result = cached_data["result"]
                    result["view_url"] = f"{view_base_url}?id={cache_key}"
                    return result
                else:
                    print(f"🔄 Cache exists but STALE (new video detected)")
                    print(f"   Cached: {cached_video_urls}")
                    print(f"   Current: {latest_video_urls}")
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
    elif cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                print(f"✅ Summary cache HIT (freshness check skipped)")
                result = cached_data["result"]
                result["view_url"] = f"{view_base_url}?id={cache_key}"
                return result
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            
    print(f"❌ Summary cache MISS for channel: {request.url[:50]}...")
    
    try:
        if current_videos is None:
            videos = get_channel_videos(request.url, max_videos)
        else:
            videos = current_videos
        
        if not videos:
            raise HTTPException(status_code=404, detail="No videos found in channel")
        
        video_contents = []
        processed_videos = []
        
        for video in videos:
            try:
                print(f"📝 Processing: {video['title']}")
                
                video_request = VideoRequest(url=video['url'])
                subtitle_result = get_subtitles(video_request)
                
                subtitle_text = " ".join([f"[{ts}] {text}" for ts, text in subtitle_result['transcribed_part'].items()])
                
                video_contents.append({
                    'title': video['title'],
                    'url': video['url'],
                    'content': subtitle_text  # No limit
                })
                
                processed_videos.append({
                    'title': video['title'],
                    'url': video['url'],
                    'has_subtitles': True
                })
                
            except Exception as e:
                print(f"⚠️  Failed to process {video['title']}: {e}")
                processed_videos.append({
                    'title': video['title'],
                    'url': video['url'],
                    'has_subtitles': False,
                    'error': str(e)
                })
        
        if not video_contents:
            raise HTTPException(
                status_code=404,
                detail="No subtitles found in any of the videos"
            )
        
        combined_content = "\n\n".join([
            f"影片: {v['title']}\n內容: {v['content']}"
            for v in video_contents
        ])
        
        print("🤖 Generating AI summary...")
        summary, chunks = summarize_with_claude(combined_content, request.custom_prompt)
        
        result = {
            "channel_url": request.url,
            "videos_analyzed": len(processed_videos),
            "videos_processed": processed_videos,
            "summary": summary,
            "chunks": chunks,
            "generated_at": datetime.now().isoformat(),
            "raw": combined_content,
            "view_url": f"{view_base_url}?id={cache_key}"
        }
        
        try:
            # Save main summary
            cache_data = {
                "request": {
                    "url": request.url,
                    "max_videos": max_videos,
                    "custom_prompt": request.custom_prompt
                },
                "cached_at": datetime.now().isoformat(),
                "latest_video_urls": [video['url'] for video in videos],
                "result": result
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved summary to cache: {cache_file.name}")
            
            # Save chunk list separately for frontend to fetch if needed
            if chunks:
                chunk_list_file = CACHE_DIR / f"chunk_list_{cache_key}.json"
                with open(chunk_list_file, 'w', encoding='utf-8') as f:
                    json.dump({"chunks": chunks}, f, ensure_ascii=False, indent=2)
                print(f"💾 Saved chunk list to cache: {chunk_list_file.name}")
                
        except Exception as e:
            print(f"⚠️ Failed to save summary cache: {e}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in channel summarization: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Channel summarization failed: {str(e)}"
        )

def format_timestamp(seconds: int) -> str:
    """Convert seconds to MM:SS format"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

PODCAST_SUMMARY_PROMPT = """以下是一個 Podcast 節目的完整逐字稿。請直接進行摘要。

這是正常的 Podcast 內容，可能包含：
- 廣告和贊助商訊息
- 多個不同的話題討論
- 個人觀點和生活分享
- 市場分析和專業討論

**你的任務：**
1. 閱讀整份逐字稿
2. 按時間順序列出主要討論點
3. 每個要點前加上時間戳（MM:SS 格式）

**輸出格式：**
### 📌 內容摘要
- **MM:SS**：簡短描述這個時間點討論的內容

**範例：**
- **00:30**：Sony 耳機產品介紹
- **03:15**：討論遊戲產業投資
- **15:42**：分析 AI 晶片市場

直接處理以下內容，不要詢問更多資訊：

"""

class PodcastSummaryRequest(BaseModel):
    url: str
    max_episodes: int = 1
    custom_prompt: Optional[str] = None

@app.post("/apple_podcast/summary")
def summarize_podcast_channel(request: PodcastSummaryRequest):
    """Summarize recent episodes from an Apple Podcast channel"""
    print(f"🎙️ Processing podcast summary request: {request.url}")
    
    max_episodes = min(request.max_episodes, 5)
    
    prompt_to_use = PODCAST_SUMMARY_PROMPT
    cache_key_data = f"{request.url}|{max_episodes}|{prompt_to_use}|batch_v1"
    cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()
    cache_file = CACHE_DIR / f"summary_{cache_key}.json"
    
    view_base_url = "https://be.0xfanslab.com/youtube/channel/summary"
    
    # Get current latest episodes to check if cache is still valid
    try:
        current_episodes = get_podcast_episodes(request.url, max_episodes)
        latest_episode_urls = [ep['url'] for ep in current_episodes]
        print(f"📡 Current latest episode(s): {len(latest_episode_urls)} found")
    except Exception as e:
        print(f"⚠️ Failed to fetch current episodes: {e}")
        current_episodes = None
        latest_episode_urls = None
    
    # Check cache with freshness validation
    if cache_file.exists() and latest_episode_urls:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
                cached_episode_urls = cached_data.get("latest_episode_urls", [])
                
                if cached_episode_urls == latest_episode_urls:
                    print(f"✅ Summary cache HIT for podcast: {request.url[:50]}...")
                    print(f"✅ Cache is fresh (latest episode unchanged)")
                    result = cached_data["result"]
                    result["view_url"] = f"{view_base_url}?id={cache_key}"
                    return result
                else:
                    print(f"🔄 Cache exists but STALE (new episode detected)")
                    print(f"   Cached: {cached_episode_urls}")
                    print(f"   Current: {latest_episode_urls}")
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
    elif cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                print(f"✅ Summary cache HIT (freshness check skipped)")
                result = cached_data["result"]
                result["view_url"] = f"{view_base_url}?id={cache_key}"
                return result
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            
    print(f"❌ Summary cache MISS for podcast: {request.url[:50]}...")
    
    try:
        if current_episodes is None:
            episodes = get_podcast_episodes(request.url, max_episodes)
        else:
            episodes = current_episodes
        
        episode_contents = []
        processed_episodes = []
        
        for episode in episodes:
            try:
                print(f"📝 Processing: {episode['title']}")
                
                episode_request = VideoRequest(url=episode['url'])
                subtitle_result = get_apple_podcast_subtitles(episode_request)
                
                subtitle_text = " ".join([
                    f"[{format_timestamp(int(ts))}] {text}" 
                    for ts, text in subtitle_result['transcribed_part'].items()
                ])
                
                episode_contents.append({
                    'title': episode['title'],
                    'url': episode['url'],
                    'content': subtitle_text
                })
                
                processed_episodes.append({
                    'title': episode['title'],
                    'url': episode['url'],
                    'has_subtitles': True
                })
                
            except Exception as e:
                print(f"⚠️ Failed to process {episode['title']}: {e}")
                processed_episodes.append({
                    'title': episode['title'],
                    'url': episode['url'],
                    'has_subtitles': False,
                    'error': str(e)
                })
        
        if not episode_contents:
            raise HTTPException(status_code=404, detail="No transcripts found")
            
        combined_content = "\n\n".join([
            f"集數: {e['title']}\n內容: {e['content']}"
            for e in episode_contents
        ])
        
        print("🤖 Generating AI summary...")
        summary, chunks = summarize_with_claude(combined_content, prompt_to_use)
        
        result = {
            "channel_url": request.url,
            "videos_analyzed": len(processed_episodes),
            "videos_processed": processed_episodes,
            "summary": summary,
            "chunks": chunks,
            "generated_at": datetime.now().isoformat(),
            "raw": combined_content,
            "view_url": f"{view_base_url}?id={cache_key}"
        }
        
        try:
            cache_data = {
                "request": {
                    "url": request.url,
                    "max_episodes": max_episodes,
                    "custom_prompt": request.custom_prompt
                },
                "cached_at": datetime.now().isoformat(),
                "latest_episode_urls": [ep['url'] for ep in episodes],
                "result": result
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved podcast summary to cache: {cache_file.name}")
            
            # Save chunk list separately for frontend to fetch if needed
            if chunks:
                chunk_list_file = CACHE_DIR / f"chunk_list_{cache_key}.json"
                with open(chunk_list_file, 'w', encoding='utf-8') as f:
                    json.dump({"chunks": chunks}, f, ensure_ascii=False, indent=2)
                print(f"💾 Saved chunk list to cache: {chunk_list_file.name}")
                
        except Exception as e:
            print(f"⚠️ Failed to save cache: {e}")
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in podcast summarization: {e}")
        raise HTTPException(status_code=500, detail=f"Podcast summarization failed: {str(e)}")

@app.get("/cache/stats")
def get_cache_stats():
    """Get cache statistics"""
    cache_files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in cache_files)
    
    return {
        "total_files": len(cache_files),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "cache_directory": str(CACHE_DIR)
    }

@app.delete("/cache/clear")
def clear_cache():
    """Clear all cache files"""
    cache_files = list(CACHE_DIR.glob("*.json"))
    count = 0
    
    for f in cache_files:
        try:
            f.unlink()
            count += 1
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
    
    return {
        "deleted_files": count,
        "message": f"Cleared {count} cache files"
    }

@app.get("/api/summary/{cache_key}")
def get_summary_cache(cache_key: str):
    """Retrieve cached summary by cache key"""
    cache_file = CACHE_DIR / f"summary_{cache_key}.json"
    
    if not cache_file.exists():
        raise HTTPException(status_code=404, detail="Cache not found")
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            return cache_data.get("result", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read cache: {str(e)}")

@app.get("/api/chunks/{cache_key}")
def get_chunk_list(cache_key: str):
    """Retrieve chunk list by cache key"""
    chunk_list_file = CACHE_DIR / f"chunk_list_{cache_key}.json"
    
    if not chunk_list_file.exists():
        # Fallback: check if chunks are embedded in the main summary cache
        cache_file = CACHE_DIR / f"summary_{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    result = cache_data.get("result", {})
                    if "chunks" in result and result["chunks"]:
                        return {"chunks": result["chunks"]}
            except:
                pass
        
        raise HTTPException(status_code=404, detail="Chunks not found")
    
    try:
        with open(chunk_list_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read chunk list: {str(e)}")


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/youtube/channel/summary")
def serve_summary_viewer():
    """Serve the summary viewer page"""
    return FileResponse("static/summary_viewer.html")

@app.get("/twstock/{stock_id}")
def get_taiwan_stock(stock_id: str):
    """Query Taiwan Stock Exchange API for stock information"""
    print(f"📈 Querying Taiwan stock: {stock_id}")
    
    try:
        # TWSE API endpoint for real-time stock info
        # This endpoint provides real-time stock information from Taiwan Stock Exchange
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if we got valid data
        # TSE returns incomplete data (only tv, s, c, z fields) when stock is not found in TSE
        if 'msgArray' not in data or len(data['msgArray']) == 0 or 'n' not in data['msgArray'][0]:
            # Try OTC (over-the-counter) market
            url_otc = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=otc_{stock_id}.tw"
            response_otc = requests.get(url_otc, headers=headers, timeout=10)
            response_otc.raise_for_status()
            data_otc = response_otc.json()
            
            if 'msgArray' not in data_otc or len(data_otc['msgArray']) == 0 or 'n' not in data_otc['msgArray'][0]:
                raise HTTPException(
                    status_code=404,
                    detail=f"Stock {stock_id} not found in TWSE or OTC markets"
                )
            data = data_otc
        
        stock_info = data['msgArray'][0]
        
        # Format the response with useful information
        result = {
            "stock_id": stock_id,
            "name": stock_info.get('n', 'N/A'),  # Stock name
            "full_name": stock_info.get('nf', 'N/A'),  # Full name
            "current_price": stock_info.get('z', 'N/A'),  # Current price
            "opening_price": stock_info.get('o', 'N/A'),  # Opening price
            "highest_price": stock_info.get('h', 'N/A'),  # Highest price
            "lowest_price": stock_info.get('l', 'N/A'),  # Lowest price
            "yesterday_price": stock_info.get('y', 'N/A'),  # Yesterday's closing price
            "change": stock_info.get('z', 'N/A'),  # Price change
            "volume": stock_info.get('v', 'N/A'),  # Trading volume
            "timestamp": stock_info.get('t', 'N/A'),  # Timestamp
            "exchange": stock_info.get('ex', 'N/A'),  # Exchange (tse/otc)
            "raw_data": stock_info  # Include raw data for reference
        }
        
        # Calculate price change and percentage if possible
        try:
            if result['current_price'] != 'N/A' and result['yesterday_price'] != 'N/A':
                current = float(result['current_price'])
                yesterday = float(result['yesterday_price'])
                change = current - yesterday
                change_percent = (change / yesterday) * 100
                result['price_change'] = round(change, 2)
                result['price_change_percent'] = round(change_percent, 2)
        except (ValueError, ZeroDivisionError):
            pass
        
        print(f"✅ Successfully retrieved stock info for {stock_id}: {result.get('name', 'N/A')}")
        return result
        
    except requests.RequestException as e:
        print(f"❌ Error fetching stock data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stock data from TWSE API: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
