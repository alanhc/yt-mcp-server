# MCP n8n Proxy Server

A **Model Context Protocol (MCP)** server that enables MCP clients (like ChatGPT, Claude Desktop, or other LLM applications) to control and create n8n workflows through standardized tool interfaces.

## 🎯 Features

- **Multiple n8n workflow management tools**:
  - `create_n8n_workflow`: Create new workflows
  - `list_n8n_workflows`: List all workflows
  - `get_n8n_workflow`: Get workflow details by ID
  - `update_n8n_workflow`: Update existing workflows
  - `delete_n8n_workflow`: Delete workflows
- **Two server implementations**:
  - **FastMCP** (recommended): Simple, decorator-based implementation inspired by FastAPI
  - **Standard MCP**: Traditional server implementation for advanced use cases
- Full MCP protocol support via official Python SDK
- Async HTTP requests using `httpx`
- Environment-based configuration
- Comprehensive error handling

## 📋 Requirements

- **Python**: 3.10 or higher
- **n8n instance**: A running n8n instance with API access
- **n8n API Token**: Bearer token for authentication

## 🚀 Installation

### 1. Clone or download this project

```bash
cd mcp-n8n-proxy
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -e .
```

Or for development with testing tools:

```bash
pip install -e ".[dev]"
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (or set environment variables in your shell):

```bash
cp .env.example .env
```

Edit `.env` and configure:

```bash
# Required: Your n8n API token
N8N_API_TOKEN=your_actual_n8n_api_token_here

# Optional: Your n8n base URL (defaults to https://n8n.0xfanslab.com)
N8N_BASE_URL=https://n8n.0xfanslab.com
```

### How to get your n8n API Token

1. Log in to your n8n instance
2. Go to **Settings** → **API**
3. Create a new API key
4. Copy the token and paste it into your `.env` file

## 🏃 Running the Server

### Standalone Mode (for testing)

**Important**: Always run from the project root directory (`mcp-n8n-proxy/`), not from inside the `mcp_n8n_proxy/` subdirectory.

#### Option 1: FastMCP Server (Recommended - Simple & Clean)

Using uv:
```bash
cd /path/to/mcp-n8n-proxy
uv run python -m mcp_n8n_proxy.server_fastmcp
```

Using standard Python:
```bash
cd /path/to/mcp-n8n-proxy
python -m mcp_n8n_proxy.server_fastmcp
```

The FastMCP server runs on HTTP with Server-Sent Events (SSE) transport by default on `http://127.0.0.1:8000`.

#### Option 2: Standard MCP Server (stdio transport)

Using uv:
```bash
cd /path/to/mcp-n8n-proxy
uv run python -m mcp_n8n_proxy.server
```

Using standard Python:
```bash
cd /path/to/mcp-n8n-proxy
python -m mcp_n8n_proxy.server
```

The standard server communicates via **stdio** (standard input/output), which is the traditional MCP transport mechanism.

#### Option 3: HTTP/SSE Server

Using uv:
```bash
cd /path/to/mcp-n8n-proxy
uv run python -m mcp_n8n_proxy.server_http
```

This runs the standard MCP server over HTTP with SSE transport on `http://127.0.0.1:8001` by default.

**Note**: Do NOT run `python server.py` directly, as this will cause import errors. Always use the `-m` module execution format.

### Using with MCP Clients

#### Claude Desktop Configuration

Add this to your Claude Desktop MCP settings file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "n8n-proxy": {
      "command": "python",
      "args": [
        "-m",
        "mcp_n8n_proxy.server"
      ],
      "env": {
        "N8N_BASE_URL": "https://n8n.0xfanslab.com",
        "N8N_API_TOKEN": "your_n8n_api_token_here"
      }
    }
  }
}
```

**Note**: Make sure to use the **absolute path** to your Python executable if you're using a virtual environment:

```json
{
  "mcpServers": {
    "n8n-proxy": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["-m", "mcp_n8n_proxy.server"],
      "env": {
        "N8N_BASE_URL": "https://n8n.0xfanslab.com",
        "N8N_API_TOKEN": "your_token"
      }
    }
  }
}
```

#### Other MCP Clients

For other MCP-compatible clients, configure them to run:

```bash
python -m mcp_n8n_proxy.server
```

With the appropriate environment variables set.

## 🛠️ Available Tools

### `create_n8n_workflow`

Creates a new workflow in your n8n instance.

**Input Schema**:
```json
{
  "workflow": {
    "name": "My Workflow",
    "nodes": [...],
    "connections": {...},
    "settings": {...}
  }
}
```

**Example Usage** (in an MCP client like Claude):

```
Please create an n8n workflow with the following definition:
{
  "name": "Test Workflow",
  "nodes": [
    {
      "parameters": {},
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "typeVersion": 1,
      "position": [240, 300]
    }
  ],
  "connections": {},
  "active": false,
  "settings": {}
}
```

**Response Format**:

Success:
```json
{
  "success": true,
  "status": 201,
  "data": {
    "id": "123",
    "name": "Test Workflow",
    ...
  }
}
```

Error:
```json
{
  "error": true,
  "status": 401,
  "message": "n8n API returned error status 401",
  "body": {"message": "Unauthorized"}
}
```

## 🧪 Testing

You can test the tool manually using the MCP Inspector or by integrating with an MCP client.

### Manual Testing with Python

```python
import asyncio
from mcp_n8n_proxy.tools import create_n8n_workflow

async def test():
    workflow = {
        "name": "Test Workflow",
        "nodes": [
            {
                "parameters": {},
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [240, 300]
            }
        ],
        "connections": {},
        "active": False,
        "settings": {}
    }
    
    result = await create_n8n_workflow(workflow)
    print(result)

asyncio.run(test())
```

## 📚 Project Structure

```
mcp-n8n-proxy/
├── mcp_n8n_proxy/
│   ├── __init__.py           # Package initialization
│   ├── server.py             # MCP server entry point
│   └── tools/
│       ├── __init__.py       # Tools package
│       └── create_n8n_workflow.py  # n8n workflow creation tool
├── pyproject.toml            # Project dependencies and metadata
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🔧 Development

### Adding New Tools

1. Create a new file in `mcp_n8n_proxy/tools/`
2. Implement your tool function
3. Register it in `server.py`:
   - Add to `list_tools()` return value
   - Add handler in `call_tool()`

### Running Tests

```bash
pytest
```

## 📝 License

MIT License - feel free to use this in your own projects!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📞 Support

For issues related to:
- **This MCP server**: Open an issue in this repository
- **MCP protocol**: Check the [MCP documentation](https://modelcontextprotocol.io)
- **n8n API**: Check the [n8n API documentation](https://docs.n8n.io/api/)
