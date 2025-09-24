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
        # If already connected, short-circuit
        try:
            conns = composio.connected_accounts.list()  # type: ignore[attr-defined]
            # Basic heuristic: if any account exists for Googlesheets, consider connected
            if conns and isinstance(conns, (list, tuple)) and len(conns) > 0:
                return {"alreadyConnected": True}
        except Exception:
            pass

        # Programmatically initiate connection; returns object with redirect URL (field name may vary)
        req = composio.connected_accounts.initiate(  # type: ignore[attr-defined]
            user_id=user_id,
            auth_config_id=auth_config_id,
        )

        # Try several shapes to find a URL
        redirect_url = None
        # Direct attributes
        for key in ("redirect_url", "redirectUrl", "url", "connect_url", "connectUrl", "authorization_url", "authorizationUrl"):
            if hasattr(req, key):
                redirect_url = getattr(req, key)
                if redirect_url:
                    break
        # Dict-like
        if redirect_url is None and isinstance(req, dict):
            for key in ("redirect_url", "redirectUrl", "url", "connect_url", "connectUrl", "authorization_url", "authorizationUrl"):
                if key in req and req[key]:
                    redirect_url = req[key]
                    break
        # Pydantic model
        if redirect_url is None and hasattr(req, "model_dump"):
            dump = req.model_dump()
            for key in ("redirect_url", "redirectUrl", "url", "connect_url", "connectUrl", "authorization_url", "authorizationUrl"):
                if key in dump and dump[key]:
                    redirect_url = dump[key]
                    break
        # Fallback to __dict__
        if redirect_url is None and hasattr(req, "__dict__"):
            dump = req.__dict__
            for key in ("redirect_url", "redirectUrl", "url", "connect_url", "connectUrl", "authorization_url", "authorizationUrl"):
                if key in dump and dump[key]:
                    redirect_url = dump[key]
                    break

        if not redirect_url:
            raise RuntimeError("No redirect URL returned by Composio.")
        return {"redirectUrl": redirect_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate Google Sheets connection: {e}")


@app.get("/composio/status/googlesheets")
def composio_status_google_sheets():
    try:
        composio, user_id = _get_api_client()
        conns = composio.connected_accounts.list()  # type: ignore[attr-defined]
        connected = bool(conns and isinstance(conns, (list, tuple)) and len(conns) > 0)
        return {"connected": connected, "count": len(conns) if isinstance(conns, (list, tuple)) else 0}
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
    """Return Composio API client (non-provider) and user id."""
    try:
        from composio import Composio as ComposioApi  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Composio SDK not installed: {e}")
    api_key = os.getenv("COMPOSIO_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing COMPOSIO_API_KEY")
    user_id = os.getenv("COMPOSIO_USER_ID", "default")
    return ComposioApi(api_key=api_key), user_id


def _ensure_spreadsheet(composio, user_id: str, title: str) -> str:
    meta = _load_gs_meta()
    spreadsheet_id = meta.get("spreadsheetId")
    if spreadsheet_id:
        return spreadsheet_id
    created = composio.actions.execute(  # type: ignore[attr-defined]
        user_id=user_id,
        action_name="GOOGLESHEETS_CREATE_GOOGLE_SHEET1",
        params={"title": title},
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
        found = composio.actions.execute(  # type: ignore[attr-defined]
            user_id=user_id,
            action_name="GOOGLESHEETS_FIND_WORKSHEET_BY_TITLE",
            params={"spreadsheetId": spreadsheet_id, "title": sheet_title},
        )
        ok = True
        if isinstance(found, dict):
            ok = bool((found.get("response_data", {}) or {}).get("found", True) or (found.get("data", {}) or {}).get("found", True))
        if not ok:
            raise RuntimeError("not found")
    except Exception:
        composio.actions.execute(  # type: ignore[attr-defined]
            user_id=user_id,
            action_name="GOOGLESHEETS_ADD_SHEET",
            params={"spreadsheetId": spreadsheet_id, "title": sheet_title},
        )


def _clear_and_append(composio, user_id: str, spreadsheet_id: str, sheet_title: str, rows: list[list[str]]) -> None:
    # Clear
    try:
        composio.actions.execute(  # type: ignore[attr-defined]
            user_id=user_id,
            action_name="GOOGLESHEETS_SPREADSHEETS_VALUES_BATCH_CLEAR",
            params={"spreadsheetId": spreadsheet_id, "ranges": [f"{sheet_title}!A:ZZ"]},
        )
    except Exception:
        composio.actions.execute(  # type: ignore[attr-defined]
            user_id=user_id,
            action_name="GOOGLESHEETS_CLEAR_VALUES",
            params={"spreadsheetId": spreadsheet_id, "range": f"{sheet_title}!A:ZZ"},
        )
    # Append rows starting at A1
    composio.actions.execute(  # type: ignore[attr-defined]
        user_id=user_id,
        action_name="GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
        params={
            "spreadsheetId": spreadsheet_id,
            "range": f"{sheet_title}!A1",
            "valueInputOption": "RAW",
            "values": rows,
        },
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
        composio, user_id = _get_api_client()

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
        raise HTTPException(status_code=500, detail=f"Failed to sync Google Sheets: {e}")
