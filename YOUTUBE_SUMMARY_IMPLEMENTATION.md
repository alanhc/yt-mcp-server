# YouTube Summary Endpoint - Implementation Summary

## 新增功能 (New Feature)

新增了 `/youtube/summary` API 端點，可以根據使用者輸入的 YouTube 影片網址進行 AI 摘要。

Added a new `/youtube/summary` API endpoint that can summarize YouTube videos based on user-provided URLs using AI.

## 最新更新 (Latest Update)

### ✨ 智能字幕獲取 (Smart Subtitle Retrieval)

現在系統會自動處理沒有字幕的影片：
1. **優先使用字幕**：如果影片有字幕（自動或手動），直接使用
2. **自動 Fallback**：如果找不到字幕，自動下載音檔並使用 Whisper 進行語音轉文字
3. **透明處理**：使用者無需關心使用哪種方法，系統會自動選擇最佳方案

The system now automatically handles videos without subtitles:
1. **Subtitle Priority**: Uses subtitles (automatic or manual) if available
2. **Automatic Fallback**: Downloads audio and transcribes with Whisper if no subtitles found
3. **Transparent Processing**: Users don't need to worry about which method is used

## 實作細節 (Implementation Details)

### 1. 新增的檔案 (New Files)

- **example_youtube_summary.py**: 示範如何使用新端點的範例程式
  - Example script demonstrating how to use the new endpoint

### 2. 修改的檔案 (Modified Files)

#### ubuntu_backend.py
- **新增 VideoSummaryRequest 類別** (Added VideoSummaryRequest class)
  - `url`: YouTube 影片網址
  - `custom_prompt`: 可選的自訂 AI 提示詞

- **新增 /youtube/summary 端點** (Added /youtube/summary endpoint)
  - 接收 YouTube 影片網址
  - 自動獲取影片字幕
  - 使用 Claude AI 進行智能摘要
  - 支援快取機制，避免重複處理
  - 返回包含摘要、時間戳記和原始內容的完整結果

#### README.md
- 更新了完整的 API 文檔
- 新增 `/youtube/summary` 端點的使用說明
- 包含請求和回應範例

## 功能特點 (Features)

1. **智能摘要** (Smart Summarization)
   - 使用 Claude AI 進行內容分析
   - 自動提取關鍵重點
   - 保留時間戳記方便回看

2. **快取機制** (Caching System)
   - 自動快取處理結果
   - 相同影片不會重複處理
   - 支援自訂提示詞的獨立快取

3. **分塊處理** (Chunk Processing)
   - 長影片自動分塊處理
   - Map-Reduce 策略確保品質
   - 支援超長內容的摘要

4. **靈活配置** (Flexible Configuration)
   - 支援自訂 AI 提示詞
   - 可調整摘要風格和重點

## 使用方式 (Usage)

### 基本用法 (Basic Usage)

```bash
curl -X POST http://localhost:8000/youtube/summary \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID"
  }'
```

### 使用自訂提示詞 (With Custom Prompt)

```bash
curl -X POST http://localhost:8000/youtube/summary \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "custom_prompt": "請用繁體中文摘要影片的投資相關內容"
  }'
```

### 使用 Python (Using Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/youtube/summary",
    json={"url": "https://www.youtube.com/watch?v=VIDEO_ID"}
)

result = response.json()
print(result['summary'])
```

## 回應格式 (Response Format)

```json
{
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_id": "VIDEO_ID",
  "title": "影片標題",
  "summary": "AI 生成的摘要內容，包含時間戳記和重點",
  "chunks": [],
  "generated_at": "2025-11-29T20:56:44",
  "raw": "完整的逐字稿內容",
  "view_url": "https://be.0xfanslab.com/youtube/channel/summary?id=CACHE_KEY"
}
```

## 測試方式 (Testing)

1. 確保伺服器正在運行:
   ```bash
   ./start_server.sh
   ```

2. 執行範例程式:
   ```bash
   python example_youtube_summary.py
   ```

3. 或使用 curl 測試:
   ```bash
   curl -X POST http://localhost:8000/youtube/summary \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
   ```

## 注意事項 (Notes)

1. **需要重啟伺服器** (Server Restart Required)
   - 修改程式碼後需要重啟伺服器才能生效
   - 使用 Ctrl+C 停止當前伺服器，然後重新執行 `./start_server.sh`

2. **API Key 需求** (API Key Required)
   - 需要設定 `ANTHROPIC_API_KEY` 環境變數
   - Claude AI 摘要功能才能正常運作

3. **GPU 需求** (GPU Required)
   - 如果影片沒有字幕，會使用 faster_whisper 進行語音轉文字
   - 需要 CUDA-capable GPU

4. **快取位置** (Cache Location)
   - 快取檔案儲存在 `.cache/` 目錄
   - 可使用 `DELETE /cache/clear` 清除快取

## 下一步 (Next Steps)

1. 重啟伺服器以載入新功能
2. 使用範例程式測試端點
3. 根據需求調整 AI 提示詞
4. 整合到現有的應用程式中
