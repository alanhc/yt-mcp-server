#!/usr/bin/env python3
"""
測試腳本：驗證自動 fallback 到 Whisper 轉錄的功能
Test script: Verify automatic fallback to Whisper transcription
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_subtitle_fallback():
    """
    測試字幕 fallback 功能
    Test subtitle fallback functionality
    """
    
    print("=" * 80)
    print("測試場景 1: 有字幕的影片")
    print("Test Case 1: Video with subtitles")
    print("=" * 80)
    
    # 測試一個有字幕的影片
    video_with_subs = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"\n📺 Testing video: {video_with_subs}")
    print("Expected: Should use subtitles\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/yt",
            json={"url": video_with_subs}
        )
        response.raise_for_status()
        result = response.json()
        
        method = result.get('transcription_method', 'unknown')
        print(f"✅ Success!")
        print(f"Transcription method: {method}")
        print(f"Video ID: {result.get('video_id')}")
        print(f"Title: {result.get('title')}")
        print(f"Transcribed segments: {len(result.get('transcribed_part', {}))}")
        
        if method == 'subtitles':
            print("✅ Correctly used subtitles")
        elif method == 'whisper':
            print("⚠️ Used Whisper (subtitles might not be available)")
        else:
            print("⚠️ Unknown transcription method")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("測試場景 2: 測試摘要功能")
    print("Test Case 2: Test summary functionality")
    print("=" * 80)
    
    print(f"\n📺 Testing summary for: {video_with_subs}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/youtube/summary",
            json={
                "url": video_with_subs,
                "custom_prompt": "請用繁體中文簡短摘要這個影片的主要內容"
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Success!")
        print(f"Video ID: {result.get('video_id')}")
        print(f"Title: {result.get('title')}")
        print(f"\n📝 Summary preview:")
        summary = result.get('summary', '')
        print(summary[:300] + "..." if len(summary) > 300 else summary)
        
        # 保存完整結果
        output_file = f"test_summary_{result.get('video_id', 'unknown')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Full result saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

def test_response_structure():
    """
    測試回應結構
    Test response structure
    """
    print("\n" + "=" * 80)
    print("測試場景 3: 驗證回應結構")
    print("Test Case 3: Verify response structure")
    print("=" * 80)
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        response = requests.post(
            f"{BASE_URL}/yt",
            json={"url": test_url}
        )
        response.raise_for_status()
        result = response.json()
        
        required_fields = ['video_id', 'title', 'page', 'total_pages', 'transcribed_part']
        optional_fields = ['transcription_method']
        
        print("\n✅ Required fields:")
        for field in required_fields:
            has_field = field in result
            status = "✅" if has_field else "❌"
            print(f"  {status} {field}: {has_field}")
        
        print("\n📋 Optional fields:")
        for field in optional_fields:
            has_field = field in result
            value = result.get(field, 'N/A')
            print(f"  - {field}: {value}")
        
        print(f"\n📊 Transcribed segments: {len(result.get('transcribed_part', {}))}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 YouTube Subtitle Fallback Test Suite")
    print("=" * 80)
    print("\n⚠️ 注意：請確保伺服器正在運行 (./start_server.sh)")
    print("⚠️ Note: Make sure the server is running (./start_server.sh)\n")
    
    test_subtitle_fallback()
    test_response_structure()
    
    print("\n" + "=" * 80)
    print("✅ 測試完成！")
    print("✅ Tests completed!")
    print("=" * 80)
