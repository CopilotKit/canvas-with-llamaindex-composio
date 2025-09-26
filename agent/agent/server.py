from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import json

# Load environment variables from .env/.env.local (repo root or agent dir) if present
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # python-dotenv may not be installed yet

def _load_env_files() -> None:
    if load_dotenv is None:
        return
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / ".env.local",  # repo root/.env.local
        here.parents[2] / ".env",        # repo root/.env
        here.parents[1] / ".env.local",  # agent/.env.local
        here.parents[1] / ".env",        # agent/.env
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(p, override=False)

_load_env_files()

from .agent import agentic_chat_router

app = FastAPI()

# Enable CORS for local Next.js dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(agentic_chat_router)


@app.get("/composio/connect/googlesheets")
def composio_connect_google_sheets():
    """Initiate Composio OAuth flow for Google Sheets and return a redirect URL.

    Requires COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID to be set in env (from Composio dashboard).
    """
    auth_config_id = os.getenv("COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID", "").strip()
    if not auth_config_id:
        raise HTTPException(status_code=400, detail="Missing COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID env var.")

    try:
        composio, user_id = _get_api_client()
        # Check if already connected for this user
        try:
            # List connected accounts for this auth config
            result = composio.connected_accounts.list(auth_config_ids=[auth_config_id])  # type: ignore[attr-defined]
            # Access items property if it exists
            if hasattr(result, "items"):
                conns = result.items if result.items is not None else []
            elif isinstance(result, list):
                conns = result
            else:
                conns = []
            # Check if any account is connected for Google Sheets for this user
            if conns and isinstance(conns, (list, tuple)):
                for conn in conns:
                    # Check if this connection belongs to our user
                    conn_user_id = None
                    if hasattr(conn, "user_id"):
                        conn_user_id = conn.user_id
                    elif hasattr(conn, "entity_id"):
                        conn_user_id = conn.entity_id
                    elif isinstance(conn, dict):
                        conn_user_id = conn.get("user_id") or conn.get("entity_id")
                    
                    # Skip if this connection is for a different user
                    if conn_user_id and conn_user_id != user_id:
                        continue
                    
                    # Check if this is a Google Sheets connection
                    if hasattr(conn, "auth_config") and hasattr(conn.auth_config, "toolkit"):
                        if conn.auth_config.toolkit.lower() == "googlesheets":
                            return {"alreadyConnected": True}
                    elif isinstance(conn, dict) and conn.get("auth_config", {}).get("toolkit", "").lower() == "googlesheets":
                        return {"alreadyConnected": True}
        except Exception:
            pass

        # Use link() method instead of initiate() as per docs
        connection_request = composio.connected_accounts.link(  # type: ignore[attr-defined]
            user_id=user_id,
            auth_config_id=auth_config_id,
            # Optional: Add callback URL if needed
            # callback_url="http://localhost:3000/callback"
        )

        # Extract redirect URL from connection request
        redirect_url = None
        # Try direct attribute access first
        if hasattr(connection_request, "redirect_url"):
            redirect_url = connection_request.redirect_url
        elif hasattr(connection_request, "redirectUrl"):
            redirect_url = connection_request.redirectUrl
        # Try dict-like access
        elif isinstance(connection_request, dict):
            redirect_url = connection_request.get("redirect_url") or connection_request.get("redirectUrl")
        # Try model dump for Pydantic models
        elif hasattr(connection_request, "model_dump"):
            dump = connection_request.model_dump()
            redirect_url = dump.get("redirect_url") or dump.get("redirectUrl")

        if not redirect_url:
            raise RuntimeError("No redirect URL returned by Composio.")
        
        # Store connection request ID if available for later status checking
        connection_id = None
        if hasattr(connection_request, "id"):
            connection_id = connection_request.id
        elif isinstance(connection_request, dict) and "id" in connection_request:
            connection_id = connection_request["id"]
            
        response = {"redirectUrl": redirect_url}
        if connection_id:
            response["connectionId"] = connection_id
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate Google Sheets connection: {e}")


@app.get("/composio/status/googlesheets")
def composio_status_google_sheets():
    try:
        composio, user_id = _get_api_client()
        auth_config_id = os.getenv("COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID", "").strip()
        
        # Get connected accounts for this auth config
        conns = []
        if auth_config_id:
            try:
                result = composio.connected_accounts.list(auth_config_ids=[auth_config_id])  # type: ignore[attr-defined]
                print(f"Debug - API result type: {type(result)}")
                print(f"Debug - API result has 'items': {hasattr(result, 'items')}")
                
                # Access items property if it exists
                if hasattr(result, "items"):
                    conns = result.items if result.items is not None else []
                    print(f"Debug - Using result.items, got {len(conns) if isinstance(conns, list) else 'non-list'} items")
                elif isinstance(result, list):
                    conns = result
                    print(f"Debug - Result is list directly, got {len(conns)} items")
                else:
                    print(f"Debug - Unexpected result structure")
                    # Try to print the result to understand its structure
                    if hasattr(result, "__dict__"):
                        print(f"Debug - Result attributes: {list(result.__dict__.keys())}")
                    conns = []
            except Exception as e:
                print(f"Debug - Error listing connections: {e}")
                conns = []
        else:
            print("Debug - No auth_config_id available")
            conns = []
        
        # Filter for Google Sheets connections and optionally by user
        google_sheets_connections = []
        print(f"Debug - Connections type: {type(conns)}, Is list/tuple: {isinstance(conns, (list, tuple))}")
        if conns and isinstance(conns, (list, tuple)):
            for conn in conns:
                # Check if this connection belongs to our user
                conn_user_id = None
                if hasattr(conn, "user_id"):
                    conn_user_id = conn.user_id
                elif hasattr(conn, "entity_id"):
                    conn_user_id = conn.entity_id
                elif isinstance(conn, dict):
                    conn_user_id = conn.get("user_id") or conn.get("entity_id")
                
                # Skip if this connection is for a different user
                if conn_user_id and conn_user_id != user_id:
                    continue
                
                # Since we're filtering by auth_config_id, these should all be Google Sheets connections
                # But let's verify just to be safe
                is_google_sheets = True  # Default to true since we filtered by auth config
                
                # Optional: verify it's actually Google Sheets
                if hasattr(conn, "auth_config"):
                    if hasattr(conn.auth_config, "toolkit"):
                        is_google_sheets = conn.auth_config.toolkit.lower() == "googlesheets"
                    elif hasattr(conn.auth_config, "app_name"):
                        is_google_sheets = "googlesheets" in conn.auth_config.app_name.lower()
                elif isinstance(conn, dict):
                    auth_config = conn.get("auth_config", {})
                    toolkit = auth_config.get("toolkit", "").lower()
                    app_name = auth_config.get("app_name", "").lower()
                    if toolkit or app_name:
                        is_google_sheets = toolkit == "googlesheets" or "googlesheets" in app_name
                
                if is_google_sheets:
                    google_sheets_connections.append(conn)
        
        connected = len(google_sheets_connections) > 0
        connection_details = []
        
        # Extract connection details for debugging
        for conn in google_sheets_connections:
            detail = {"id": None, "status": None, "user_id": None}
            if hasattr(conn, "id"):
                detail["id"] = conn.id
            elif isinstance(conn, dict) and "id" in conn:
                detail["id"] = conn["id"]
                
            if hasattr(conn, "status"):
                detail["status"] = conn.status
            elif isinstance(conn, dict) and "status" in conn:
                detail["status"] = conn["status"]
                
            # Include user/entity ID for debugging
            if hasattr(conn, "user_id"):
                detail["user_id"] = conn.user_id
            elif hasattr(conn, "entity_id"):
                detail["user_id"] = conn.entity_id
            elif isinstance(conn, dict):
                detail["user_id"] = conn.get("user_id") or conn.get("entity_id")
                
            connection_details.append(detail)
        
        # Debug: log all connections to understand the structure
        print(f"Debug - Total connections found: {len(conns) if isinstance(conns, (list, tuple)) else 0}")
        print(f"Debug - Auth config ID used: {auth_config_id}")
        if conns and isinstance(conns, (list, tuple)) and len(conns) > 0:
            sample_conn = conns[0]
            print(f"Debug - Sample connection type: {type(sample_conn)}")
            if hasattr(sample_conn, "__dict__"):
                print(f"Debug - Sample connection attributes: {list(sample_conn.__dict__.keys())}")
            elif isinstance(sample_conn, dict):
                print(f"Debug - Sample connection keys: {list(sample_conn.keys())}")
            # Print full connection details for debugging
            for idx, conn in enumerate(conns):
                print(f"Debug - Connection {idx}: {conn}")
        
        return {
            "connected": connected,
            "count": len(google_sheets_connections),
            "connections": connection_details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query connection status: {e}")


# --- Minimal persistence for spreadsheet metadata (file-based) ---
GS_META_FILE = (Path(__file__).resolve().parents[1] / ".gs_meta.json")

def _load_gs_meta() -> dict:
    try:
        if GS_META_FILE.exists():
            return json.loads(GS_META_FILE.read_text())
    except Exception:
        pass
    return {}

def _save_gs_meta(meta: dict) -> None:
    try:
        GS_META_FILE.write_text(json.dumps(meta, ensure_ascii=False))
    except Exception:
        pass


def _get_api_client():
    """Return Composio SDK client and user id.

    The SDK exposes a `tools.execute(user_id, action_name, params)` and also
    supports `entities.get(user_id).execute(action="...", params={...})` in
    recent versions. We will try the latter first, then fall back to tools API.
    """
    try:
        from composio import Composio as ComposioSdk  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Composio SDK not installed: {e}")
    api_key = os.getenv("COMPOSIO_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing COMPOSIO_API_KEY")
    user_id = os.getenv("COMPOSIO_USER_ID", "default")
    return ComposioSdk(api_key=api_key), user_id


def _get_provider_client():
    """Return Composio provider client (LlamaIndexProvider) and user id."""
    try:
        from composio import Composio as ComposioSdk  # type: ignore
        from composio_llamaindex import LlamaIndexProvider  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Composio provider not available: {e}")
    user_id = os.getenv("COMPOSIO_USER_ID", "default")
    return ComposioSdk(provider=LlamaIndexProvider()), user_id


def _ensure_spreadsheet(composio, user_id: str, title: str) -> str:
    meta = _load_gs_meta()
    spreadsheet_id = meta.get("spreadsheetId")
    if spreadsheet_id:
        return spreadsheet_id
    # Use provider tools API
    # Try common param shapes
    created = composio.tools.execute(  # type: ignore[attr-defined]
        user_id,
        "GOOGLESHEETS_CREATE_GOOGLE_SHEET1",
        {"title": title}
    )
    spreadsheet_id = (
        (created.get("response_data", {}) or {}).get("spreadsheetId")
        or (created.get("data", {}) or {}).get("spreadsheetId")
        or created.get("spreadsheetId")
    )
    if not spreadsheet_id:
        # Fallback to properties.title shape
        created = composio.tools.execute(  # type: ignore[attr-defined]
            user_id,
            "GOOGLESHEETS_CREATE_GOOGLE_SHEET1",
            {"properties": {"title": title}}
        )
    spreadsheet_id = (
        (created.get("response_data", {}) or {}).get("spreadsheetId")
        or (created.get("data", {}) or {}).get("spreadsheetId")
        or created.get("spreadsheetId")
    )
    if not spreadsheet_id:
        raise RuntimeError("Unable to create spreadsheet (no id returned)")
    meta["spreadsheetId"] = spreadsheet_id
    _save_gs_meta(meta)
    return spreadsheet_id


def _ensure_sheet(composio, user_id: str, spreadsheet_id: str, sheet_title: str) -> None:
    try:
        found = composio.tools.execute(  # type: ignore[attr-defined]
            user_id,
            "GOOGLESHEETS_FIND_WORKSHEET_BY_TITLE",
            {"spreadsheetId": spreadsheet_id, "title": sheet_title}
        )
        ok = True
        if isinstance(found, dict):
            ok = bool((found.get("response_data", {}) or {}).get("found", True) or (found.get("data", {}) or {}).get("found", True))
        if not ok:
            raise RuntimeError("not found")
    except Exception:
        composio.tools.execute(  # type: ignore[attr-defined]
            user_id,
            "GOOGLESHEETS_ADD_SHEET",
            {"spreadsheetId": spreadsheet_id, "title": sheet_title}
        )


def _clear_and_append(composio, user_id: str, spreadsheet_id: str, sheet_title: str, rows: list[list[str]]) -> None:
    # Clear
    try:
        composio.tools.execute(  # type: ignore[attr-defined]
            user_id,
            "GOOGLESHEETS_SPREADSHEETS_VALUES_BATCH_CLEAR",
            {"spreadsheetId": spreadsheet_id, "ranges": [f"{sheet_title}!A:ZZ"]}
        )
    except Exception:
        composio.tools.execute(  # type: ignore[attr-defined]
            user_id,
            "GOOGLESHEETS_CLEAR_VALUES",
            {"spreadsheetId": spreadsheet_id, "range": f"{sheet_title}!A:ZZ"}
        )
    # Append rows starting at A1
    composio.tools.execute(  # type: ignore[attr-defined]
        user_id=user_id,
        tool="GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
        parameters={
            "spreadsheetId": spreadsheet_id,
            "range": f"{sheet_title}!A1",
            "valueInputOption": "RAW",
            "values": rows,
        }
    )


@app.post("/composio/sync")
def composio_sync_google_sheets(
    payload: dict = Body(...),
):
    """Sync the provided canvas snapshot to Google Sheets.

    Expected payload shape: { items: Item[], globalTitle?: str, globalDescription?: str }
    Will create spreadsheet if missing and reuse it; ensures a 'Canvas' sheet by default.
    """
    try:
        # Use provider client; tools.execute is available
        composio, user_id = _get_provider_client()

        # Check connection via API client
        try:
            api_client, api_user_id = _get_api_client()
            auth_config_id = os.getenv("COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID", "").strip()
            
            # Get connected accounts for this auth config
            if auth_config_id:
                result = api_client.connected_accounts.list(auth_config_ids=[auth_config_id])  # type: ignore[attr-defined]
                # Access items property if it exists
                if hasattr(result, "items"):
                    conns = result.items if result.items is not None else []
                elif isinstance(result, list):
                    conns = result
                else:
                    conns = []
            else:
                # Fallback if no auth config ID
                conns = []
            
            # Since we're filtering by auth_config_id (Google Sheets specific), 
            # any connections returned should be Google Sheets connections
            has_google_sheets = len(conns) > 0 if isinstance(conns, (list, tuple)) else False
            
            print(f"Debug Sync - Total connections found: {len(conns) if isinstance(conns, (list, tuple)) else 0}")
            print(f"Debug Sync - Auth config ID: {auth_config_id}")
            print(f"Debug Sync - User ID: {api_user_id}")
            print(f"Debug Sync - Has Google Sheets: {has_google_sheets}")
            
            # Optional: filter by user if needed
            if has_google_sheets and api_user_id != "default":
                user_connections = []
                for conn in conns:
                    conn_user_id = None
                    if hasattr(conn, "user_id"):
                        conn_user_id = conn.user_id
                    elif hasattr(conn, "entity_id"):
                        conn_user_id = conn.entity_id
                    elif isinstance(conn, dict):
                        conn_user_id = conn.get("user_id") or conn.get("entity_id")
                    
                    if conn_user_id == api_user_id:
                        user_connections.append(conn)
                
                has_google_sheets = len(user_connections) > 0
                print(f"Debug Sync - User-specific connections: {len(user_connections)}")
            
            if not has_google_sheets:
                raise HTTPException(status_code=400, detail="Google Sheets is not connected. Click 'Connect Google Sheets' and complete consent.")
        except HTTPException as he:
            print(f"Debug Sync - HTTPException caught: {he.status_code}: {he.detail}")
            raise
        except Exception as e:
            # If checking fails, proceed anyway; auth errors will surface during API calls
            print(f"Warning: Could not verify Google Sheets connection: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            pass

        title = os.getenv("COMPOSIO_SHEETS_TITLE", "AG-UI Canvas Snapshot").strip() or "AG-UI Canvas Snapshot"
        sheet_title = os.getenv("COMPOSIO_SHEETS_SHEET", "Canvas").strip() or "Canvas"
        items = list(payload.get("items", []) or [])

        # Build rows
        header = ["id", "type", "name", "subtitle", "data_json"]
        rows: list[list[str]] = [header]
        for it in items:
            data_json = json.dumps(it.get("data", {}), ensure_ascii=False)
            rows.append([
                str(it.get("id", "")),
                str(it.get("type", "")),
                str(it.get("name", "")),
                str(it.get("subtitle", "")),
                data_json,
            ])

        # Create spreadsheet if needed and ensure sheet exists
        spreadsheet_id = _ensure_spreadsheet(composio, user_id, title)
        try:
            _ensure_sheet(composio, user_id, spreadsheet_id, sheet_title)
        except Exception:
            # If sheet creation fails due to stale spreadsheet id, reset and recreate
            _save_gs_meta({})
            spreadsheet_id = _ensure_spreadsheet(composio, user_id, title)
            _ensure_sheet(composio, user_id, spreadsheet_id, sheet_title)

        # Clear and append
        _clear_and_append(composio, user_id, spreadsheet_id, sheet_title, rows)

        return {"ok": True, "spreadsheetId": spreadsheet_id, "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync Google Sheets: {type(e).__name__}: {e}")


@app.get("/composio/sync")
def composio_sync_method_info():
    return {"error": "Method Not Allowed", "hint": "POST JSON payload {items:[...]} to this endpoint."}
