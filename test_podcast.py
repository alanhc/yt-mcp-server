import requests
import json

url = "http://localhost:8000/apple_podcast"
data = {
    "url": "https://podcasts.apple.com/tw/podcast/gooaye-%E8%82%A1%E7%99%8C/id1500839292?i=1000738486982"
}

print("Sending request...")
response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response Headers: {response.headers}")
print(f"Response Length: {len(response.text)} characters")

if response.status_code == 200:
    result = response.json()
    print(f"\nTitle: {result.get('title')}")
    print(f"Video ID: {result.get('video_id')}")
    print(f"Number of segments: {len(result.get('transcribed_part', {}))}")
    print("\nFirst 5 segments:")
    for i, (timestamp, text) in enumerate(list(result.get('transcribed_part', {}).items())[:5]):
        print(f"  [{timestamp}s] {text}")
else:
    print(f"Error: {response.text}")
