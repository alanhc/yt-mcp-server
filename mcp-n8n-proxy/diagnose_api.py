#!/usr/bin/env python3
"""
Diagnostic script to test n8n API connection and authentication
"""

import asyncio
import httpx
import os
import json
from dotenv import load_dotenv


async def test_n8n_connection():
    load_dotenv()
    
    base_url = os.getenv("N8N_BASE_URL", "https://n8n.0xfanslab.com")
    api_token = os.getenv("N8N_API_TOKEN")
    
    print("=" * 70)
    print("🔍 n8n API Connection Diagnostic")
    print("=" * 70)
    print(f"Base URL: {base_url}")
    print(f"API Token (first 20 chars): {api_token[:20] if api_token else 'NOT SET'}...")
    print("=" * 70)
    print()
    
    if not api_token:
        print("❌ API token not set!")
        return
    
    async with httpx.AsyncClient() as client:
        # Test 1: Check API health/status
        print("Test 1: Checking API endpoint accessibility")
        print("-" * 70)
        try:
            response = await client.get(f"{base_url}/healthz", timeout=10.0)
            print(f"Health check status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"Health check failed: {e}")
        print()
        
        # Test 2: Try to list workflows with Bearer token
        print("Test 2: Testing Bearer token authentication (GET /api/v1/workflows)")
        print("-" * 70)
        headers_v1 = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        }
        try:
            response = await client.get(
                f"{base_url}/api/v1/workflows",
                headers=headers_v1,
                timeout=10.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"Request failed: {e}")
        print()
        
        # Test 3: Try alternative endpoint /rest/workflows
        print("Test 3: Testing /rest/workflows endpoint")
        print("-" * 70)
        headers_rest = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        }
        try:
            response = await client.get(
                f"{base_url}/rest/workflows",
                headers=headers_rest,
                timeout=10.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"Request failed: {e}")
        print()
        
        # Test 4: Try with X-N8N-API-KEY header (alternative auth method)
        print("Test 4: Testing X-N8N-API-KEY authentication")
        print("-" * 70)
        headers_api_key = {
            "X-N8N-API-KEY": api_token,
            "Accept": "application/json"
        }
        try:
            response = await client.get(
                f"{base_url}/api/v1/workflows",
                headers=headers_api_key,
                timeout=10.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"Request failed: {e}")
        print()
        
        print("=" * 70)
        print("💡 Suggestions:")
        print("   1. Check if the API token is still valid in n8n settings")
        print("   2. Verify the correct API endpoint (might be /api/v1 instead of /rest)")
        print("   3. Check if n8n requires a different authentication header")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_n8n_connection())
