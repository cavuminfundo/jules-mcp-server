import os
import httpx
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP, Context

mcp = FastMCP("Jules MCP Server", version="0.2.0")

JULES_API_BASE = os.getenv("JULES_API_BASE", "https://jules.googleapis.com/v1alpha")
JULES_API_KEY = os.getenv("JULES_API_KEY", "")

def get_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if JULES_API_KEY:
        headers["X-Goog-Api-Key"] = JULES_API_KEY
    return headers

async def _make_api_request(method: str, url: str, success_override: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Helper function to make API requests with standard error handling."""
    kwargs.setdefault("timeout", 15.0)
    kwargs.setdefault("headers", get_headers())

    async with httpx.AsyncClient() as client:
        res = await client.request(method, url, **kwargs)
        if res.status_code not in (200, 204):
            return {"error": f"API error {res.status_code}: {res.text}"}
        if success_override is not None:
            return success_override
        return res.json()

def _clean_session_id(session_id: str) -> str:
    return session_id.split('/')[-1] if '/' in session_id else session_id

def _get_pagination_params(page_size: Optional[int], page_token: Optional[str]) -> Dict[str, Any]:
    params = {}
    if page_size is not None and isinstance(page_size, int):
        params["pageSize"] = page_size
    if page_token and isinstance(page_token, str):
        params["pageToken"] = page_token
    return params

@mcp.tool()
async def list_sessions(page_size: Optional[int] = 50, page_token: Optional[str] = None, fetch_all: bool = True) -> Dict[str, Any]:
    """List sessions with optional automatic pagination to retrieve all sessions natively."""
    if not fetch_all:
        params = _get_pagination_params(page_size, page_token)
        return await _make_api_request("GET", f"{JULES_API_BASE}/sessions", params=params)

    all_sessions = []
    current_token = page_token

    while True:
        params = _get_pagination_params(page_size, current_token)
        res = await _make_api_request("GET", f"{JULES_API_BASE}/sessions", params=params)

        if "error" in res:
            return res if not all_sessions else {"sessions": all_sessions, "error": res["error"]}

        sessions = res.get("sessions", [])
        all_sessions.extend(sessions)

        current_token = res.get("nextPageToken")
        if not current_token:
            break

    return {"sessions": all_sessions, "total": len(all_sessions)}

@mcp.tool()
async def get_session(session_id: str) -> Dict[str, Any]:
    """Get details for a single session by ID or resource name."""
    if not session_id:
        return {"error": "session_id is required"}
    
    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}"

    return await _make_api_request("GET", url)

@mcp.tool()
async def list_activities(session_id: str, page_size: Optional[int] = 20, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List activities for a specific session."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    params = _get_pagination_params(page_size, page_token)

    url = f"{JULES_API_BASE}/sessions/{clean_id}/activities"

    return await _make_api_request("GET", url, params=params)

@mcp.tool()
async def approve_session_plan(session_id: str) -> Dict[str, Any]:
    """Approve the generated plan for a session in a single native MCP call."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}:approvePlan"

    return await _make_api_request("POST", url, success_override={"status": "approved", "session_id": clean_id}, json={})

@mcp.tool()
async def send_session_message(session_id: str, message: str) -> Dict[str, Any]:
    """Send a feedback message or mentoring directive to a Jules session."""
    if not session_id or not message:
        return {"error": "session_id and message are required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}:sendMessage"
    payload = {"prompt": message}

    return await _make_api_request("POST", url, success_override={"status": "sent", "session_id": clean_id}, json=payload)

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000, host="0.0.0.0")
