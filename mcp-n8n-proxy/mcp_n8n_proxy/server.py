#!/usr/bin/env python3
"""
MCP n8n Proxy Server

Main server entry point that registers tools and handles MCP protocol communication.
"""

import asyncio
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools import create_n8n_workflow


# Load environment variables from .env file
load_dotenv()


# Create MCP server instance
app = Server("mcp-n8n-proxy")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools provided by this MCP server.
    """
    return [
        Tool(
            name="create_n8n_workflow",
            description="Create an n8n workflow by posting the workflow JSON to the n8n REST API. "
                       "This tool accepts a complete n8n workflow definition and creates it in your n8n instance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow": {
                        "type": "object",
                        "description": "Complete n8n workflow definition. This should include all nodes, "
                                     "connections, and settings required for the workflow. "
                                     "The workflow object will be sent directly to the n8n API.",
                    }
                },
                "required": ["workflow"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool execution requests from MCP clients.
    
    Args:
        name: The name of the tool to execute
        arguments: Dictionary of arguments passed to the tool
        
    Returns:
        List of TextContent objects containing the tool's response
    """
    if name == "create_n8n_workflow":
        # Extract workflow from arguments
        workflow = arguments.get("workflow")
        
        if workflow is None:
            return [
                TextContent(
                    type="text",
                    text="Error: 'workflow' parameter is required"
                )
            ]
        
        # Execute the tool
        result = await create_n8n_workflow(workflow)
        
        # Format the response
        import json
        result_text = json.dumps(result, indent=2, ensure_ascii=False)
        
        return [
            TextContent(
                type="text",
                text=result_text
            )
        ]
    else:
        return [
            TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )
        ]


async def main():
    """
    Main entry point for the MCP server.
    Runs the server using stdio transport.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
