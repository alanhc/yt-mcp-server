# Ubuntu Backend 完整解析

本文件詳細說明 `ubuntu_backend.py` 的架構、功能和實作細節。

## 概覽

`ubuntu_backend.py` 是本專案的主要生產環境後端伺服器，提供 YouTube 影片和 Apple Podcast 的轉錄與 AI 摘要服務。

### 核心功能

1. **雙重轉錄策略**
   - 優先使用字幕（快速、準確）
   - 字幕不可用時自動切換到 Whisper 音訊轉錄
   - 對客戶端透明，回傳格式一致

2. **AI 智能摘要**
   - 使用 Claude AI (claude-3-5-haiku-latest) 進行內容分析
   - 支援 Map-Reduce 策略處理長內容
   - 可自訂提示詞（prompt）
   - 預設針對繁體中文投資內容最佳化

3. **多層快取系統**
   - URL 層級快取：避免重複轉錄
   - 區塊（chunk）層級快取：Map-Reduce 中間結果快取
   - 頻道摘要快取新鮮度驗證：檢查最新影片是否改變
   - 使用 MD5 雜湊作為快取鍵
   - 快取檔案以 JSON 格式儲存於 `.cache/` 目錄

4. **GPU 加速**
   - 使用 `faster_whisper` 與 CUDA 加速
   - 伺服器啟動時預載模型（避免首次請求延遲）
   - GPU-only 模式（不支援 CPU fallback）

5. **特殊功能**
   - 台股查詢整合（TWSE 和 OTC 市場）
   - 批量頻道影片處理
   - Apple Podcast 支援

## 主要 API 端點

| 端點 | 方法 | 功能 | 重要參數 |
|------|------|------|----------|
| `/` | GET | 健康檢查 | - |
| `/yt` | POST | YouTube 影片轉錄 | `url`, `lang`, `page`, `page_size` |
| `/api/youtube/summary` | POST | YouTube 影片摘要 | `url`, `prompt`, `lang` |
| `/api/channel/summary` | POST | YouTube 頻道摘要 | `url`, `max_videos`, `prompt` |
| `/api/podcast/summary` | POST | Apple Podcast 摘要 | `url`, `prompt` |
| `/api/stock/info` | GET | 台股即時資訊 | `stock_id` |
| `/api/summary/{cache_key}` | GET | 取得快取摘要 | `cache_key` |
| `/cache/stats` | GET | 快取統計資訊 | - |
| `/cache/clear` | DELETE | 清除所有快取 | - |
| `/cache/view` | GET | 檢視快取內容 | `id` |
| `/cache/raw` | GET | 取得原始轉錄內容 | `id` |

## 技術架構詳解

### 1. 轉錄流程

#### 字幕轉錄（優先）

```
YouTube URL → yt-dlp 下載字幕 → VTT 格式解析 → 時間戳記整併 → 結構化輸出
```

**實作細節**：
- 支援多語言字幕（預設：繁體中文 zh-TW）
- 自動字幕和手動字幕都支援
- VTT 格式解析，提取時間戳記和文字
- 合併 5 秒內的連續字幕條目
- 輸出格式：`{timestamp_seconds: "text"}`

**關鍵程式碼位置**：
- `parse_vtt()` 函數（lines 74-106）：VTT 格式解析
- `/yt` 端點（lines 538-687）：字幕下載邏輯

#### Whisper 音訊轉錄（備援）

```
YouTube URL → yt-dlp 下載音訊 → faster_whisper GPU 轉錄 → 時間戳記對齊 → 結構化輸出
```

**實作細節**：
- 使用預載的 `faster_whisper` 模型（base size）
- GPU-only 模式，使用 CUDA 和 float16 精度
- 音訊下載至臨時目錄（`/tmp/{uuid}/`）
- 轉錄完成後自動清理臨時檔案
- 輸出格式與字幕一致

**關鍵程式碼位置**：
- 模型預載（lines 466-486）：lifespan 管理
- Whisper 轉錄（lines 619-674）：音訊下載和轉錄邏輯

### 2. AI 摘要流程

#### 短內容摘要（< 30,000 字元）

```
轉錄內容 → 單一 Claude API 呼叫 → 摘要輸出
```

#### 長內容摘要（≥ 30,000 字元）- Map-Reduce 策略

```
轉錄內容 → 分割區塊（~25,000 字元/塊）
         ↓
    Map 階段：每個區塊獨立摘要（帶快取）
         ↓
    Reduce 階段：
    1. 串接所有區塊摘要
    2. 生成最終總覽摘要
         ↓
    輸出：{總覽, 分段摘要列表}
```

**Map 階段細節**：
- 使用 `split_text()` 將內容分割成約 25,000 字元的區塊
- 每個區塊生成獨立的 MD5 快取鍵
- 區塊摘要結果快取於 `.cache/chunk_{hash}.json`
- 快取命中率高（相同影片不同提示詞可共用區塊）

**Reduce 階段細節**：
- 將所有區塊摘要串接
- 生成 5-8 個要點的總覽摘要
- 使用自適應提示詞（根據區塊數量調整）

**關鍵程式碼位置**：
- `summarize_with_claude()` 函數（lines 221-464）：完整 Map-Reduce 實作
- `split_text()` 函數（lines 193-218）：智能文字分割

### 3. 快取系統

#### 快取鍵生成

```python
cache_key = hashlib.md5(url.encode()).hexdigest()
cache_file = CACHE_DIR / f"{cache_key}.json"
```

**特性**：
- 基於完整 URL（包含查詢參數）
- 不同自訂提示詞會生成不同快取
- MD5 確保鍵長度固定

#### 快取資料結構

```json
{
  "url": "原始請求 URL",
  "timestamp": "快取建立時間（ISO 8601）",
  "result": {
    "video_url": "影片 URL",
    "summary": "AI 摘要內容",
    "chunks": ["區塊摘要列表"],
    "raw": "完整原始轉錄",
    "generated_at": "生成時間",
    "view_url": "快取檢視 URL"
  }
}
```

#### 頻道摘要快取驗證

```python
# 額外儲存最新影片 URL 列表
{
  "latest_video_urls": ["最新影片 URL 列表"],
  "url": "...",
  "timestamp": "...",
  "result": {...}
}

# 驗證邏輯
if cached_video_urls == current_latest_video_urls:
    return cached_result  # 快取仍然新鮮
else:
    regenerate_summary()  # 頻道有新影片，重新生成
```

**關鍵程式碼位置**：
- `get_cached_result()` 函數（lines 108-132）：讀取快取
- `save_to_cache()` 函數（lines 135-156）：寫入快取
- 頻道摘要快取驗證（lines 942-982）：新鮮度檢查邏輯

## 性能優化

### 1. 模型預載

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global WHISPER_MODEL
    print("🚀 Starting up server...")
    WHISPER_MODEL = WhisperModel(
        WHISPER_MODEL_SIZE,
        device="cuda",
        compute_type="float16"
    )
    print("✅ Model preloaded successfully on GPU!")
    yield
    print("👋 Shutting down server...")
```

**優點**：
- 首次請求無需等待模型載入
- 所有請求共用同一個模型實例
- 減少記憶體使用

### 2. 多層快取

- **URL 快取**：完全避免重複轉錄和摘要
- **區塊快取**：Map-Reduce 中間結果複用
- **快取檢視端點**：直接存取快取內容無需再處理

### 3. 臨時檔案管理

```python
temp_dir = f"/tmp/{uuid.uuid4()}"
os.makedirs(temp_dir, exist_ok=True)
try:
    # 處理音訊檔案
    audio_file = os.path.join(temp_dir, "audio.mp3")
    # ... 下載和轉錄 ...
finally:
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
```

**優點**：
- UUID 確保並行請求不會衝突
- finally 區塊確保清理執行
- 避免磁碟空間浪費

### 4. GPU 加速

- CUDA 加速的 Whisper 轉錄（比 CPU 快 10-20 倍）
- float16 精度（平衡速度和準確度）
- 預設使用 base 模型（速度和準確度平衡）

## 環境配置

### 必要環境變數

```bash
ANTHROPIC_API_KEY=your_api_key_here  # AI 摘要功能必需
```

### CUDA 函式庫路徑

在 `start_server.sh` 中設定：

```bash
export LD_LIBRARY_PATH=".venv/lib/python3.12/site-packages/nvidia/cudnn/lib:.venv/lib/python3.12/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH"
```

### 相依套件

**核心套件**：
- `fastapi` - Web 框架
- `uvicorn` - ASGI 伺服器
- `yt-dlp` - YouTube/媒體下載
- `faster_whisper` - GPU 加速轉錄
- `anthropic` - Claude AI 客戶端
- `beautifulsoup4` - HTML 解析（Podcast）
- `pydantic` - 請求/回應驗證

## 特殊功能

### 1. 台股查詢整合

**端點**：`GET /api/stock/info?stock_id={股票代碼}`

**功能**：
- 查詢台灣證券交易所（TWSE）上市股票
- 查詢櫃買中心（OTC）上櫃股票
- 回傳即時股價、漲跌幅等資訊

**API 來源**：
- TWSE: `https://mis.twse.com.tw/stock/api/getStockInfo.jsp`
- OTC: `https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingInfo`

**關鍵程式碼位置**：lines 1393-1448

### 2. 批量頻道處理

**端點**：`POST /api/channel/summary`

**功能**：
- 自動擷取頻道最新 N 部影片
- 批量轉錄所有影片
- 生成整體頻道內容摘要
- 支援快取新鮮度驗證（檢查最新影片是否改變）

**使用場景**：
- 追蹤特定 YouTuber 的內容
- 投資頻道的定期分析
- 新聞頻道的議題追蹤

**關鍵程式碼位置**：lines 919-1050

### 3. Apple Podcast 支援

**端點**：`POST /api/podcast/summary`

**功能**：
- 解析 Apple Podcast 頁面
- 擷取 episode 的音訊 URL
- 使用 Whisper 轉錄音訊
- 生成 AI 摘要

**實作細節**：
- 使用 BeautifulSoup 解析 HTML
- 支援完整 episode URL 和 podcast 頁面 URL
- 從頁面擷取第一個 episode（如果未指定）

**關鍵程式碼位置**：lines 1053-1232

## 設計特點

### 1. 統一回應格式

所有轉錄端點回傳一致的格式：

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
  "transcription_method": "subtitles" | "whisper"
}
```

**優點**：
- 客戶端無需處理不同格式
- 透明的備援切換
- 易於除錯（`transcription_method` 欄位）

### 2. 分頁支援

轉錄結果支援分頁（`page` 和 `page_size` 參數）：

```python
# 計算分頁
start_idx = (page - 1) * page_size
end_idx = start_idx + page_size
total_pages = (len(items) + page_size - 1) // page_size

# 只回傳當前頁的內容
transcribed_part = dict(list(sorted_items)[start_idx:end_idx])
```

**使用場景**：
- 長影片轉錄結果太大
- 漸進式載入內容
- 減少單次請求負載

### 3. 錯誤處理

```python
try:
    # 主要邏輯
    result = process_video(url)
except HTTPException:
    raise  # 重新拋出 HTTP 例外
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    raise HTTPException(
        status_code=500,
        detail=f"Internal server error: {str(e)}"
    )
finally:
    # 清理臨時檔案
    cleanup_temp_files()
```

**特點**：
- 明確的 HTTP 狀態碼
- 詳細的錯誤訊息
- 確保資源清理

### 4. 可擴展性

- **自訂提示詞**：每個摘要端點支援 `prompt` 參數
- **語言彈性**：轉錄端點支援 `lang` 參數
- **模型切換**：透過環境變數 `WHISPER_MODEL_SIZE` 調整
- **快取策略**：基於 URL 的快取允許不同參數組合

## API 使用範例

### 1. YouTube 影片轉錄

```bash
curl -X POST "http://localhost:8000/yt" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "lang": "zh-TW",
    "page": 1,
    "page_size": 100
  }'
```

### 2. YouTube 影片摘要

```bash
curl -X POST "http://localhost:8000/api/youtube/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "prompt": "請摘要這部影片的主要投資觀點",
    "lang": "zh-TW"
  }'
```

### 3. 頻道摘要

```bash
curl -X POST "http://localhost:8000/api/channel/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/@channel_name",
    "max_videos": 5,
    "prompt": "分析這個頻道最近的主要議題"
  }'
```

### 4. 快取管理

```bash
# 查看快取統計
curl "http://localhost:8000/cache/stats"

# 清除所有快取
curl -X DELETE "http://localhost:8000/cache/clear"

# 檢視特定快取
curl "http://localhost:8000/cache/view?id=CACHE_KEY"
```

## 開發和部署

### 啟動伺服器

```bash
./start_server.sh
```

這個腳本會：
1. 設定 CUDA 函式庫路徑
2. 使用 `uv` 執行 Python
3. 啟動 FastAPI 伺服器（port 8000）

### Docker 部署

```bash
./docker-start.sh  # 建置並執行
./docker-stop.sh   # 停止容器
```

### Systemd 服務

```bash
./install-service.sh    # 安裝為系統服務
./uninstall-service.sh  # 移除系統服務
```

## 注意事項

### GPU 需求

- 需要 CUDA-capable GPU
- 確保安裝 CUDA toolkit 和 cuDNN
- 建議至少 4GB VRAM

### 快取管理

- 快取目錄：`.cache/`
- 快取不會自動過期（需手動清理）
- 頻道摘要有新鮮度驗證機制

### 並行請求

- UUID 臨時目錄確保檔案不衝突
- 模型實例共用（thread-safe）
- 無需擔心並行安全性

### API 配額

- Claude AI 有 API 使用配額
- Map-Reduce 策略會增加 API 呼叫次數
- 建議監控 `ANTHROPIC_API_KEY` 使用量

## 故障排除

### GPU 載入失敗

```
❌ FATAL: Could not load model on GPU
💡 Ensure CUDA and cuDNN are properly installed
```

**解決方法**：
1. 檢查 CUDA 安裝：`nvidia-smi`
2. 驗證 cuDNN 函式庫路徑
3. 確認 `LD_LIBRARY_PATH` 設定正確

### 字幕不可用

伺服器會自動切換到 Whisper 轉錄：

```
⚠️ Subtitles not available, falling back to Whisper transcription
```

這是正常行為，無需介入。

### AI 摘要失敗

```
503 Service Unavailable
AI summarization not available - ANTHROPIC_API_KEY not configured
```

**解決方法**：
設定環境變數 `ANTHROPIC_API_KEY`

## 相關文件

- `YOUTUBE_SUMMARY_IMPLEMENTATION.md` - 摘要功能詳細實作
- `UPDATE_WHISPER_FALLBACK.md` - Whisper 備援實作指南
- `CHANNEL_SUMMARY_GUIDE.md` - 頻道摘要文件
- `CLAUDE.md` - Claude Code 開發指引

## 總結

`ubuntu_backend.py` 是一個功能完整、性能優化的生產環境後端：

✅ **智能轉錄**：字幕優先，Whisper 備援
✅ **AI 驅動**：Claude API 摘要，Map-Reduce 處理長內容
✅ **高效快取**：多層快取系統，新鮮度驗證
✅ **GPU 加速**：CUDA + float16 快速轉錄
✅ **豐富功能**：支援 YouTube、Podcast、頻道、台股查詢
✅ **生產就緒**：錯誤處理、資源清理、並行安全

適合用於構建影片/音訊內容分析、投資研究、內容聚合等應用。
