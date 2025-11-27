#!/usr/bin/env python3
"""
Test script for async podcast transcription API
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def submit_task(url):
    """Submit a transcription task"""
    print("📤 Submitting transcription task...")
    response = requests.post(
        f"{BASE_URL}/apple_podcast/async",
        json={"url": url}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Task submitted!")
        print(f"   Task ID: {data['task_id']}")
        print(f"   Status: {data['status']}")
        print(f"   Message: {data['message']}")
        return data['task_id']
    else:
        print(f"❌ Error: {response.text}")
        return None

def check_status(task_id):
    """Check task status"""
    response = requests.get(f"{BASE_URL}/apple_podcast/status/{task_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error: {response.text}")
        return None

def wait_for_completion(task_id, check_interval=5):
    """Wait for task to complete"""
    print(f"\n⏳ Waiting for task to complete...")
    print(f"   Checking every {check_interval} seconds...")
    
    while True:
        status_data = check_status(task_id)
        
        if not status_data:
            break
        
        status = status_data['status']
        progress = status_data['progress']
        
        print(f"\n📊 Status: {status}")
        print(f"   Progress: {progress}")
        
        if status_data.get('title'):
            print(f"   Title: {status_data['title']}")
        
        if status == 'completed':
            print("\n✅ Task completed!")
            result = status_data['result']
            print(f"   Processing time: {result['processing_time']:.1f}s")
            print(f"   Segments: {len(result['transcribed_part'])}")
            print(f"\n   First 3 segments:")
            for i, (timestamp, text) in enumerate(list(result['transcribed_part'].items())[:3]):
                print(f"     [{timestamp}s] {text}")
            return result
        elif status == 'failed':
            print(f"\n❌ Task failed!")
            print(f"   Error: {status_data.get('error')}")
            return None
        
        time.sleep(check_interval)

def list_all_tasks():
    """List all tasks"""
    print("\n📋 Listing all tasks...")
    response = requests.get(f"{BASE_URL}/apple_podcast/tasks")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Total tasks: {data['total']}")
        for task in data['tasks']:
            print(f"   - {task['task_id'][:8]}... | {task['status']} | {task['title']}")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    # Test URL
    podcast_url = "requests"
    
    print("=" * 60)
    print("🎙️  Async Podcast Transcription Test")
    print("=" * 60)
    
    # Submit task
    task_id = submit_task(podcast_url)
    
    if task_id:
        # Wait for completion
        result = wait_for_completion(task_id)
        
        # List all tasks
        list_all_tasks()
        
        print("\n" + "=" * 60)
        print("✨ Test completed!")
        print("=" * 60)
