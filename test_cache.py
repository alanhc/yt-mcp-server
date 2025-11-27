#!/usr/bin/env python3
"""Test script to verify cache functionality"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_cache():
    print("=" * 60)
    print("🧪 Testing Cache Functionality")
    print("=" * 60)
    
    # Test URL
    podcast_url = "https://podcasts.apple.com/tw/podcast/gooaye-%E8%82%A1%E7%99%8C/id1500839292?i=1000738486982"
    
    # Get cache stats before
    print("\n📊 Cache stats BEFORE:")
    response = requests.get(f"{BASE_URL}/cache/stats")
    stats_before = response.json()
    print(f"  Cached items: {stats_before['total_cached_items']}")
    print(f"  Total size: {stats_before['total_size_mb']} MB")
    
    # First request (should process and cache)
    print("\n🔄 First request (should process)...")
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/apple_podcast",
        json={"url": podcast_url}
    )
    first_duration = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Success in {first_duration:.2f}s")
        print(f"  Title: {result['title']}")
        print(f"  Segments: {len(result['transcribed_part'])}")
    else:
        print(f"  ❌ Failed: {response.status_code}")
        return
    
    # Second request (should use cache)
    print("\n⚡ Second request (should use cache)...")
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/apple_podcast",
        json={"url": podcast_url}
    )
    second_duration = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Success in {second_duration:.2f}s")
        print(f"  Title: {result['title']}")
        print(f"  Segments: {len(result['transcribed_part'])}")
    else:
        print(f"  ❌ Failed: {response.status_code}")
        return
    
    # Get cache stats after
    print("\n📊 Cache stats AFTER:")
    response = requests.get(f"{BASE_URL}/cache/stats")
    stats_after = response.json()
    print(f"  Cached items: {stats_after['total_cached_items']}")
    print(f"  Total size: {stats_after['total_size_mb']} MB")
    
    # Performance comparison
    print("\n⚡ Performance Comparison:")
    print(f"  First request:  {first_duration:.2f}s (processed)")
    print(f"  Second request: {second_duration:.2f}s (cached)")
    speedup = first_duration / second_duration if second_duration > 0 else 0
    print(f"  Speedup: {speedup:.1f}x faster!")
    
    print("\n" + "=" * 60)
    print("✅ Cache test completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_cache()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server. Is it running?")
        print("   Start it with: ./start_server.sh")
    except Exception as e:
        print(f"❌ Error: {e}")
