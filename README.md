# Jules MCP Server

Production-grade Model Context Protocol (MCP) server for the Google Jules API, built with [FastMCP](https://github.com/jlowin/fastmcp).

## Features
- **Native Single-Call Execution**: Approves plans, lists sessions, sends messages, and deletes completed sessions directly via MCP.
- **Automatic Session Pagination**: Automatically fetches all active sessions natively without manual token loops.
- **Extended Session Cleanup**: Includes tools to scan and remove completed, terminated, failed, cancelled, expired, or inactive sessions (`clean_completed_sessions`).
- **Pydantic Type Sanitization**: Ensures string parameters (`page_token`, `title`, `starting_branch`) default to clean primitive types avoiding `None` validation schemas in MCP clients.
- **FastMCP SSE Transport**: Provides a native Server-Sent Events endpoint (`http://<host>:8000/sse`).

## MCP Tools Reference

| Tool Name | Description |
| --- | --- |
| `list_sessions(page_size, page_token, fetch_all)` | List sessions with optional automatic pagination (`fetch_all=true`) and sanitized string defaults. |
| `get_session(session_id)` | Retrieve details for a specific session. |
| `create_session(source, prompt, title, starting_branch, require_plan_approval)` | Create a new session with non-null string defaults for optional parameters. |
| `list_activities(session_id)` | Retrieve activity logs and plans (`plan_generated`). |
| `approve_session_plan(session_id)` | Approve a pending session plan in a single call. |
| `send_session_message(session_id, message)` | Send feedback or directives to an active session. |
| `delete_session(session_id)` | Delete or archive a completed session. |
| `clean_completed_sessions()` | Automatically scan and delete all sessions in terminal states (`COMPLETED`, `TERMINATED`, `FAILED`, `CANCELLED`, `EXPIRED`, etc.). |

## Quickstart & Docker Deployment

```yaml
services:
  jules-mcp:
    image: ghcr.io/cavuminfundo/jules-mcp-server:latest
    container_name: jules-mcp-server
    environment:
      - JULES_API_KEY=your_jules_api_key
    ports:
      - "8000:8000"
    restart: unless-stopped
```

## Client Configuration Example

Add the server to your MCP client configuration (`mcp_config.json`):

```json
{
  "mcpServers": {
    "jules-mcp": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```
