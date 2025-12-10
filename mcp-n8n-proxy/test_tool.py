#!/usr/bin/env python3
"""
Test script for create_n8n_workflow tool

This script directly tests the n8n API integration by creating a simple workflow.
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from mcp_n8n_proxy.tools import create_n8n_workflow


async def main():
    # Load environment variables
    load_dotenv()
    
    # Check if required env vars are set
    n8n_base_url = os.getenv("N8N_BASE_URL", "https://n8n.0xfanslab.com")
    n8n_api_token = os.getenv("N8N_API_TOKEN")
    
    print("=" * 60)
    print("🧪 Testing create_n8n_workflow tool")
    print("=" * 60)
    print(f"📡 n8n Base URL: {n8n_base_url}")
    print(f"🔑 API Token: {'✅ Set' if n8n_api_token else '❌ Not set'}")
    print("=" * 60)
    print()
    
    if not n8n_api_token:
        print("❌ Error: N8N_API_TOKEN is not set in .env file")
        print("Please set it before running this test.")
        return
    
    # Create a simple test workflow
    test_workflow = {
        "name": "MCP Test Workflow - " + str(asyncio.get_event_loop().time()),
        "nodes": [
            {
                "parameters": {},
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [240, 300],
                "id": "start-node"
            },
            {
                "parameters": {
                    "content": "This workflow was created via MCP server!",
                    "options": {}
                },
                "name": "Note",
                "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1,
                "position": [450, 300],
                "id": "note-node"
            }
        ],
        "connections": {},
        "settings": {
            "saveManualExecutions": True
        }
    }
    
    print("📝 Test Workflow Definition:")
    print(json.dumps(test_workflow, indent=2, ensure_ascii=False))
    print()
    print("-" * 60)
    print("🚀 Sending request to n8n API...")
    print("-" * 60)
    print()
    
    # Execute the tool
    result = await create_n8n_workflow(test_workflow)
    
    # Display results
    print("=" * 60)
    print("📊 Result:")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()
    
    # Check if successful
    if result.get("success"):
        workflow_id = result.get("data", {}).get("id")
        workflow_name = result.get("data", {}).get("name")
        print("✅ SUCCESS! Workflow created successfully!")
        print(f"   ID: {workflow_id}")
        print(f"   Name: {workflow_name}")
        print(f"   URL: {n8n_base_url}/workflow/{workflow_id}")
        print()
        print("🔍 Please check your n8n UI to verify the workflow appears!")
    else:
        print("❌ FAILED! There was an error:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        if result.get("body"):
            print(f"   Details: {result.get('body')}")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
