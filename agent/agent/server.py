from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

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
from .agent import _get_composio_client

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
        composio, user_id = _get_composio_client()
        # Programmatically initiate connection; returns object with redirect URL
        req = composio.connected_accounts.initiate(  # type: ignore[attr-defined]
            user_id=user_id,
            auth_config_id=auth_config_id,
        )
        # Normalize common attribute names
        redirect_url = getattr(req, "redirect_url", None) or getattr(req, "redirectUrl", None) or req.get("redirect_url") if isinstance(req, dict) else None
        if not redirect_url:
            raise RuntimeError("No redirect URL returned by Composio.")
        return {"redirectUrl": redirect_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate Google Sheets connection: {e}")
