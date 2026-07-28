import os
import asyncio
import httpx
import urllib.parse
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP

import uuid
from starlette.middleware.base import BaseHTTPMiddleware

TOOLS_LIST_METADATA = [
    {"name": "list_sessions", "description": "List Jules sessions with optional pagination.", "inputSchema": {"type": "object", "properties": {"page_size": {"type": "integer"}, "page_token": {"type": "string"}, "fetch_all": {"type": "boolean"}}}},
    {"name": "get_session", "description": "Retrieve full details and current state for a specific session ID or name.", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]}},
    {"name": "create_session", "description": "Launch a new Jules AI session for a target repository.", "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "prompt": {"type": "string"}, "title": {"type": "string"}, "starting_branch": {"type": "string"}, "require_plan_approval": {"type": "boolean"}}, "required": ["source", "prompt"]}},
    {"name": "list_activities", "description": "Fetch activity history and generated plans for a session.", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}, "page_size": {"type": "integer"}, "page_token": {"type": "string"}}, "required": ["session_id"]}},
    {"name": "list_all_activities", "description": "Fetch all activity history for a session using automatic pagination.", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]}},
    {"name": "get_activity", "description": "Retrieve details for a specific activity ID within a session.", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}, "activity_id": {"type": "string"}}, "required": ["session_id", "activity_id"]}},
    {"name": "approve_session_plan", "description": "Approve a pending session plan in a single native call.", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]}},
    {"name": "send_session_message", "description": "Send mentoring feedback, answers, or directives to an active session.", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}, "prompt": {"type": "string"}, "message": {"type": "string"}}, "required": ["session_id"]}},
    {"name": "delete_session", "description": "Permanently delete a completed or inactive session.", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]}},
    {"name": "clean_completed_sessions", "description": "Concurrently scan and delete all terminal/inactive sessions.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "list_sources", "description": "List accessible source GitHub repositories connected to Jules.", "inputSchema": {"type": "object", "properties": {"page_size": {"type": "integer"}, "page_token": {"type": "string"}, "filter_str": {"type": "string"}}}},
    {"name": "get_all_sources", "description": "Retrieve all accessible source repositories with auto-pagination.", "inputSchema": {"type": "object", "properties": {"filter_str": {"type": "string"}}}}
]

class CatchAllMessagesFallbackMiddleware(BaseHTTPMiddleware):
    """Middleware to catch POST requests on /messages or /messages/ (even with expired/cached SSE session IDs) and execute JSON-RPC tool calls directly without 404 error."""
    async def dispatch(self, request, call_next):
        if request.method == "POST" and (request.url.path.startswith("/messages") or request.url.path.startswith("/sse")):
            from starlette.responses import JSONResponse
            try:
                body = await request.body()
                if body:
                    import json
                    data = json.loads(body)
                    method = data.get("method")
                    req_id = data.get("id", 1)
                    if method == "tools/call":
                        params = data.get("params", {})
                        tool_name = params.get("name")
                        args = params.get("arguments", {})
                        tool_fn = globals().get(tool_name)
                        if tool_fn and callable(tool_fn):
                            res = await tool_fn(**args)
                            text_res = json.dumps(res) if not isinstance(res, str) else res
                            return JSONResponse({"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": text_res}]}, "id": req_id})
                    elif method == "tools/list":
                        return JSONResponse({"jsonrpc": "2.0", "result": {"tools": TOOLS_LIST_METADATA}, "id": req_id})
                    elif method == "initialize":
                        return JSONResponse({"jsonrpc": "2.0", "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "Jules MCP Server", "version": "0.2.0"}}, "id": req_id})
            except Exception:
                pass
        response = await call_next(request)
        if response.status_code == 404 and request.method == "POST" and "session_id" in request.url.query:
            from starlette.responses import JSONResponse
            try:
                body = await request.body()
                if body:
                    import json
                    data = json.loads(body)
                    method = data.get("method")
                    req_id = data.get("id", 1)
                    if method == "tools/call":
                        params = data.get("params", {})
                        tool_name = params.get("name")
                        args = params.get("arguments", {})
                        tool_fn = globals().get(tool_name)
                        if tool_fn and callable(tool_fn):
                            res = await tool_fn(**args)
                            text_res = json.dumps(res) if not isinstance(res, str) else res
                            return JSONResponse({"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": text_res}]}, "id": req_id})
                    elif method == "tools/list":
                        return JSONResponse({"jsonrpc": "2.0", "result": {"tools": TOOLS_LIST_METADATA}, "id": req_id})
                    elif method == "initialize":
                        return JSONResponse({"jsonrpc": "2.0", "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "Jules MCP Server", "version": "0.2.0"}}, "id": req_id})
            except Exception:
                pass
        return response

mcp = FastMCP("Jules MCP Server", version="0.2.0")

@mcp.custom_route("/rpc", methods=["POST"])
async def direct_rpc_handler(request):
    from starlette.responses import JSONResponse
    try:
        data = await request.json()
        method = data.get("method")
        req_id = data.get("id", 1)
        
        if method == "initialize":
            return JSONResponse({"jsonrpc": "2.0", "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "Jules MCP Server", "version": "0.2.0"}}, "id": req_id})
        elif method == "tools/list":
            return JSONResponse({"jsonrpc": "2.0", "result": {"tools": TOOLS_LIST_METADATA}, "id": req_id})
            
        elif method == "tools/call":
            params = data.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})
            
            tool_fn = globals().get(tool_name)
            if tool_fn and callable(tool_fn):
                res = await tool_fn(**args)
                import json
                text_res = json.dumps(res) if not isinstance(res, str) else res
                return JSONResponse({"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": text_res}]}, "id": req_id})
            return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"}, "id": req_id}, status_code=404)
            
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method '{method}' not supported"}, "id": req_id}, status_code=400)
    except Exception as e:
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": 1}, status_code=500)

JULES_API_BASE = os.getenv("JULES_API_BASE", "https://jules.googleapis.com/v1alpha")
JULES_API_KEY = os.getenv("JULES_API_KEY", "")

def get_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("JULES_API_KEY", JULES_API_KEY)
    if api_key:
        headers["X-Goog-Api-Key"] = api_key
    return headers

async def _make_api_request(method: str, url: str, success_override: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Helper function to make API requests with rigid hard timeouts."""
    headers = get_headers()
    if "headers" in kwargs:
        headers.update(kwargs.pop("headers"))
    
    timeout = httpx.Timeout(8.0, connect=3.0)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await asyncio.wait_for(client.request(method, url, headers=headers, **kwargs), timeout=10.0)
            if res.status_code not in (200, 204):
                return {"error": f"API error {res.status_code}: {res.text[:200]}"}
            if success_override is not None:
                return success_override
            try:
                data = res.json()
                if isinstance(data, dict):
                    return data
                return {"data": data}
            except Exception as json_err:
                return {"error": f"Invalid JSON response: {str(json_err)}"}
    except (Exception, asyncio.CancelledError, asyncio.TimeoutError) as e:
        return {"error": f"Timeout / Connection error: {str(e)}", "sessions": []}


def _clean_session_id(session_id: str) -> str:
    clean_id = session_id.split('/')[-1] if '/' in session_id else session_id
    return urllib.parse.quote(clean_id, safe='')

def _get_pagination_params(page_size: Optional[int], page_token: Optional[str]) -> Dict[str, Any]:
    params = {}
    if page_size is not None and isinstance(page_size, int):
        params["pageSize"] = page_size
    if page_token and isinstance(page_token, str):
        params["pageToken"] = page_token
    return params

@mcp.tool()
async def list_sessions(page_size: int = 50, page_token: str = "", fetch_all: bool = False, _meta: Any = None) -> Dict[str, Any]:
    """List sessions with optional automatic pagination to retrieve sessions natively."""
    token = page_token if page_token else None
    if not fetch_all:
        params = _get_pagination_params(page_size, token)
        return await _make_api_request("GET", f"{JULES_API_BASE}/sessions", params=params)

    all_sessions = []
    current_token = token
    seen_tokens = set()
    max_pages = 5
    page_count = 0

    while page_count < max_pages:
        page_count += 1
        if current_token:
            if current_token in seen_tokens:
                break
            seen_tokens.add(current_token)

        params = _get_pagination_params(page_size, current_token)
        res = await _make_api_request("GET", f"{JULES_API_BASE}/sessions", params=params)

        if not isinstance(res, dict) or "error" in res:
            break

        sessions = res.get("sessions")
        if not isinstance(sessions, list) or not sessions:
            break

        all_sessions.extend(sessions)

        next_token = res.get("nextPageToken")
        if not next_token or next_token == current_token:
            break
        current_token = next_token

    return {"sessions": all_sessions, "total": len(all_sessions)}

@mcp.tool()
async def get_session(session_id: str, _meta: Any = None) -> Dict[str, Any]:
    """Get details for a single session by ID or resource name."""
    if not session_id:
        return {"error": "session_id is required"}
    
    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}"

    return await _make_api_request("GET", url)

@mcp.tool()
async def create_session(source: str,
    prompt: str,
    title: str = "",
    starting_branch: str = "",
    require_plan_approval: bool = False, _meta: Any = None) -> Dict[str, Any]:
    """Create a new Jules session for a given source and prompt."""
    branch = starting_branch if starting_branch else "main"
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "sourceContext": {
            "source": source,
            "startingBranch": branch
        },
        "requirePlanApproval": require_plan_approval
    }
    if title:
        payload["title"] = title

    return await _make_api_request("POST", f"{JULES_API_BASE}/sessions", json=payload)

@mcp.tool()
async def delete_session(session_id: str, _meta: Any = None) -> Dict[str, Any]:
    """Delete a completed or terminated session by ID."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}"

    return await _make_api_request("DELETE", url, success_override={"status": "deleted", "session_id": clean_id})

@mcp.tool()
async def clean_completed_sessions(_meta: Any = None) -> Dict[str, Any]:
    """Scans all sessions and deletes completed, terminated, failed, or inactive sessions automatically."""
    sessions_res = await list_sessions(fetch_all=False)
    if "error" in sessions_res:
        return sessions_res

    sessions = sessions_res.get("sessions", [])
    deleted_ids = []
    errors = []

    terminal_states = (
        "COMPLETED", "SUCCEEDED", "TERMINATED", "CANCELLED",
        "CLOSED", "FAILED", "EXPIRED", "REJECTED", "FINISHED", "ABORTED"
    )

    to_delete = []
    for s in sessions:
        sid = s.get("id") or s.get("name")
        state = s.get("state", "").upper()
        if sid and state in terminal_states:
            to_delete.append(sid)

    if not to_delete:
        return {"status": "success", "deleted_count": 0, "deleted_sessions": [], "errors": []}

    async def _delete_one(sid: str):
        try:
            return sid, await asyncio.wait_for(delete_session(sid), timeout=3.0)
        except (Exception, asyncio.CancelledError, asyncio.TimeoutError) as e:
            return sid, {"error": str(e)}

    results = await asyncio.gather(*[_delete_one(sid) for sid in to_delete], return_exceptions=True)

    for res in results:
        if isinstance(res, tuple) and len(res) == 2:
            sid, del_res = res
            if isinstance(del_res, dict) and "error" in del_res:
                errors.append({"session_id": sid, "error": del_res["error"]})
            else:
                deleted_ids.append(sid)

    return {
        "status": "success",
        "deleted_count": len(deleted_ids),
        "deleted_sessions": deleted_ids,
        "errors": errors
    }


@mcp.tool()
async def list_activities(session_id: str, page_size: int = 20, page_token: str = "", _meta: Any = None) -> Dict[str, Any]:
    """List activities for a specific session."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    params = _get_pagination_params(page_size, page_token)

    url = f"{JULES_API_BASE}/sessions/{clean_id}/activities"

    return await _make_api_request("GET", url, params=params)

@mcp.tool()
async def get_activity(session_id: str, activity_id: str, _meta: Any = None) -> Dict[str, Any]:
    """Get details for a single activity by ID."""
    if not session_id or not activity_id:
        return {"error": "session_id and activity_id are required"}
    
    clean_sid = _clean_session_id(session_id)
    clean_aid = _clean_session_id(activity_id)
    url = f"{JULES_API_BASE}/sessions/{clean_sid}/activities/{clean_aid}"

    return await _make_api_request("GET", url)

@mcp.tool()
async def list_all_activities(session_id: str, _meta: Any = None) -> Dict[str, Any]:
    """List all activities for a session with automatic pagination."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_sid = _clean_session_id(session_id)
    all_activities = []
    current_token = None
    seen_tokens = set()
    max_pages = 20
    page_count = 0

    while page_count < max_pages:
        page_count += 1
        if current_token:
            if current_token in seen_tokens:
                break
            seen_tokens.add(current_token)

        params = _get_pagination_params(50, current_token)
        res = await _make_api_request("GET", f"{JULES_API_BASE}/sessions/{clean_sid}/activities", params=params)

        if not isinstance(res, dict) or "error" in res:
            err_msg = res.get("error", "Unknown API response format") if isinstance(res, dict) else "Non-dict API response"
            return res if not all_activities else {"activities": all_activities, "total": len(all_activities), "error": err_msg}

        activities = res.get("activities")
        if not isinstance(activities, list) or not activities:
            break

        all_activities.extend(activities)

        next_token = res.get("nextPageToken")
        if not next_token or next_token == current_token:
            break
        current_token = next_token

    return {"activities": all_activities, "total": len(all_activities)}

@mcp.tool()
async def approve_session_plan(session_id: str, _meta: Any = None) -> Dict[str, Any]:
    """Approve the generated plan for a session in a single native MCP call."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}:approvePlan"

    return await _make_api_request("POST", url, success_override={"status": "approved", "session_id": clean_id}, json={})

@mcp.tool()
async def send_session_message(session_id: str, prompt: str = "", message: str = "", _meta: Any = None) -> Dict[str, Any]:
    """Send a user message (prompt) to an existing session."""
    msg = prompt or message
    if not session_id or not msg:
        return {"error": "session_id and prompt/message are required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}:sendMessage"
    payload = {"prompt": msg}

    return await _make_api_request("POST", url, success_override={"status": "sent", "session_id": clean_id}, json=payload)

@mcp.tool()
async def list_sources(page_size: int = 50, page_token: str = "", filter_str: str = "", _meta: Any = None) -> Dict[str, Any]:
    """List sources with optional filter and pagination."""
    params = _get_pagination_params(page_size, page_token)
    if filter_str:
        params["filter"] = filter_str

    return await _make_api_request("GET", f"{JULES_API_BASE}/sources", params=params)

@mcp.tool()
async def get_source(source_id: str, _meta: Any = None) -> Dict[str, Any]:
    """Get details for a single source by ID."""
    if not source_id:
        return {"error": "source_id is required"}

    clean_id = _clean_session_id(source_id)
    return await _make_api_request("GET", f"{JULES_API_BASE}/sources/{clean_id}")

@mcp.tool()
async def get_all_sources(filter_str: str = "", _meta: Any = None) -> Dict[str, Any]:
    """Get all sources with optional filtering (auto-pagination)."""
    all_sources = []
    current_token = None
    seen_tokens = set()
    max_pages = 20
    page_count = 0

    while page_count < max_pages:
        page_count += 1
        if current_token:
            if current_token in seen_tokens:
                break
            seen_tokens.add(current_token)

        params = _get_pagination_params(50, current_token)
        if filter_str:
            params["filter"] = filter_str

        res = await _make_api_request("GET", f"{JULES_API_BASE}/sources", params=params)

        if not isinstance(res, dict) or "error" in res:
            err_msg = res.get("error", "Unknown API response format") if isinstance(res, dict) else "Non-dict API response"
            return res if not all_sources else {"sources": all_sources, "total": len(all_sources), "error": err_msg}

        sources = res.get("sources")
        if not isinstance(sources, list) or not sources:
            break

        all_sources.extend(sources)

        next_token = res.get("nextPageToken")
        if not next_token or next_token == current_token:
            break
        current_token = next_token

    return {"sources": all_sources, "total": len(all_sources)}

if __name__ == "__main__":
    import sys, uvicorn
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp.run(transport="stdio")
    else:
        app = mcp.http_app(transport="http")
        app.add_middleware(CatchAllMessagesFallbackMiddleware)
        uvicorn.run(app, host="0.0.0.0", port=8000)
