#!/usr/bin/env python3
"""
MCP n8n Proxy Server using FastMCP

A simplified MCP server implementation using FastMCP that provides
tools for interacting with n8n via its REST API.

Run with:
    uv run python -m mcp_n8n_proxy.server_fastmcp
    
Or with custom port:
    FASTMCP_PORT=8003 uv run python -m mcp_n8n_proxy.server_fastmcp
"""

import os
import httpx
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Configure port and host
DEFAULT_PORT = 8003
port = int(os.getenv("FASTMCP_PORT", str(DEFAULT_PORT)))

# Configure host binding - use 0.0.0.0 to allow connections from reverse proxy
# Set FASTMCP_HOST=127.0.0.1 for local-only access
host = os.getenv("FASTMCP_HOST", "0.0.0.0")

# Configure transport security for deployment behind reverse proxy
# This allows requests from the external domain
external_domain = os.getenv("MCP_EXTERNAL_DOMAIN", "n8n-proxy-mcp-server.0xfanslab.com")
transport_security = TransportSecuritySettings(
    enabled=True,
    allowed_hosts=[
        f"{external_domain}:*",
        f"{external_domain}",
        "127.0.0.1:*",
        "localhost:*",
    ],
    allowed_origins=[
        f"https://{external_domain}",
        f"https://{external_domain}:*",
        "http://127.0.0.1:*",
        "http://localhost:*",
    ],
)

# Create MCP server with configured port, host, and transport security
mcp = FastMCP(
    "n8n-proxy",
    json_response=True,
    port=port,
    host=host,
    transport_security=transport_security,
)


@mcp.tool()
async def create_n8n_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an n8n workflow by posting the workflow JSON to the n8n REST API.
    
    Args:
        workflow: Complete n8n workflow definition including nodes, connections, and settings
        
    Returns:
        Dict containing workflow creation result with success status and data or error details
    """
    # Get environment variables
    n8n_base_url = os.getenv("N8N_BASE_URL", "https://n8n.0xfanslab.com")
    n8n_api_token = os.getenv("N8N_API_TOKEN")
    
    # Validate API token
    if not n8n_api_token:
        return {
            "error": True,
            "status": None,
            "message": "N8N_API_TOKEN environment variable is not set. Please configure your n8n API token.",
            "body": None
        }
    
    # Validate workflow input
    if not isinstance(workflow, dict):
        return {
            "error": True,
            "status": None,
            "message": "Invalid workflow input: expected an object/dict",
            "body": None
        }
    
    # Prepare API request
    url = f"{n8n_base_url.rstrip('/')}/api/v1/workflows"
    headers = {
        "X-N8N-API-KEY": n8n_api_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=workflow,
                headers=headers,
                timeout=30.0
            )
            
            # Check if request was successful
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "status": response.status_code,
                    "data": response.json()
                }
            else:
                # Handle error responses
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                
                return {
                    "error": True,
                    "status": response.status_code,
                    "message": f"n8n API returned error status {response.status_code}",
                    "body": error_body
                }
                
    except httpx.TimeoutException:
        return {
            "error": True,
            "status": None,
            "message": "Request to n8n API timed out",
            "body": None
        }
    except httpx.RequestError as e:
        return {
            "error": True,
            "status": None,
            "message": f"Failed to connect to n8n API: {str(e)}",
            "body": None
        }
    except Exception as e:
        return {
            "error": True,
            "status": None,
            "message": f"Unexpected error: {str(e)}",
            "body": None
        }

@mcp.tool()
async def set_n8n_workflow_activation(workflow_id: str, activate: bool = True) -> Dict[str, Any]:
    """
    Activate or deactivate an n8n workflow.

    Args:
        workflow_id: The ID of the workflow to activate/deactivate
        activate: True to activate, False to deactivate

    Returns:
        Dict containing result or error details
    """
    n8n_base_url = os.getenv("N8N_BASE_URL", "https://n8n.0xfanslab.com")
    n8n_api_token = os.getenv("N8N_API_TOKEN")

    if not n8n_api_token:
        return {
            "error": True,
            "message": "N8N_API_TOKEN environment variable is not set"
        }

    action = "activate" if activate else "deactivate"
    url = f"{n8n_base_url.rstrip('/')}/api/v1/workflows/{workflow_id}/{action}"
    headers = {
        "X-N8N-API-KEY": n8n_api_token,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, timeout=30.0)

            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "status": response.status_code,
                    "data": response.json() if response.text else None,
                    "message": f"Workflow {workflow_id} {action}d successfully",
                }
            else:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text

                return {
                    "error": True,
                    "status": response.status_code,
                    "message": f"n8n API returned error status {response.status_code} when trying to {action} workflow",
                    "body": error_body,
                }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to {action} workflow: {str(e)}",
        }

@mcp.tool()
async def list_n8n_workflows() -> Dict[str, Any]:
    """
    List all workflows from n8n instance.
    
    Returns:
        Dict containing list of workflows or error details
    """
    n8n_base_url = os.getenv("N8N_BASE_URL", "https://n8n.0xfanslab.com")
    n8n_api_token = os.getenv("N8N_API_TOKEN")
    
    if not n8n_api_token:
        return {
            "error": True,
            "message": "N8N_API_TOKEN environment variable is not set"
        }
    
    url = f"{n8n_base_url.rstrip('/')}/api/v1/workflows"
    headers = {
        "X-N8N-API-KEY": n8n_api_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "status": response.status_code,
                    "data": response.json()
                }
            else:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                
                return {
                    "error": True,
                    "status": response.status_code,
                    "message": f"n8n API returned error status {response.status_code}",
                    "body": error_body
                }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to list workflows: {str(e)}"
        }


@mcp.tool()
async def get_n8n_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    Get a specific workflow from n8n by ID.
    
    Args:
        workflow_id: The ID of the workflow to retrieve
        
    Returns:
        Dict containing workflow details or error details
    """
    n8n_base_url = os.getenv("N8N_BASE_URL", "https://n8n.0xfanslab.com")
    n8n_api_token = os.getenv("N8N_API_TOKEN")
    
    if not n8n_api_token:
        return {
            "error": True,
            "message": "N8N_API_TOKEN environment variable is not set"
        }
    
    url = f"{n8n_base_url.rstrip('/')}/api/v1/workflows/{workflow_id}"
    headers = {
        "X-N8N-API-KEY": n8n_api_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "status": response.status_code,
                    "data": response.json()
                }
            else:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                
                return {
                    "error": True,
                    "status": response.status_code,
                    "message": f"n8n API returned error status {response.status_code}",
                    "body": error_body
                }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to get workflow: {str(e)}"
        }


@mcp.tool()
async def delete_n8n_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    Delete a workflow from n8n by ID.
    
    Args:
        workflow_id: The ID of the workflow to delete
        
    Returns:
        Dict containing deletion result or error details
    """
    n8n_base_url = os.getenv("N8N_BASE_URL", "https://n8n.0xfanslab.com")
    n8n_api_token = os.getenv("N8N_API_TOKEN")
    
    if not n8n_api_token:
        return {
            "error": True,
            "message": "N8N_API_TOKEN environment variable is not set"
        }
    
    url = f"{n8n_base_url.rstrip('/')}/api/v1/workflows/{workflow_id}"
    headers = {
        "X-N8N-API-KEY": n8n_api_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers, timeout=30.0)
            
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "status": response.status_code,
                    "message": f"Workflow {workflow_id} deleted successfully"
                }
            else:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                
                return {
                    "error": True,
                    "status": response.status_code,
                    "message": f"n8n API returned error status {response.status_code}",
                    "body": error_body
                }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to delete workflow: {str(e)}"
        }


@mcp.tool()
async def update_n8n_workflow(workflow_id: str, workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing n8n workflow.
    
    Args:
        workflow_id: The ID of the workflow to update
        workflow: Updated workflow definition
        
    Returns:
        Dict containing update result or error details
    """
    n8n_base_url = os.getenv("N8N_BASE_URL", "https://n8n.0xfanslab.com")
    n8n_api_token = os.getenv("N8N_API_TOKEN")
    
    if not n8n_api_token:
        return {
            "error": True,
            "message": "N8N_API_TOKEN environment variable is not set"
        }
    
    if not isinstance(workflow, dict):
        return {
            "error": True,
            "message": "Invalid workflow input: expected an object/dict"
        }
    
    url = f"{n8n_base_url.rstrip('/')}/api/v1/workflows/{workflow_id}"
    headers = {
        "X-N8N-API-KEY": n8n_api_token,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                json=workflow,
                headers=headers,
                timeout=30.0
            )
            
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "status": response.status_code,
                    "data": response.json()
                }
            else:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                
                return {
                    "error": True,
                    "status": response.status_code,
                    "message": f"n8n API returned error status {response.status_code}",
                    "body": error_body
                }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to update workflow: {str(e)}"
        }



# Run with streamable HTTP transport
if __name__ == "__main__":
    import sys
    
    print(f"🚀 FastMCP n8n Proxy Server starting on http://{host}:{port}", file=sys.stderr)
    print(f"📡 Available tools: create_n8n_workflow, list_n8n_workflows, get_n8n_workflow, update_n8n_workflow, delete_n8n_workflow", file=sys.stderr)
    print(f"🌐 External domain: {external_domain}", file=sys.stderr)
    print(f"💡 Environment variables:", file=sys.stderr)
    print(f"   FASTMCP_PORT={port} (default: 8003)", file=sys.stderr)
    print(f"   FASTMCP_HOST={host} (default: 0.0.0.0)", file=sys.stderr)
    print(f"   MCP_EXTERNAL_DOMAIN={external_domain}", file=sys.stderr)
    
    mcp.run(transport="streamable-http")
