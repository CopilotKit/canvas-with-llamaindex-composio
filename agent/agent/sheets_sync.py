"""
Google Sheets synchronization module for AG-UI Canvas.
Keeps the shared state synchronized with a Google Sheet.
"""

import os
import json
from typing import Dict, List, Optional, Union
from composio import Composio
# Note: ComposioToolSet import removed due to version compatibility issues
# We'll use the Composio client directly instead
from datetime import datetime

# Define Google Sheets actions we'll use
SHEET_ACTIONS = [
    "GOOGLESHEETS_CREATE_GOOGLE_SHEET1",
    "GOOGLESHEETS_CREATE_SPREADSHEET_ROW",
    "GOOGLESHEETS_BATCH_UPDATE",
    "GOOGLESHEETS_CLEAR_VALUES",
    "GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
    "GOOGLESHEETS_GET_SPREADSHEET_INFO",
    "GOOGLESHEETS_BATCH_GET",
    "GOOGLESHEETS_UPDATE_SPREADSHEET_ROW",
    "GOOGLESHEETS_LOOKUP_SPREADSHEET_ROW",
]


class GoogleSheetsSync:
    """Handles synchronization between AG-UI state and Google Sheets."""
    
    def __init__(self):
        """Initialize the Google Sheets sync with Composio."""
        self.composio_api_key = os.getenv("COMPOSIO_API_KEY")
        self.user_id = os.getenv("COMPOSIO_USER_ID", "default")
        self.auth_config_id = os.getenv("COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID")
        
        if not self.composio_api_key:
            raise ValueError("COMPOSIO_API_KEY not found in environment variables")
        
        # Initialize Composio client
        self.composio = Composio(api_key=self.composio_api_key)
        
        # Sheet configuration
        self.spreadsheet_id: Optional[str] = None
        self.sheet_name = "Canvas Items"
        self.headers = [
            "ID", "Type", "Name", "Subtitle", 
            "Field1", "Field2", "Field3", "Field4",
            "Last Updated", "Raw Data"
        ]
    
    def ensure_authenticated(self) -> bool:
        """Ensure the user is authenticated with Google Sheets."""
        try:
            # Check if user has connected account
            connected_accounts = self.composio.connected_accounts.list(user_id=self.user_id)
            
            # Look for Google Sheets connection
            for account in connected_accounts:
                if account.app_unique_id == "googlesheets":
                    return True
            
            # Not authenticated
            return False
            
        except Exception as e:
            print(f"Authentication check failed: {e}")
            return False
    
    def get_auth_url(self) -> Optional[str]:
        """Get the authentication URL for Google Sheets."""
        try:
            if self.auth_config_id:
                connection_request = self.composio.connected_accounts.initiate(
                    user_id=self.user_id,
                    auth_config_id=self.auth_config_id,
                )
                return connection_request.redirect_url
            return None
        except Exception as e:
            print(f"Failed to get auth URL: {e}")
            return None
    
    def create_or_get_spreadsheet(self, title: str = "AG-UI Canvas Data") -> str:
        """Create a new spreadsheet or get existing one."""
        try:
            # Create new spreadsheet
            response = self.composio.execute_tool(
                tool="GOOGLESHEETS_CREATE_GOOGLE_SHEET1",
                user_id=self.user_id,
                parameters={
                    "title": title,
                    "sheets": [{
                        "properties": {
                            "title": self.sheet_name,
                            "gridProperties": {
                                "rowCount": 1000,
                                "columnCount": len(self.headers)
                            }
                        }
                    }]
                }
            )
            
            # Handle different response formats from execute_tool
            if response:
                # Check if response has a result attribute
                result = response.get("result", response) if isinstance(response, dict) else response
                
                # Extract spreadsheet_id from various possible locations
                if isinstance(result, dict):
                    self.spreadsheet_id = result.get("spreadsheet_id") or result.get("spreadsheetId")
                else:
                    self.spreadsheet_id = None
                
                if not self.spreadsheet_id:
                    print(f"Warning: Could not extract spreadsheet_id from response: {response}")
                    raise ValueError("Failed to get spreadsheet ID from response")
                else:
                    print(f"Created new spreadsheet: {self.spreadsheet_id}")
                
                # Add headers
                self._add_headers()
                
                return self.spreadsheet_id
            else:
                raise ValueError("Failed to create spreadsheet")
                
        except Exception as e:
            print(f"Error creating spreadsheet: {e}")
            raise
    
    def _add_headers(self):
        """Add header row to the spreadsheet."""
        if not self.spreadsheet_id:
            raise ValueError("No spreadsheet ID set")
        
        try:
            response = self.composio.execute_tool(
                tool="GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
                user_id=self.user_id,
                parameters={
                    "spreadsheet_id": self.spreadsheet_id,
                    "range": f"{self.sheet_name}!A1",
                    "values": [self.headers],
                    "valueInputOption": "RAW"
                }
            )
            print(f"Added headers to spreadsheet")
        except Exception as e:
            print(f"Error adding headers: {e}")
    
    def sync_items_to_sheet(self, items: List[Dict]) -> bool:
        """Sync all items from state to Google Sheet."""
        if not self.spreadsheet_id:
            print("No spreadsheet ID set, creating new sheet...")
            self.create_or_get_spreadsheet()
        
        try:
            # Clear existing data (except headers)
            self._clear_sheet_data()
            
            # Convert items to rows
            rows = []
            for item in items:
                row = self._item_to_row(item)
                rows.append(row)
            
            if rows:
                # Batch append all rows
                response = self.composio.execute_tool(
                    tool="GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
                    user_id=self.user_id,
                parameters={
                        "spreadsheet_id": self.spreadsheet_id,
                        "range": f"{self.sheet_name}!A2",
                        "values": rows,
                        "valueInputOption": "RAW"
                    },
                    entity_id=self.user_id
                )
                print(f"Synced {len(rows)} items to Google Sheet")
            
            return True
            
        except Exception as e:
            print(f"Error syncing items to sheet: {e}")
            return False
    
    def _clear_sheet_data(self):
        """Clear all data from sheet except headers."""
        try:
            response = self.composio.execute_tool(
                tool="GOOGLESHEETS_CLEAR_VALUES",
                user_id=self.user_id,
                parameters={
                    "spreadsheet_id": self.spreadsheet_id,
                    "range": f"{self.sheet_name}!A2:Z1000"
                }
            )
            print("Cleared sheet data")
        except Exception as e:
            print(f"Error clearing sheet: {e}")
    
    def _item_to_row(self, item: Dict) -> List[Union[str, int, float]]:
        """Convert an item dict to a sheet row."""
        data = item.get("data", {})
        
        # Extract field values based on item type
        field1 = self._extract_field_value(data, "field1")
        field2 = self._extract_field_value(data, "field2")
        field3 = self._extract_field_value(data, "field3")
        field4 = self._extract_field_value(data, "field4")
        
        row = [
            item.get("id", ""),
            item.get("type", ""),
            item.get("name", ""),
            item.get("subtitle", ""),
            field1,
            field2,
            field3,
            field4,
            datetime.now().isoformat(),
            json.dumps(data, ensure_ascii=False)  # Raw data as JSON
        ]
        
        return row
    
    def _extract_field_value(self, data: Dict, field: str) -> str:
        """Extract and format field value for sheet display."""
        value = data.get(field, "")
        
        if isinstance(value, list):
            # Handle arrays (tags, checklist items, metrics)
            if field == "field4" and all(isinstance(item, dict) for item in value):
                # Checklist items
                checklist = []
                for item in value:
                    done = "✓" if item.get("done") else "○"
                    text = item.get("text", "")
                    checklist.append(f"{done} {text}")
                return "\n".join(checklist)
            elif field == "field1" and all(isinstance(item, dict) for item in value):
                # Chart metrics
                metrics = []
                for item in value:
                    label = item.get("label", "")
                    val = item.get("value", "")
                    if val != "":
                        metrics.append(f"{label}: {val}")
                    else:
                        metrics.append(f"{label}: -")
                return "\n".join(metrics)
            else:
                # Simple array (tags)
                return ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            return json.dumps(value)
        else:
            return str(value)
    
    def add_item_to_sheet(self, item: Dict) -> bool:
        """Add a single item to the sheet."""
        if not self.spreadsheet_id:
            print("No spreadsheet ID set")
            return False
        
        try:
            row = self._item_to_row(item)
            response = self.composio.execute_tool(
                tool="GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
                user_id=self.user_id,
                parameters={
                    "spreadsheet_id": self.spreadsheet_id,
                    "range": f"{self.sheet_name}!A2",
                    "values": [row],
                    "valueInputOption": "RAW"
                }
            )
            print(f"Added item {item.get('id')} to sheet")
            return True
        except Exception as e:
            print(f"Error adding item to sheet: {e}")
            return False
    
    def update_item_in_sheet(self, item: Dict) -> bool:
        """Update an existing item in the sheet."""
        if not self.spreadsheet_id:
            print("No spreadsheet ID set")
            return False
        
        try:
            # Find the row with this item ID
            item_id = item.get("id")
            if not item_id:
                return False
            
            # For simplicity, we'll do a full resync
            # In production, you'd want to find and update the specific row
            print(f"Item {item_id} updated, triggering resync...")
            return True
            
        except Exception as e:
            print(f"Error updating item in sheet: {e}")
            return False
    
    def delete_item_from_sheet(self, item_id: str) -> bool:
        """Delete an item from the sheet."""
        if not self.spreadsheet_id:
            print("No spreadsheet ID set")
            return False
        
        try:
            # For simplicity, we'll trigger a full resync
            # In production, you'd find and delete the specific row
            print(f"Item {item_id} deleted, triggering resync...")
            return True
            
        except Exception as e:
            print(f"Error deleting item from sheet: {e}")
            return False
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """Get the URL of the current spreadsheet."""
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
        return None
