# Jules MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-0.2.0-green.svg)](https://github.com/jlowin/fastmcp)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/cavuminfundo/jules-mcp-server/pkgs/container/jules-mcp-server)

Production-grade [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for [Google Jules AI](https://jules.google.com), built with [FastMCP](https://github.com/jlowin/fastmcp).

Provides an enterprise-ready bridge for AI Agents (Antigravity, Claude Desktop, Cursor, VS Code, Goose) to inspect, mentor, plan, and automate Google Jules execution sessions natively via HTTP, SSE, or Stdio transport.

---

## Key Features

- ⚡ **Sub-Second Response Times**: Single-page fast listing (`fetch_all=False` by default) returning session data in <200ms.
- 🛡️ **Hardened Network Resilience**: Per-request isolated HTTP clients (`httpx.AsyncClient`) with strict timeouts (`httpx.Timeout(8.0)`) catching `asyncio.CancelledError` and `TimeoutError` to guarantee non-blocking agent turns.
- 🧹 **Concurrent Automatic Session Cleanup**: Parallel scanning and deletion of terminal/inactive sessions (`COMPLETED`, `FINISHED`, `TERMINATED`, `CANCELLED`, `FAILED`, `EXPIRED`, `CLOSED`) using `asyncio.gather` (`clean_completed_sessions`).
- 🔒 **Type Sanitization**: Primitive string and boolean defaults (`title: ""`, `starting_branch: "main"`, `fetch_all: false`) eliminating `null` validation errors in client schema parsers.
- 🔌 **Multi-Transport Support**: Native HTTP JSON-RPC (`/mcp`), Server-Sent Events (`/sse`), and Stdio bridge support.
- 🐳 **Production Docker Image**: Pre-compiled multi-arch image hosted on GitHub Container Registry (`ghcr.io/cavuminfundo/jules-mcp-server:latest`).

---

## 🛠️ MCP Tools Reference

| Tool Name | Description | Default Parameters |
| --- | --- | --- |
| `list_sessions` | List Jules sessions with fast single-page default or optional auto-pagination. | `page_size: 50`, `page_token: ""`, `fetch_all: false` |
| `get_session` | Retrieve full details and current state for a specific session ID or name. | `session_id: string` |
| `create_session` | Launch a new Jules AI session for a target repository. | `source: string`, `prompt: string`, `title: ""`, `starting_branch: "main"`, `require_plan_approval: false` |
| `list_activities` | Fetch activity history and generated plans for a session. | `session_id: string`, `page_size: 20`, `page_token: ""` |
| `list_all_activities` | Fetch all activity history for a session using automatic pagination. | `session_id: string` |
| `get_activity` | Retrieve details for a specific activity ID within a session. | `session_id: string`, `activity_id: string` |
| `approve_session_plan` | Approve a pending session plan in a single native call. | `session_id: string` |
| `send_session_message` | Send mentoring feedback, answers, or directives to an active session. | `session_id: string`, `message: string` |
| `delete_session` | Permanently delete a completed or inactive session. | `session_id: string` |
| `clean_completed_sessions` | Concurrently scan and delete all terminal/inactive sessions. | *None* |
| `list_sources` | List accessible source GitHub repositories connected to Jules. | `page_size: 50`, `page_token: ""`, `filter_str: ""` |
| `get_all_sources` | Retrieve all accessible source repositories with auto-pagination. | `filter_str: ""` |

---

## 🚀 Quickstart & Container Deployment

### 1. Docker Compose (Recommended Production Setup)

Create a `docker-compose.yml` file:

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

Run the container:
```bash
docker compose up -d
```

### 2. Standalone Docker Run

```bash
docker run -d \
  --name jules_mcp_server \
  -e JULES_API_KEY="your_google_jules_api_key_here" \
  -p 8000:8000 \
  --restart unless-stopped \
  ghcr.io/cavuminfundo/jules-mcp-server:latest
```

---

## 🔌 Client Integration Guide (`mcp_config.json`)

Add `jules-mcp` to your AI client configuration (Antigravity, Claude Desktop, Cursor, VS Code, Goose).

### Option A: Stateless HTTP JSON-RPC Transport (Recommended - Zero Session State)

Stateless endpoint (`/rpc`) executing tool calls instantly without stateful SSE connection ID caching or reconnection timeouts:

```json
{
  "mcpServers": {
    "jules-mcp": {
      "type": "http",
      "url": "http://<SERVER_IP_OR_HOST>:8000/rpc"
    }
  }
}
```

### Option B: Native Stdio Transport Bridge (SSH / Docker)

Direct process stdio stream execution bypassing HTTP network sockets completely:

```json
{
  "mcpServers": {
    "jules-mcp": {
      "command": "ssh",
      "args": [
        "-o",
        "StrictHostKeyChecking=no",
        "user@<SERVER_IP_OR_HOST>",
        "docker",
        "exec",
        "-i",
        "jules_mcp_server",
        "python3",
        "-m",
        "jules_mcp.jules_mcp",
        "stdio"
      ]
    }
  }
}
```

### Option C: SSE Transport (Server-Sent Events)

Stateful stream connection for streaming clients:

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

### Stdio Transport Bridge (`mcp-remote`)

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
# Clone the repo
git clone https://github.com/cavuminfundo/jules-mcp-server.git
cd jules-mcp-server

# Set environment API key
export JULES_API_KEY="your_google_jules_api_key"

# Install dependencies and start server with uv
uv sync
uv run python -m jules_mcp.jules_mcp
```

---

## 📄 License

Distributed under the [MIT License](LICENSE). See `LICENSE` for more information.
