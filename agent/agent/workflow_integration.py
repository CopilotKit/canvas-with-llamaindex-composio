"""
Integration module for AG-UI workflow and Google Sheets sync.
This module provides the glue between the AG-UI workflow system and our sheets sync.
"""

from typing import Dict, Any, Optional
from llama_index.core.workflow import Context
from .sheets_tools import sync_state_to_sheets, get_sheet_url, create_new_sheet


class WorkflowSheetsIntegration:
    """Handles integration between AG-UI workflow and Google Sheets."""
    
    def __init__(self):
        self.last_sync_result = None
    
    async def sync_from_context(self, ctx: Context) -> str:
        """Sync items from workflow context to Google Sheets."""
        try:
            # Get the shared state from context
            state = await ctx.get("__shared_state", {})
            
            # Sync to sheets
            result = sync_state_to_sheets(state)
            self.last_sync_result = result
            
            return result
        except Exception as e:
            return f"Error accessing workflow state: {e}"
    
    async def get_url(self, ctx: Context) -> str:
        """Get the Google Sheets URL."""
        return get_sheet_url()
    
    async def create_sheet(self, ctx: Context, title: Optional[str] = None) -> str:
        """Create a new sheet and sync current state."""
        try:
            # Get the shared state
            state = await ctx.get("__shared_state", {})
            
            # Create sheet and sync
            result = create_new_sheet(title, state)
            
            return result
        except Exception as e:
            return f"Error creating sheet: {e}"


# Global instance
workflow_integration = WorkflowSheetsIntegration()


# Workflow-aware backend tools
async def workflow_sync_all_to_sheets(ctx: Context) -> str:
    """Sync all current canvas items to Google Sheets."""
    return await workflow_integration.sync_from_context(ctx)


async def workflow_get_sheet_url(ctx: Context) -> str:
    """Get the URL of the synced Google Sheet."""
    return await workflow_integration.get_url(ctx)


async def workflow_create_new_sheet(ctx: Context, title: Optional[str] = None) -> str:
    """Create a new Google Sheet for syncing canvas data."""
    return await workflow_integration.create_sheet(ctx, title)
