# Google Sheets Integration for AG-UI Canvas

This document describes the Google Sheets integration for the AG-UI Canvas template, which keeps your canvas items synchronized with a Google Sheet.

## Overview

The integration automatically syncs all canvas items (projects, entities, notes, and charts) to a Google Sheet, with one row per item. This enables:

- Real-time backup of canvas data
- Easy sharing and collaboration via Google Sheets
- Data export and analysis capabilities
- Integration with other Google Workspace tools

## Setup

### 1. Environment Variables

Add these to your `.env` file:

```env
COMPOSIO_API_KEY=your_composio_api_key
COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID=your_auth_config_id
COMPOSIO_USER_ID=default
```

### 2. Install Dependencies

The required dependencies are already added to `agent/pyproject.toml`:

```bash
cd agent
pip install -e .
```

### 3. Authentication

On first run, you'll need to authenticate with Google Sheets:

1. The system will provide an authentication URL
2. Visit the URL and authorize access to Google Sheets
3. The authentication will be saved for future use

## Usage

### Agent Commands

The agent can interact with Google Sheets using these commands:

- **"Sync to Google Sheets"** - Manually trigger a sync of all items
- **"Get sheet URL"** - Get the link to the synced spreadsheet
- **"Create new sheet"** - Create a fresh spreadsheet

### Automatic Syncing

The system can be configured to automatically sync on state changes:

- When items are created
- When items are updated
- When items are deleted

### Sheet Structure

The Google Sheet contains these columns:

| Column | Description |
|--------|-------------|
| ID | Unique item identifier |
| Type | Item type (project, entity, note, chart) |
| Name | Item name/title |
| Subtitle | Item subtitle/description |
| Field1 | Type-specific field 1 |
| Field2 | Type-specific field 2 |
| Field3 | Type-specific field 3 |
| Field4 | Type-specific field 4 |
| Last Updated | Timestamp of last update |
| Raw Data | Complete item data as JSON |

### Field Mappings

- **Project**: field1=text, field2=select, field3=date, field4=checklist
- **Entity**: field1=text, field2=select, field3=tags
- **Note**: field1=content (multiline text)
- **Chart**: field1=metrics array

## Architecture

The integration consists of three main components:

1. **sheets_sync.py** - Core synchronization logic and Google Sheets API interactions
2. **sheets_tools.py** - Backend tools for the AG-UI workflow
3. **workflow_integration.py** - Integration layer between AG-UI and sheets sync

## Testing

Run the test script to verify the integration:

```bash
cd agent
python test_sheets_integration.py
```

This will:
1. Initialize the Google Sheets connection
2. Create a test sheet with sample data
3. Perform sync operations
4. Display the sheet URL

## API Reference

### Backend Tools

```python
# Sync all items to Google Sheets
sync_all_to_sheets() -> str

# Get the spreadsheet URL
get_sheet_url() -> str

# Create a new spreadsheet
create_new_sheet(title: Optional[str] = None) -> str
```

### Sheet Sync Methods

```python
# Initialize and authenticate
sheets_sync = GoogleSheetsSync()
sheets_sync.ensure_authenticated()

# Create or get spreadsheet
sheet_id = sheets_sync.create_or_get_spreadsheet(title)

# Sync items
sheets_sync.sync_items_to_sheet(items)

# Get spreadsheet URL
url = sheets_sync.get_spreadsheet_url()
```

## Troubleshooting

### Authentication Issues

1. Verify environment variables are set correctly
2. Check Composio dashboard for auth config status
3. Try re-authenticating by deleting and recreating the connection

### Sync Failures

1. Check console logs for detailed error messages
2. Verify Google Sheets API quotas haven't been exceeded
3. Ensure sheet structure hasn't been manually modified

### Performance

- For large datasets (>1000 items), consider batch operations
- Implement throttling to avoid API rate limits
- Use incremental updates instead of full syncs when possible

## Future Enhancements

- Bidirectional sync (changes in sheet reflected in canvas)
- Selective sync (filter which items to sync)
- Multiple sheet support (different sheets for different item types)
- Real-time collaboration features
- Advanced formatting and charts in Google Sheets
