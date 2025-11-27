#!/usr/bin/env python3
"""Test script for YouTube channel summarization"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_channel_summary():
    print("=" * 60)
    print("📺 Testing YouTube Channel Summarization")
    print("=" * 60)
    
    # YouTube channel URL
    channel_url = "https://www.youtube.com/@yutinghaofinance/streams"
    
    print(f"\n📻 Channel URL: {channel_url}")
    print("\n🔄 Requesting channel summary (this may take a while)...")
    print("   - Fetching recent videos")
    print("   - Extracting subtitles")
    print("   - Generating AI summary")
    
    try:
        response = requests.post(
            f"{BASE_URL}/youtube/channel/summary",
            json={
                "url": channel_url,
                "max_videos": 1  # Only process the latest video
            },
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success!")
            print(f"\n📊 Results:")
            print(f"  Channel: {result['channel_url']}")
            print(f"  Videos analyzed: {result['videos_analyzed']}")
            print(f"  Generated at: {result['generated_at']}")
            
            print(f"\n📹 Processed Videos:")
            for video in result['videos_processed']:
                status = "✅" if video['has_subtitles'] else "❌"
                print(f"  {status} {video['title']}")
                if not video['has_subtitles']:
                    print(f"     Error: {video.get('error', 'Unknown')}")
            
            print(f"\n📝 AI Summary:")
            print("=" * 60)
            print(result['summary'])
            print("=" * 60)
            
            # Save full result to file
            with open('channel_summary_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Full result saved to: channel_summary_result.json")
            
        elif response.status_code == 503:
            print("\n⚠️  AI summarization not available")
            print("   Please set ANTHROPIC_API_KEY in your .env file")
            print("\n   Example:")
            print("   ANTHROPIC_API_KEY=sk-ant-...")
        else:
            print(f"\n❌ Failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n⏱️  Request timed out.")
        print("   Channel summarization can take several minutes.")
        print("   Try reducing max_videos or check server logs.")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server. Is it running?")
        print("   Start it with: ./start_server.sh")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_channel_summary()
