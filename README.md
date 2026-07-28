# Jules MCP Server

Production-grade Model Context Protocol (MCP) server for the Google Jules API, built with [FastMCP](https://github.com/jlowin/fastmcp).

## Features
- **Native Single-Call Execution**: Approves plans, lists sessions, sends messages, and deletes completed sessions directly via MCP.
- **Sub-Second Fast Response**: Single-page fast listing (`fetch_all=False` by default) returning JSON results in <200ms.
- **Hardened Timeout & Connection Resilience**: Isolated HTTP client requests with strict timeouts (`httpx.Timeout(8.0)`) catching `asyncio.CancelledError` and `TimeoutError` to prevent interface hanging.
- **Automatic Concurrent Session Cleanup**: Deletes terminal sessions (`COMPLETED`, `TERMINATED`, `FAILED`, `CANCELLED`, `EXPIRED`, etc.) in parallel via `asyncio.gather` (`clean_completed_sessions`).
- **Flexible Transport**: Supports both native HTTP (`/mcp`), SSE (`/sse`), and stdio bridges.

---

## MCP Tools Reference

| Tool Name | Description | Parameters |
| --- | --- | --- |
| `list_sessions` | List sessions with optional automatic pagination (`fetch_all=False` for sub-second fast listing). | `page_size: 50`, `page_token: ""`, `fetch_all: false` |
| `get_session` | Retrieve details for a specific session by ID or resource name. | `session_id: string` |
| `create_session` | Create a new session for a target source repository. | `source: string`, `prompt: string`, `title: ""`, `starting_branch: "main"`, `require_plan_approval: false` |
| `list_activities` | Retrieve activity logs and generated plans for a session. | `session_id: string`, `page_size: 20`, `page_token: ""` |
| `list_all_activities` | Automatically fetch all activity logs for a session. | `session_id: string` |
| `get_activity` | Get details for a specific activity ID. | `session_id: string`, `activity_id: string` |
| `approve_session_plan` | Approve a generated session plan in a single call. | `session_id: string` |
| `send_session_message` | Send guidance or answers to an active session waiting for feedback. | `session_id: string`, `prompt: string` / `message: string` |
| `delete_session` | Delete a completed or terminated session by ID. | `session_id: string` |
| `clean_completed_sessions` | Automatically scan and delete all terminal/inactive sessions concurrently. | *None* |
| `list_sources` | List accessible source repositories. | `page_size: 50`, `page_token: ""`, `filter_str: ""` |
| `get_all_sources` | Retrieve all accessible source repositories with auto-pagination. | `filter_str: ""` |

---

## 🚀 Deployment & Container Setup

### 1. Docker Compose (Production)

Deploy using the pre-compiled image from GitHub Container Registry (GHCR):

```yaml
services:
  jules-mcp:
    image: ghcr.io/cavuminfundo/jules-mcp-server:latest
    container_name: jules_mcp_server
    dns:
      - 8.8.8.8
      - 8.8.4.4
    environment:
      - JULES_API_KEY=your_google_jules_api_key_here
    ports:
      - "8000:8000"
    restart: unless-stopped
```

Start the container:
```bash
docker compose up -d
```

---

## 🔌 MCP Client Configuration Guide (`mcp_config.json`)

You can connect your AI Agent or MCP Client (Antigravity, Claude Desktop, Cursor, etc.) using any of the following transport methods:

### Option A: Native HTTP Transport (Recommended & Super Fast)

Direct HTTP JSON-RPC endpoint without session state overhead:

```json
{
  "mcpServers": {
    "jules-mcp": {
      "type": "http",
      "url": "http://<SERVER_IP_OR_HOST>:8000/mcp"
    }
  }
}
```

### Option B: Native SSE Transport

Server-Sent Events connection:

```json
{
  "mcpServers": {
    "jules-mcp": {
      "type": "sse",
      "url": "http://<SERVER_IP_OR_HOST>:8000/sse"
    }
  }
}
```

### Option C: Stdio Bridge via `mcp-remote` (npx)

If your client only supports stdio process execution:

```json
{
  "mcpServers": {
    "jules-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://<SERVER_IP_OR_HOST>:8000/sse",
        "--allow-http"
      ]
    }
  }
}
```

---

## 🛠️ Local Development & Testing

```bash
# Clone the repository
git clone https://github.com/cavuminfundo/jules-mcp-server.git
cd jules-mcp-server

# Set environment variable
export JULES_API_KEY="your_google_jules_api_key"

# Install dependencies and run with uv
uv sync
uv run python -m jules_mcp.jules_mcp
```
