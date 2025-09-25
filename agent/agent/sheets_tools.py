"""
Backend tools for Google Sheets synchronization in AG-UI workflow.
These tools are designed to work with the AG-UI workflow system.
"""

from typing import Optional, Dict, Any
from .sheets_sync import GoogleSheetsSync

# Global sheets sync instance
_sheets_sync: Optional[GoogleSheetsSync] = None
_last_synced_state: Optional[Dict[str, Any]] = None


def initialize_sheets_sync() -> Optional[GoogleSheetsSync]:
    """Initialize and return the global sheets sync instance."""
    global _sheets_sync
    if _sheets_sync is None:
        try:
            _sheets_sync = GoogleSheetsSync()
            # Don't require authentication at initialization
            # Authentication will be handled when tools are called
            print("Google Sheets sync initialized")
        except Exception as e:
            print(f"Failed to initialize Google Sheets sync: {e}")
            _sheets_sync = None
    return _sheets_sync


def sync_state_to_sheets(state: Dict[str, Any]) -> str:
    """Sync the provided state to Google Sheets."""
    global _last_synced_state
    
    sync = initialize_sheets_sync()
    if not sync:
        return "Google Sheets sync not available - initialization failed"
    
    # Ensure authenticated before syncing
    if not sync.ensure_authenticated():
        auth_url = sync.get_auth_url()
        if auth_url:
            return f"Google Sheets authentication required.\n\nPlease visit this URL to connect your Google account:\n{auth_url}\n\nAfter authentication, try syncing again."
        return "Google Sheets authentication required. Please check your configuration."
    
    try:
        items = state.get("items", [])
        
        # Check if this is the first sync or if state has changed
        if _last_synced_state is None or _last_synced_state != state:
            if sync.sync_items_to_sheet(items):
                _last_synced_state = state.copy()
                url = sync.get_spreadsheet_url()
                return f"Successfully synced {len(items)} items to Google Sheet: {url}"
            else:
                return "Failed to sync items to Google Sheet"
        else:
            return "State unchanged, skipping sync"
            
    except Exception as e:
        return f"Error syncing to sheets: {e}"


def get_sheet_url_backend() -> str:
    """Get the URL of the synced Google Sheet."""
    sync = initialize_sheets_sync()
    if not sync:
        return "Google Sheets sync not available - initialization failed"
    
    # Check if authenticated
    if not sync.ensure_authenticated():
        auth_url = sync.get_auth_url()
        if auth_url:
            return f"Google Sheets authentication required.\n\nPlease visit this URL to connect your Google account:\n{auth_url}"
        return "Google Sheets authentication required. Please check your configuration."
    
    url = sync.get_spreadsheet_url()
    if url:
        return f"Your Google Sheet is available at:\n{url}\n\nThis sheet contains all your canvas items and is automatically updated when you sync."
    else:
        return "No Google Sheet has been created yet. Use 'Create a new Google Sheet' to get started."


def create_new_sheet_backend(title: Optional[str] = None, state: Optional[Dict[str, Any]] = None) -> str:
    """Create a new Google Sheet for syncing canvas data."""
    sync = initialize_sheets_sync()
    if not sync:
        return "Google Sheets sync not available - initialization failed"
    
    # Ensure authenticated before creating sheet
    if not sync.ensure_authenticated():
        auth_url = sync.get_auth_url()
        if auth_url:
            return f"Google Sheets authentication required.\n\nPlease visit this URL to connect your Google account:\n{auth_url}\n\nAfter authentication, you can create a new sheet."
        return "Google Sheets authentication required. Please check your configuration."
    
    try:
        sheet_title = title or "AG-UI Canvas Data"
        sheet_id = sync.create_or_get_spreadsheet(sheet_title)
        
        # If state provided, sync it to the new sheet
        if state:
            items = state.get("items", [])
            sync.sync_items_to_sheet(items)
        
        return f"Created new sheet: {sync.get_spreadsheet_url()}"
    except Exception as e:
        return f"Failed to create sheet: {e}"


def get_sheets_auth_status() -> Dict[str, Any]:
    """Get the Google Sheets authentication status and URL."""
    sync = initialize_sheets_sync()
    if not sync:
        return {
            "authenticated": False,
            "error": "Google Sheets sync not available"
        }
    
    is_authenticated = sync.ensure_authenticated()
    
    if not is_authenticated:
        auth_url = sync.get_auth_url()
        return {
            "authenticated": False,
            "auth_url": auth_url,
            "message": "Please authenticate with Google Sheets"
        }
    
    return {
        "authenticated": True,
        "message": "Google Sheets connected"
    }


# Wrapper functions that will be used as backend tools
def sync_all_to_sheets(state: Dict[str, Any]) -> str:
    """
    Sync all current canvas items to Google Sheets.
    This is called by the AG-UI workflow with the current state.
    """
    return sync_state_to_sheets(state)


def get_sheet_url() -> str:
    """Get the URL of the synced Google Sheet."""
    return get_sheet_url_backend()


def create_new_sheet(title: Optional[str] = None, state: Optional[Dict[str, Any]] = None) -> str:
    """Create a new Google Sheet for syncing canvas data."""
    return create_new_sheet_backend(title, state)


def check_sheets_auth() -> str:
    """Check Google Sheets authentication status."""
    status = get_sheets_auth_status()
    if status["authenticated"]:
        return "Google Sheets is connected and ready to use! You can now create a new sheet or sync your canvas items."
    else:
        auth_url = status.get("auth_url")
        if auth_url:
            return f"To use Google Sheets features, you need to authenticate first.\n\nPlease visit this URL to connect your Google account:\n{auth_url}\n\nAfter authentication, you can create sheets and sync your canvas data."
        else:
            return "Google Sheets authentication is not properly configured. Please ensure your environment variables (COMPOSIO_API_KEY, COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID) are set correctly."
