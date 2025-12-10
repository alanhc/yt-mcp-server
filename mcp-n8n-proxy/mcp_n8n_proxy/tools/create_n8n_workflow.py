"""
n8n workflow creation tool implementation
"""

import os
import httpx
from typing import Any, Dict


async def create_n8n_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an n8n workflow by posting the workflow JSON to the n8n REST API.
    
    Args:
        workflow: Complete n8n workflow definition (will be sent to /rest/workflows)
        
    Returns:
        Dict containing either:
        - Success: The workflow data returned from n8n
        - Error: Object with 'error', 'status', 'message', and optionally 'body'
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
    # n8n uses X-N8N-API-KEY header for authentication
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
            
            # Check if request was successful (2xx status codes)
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
