import os
import httpx
import urllib.parse
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP

mcp = FastMCP("Jules MCP Server", version="0.2.0")

JULES_API_BASE = os.getenv("JULES_API_BASE", "https://jules.googleapis.com/v1alpha")
JULES_API_KEY = os.getenv("JULES_API_KEY", "")

def get_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if JULES_API_KEY:
        headers["X-Goog-Api-Key"] = JULES_API_KEY
    return headers

_http_client: Optional[httpx.AsyncClient] = None

def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient()
    return _http_client

async def _make_api_request(method: str, url: str, success_override: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Helper function to make API requests with standard error handling."""
    kwargs.setdefault("timeout", 120.0)
    kwargs.setdefault("headers", get_headers())

    client = _get_client()
    res = await client.request(method, url, **kwargs)
    if res.status_code not in (200, 204):
        return {"error": f"API error {res.status_code}: {res.text}"}
    if success_override is not None:
        return success_override
    return res.json()


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
async def list_sessions(page_size: int = 50, page_token: str = "", fetch_all: bool = True) -> Dict[str, Any]:
    """List sessions with optional automatic pagination to retrieve all sessions natively."""
    token_arg = page_token if page_token else None
    if not fetch_all:
        params = _get_pagination_params(page_size, token_arg)
        return await _make_api_request("GET", f"{JULES_API_BASE}/sessions", params=params)

    all_sessions = []
    current_token = token_arg

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
async def create_session(
    source: str,
    prompt: str,
    title: str = "",
    starting_branch: str = "",
    require_plan_approval: bool = False
) -> Dict[str, Any]:
    """Create a new Jules session for a given source and prompt."""
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "sourceContext": {
            "source": source
        },
        "requirePlanApproval": require_plan_approval
    }
    if title:
        payload["title"] = title
    if starting_branch:
        payload["sourceContext"]["startingBranch"] = starting_branch

    return await _make_api_request("POST", f"{JULES_API_BASE}/sessions", json=payload)

@mcp.tool()
async def delete_session(session_id: str) -> Dict[str, Any]:
    """Delete a completed or terminated session by ID."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}"

    return await _make_api_request("DELETE", url, success_override={"status": "deleted", "session_id": clean_id})

@mcp.tool()
async def clean_completed_sessions() -> Dict[str, Any]:
    """Scans all sessions and deletes completed, terminated, failed, or inactive sessions automatically."""
    sessions_res = await list_sessions(fetch_all=True)
    if "error" in sessions_res:
        return sessions_res

    sessions = sessions_res.get("sessions", [])
    deleted_ids = []
    errors = []

    terminal_states = (
        "COMPLETED", "SUCCEEDED", "TERMINATED", "CANCELLED",
        "CLOSED", "FAILED", "EXPIRED", "REJECTED", "FINISHED", "ABORTED"
    )

    for s in sessions:
        sid = s.get("id") or s.get("name")
        state = s.get("state", "").upper()
        if state in terminal_states:
            del_res = await delete_session(sid)
            if "error" in del_res:
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
async def list_activities(session_id: str, page_size: Optional[int] = 20, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List activities for a specific session."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    params = _get_pagination_params(page_size, page_token)

    url = f"{JULES_API_BASE}/sessions/{clean_id}/activities"

    return await _make_api_request("GET", url, params=params)

@mcp.tool()
async def get_activity(session_id: str, activity_id: str) -> Dict[str, Any]:
    """Get details for a single activity by ID."""
    if not session_id or not activity_id:
        return {"error": "session_id and activity_id are required"}
    
    clean_sid = _clean_session_id(session_id)
    clean_aid = _clean_session_id(activity_id)
    url = f"{JULES_API_BASE}/sessions/{clean_sid}/activities/{clean_aid}"

    return await _make_api_request("GET", url)

@mcp.tool()
async def list_all_activities(session_id: str) -> Dict[str, Any]:
    """List all activities for a session with automatic pagination."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_sid = _clean_session_id(session_id)
    all_activities = []
    current_token = None

    while True:
        params = _get_pagination_params(50, current_token)
        res = await _make_api_request("GET", f"{JULES_API_BASE}/sessions/{clean_sid}/activities", params=params)

        if "error" in res:
            return res if not all_activities else {"activities": all_activities, "error": res["error"]}

        activities = res.get("activities", [])
        all_activities.extend(activities)

        current_token = res.get("nextPageToken")
        if not current_token:
            break

    return {"activities": all_activities, "total": len(all_activities)}

@mcp.tool()
async def approve_session_plan(session_id: str) -> Dict[str, Any]:
    """Approve the generated plan for a session in a single native MCP call."""
    if not session_id:
        return {"error": "session_id is required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}:approvePlan"

    return await _make_api_request("POST", url, success_override={"status": "approved", "session_id": clean_id}, json={})

@mcp.tool()
async def send_session_message(session_id: str, prompt: str = "", message: str = "") -> Dict[str, Any]:
    """Send a user message (prompt) to an existing session."""
    msg = prompt or message
    if not session_id or not msg:
        return {"error": "session_id and prompt/message are required"}

    clean_id = _clean_session_id(session_id)
    url = f"{JULES_API_BASE}/sessions/{clean_id}:sendMessage"
    payload = {"prompt": msg}

    return await _make_api_request("POST", url, success_override={"status": "sent", "session_id": clean_id}, json=payload)

@mcp.tool()
async def list_sources(page_size: Optional[int] = 50, page_token: Optional[str] = None, filter_str: Optional[str] = None) -> Dict[str, Any]:
    """List sources with optional filter and pagination."""
    params = _get_pagination_params(page_size, page_token)
    if filter_str:
        params["filter"] = filter_str

    return await _make_api_request("GET", f"{JULES_API_BASE}/sources", params=params)

@mcp.tool()
async def get_source(source_id: str) -> Dict[str, Any]:
    """Get details for a single source by ID."""
    if not source_id:
        return {"error": "source_id is required"}

    clean_id = _clean_session_id(source_id)
    return await _make_api_request("GET", f"{JULES_API_BASE}/sources/{clean_id}")

@mcp.tool()
async def get_all_sources(filter_str: Optional[str] = None) -> Dict[str, Any]:
    """Get all sources with optional filtering (auto-pagination)."""
    all_sources = []
    current_token = None

    while True:
        params = _get_pagination_params(50, current_token)
        if filter_str:
            params["filter"] = filter_str

        res = await _make_api_request("GET", f"{JULES_API_BASE}/sources", params=params)

        if "error" in res:
            return res if not all_sources else {"sources": all_sources, "error": res["error"]}

        sources = res.get("sources", [])
        all_sources.extend(sources)

        current_token = res.get("nextPageToken")
        if not current_token:
            break

    return {"sources": all_sources, "total": len(all_sources)}

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000, host="0.0.0.0")
