#!/usr/bin/env python3
"""
Test script for n8n FastMCP server
"""

import os
import json
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_list_workflows():
    """Test listing workflows"""
    print("Testing list_n8n_workflows...")
    
    # Call the MCP server endpoint
    url = "http://127.0.0.1:8000/sse"
    
    async with httpx.AsyncClient() as client:
        # This would be an MCP protocol request
        # For now, let's just test if server is responding
        try:
            response = await client.get(url, timeout=5.0)
            print(f"Server responding: {response.status_code}")
        except Exception as e:
            print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    asyncio.run(test_list_workflows())
