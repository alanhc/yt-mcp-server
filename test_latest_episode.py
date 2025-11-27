#!/usr/bin/env python3
"""Test script to verify latest episode functionality"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_latest_episode():
    print("=" * 60)
    print("🎙️  Testing Latest Episode Functionality")
    print("=" * 60)
    
    # Podcast show URL (without specific episode)
    podcast_url = "https://podcasts.apple.com/tw/podcast/gooaye-%E8%82%A1%E7%99%8C/id1500839292"
    
    print(f"\n📻 Podcast URL: {podcast_url}")
    print("\n🔄 Requesting latest episode transcription...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/apple_podcast/latest",
            json={"url": podcast_url},
            timeout=120  # Allow time for transcription
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success!")
            print(f"\n📊 Results:")
            print(f"  Podcast Show: {result.get('podcast_show_url', 'N/A')}")
            print(f"  Episode URL:  {result.get('episode_url', 'N/A')}")
            print(f"  Episode ID:   {result.get('video_id', 'N/A')}")
            print(f"  Title:        {result.get('title', 'N/A')}")
            print(f"  Segments:     {len(result.get('transcribed_part', {}))}")
            print(f"  Is Latest:    {result.get('is_latest_episode', False)}")
            
            # Show first few segments
            transcribed = result.get('transcribed_part', {})
            if transcribed:
                print(f"\n📝 First 3 segments:")
                for i, (timestamp, text) in enumerate(list(transcribed.items())[:3]):
                    print(f"  [{timestamp}s] {text[:80]}...")
            
            # Save full result to file
            with open('latest_episode_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Full result saved to: latest_episode_result.json")
            
        else:
            print(f"\n❌ Failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n⏱️  Request timed out. The transcription might still be processing.")
        print("   Try checking the async endpoint instead.")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server. Is it running?")
        print("   Start it with: ./start_server.sh")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_latest_episode()
