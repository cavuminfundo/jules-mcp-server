# Jules MCP Server

Production-grade, robust Model Context Protocol (MCP) server for Google Jules API, powered by FastMCP.

## Features
- **Native Single-Call Execution**: Approves plans, lists sessions, and sends messages directly via MCP.
- **Strict Parameter Coercion**: Handles `null` or omitted parameters safely without RPC validation errors.
- **FastMCP SSE Protocol**: Native Server-Sent Events endpoint (`http://<host>:8000/sse`).

## Docker Deployment

```yaml
services:
  jules-mcp:
    image: ghcr.io/cavuminfundo/jules-mcp-server:latest
    container_name: jules_mcp_server
    environment:
      - JULES_API_KEY=your_jules_api_key
    ports:
      - "8000:8000"
    restart: unless-stopped
```
