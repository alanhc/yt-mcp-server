#!/usr/bin/env python3
"""Test script to verify view_url in response"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_view_url():
    print("=" * 60)
    print("🔗 Testing View URL Generation")
    print("=" * 60)
    
    # YouTube channel URL
    channel_url = "https://www.youtube.com/@yutinghaofinance/streams"
    
    print(f"\n📻 Channel URL: {channel_url}")
    print("\n🔄 Requesting channel summary...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/youtube/channel/summary",
            json={
                "url": channel_url,
                "max_videos": 1
            },
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success!")
            
            view_url = result.get('view_url')
            if view_url:
                print(f"\n🔗 View URL found:")
                print(f"   {view_url}")
                print(f"\n   You can open this URL in your browser to view the summary.")
            else:
                print("\n❌ view_url NOT found in response!")
                print("Response keys:", result.keys())
            
        else:
            print(f"\n❌ Failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_view_url()
