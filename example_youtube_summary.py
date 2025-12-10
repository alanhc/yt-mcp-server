#!/usr/bin/env python3
"""
Example script to test the /youtube/summary endpoint
"""

import requests
import json

# Server URL
BASE_URL = "http://localhost:8000"

def test_youtube_summary(video_url: str, custom_prompt: str = None):
    """
    Test the /youtube/summary endpoint
    
    Args:
        video_url: YouTube video URL
        custom_prompt: Optional custom prompt for AI summarization
    """
    endpoint = f"{BASE_URL}/youtube/summary"
    
    payload = {
        "url": video_url
    }
    
    if custom_prompt:
        payload["custom_prompt"] = custom_prompt
    
    print(f"📺 Requesting summary for: {video_url}")
    print(f"🔗 Endpoint: {endpoint}")
    print(f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}\n")
    
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        print("✅ Success!")
        print(f"\n📊 Results:")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Video ID: {result.get('video_id', 'N/A')}")
        print(f"Generated at: {result.get('generated_at', 'N/A')}")
        print(f"View URL: {result.get('view_url', 'N/A')}")
        print(f"\n📝 Summary:")
        print(result.get('summary', 'No summary available')[:500] + "...")
        
        # Save full result to file
        output_file = f"summary_{result.get('video_id', 'unknown')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Full result saved to: {output_file}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

if __name__ == "__main__":
    # Example 1: Basic usage
    print("=" * 80)
    print("Example 1: Basic YouTube video summary")
    print("=" * 80)
    test_youtube_summary("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    print("\n\n")
    
    # Example 2: With custom prompt
    print("=" * 80)
    print("Example 2: YouTube video summary with custom prompt")
    print("=" * 80)
    custom_prompt = """
    請用繁體中文摘要這個影片的主要內容，並列出：
    1. 影片主題
    2. 關鍵重點（3-5點）
    3. 重要時間戳記
    """
    test_youtube_summary(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        custom_prompt=custom_prompt
    )
