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
    container_name: jules-mcp-server
    environment:
      - JULES_API_KEY=your_jules_api_key
    ports:
      - "8000:8000"
    restart: unless-stopped
```

## 🛠️ Guida alla Configurazione per gli Agenti & MCP Client

Per evitare disallineamenti di parametri o navigazione "al buio", utilizzare le seguenti direttive standard:

### 1. Repository Ufficiale GitHub
- **Owner**: `cavuminfundo`
- **Repo**: `jules-mcp-server`
- **Workspace Locale**: `/home/federico/jules`

### 2. Strumenti MCP Disponibili (`jules-mcp`)
- **`list_sessions`**: Recupera le sessioni di Jules. Di default raccoglie **nativamente il 100% delle sessioni** in auto-paginazione (`fetch_all: true`).
- **`get_session(session_id)`**: Dettagli di una singola sessione.
- **`list_activities(session_id)`**: Attività e piani generati (`plan_generated`).
- **`approve_session_plan(session_id)`**: Approvazione del piano di lavoro.
- **`send_session_message(session_id, message)`**: Invio di direttive o messaggi di mentoring.
- **`delete_session(session_id)`**: Eliminazione/archiviazione di una sessione terminata.
- **`clean_completed_sessions()`**: Scansione ed eliminazione automatica di tutte le sessioni in stato `COMPLETED`, `SUCCEEDED` o `TERMINATED`.

### 3. Regole per gli Agenti Supervisori
1. **No Script Esterni**: Interagire unicamente tramite le chiamate MCP dirette (`jules-mcp` e `github-mcp-server`).
2. **Single Worker**: Il Sub-Agente invocato per la supervisione agisce da esecutore diretto e non deve creare sub-agenti a cascata.
3. **Paginazione Nativa**: Le risposte a `list_sessions` integrano già la totalità delle sessioni senza richiedere il ciclo manuale di `pageToken`.
