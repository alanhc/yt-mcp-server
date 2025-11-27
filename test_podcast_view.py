#!/usr/bin/env python3
"""Test script to verify Podcast view_url"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_podcast_view_url():
    print("=" * 60)
    print("🎙️  Testing Podcast View URL")
    print("=" * 60)
    
    # Podcast show URL
    podcast_url = "https://podcasts.apple.com/tw/podcast/gooaye-%E8%82%A1%E7%99%8C/id1500839292"
    
    print(f"\n📻 Podcast URL: {podcast_url}")
    print("\n🔄 Requesting latest episode...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/apple_podcast/latest",
            json={"url": podcast_url},
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success!")
            
            view_url = result.get('view_url')
            if view_url:
                print(f"\n🔗 View URL found:")
                print(f"   {view_url}")
                print(f"\n   Open this URL to view the podcast transcript.")
            else:
                print("\n❌ view_url NOT found in response!")
            
        else:
            print(f"\n❌ Failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_podcast_view_url()
