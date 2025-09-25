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
            if _sheets_sync.ensure_authenticated():
                print("Google Sheets authentication successful")
            else:
                print("Google Sheets authentication failed")
                _sheets_sync = None
        except Exception as e:
            print(f"Failed to initialize Google Sheets sync: {e}")
            _sheets_sync = None
    return _sheets_sync


def sync_state_to_sheets(state: Dict[str, Any]) -> str:
    """Sync the provided state to Google Sheets."""
    global _last_synced_state
    
    sync = initialize_sheets_sync()
    if not sync:
        return "Google Sheets sync not available"
    
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
        return "Google Sheets sync not available"
    
    url = sync.get_spreadsheet_url()
    if url:
        return f"Sheet URL: {url}"
    else:
        return "No sheet created yet. Run sync first."


def create_new_sheet_backend(title: Optional[str] = None, state: Optional[Dict[str, Any]] = None) -> str:
    """Create a new Google Sheet for syncing canvas data."""
    sync = initialize_sheets_sync()
    if not sync:
        return "Google Sheets sync not available"
    
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


def create_new_sheet(title: Optional[str] = None) -> str:
    """Create a new Google Sheet for syncing canvas data."""
    return create_new_sheet_backend(title)
