import os
import httpx
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

mcp = FastMCP("Jules MCP Server", version="0.2.0")

JULES_API_BASE = os.getenv("JULES_API_BASE", "https://jules.googleapis.com/v1alpha")
JULES_API_KEY = os.getenv("JULES_API_KEY", "")

def get_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if JULES_API_KEY:
        headers["X-Goog-Api-Key"] = JULES_API_KEY
    return headers

def _clean_session_id(session_id: str) -> str:
    return session_id.split('/')[-1] if '/' in session_id else session_id

@mcp.tool()
async def list_sessions(page_size: Optional[int] = 10, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List sessions with safe pagination and parameter coercion."""
    params = {}
    if page_size is not None and isinstance(page_size, int):
        params["pageSize"] = page_size
    if page_token and isinstance(page_token, str):
        params["pageToken"] = page_token

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{JULES_API_BASE}/sessions", headers=get_headers(), params=params, timeout=15.0)
        if res.status_code != 200:
            return {"error": f"API error {res.status_code}: {res.text}"}
        return res.json()

@mcp.tool()
async def get_session(session_id: str) -> Dict[str, Any]:
    """Get details for a single session by ID or resource name."""
    if not session_id:
        return {"error": "session_id is required"}
    
    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=get_headers(), timeout=15.0)
        if res.status_code != 200:
            return {"error": f"API error {res.status_code}: {res.text}"}
        return res.json()

@mcp.tool()
async def list_activities(session_id: str, page_size: Optional[int] = 20, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List activities for a specific session."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    params = {}
    if page_size is not None and isinstance(page_size, int):
        params["pageSize"] = page_size
    if page_token and isinstance(page_token, str):
        params["pageToken"] = page_token

    url = f"{JULES_API_BASE}/sessions/{clean_id}/activities"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=get_headers(), params=params, timeout=15.0)
        if res.status_code != 200:
            return {"error": f"API error {res.status_code}: {res.text}"}
        return res.json()

@mcp.tool()
async def approve_session_plan(session_id: str) -> Dict[str, Any]:
    """Approve the generated plan for a session in a single native MCP call."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}:approvePlan"

    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=get_headers(), json={}, timeout=15.0)
        if res.status_code not in (200, 204):
            return {"error": f"API error {res.status_code}: {res.text}"}
        return {"status": "approved", "session_id": clean_id}

@mcp.tool()
async def send_session_message(session_id: str, message: str) -> Dict[str, Any]:
    """Send a feedback message or mentoring directive to a Jules session."""
    if not session_id or not message:
        return {"error": "session_id and message are required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}:sendMessage"
    payload = {"prompt": message}

    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=get_headers(), json=payload, timeout=15.0)
        if res.status_code not in (200, 204):
            return {"error": f"API error {res.status_code}: {res.text}"}
        return {"status": "sent", "session_id": clean_id}

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000, host="0.0.0.0")
