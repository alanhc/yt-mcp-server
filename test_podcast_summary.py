#!/usr/bin/env python3
"""Test script for Podcast Channel Summary"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_podcast_summary():
    print("=" * 60)
    print("🎙️  Testing Podcast Channel Summary")
    print("=" * 60)
    
    # Podcast show URL (Gooaye 股癌)
    podcast_url = "https://podcasts.apple.com/tw/podcast/gooaye-%E8%82%A1%E7%99%8C/id1500839292"
    
    print(f"\n📻 Podcast URL: {podcast_url}")
    print("\n🔄 Requesting summary for latest 1 episodes...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/apple_podcast/summary",
            json={
                "url": podcast_url,
                "max_episodes": 1,
                "custom_prompt": "請總結這幾集的主要觀點，特別關注市場分析部分。"
            },
            timeout=600  # Long timeout for processing
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success! (Took {elapsed:.1f}s)")
            
            print(f"\n📊 Summary:")
            print("-" * 40)
            print(result.get('summary', 'No summary provided'))
            print("-" * 40)
            
            print(f"\n🔗 View URL:")
            print(f"   {result.get('view_url')}")
            
            print(f"\n📁 Episodes Processed: {result.get('videos_analyzed')}")
            for ep in result.get('videos_processed', []):
                status = "✅" if ep.get('has_subtitles') else "❌"
                print(f"   {status} {ep.get('title')}")
            
        else:
            print(f"\n❌ Failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_podcast_summary()
