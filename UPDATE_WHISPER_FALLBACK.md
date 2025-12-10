# 更新說明：自動 Whisper Fallback 功能

## 📅 更新時間
2025-11-29

## 🎯 更新內容

### 新增功能：智能字幕獲取

修改了 `/yt` 端點，現在會自動處理沒有字幕的影片：

#### 工作流程

```
1. 嘗試獲取字幕
   ├─ 有字幕 → 使用字幕 ✅
   └─ 無字幕 → 自動 fallback
                ↓
2. 下載音檔
   ↓
3. 使用 Whisper 轉錄
   ↓
4. 返回結果 ✅
```

#### 技術細節

**修改的檔案：** `ubuntu_backend.py`

**修改的函數：** `get_subtitles()`

**主要變更：**

1. **優先使用字幕**
   - 先嘗試下載並解析字幕檔案（VTT 格式）
   - 支援多語言字幕（預設 zh-TW）
   - 支援自動生成的字幕

2. **自動 Fallback 到 Whisper**
   - 如果找不到字幕檔案，自動下載音檔
   - 使用 faster_whisper 進行 GPU 加速轉錄
   - 保持與字幕相同的輸出格式

3. **新增回應欄位**
   - `transcription_method`: 標示使用的轉錄方法
     - `"subtitles"`: 使用字幕
     - `"whisper"`: 使用 Whisper 轉錄

## 📊 回應格式

### 使用字幕時

```json
{
  "video_id": "VIDEO_ID",
  "title": "影片標題",
  "page": 1,
  "total_pages": 1,
  "transcribed_part": {
    "0": "第一段文字",
    "3": "第二段文字",
    ...
  },
  "transcription_method": "subtitles"
}
```

### 使用 Whisper 時

```json
{
  "video_id": "VIDEO_ID",
  "title": "影片標題",
  "page": 1,
  "total_pages": 1,
  "transcribed_part": {
    "0": "第一段文字",
    "3": "第二段文字",
    ...
  },
  "transcription_method": "whisper"
}
```

## 🔧 使用方式

### 基本用法（不變）

```bash
curl -X POST http://localhost:8000/yt \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Python 範例

```python
import requests

response = requests.post(
    "http://localhost:8000/yt",
    json={"url": "https://www.youtube.com/watch?v=VIDEO_ID"}
)

result = response.json()
method = result.get('transcription_method')

if method == 'subtitles':
    print("使用字幕")
elif method == 'whisper':
    print("使用 Whisper 轉錄")
```

## 🧪 測試

執行測試腳本：

```bash
python test_subtitle_fallback.py
```

這個腳本會：
1. 測試有字幕的影片
2. 測試摘要功能
3. 驗證回應結構

## ⚡ 效能考量

### 字幕模式（快速）
- 處理時間：~1-3 秒
- 不需要下載音檔
- 不需要 GPU 運算

### Whisper 模式（較慢）
- 處理時間：取決於影片長度
  - 估算：檔案大小(MB) × 2 秒
  - 例如：10MB 音檔 ≈ 20 秒
- 需要下載音檔
- 需要 GPU 加速（faster_whisper）

## 📝 注意事項

1. **快取機制**
   - 兩種方法的結果都會被快取
   - 相同 URL 不會重複處理
   - 快取檔案位於 `.cache/` 目錄

2. **GPU 需求**
   - Whisper 轉錄需要 CUDA-capable GPU
   - 如果 GPU 不可用，會返回錯誤

3. **臨時檔案**
   - Whisper 模式會下載音檔到 `/tmp/`
   - 處理完成後自動清理

4. **錯誤處理**
   - 如果字幕和 Whisper 都失敗，會返回 500 錯誤
   - 錯誤訊息會說明失敗原因

## 🔄 向後相容性

✅ **完全向後相容**

- API 端點不變（`/yt`）
- 請求格式不變
- 回應格式保持相容（只新增 `transcription_method` 欄位）
- 現有客戶端無需修改

## 📦 影響的端點

這個更新影響以下端點：

1. **`POST /yt`** - 直接影響
2. **`POST /youtube/summary`** - 間接影響（使用 `/yt` 的功能）
3. **`POST /youtube/channel/summary`** - 間接影響（使用 `/yt` 的功能）

## 🚀 部署步驟

1. 停止當前伺服器
   ```bash
   # 在運行 ./start_server.sh 的終端按 Ctrl+C
   ```

2. 重新啟動伺服器
   ```bash
   ./start_server.sh
   ```

3. 驗證功能
   ```bash
   python test_subtitle_fallback.py
   ```

## 📚 相關文檔

- `README.md` - 已更新 API 說明
- `YOUTUBE_SUMMARY_IMPLEMENTATION.md` - 已更新實作細節
- `test_subtitle_fallback.py` - 新增測試腳本

## ✅ 檢查清單

- [x] 修改 `get_subtitles()` 函數
- [x] 新增 Whisper fallback 邏輯
- [x] 新增 `transcription_method` 欄位
- [x] 更新文檔
- [x] 創建測試腳本
- [x] 保持向後相容性
- [ ] 重啟伺服器（需要使用者執行）
- [ ] 執行測試驗證（需要使用者執行）
