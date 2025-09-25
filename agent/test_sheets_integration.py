#!/usr/bin/env python3
"""
Test script for Google Sheets integration with AG-UI Canvas.
This script demonstrates and tests the synchronization functionality.
"""

import os
import sys
from pathlib import Path

# Add the agent module to the path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from agent.sheets_sync import GoogleSheetsSync
from agent.sheets_tools import sync_state_to_sheets, get_sheet_url, create_new_sheet


def test_basic_sync():
    """Test basic synchronization functionality."""
    print("=== Testing Google Sheets Integration ===\n")
    
    # Test data representing canvas state
    test_state = {
        "globalTitle": "Test Canvas",
        "globalDescription": "Testing Google Sheets sync",
        "items": [
            {
                "id": "0001",
                "type": "project",
                "name": "Project Alpha",
                "subtitle": "Main development project",
                "data": {
                    "field1": "Project overview text",
                    "field2": "Option A",
                    "field3": "2024-12-31",
                    "field4": [
                        {"id": "001", "text": "Design phase", "done": True},
                        {"id": "002", "text": "Implementation", "done": False},
                        {"id": "003", "text": "Testing", "done": False}
                    ]
                }
            },
            {
                "id": "0002",
                "type": "entity",
                "name": "Customer Entity",
                "subtitle": "Key stakeholder",
                "data": {
                    "field1": "Entity description",
                    "field2": "Option B",
                    "field3": ["Tag 1", "Tag 3"],
                    "field3_options": ["Tag 1", "Tag 2", "Tag 3"]
                }
            },
            {
                "id": "0003",
                "type": "note",
                "name": "Meeting Notes",
                "subtitle": "",
                "data": {
                    "field1": "Discussion points:\n- Feature requirements\n- Timeline\n- Budget constraints"
                }
            },
            {
                "id": "0004",
                "type": "chart",
                "name": "Progress Chart",
                "subtitle": "Project metrics",
                "data": {
                    "field1": [
                        {"id": "m1", "label": "Completion", "value": 35},
                        {"id": "m2", "label": "Quality", "value": 85},
                        {"id": "m3", "label": "Budget Used", "value": 45}
                    ]
                }
            }
        ]
    }
    
    # Step 1: Initialize and authenticate
    print("1. Initializing Google Sheets sync...")
    try:
        sync = GoogleSheetsSync()
        if sync.ensure_authenticated():
            print("   ✓ Authentication successful")
        else:
            print("   ✗ Authentication failed")
            print("\nPlease check your environment variables:")
            print("   - COMPOSIO_API_KEY")
            print("   - COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID")
            print("   - COMPOSIO_USER_ID")
            return
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return
    
    # Step 2: Create a new sheet
    print("\n2. Creating new Google Sheet...")
    result = create_new_sheet("AG-UI Canvas Test Sheet", test_state)
    print(f"   {result}")
    
    # Step 3: Get sheet URL
    print("\n3. Getting sheet URL...")
    url = get_sheet_url()
    print(f"   {url}")
    
    # Step 4: Test sync
    print("\n4. Testing sync with sample data...")
    sync_result = sync_state_to_sheets(test_state)
    print(f"   {sync_result}")
    
    # Step 5: Test update
    print("\n5. Testing update (adding new item)...")
    test_state["items"].append({
        "id": "0005",
        "type": "project",
        "name": "Project Beta",
        "subtitle": "Secondary project",
        "data": {
            "field1": "New project description",
            "field2": "Option C",
            "field3": "2025-01-15",
            "field4": []
        }
    })
    sync_result = sync_state_to_sheets(test_state)
    print(f"   {sync_result}")
    
    print("\n=== Test Complete ===")
    print(f"\nVisit your Google Sheet to see the synced data:")
    if sync.get_spreadsheet_url():
        print(f"   {sync.get_spreadsheet_url()}")
    

if __name__ == "__main__":
    test_basic_sync()
