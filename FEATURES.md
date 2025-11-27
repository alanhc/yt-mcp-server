# Ubuntu Backend - 功能總結

## 🎯 已實現功能

### 1. GPU 加速轉錄 ⚡
- ✅ 使用 `faster-whisper` 替代 `mlx-whisper`
- ✅ NVIDIA GPU (CUDA) 支持
- ✅ 強制 GPU 模式（禁用 CPU 降級）
- ✅ 性能提升：~31x 加速（92s → 2.9s）

### 2. 結果緩存 💾
- ✅ 自動緩存轉錄結果到 `.cache/` 目錄
- ✅ 使用 URL MD5 hash 作為緩存 key
- ✅ 同步和異步端點都支持緩存
- ✅ 緩存管理 API：
  - `GET /cache/stats` - 查看緩存統計
  - `DELETE /cache/clear` - 清空所有緩存
  - `DELETE /cache/{hash}` - 刪除特定緩存

### 3. 自動獲取最新一集 🎙️
- ✅ 新端點：`POST /apple_podcast/latest`
- ✅ 接受 Podcast 頻道 URL
- ✅ 自動抓取最新一集
- ✅ 自動轉錄最新一集
- ✅ 返回額外元數據（頻道 URL、集數 URL 等）

### 4. YouTube 頻道總結 🤖 (新功能)
- ✅ 新端點：`POST /youtube/channel/summary`
- ✅ 自動獲取頻道最新影片
- ✅ 提取所有影片字幕
- ✅ 使用 Claude AI 生成繁體中文總結
- ✅ 支持自定義總結提示詞
- ✅ 可配置分析影片數量（最多 10 部）

## 📡 API 端點

### YouTube 字幕
```http
POST /yt
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=...",
  "lang": "zh-TW"  // optional
}
```

### Apple Podcast 轉錄（單集）
```http
POST /apple_podcast
Content-Type: application/json

{
  "url": "https://podcasts.apple.com/tw/podcast/.../id...?i=..."
}
```

### Apple Podcast 最新一集（新功能）
```http
POST /apple_podcast/latest
Content-Type: application/json

{
  "url": "https://podcasts.apple.com/tw/podcast/gooaye-%E8%82%A1%E7%99%8C/id1500839292"
}
```

### 異步轉錄
```http
POST /apple_podcast/async
GET /apple_podcast/status/{task_id}
GET /apple_podcast/tasks
```

### 緩存管理
```http
GET /cache/stats
DELETE /cache/clear
DELETE /cache/{url_hash}
```

### YouTube 頻道總結 (新功能)
```http
POST /youtube/channel/summary
Content-Type: application/json

{
  "url": "https://www.youtube.com/@yutinghaofinance/streams",
  "max_videos": 5,  // optional, default: 5, max: 10
  "custom_prompt": "請總結這些影片的主要投資建議"  // optional
}
```

## 🚀 使用方式

### 啟動服務器
```bash
cd /home/alanhc/workspace/yt-mcp-server
./start_server.sh
```

### 測試緩存功能
```bash
uv run test_cache.py
```

### 測試最新一集功能
```bash
uv run test_latest_episode.py
```

### 測試頻道總結功能 (新)
```bash
# 需要先設置 ANTHROPIC_API_KEY
uv run test_channel_summary.py
```

## 📦 依賴項

新增的依賴：
- `faster-whisper` - GPU 加速 Whisper
- `nvidia-cudnn-cu12` - cuDNN 庫
- `nvidia-cublas-cu12` - cuBLAS 庫
- `requests` - HTTP 請求
- `beautifulsoup4` - HTML 解析
- `lxml` - XML/HTML 解析器
- `anthropic` - Claude AI API 客戶端
- `feedparser` - RSS feed 解析

## 🔧 技術細節

### 緩存機制
- 緩存文件格式：JSON
- 緩存 key：MD5(URL)
- 緩存位置：`.cache/` 目錄
- 緩存內容：完整轉錄結果 + 元數據

### 最新一集抓取
1. 使用 `requests` + `BeautifulSoup` 抓取 Podcast 頁面
2. 解析 HTML 找到第一個集數連結（最新）
3. 構建完整的集數 URL
4. 調用現有的轉錄端點處理

### GPU 設置
- 環境變量：`LD_LIBRARY_PATH` 包含 cuDNN/cuBLAS 路徑
- 啟動腳本：`start_server.sh` 自動設置環境
- 模型精度：float16（GPU）
- 設備檢測：啟動時自動檢測 CUDA

## 📊 性能數據

| 指標 | 數值 |
|------|------|
| GPU 型號 | RTX 3060 (12GB) |
| 音頻大小 | 46.4 MB |
| CPU 預估 | ~92 秒 |
| GPU 實際 | 2.9 秒 |
| 加速比 | 31.7x |
| GPU 使用率 | 79% |
| GPU 記憶體 | ~500 MB |

## 🎯 使用範例

### 範例 1：轉錄最新一集
```python
import requests

response = requests.post(
    "http://localhost:8000/apple_podcast/latest",
    json={
        "url": "https://podcasts.apple.com/tw/podcast/gooaye-%E8%82%A1%E7%99%8C/id1500839292"
    }
)

result = response.json()
print(f"最新一集：{result['title']}")
print(f"集數 URL：{result['episode_url']}")
print(f"轉錄片段數：{len(result['transcribed_part'])}")
```

### 範例 2：查看緩存統計
```python
import requests

response = requests.get("http://localhost:8000/cache/stats")
stats = response.json()

print(f"已緩存項目：{stats['total_cached_items']}")
print(f"緩存大小：{stats['total_size_mb']} MB")
```

### 範例 3：清空緩存
```python
import requests

response = requests.delete("http://localhost:8000/cache/clear")
result = response.json()

print(result['message'])  # "Cleared X cached items"
```

### 範例 4：YouTube 頻道總結 (新)
```python
import requests

response = requests.post(
    "http://localhost:8000/youtube/channel/summary",
    json={
        "url": "https://www.youtube.com/@yutinghaofinance/streams",
        "max_videos": 3,
        "custom_prompt": "請總結這些影片的主要投資策略和建議"
    }
)

result = response.json()
print(f"分析了 {result['videos_analyzed']} 部影片")
print(f"\nAI 總結：\n{result['summary']}")

# 查看處理的影片
for video in result['videos_processed']:
    status = "✅" if video['has_subtitles'] else "❌"
    print(f"{status} {video['title']}")
```

## 🔍 故障排除

### 問題：找不到 cuDNN 庫
**解決方案**：使用 `./start_server.sh` 而不是直接運行 Python

### 問題：無法找到最新一集
**可能原因**：
1. Podcast URL 格式不正確
2. 網頁結構變更
3. 網絡連接問題

**解決方案**：檢查 URL 格式，確保是頻道頁面而非單集頁面

### 問題：緩存未生效
**檢查**：
1. `.cache/` 目錄是否存在
2. 權限是否正確
3. 使用 `GET /cache/stats` 查看緩存狀態

## 📝 注意事項

1. **GPU 模式**：服務器現在強制使用 GPU，如果 GPU 不可用會啟動失敗
2. **緩存持久化**：緩存文件會一直保留直到手動清除
3. **URL 格式**：最新一集功能需要頻道 URL，不是單集 URL
4. **網絡依賴**：抓取最新一集需要網絡連接到 Apple Podcasts

## 🎉 總結

所有功能已完整實現並測試：
- ✅ GPU 加速（31x 提速）
- ✅ 結果緩存（避免重複處理）
- ✅ 自動獲取最新一集（便捷使用）
- ✅ 完整的 API 文檔
- ✅ 測試腳本
