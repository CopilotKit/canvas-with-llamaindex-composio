from typing import Annotated, List, Optional, Dict, Any
import asyncio
import os

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.protocols.ag_ui.events import StateSnapshotWorkflowEvent
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router

from .sheets_tools import sync_all_to_sheets, get_sheet_url_backend as get_sheet_url, create_new_sheet_backend as create_new_sheet, sync_state_to_sheets, check_sheets_auth


# Google Sheets sync will be initialized on first use

# Check environment variables on startup
print("=== CHECKING ENVIRONMENT VARIABLES ===")
print(f"COMPOSIO_API_KEY: {'SET' if os.getenv('COMPOSIO_API_KEY') else 'NOT SET'}")
print(f"COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID: {os.getenv('COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID', 'NOT SET')}")
print(f"COMPOSIO_USER_ID: {os.getenv('COMPOSIO_USER_ID', 'NOT SET')}")

# Global variable to store the current canvas state
_current_canvas_state: Dict[str, Any] = {}

def update_canvas_state(state: Dict[str, Any]) -> None:
    """Update the global canvas state."""
    global _current_canvas_state
    _current_canvas_state = state
    print(f"Updated canvas state with {len(state.get('items', []))} items")

# --- Backend tools (server-side) ---

def sheets_sync_all(**kwargs) -> str:
    """
    Sync all current canvas items to Google Sheets.
    
    This backend tool will sync all items in the canvas to a Google Sheet.
    Call this when asked to 'sync to sheets', 'sync to Google Sheets', 'update sheet', etc.
    """
    print("=== BACKEND TOOL CALLED: sheets_sync_all ===")
    print(f"Received kwargs: {list(kwargs.keys())}")
    try:
        # Try to get state from various possible sources
        state = None
        
        # Check if state is passed directly
        if '__shared_state' in kwargs:
            state = kwargs['__shared_state']
            print(f"Got state from __shared_state")
        elif 'state' in kwargs:
            state = kwargs['state']
            print(f"Got state from state")
        elif 'context' in kwargs:
            # Try to get from context
            ctx = kwargs['context']
            if hasattr(ctx, 'get'):
                state = ctx.get('__shared_state', _current_canvas_state)
                print(f"Got state from context")
        else:
            # Fall back to global state
            state = _current_canvas_state
            print(f"Using global state")
            
        print(f"Syncing state with {len(state.get('items', []))} items")
        result = sync_all_to_sheets(state)
        print(f"Sync result: {result}")
        return result
    except Exception as e:
        print(f"Error in sheets_sync_all: {e}")
        import traceback
        traceback.print_exc()
        return f"Error syncing to sheets: {str(e)}"

def sheets_get_url(**kwargs) -> str:
    """
    Get the URL of the synced Google Sheet.
    
    This backend tool returns the URL of the current Google Sheet.
    Call this when asked for 'sheet URL', 'sheet link', 'Google Sheets link', etc.
    """
    print("=== BACKEND TOOL CALLED: sheets_get_url ===")
    print(f"Received kwargs: {list(kwargs.keys())}")
    try:
        result = get_sheet_url()
        print(f"URL result: {result}")
        return result
    except Exception as e:
        print(f"Error in sheets_get_url: {e}")
        return f"Error getting sheet URL: {str(e)}"

def sheets_create_new(title: Optional[str] = None, **kwargs) -> str:
    """
    Create a new Google Sheet for syncing canvas data.
    
    This backend tool creates a new Google Sheet and optionally syncs current canvas items.
    Call this when asked to 'create a new Google Sheet', 'create sheet', 'new sheet', etc.
    
    Args:
        title: Optional title for the new sheet
    """
    print(f"=== BACKEND TOOL CALLED: sheets_create_new with title: {title} ===")
    print(f"Received kwargs: {list(kwargs.keys())}")
    try:
        # Try to get state from various possible sources
        state = None
        
        # Check if state is passed directly
        if '__shared_state' in kwargs:
            state = kwargs['__shared_state']
            print(f"Got state from __shared_state")
        elif 'state' in kwargs:
            state = kwargs['state']
            print(f"Got state from state")
        elif 'context' in kwargs:
            # Try to get from context
            ctx = kwargs['context']
            if hasattr(ctx, 'get'):
                state = ctx.get('__shared_state', _current_canvas_state)
                print(f"Got state from context")
        else:
            # Fall back to global state
            state = _current_canvas_state
            print(f"Using global state")
            
        print(f"Creating sheet with initial state of {len(state.get('items', []) if state else [])} items")
        result = create_new_sheet(title, state)
        print(f"Create result: {result}")
        return result
    except Exception as e:
        print(f"Error in sheets_create_new: {e}")
        import traceback
        traceback.print_exc()
        return f"Error creating sheet: {str(e)}"

def sheets_check_auth(**kwargs) -> str:
    """
    Check Google Sheets authentication status.
    
    This backend tool checks if the user is authenticated with Google Sheets.
    Call this when asked about 'auth', 'authentication', 'login', 'connection status', etc.
    """
    print("=== BACKEND TOOL CALLED: sheets_check_auth ===")
    print(f"Received kwargs: {list(kwargs.keys())}")
    try:
        result = check_sheets_auth()
        print(f"Auth check result: {result}")
        return result
    except Exception as e:
        print(f"Error in sheets_check_auth: {e}")
        import traceback
        traceback.print_exc()
        return f"Error checking auth: {str(e)}"


# --- Frontend tool stubs (names/signatures only; execution happens in the UI) ---

# Helper to trigger sync after state changes
def _trigger_sync_if_needed(state: Dict[str, Any], action: str = "") -> None:
    """Helper to sync to sheets after state changes."""
    try:
        # Only sync on significant actions
        if action in ["created", "deleted", "updated"]:
            result = sync_state_to_sheets(state)
            print(f"Auto-sync after {action}: {result}")
    except Exception as e:
        print(f"Auto-sync error: {e}")

def createItem(
    type: Annotated[str, "One of: project, entity, note, chart."],
    name: Annotated[Optional[str], "Optional item name."] = None,
) -> str:
    """Create a new canvas item and return its id."""
    return f"createItem({type}, {name})"

def deleteItem(
    itemId: Annotated[str, "Target item id."],
) -> str:
    """Delete an item by id."""
    return f"deleteItem({itemId})"

def setItemName(
    name: Annotated[str, "New item name/title."],
    itemId: Annotated[str, "Target item id."],
) -> str:
    """Set an item's name."""
    return f"setItemName(name, {itemId})"

def setItemSubtitleOrDescription(
    subtitle: Annotated[str, "Item subtitle/short description."],
    itemId: Annotated[str, "Target item id."],
) -> str:
    """Set an item's subtitle/description (not data fields)."""
    return f"setItemSubtitleOrDescription({subtitle}, {itemId})"

def setGlobalTitle(title: Annotated[str, "New global title."]) -> str:
    """Set the global canvas title."""
    return f"setGlobalTitle({title})"

def setGlobalDescription(description: Annotated[str, "New global description."]) -> str:
    """Set the global canvas description."""
    return f"setGlobalDescription({description})"

# Note actions
def setNoteField1(
    value: Annotated[str, "New content for note.data.field1."],
    itemId: Annotated[str, "Target note id."],
) -> str:
    return f"setNoteField1({value}, {itemId})"

def appendNoteField1(
    value: Annotated[str, "Text to append to note.data.field1."],
    itemId: Annotated[str, "Target note id."],
    withNewline: Annotated[Optional[bool], "Prefix with newline if true." ] = None,
) -> str:
    return f"appendNoteField1({value}, {itemId}, {withNewline})"

def clearNoteField1(
    itemId: Annotated[str, "Target note id."],
) -> str:
    return f"clearNoteField1({itemId})"

# Project actions
def setProjectField1(value: Annotated[str, "New value for project.data.field1."], itemId: Annotated[str, "Project id."]) -> str:
    return f"setProjectField1({value}, {itemId})"

def setProjectField2(value: Annotated[str, "New value for project.data.field2."], itemId: Annotated[str, "Project id."]) -> str:
    return f"setProjectField2({value}, {itemId})"

def setProjectField3(date: Annotated[str, "Date YYYY-MM-DD for project.data.field3."], itemId: Annotated[str, "Project id."]) -> str:
    return f"setProjectField3({date}, {itemId})"

def clearProjectField3(itemId: Annotated[str, "Project id."]) -> str:
    return f"clearProjectField3({itemId})"

def addProjectChecklistItem(
    itemId: Annotated[str, "Project id."],
    text: Annotated[Optional[str], "Checklist text."] = None,
) -> str:
    return f"addProjectChecklistItem({itemId}, {text})"

def setProjectChecklistItem(
    itemId: Annotated[str, "Project id."],
    checklistItemId: Annotated[str, "Checklist item id or index."],
    text: Annotated[Optional[str], "New text."] = None,
    done: Annotated[Optional[bool], "New done status."] = None,
) -> str:
    return f"setProjectChecklistItem({itemId}, {checklistItemId}, {text}, {done})"

def removeProjectChecklistItem(
    itemId: Annotated[str, "Project id."],
    checklistItemId: Annotated[str, "Checklist item id."],
) -> str:
    return f"removeProjectChecklistItem({itemId}, {checklistItemId})"

# Entity actions
def setEntityField1(value: Annotated[str, "New value for entity.data.field1."], itemId: Annotated[str, "Entity id."]) -> str:
    return f"setEntityField1({value}, {itemId})"

def setEntityField2(value: Annotated[str, "New value for entity.data.field2."], itemId: Annotated[str, "Entity id."]) -> str:
    return f"setEntityField2({value}, {itemId})"

def addEntityField3(tag: Annotated[str, "Tag to add."], itemId: Annotated[str, "Entity id."]) -> str:
    return f"addEntityField3({tag}, {itemId})"

def removeEntityField3(tag: Annotated[str, "Tag to remove."], itemId: Annotated[str, "Entity id."]) -> str:
    return f"removeEntityField3({tag}, {itemId})"

# Chart actions
def addChartField1(
    itemId: Annotated[str, "Chart id."],
    label: Annotated[Optional[str], "Metric label."] = None,
    value: Annotated[Optional[float], "Metric value 0..100."] = None,
) -> str:
    return f"addChartField1({itemId}, {label}, {value})"

def setChartField1Label(itemId: Annotated[str, "Chart id."], index: Annotated[int, "Metric index (0-based)."], label: Annotated[str, "New metric label."]) -> str:
    return f"setChartField1Label({itemId}, {index}, {label})"

def setChartField1Value(itemId: Annotated[str, "Chart id."], index: Annotated[int, "Metric index (0-based)."], value: Annotated[float, "Value 0..100."]) -> str:
    return f"setChartField1Value({itemId}, {index}, {value})"

def clearChartField1Value(itemId: Annotated[str, "Chart id."], index: Annotated[int, "Metric index (0-based)."]) -> str:
    return f"clearChartField1Value({itemId}, {index})"

def removeChartField1(itemId: Annotated[str, "Chart id."], index: Annotated[int, "Metric index (0-based)."]) -> str:
    return f"removeChartField1({itemId}, {index})"

FIELD_SCHEMA = (
    "FIELD SCHEMA (authoritative):\n"
    "- project.data:\n"
    "  - field1: string (text)\n"
    "  - field2: string (select: 'Option A' | 'Option B' | 'Option C')\n"
    "  - field3: string (date 'YYYY-MM-DD')\n"
    "  - field4: ChecklistItem[] where ChecklistItem={id: string, text: string, done: boolean, proposed: boolean}\n"
    "- entity.data:\n"
    "  - field1: string\n"
    "  - field2: string (select: 'Option A' | 'Option B' | 'Option C')\n"
    "  - field3: string[] (selected tags; subset of field3_options)\n"
    "  - field3_options: string[] (available tags)\n"
    "- note.data:\n"
    "  - field1: string (textarea; represents description)\n"
    "- chart.data:\n"
    "  - field1: Array<{id: string, label: string, value: number | ''}> with value in [0..100] or ''\n"
)

SYSTEM_PROMPT = (
    "You are a helpful AG-UI assistant with Google Sheets integration.\n\n"
    + FIELD_SCHEMA +
    "\nMUTATION/TOOL POLICY:\n"
    "- When you claim to create/update/delete, you MUST call the corresponding tool(s) (frontend or backend).\n"
    "- To create new cards, call the frontend tool `createItem` with `type` in {project, entity, note, chart} and optional `name`.\n"
    "- GOOGLE SHEETS: When asked about Google Sheets, you MUST call the backend tools:\n"
    "  - 'Create a new Google Sheet' → call sheets_create_new\n"
    "  - 'Sync to sheets' → call sheets_sync_all\n"
    "  - 'Get sheet URL' → call sheets_get_url\n"
    "  - These are BACKEND tools, not frontend tools - you must actually call them!\n"
    "- After tools run, rely on the latest shared state (ground truth) when replying.\n"
    "- To set a card's subtitle (never the data fields): use setItemSubtitleOrDescription.\n\n"
    "DESCRIPTION MAPPING:\n"
    "- For project/entity/chart: treat 'description', 'overview', 'summary', 'caption', 'blurb' as the card subtitle; use setItemSubtitleOrDescription.\n"
    "- For notes: 'content', 'description', 'text', or 'note' refers to note content; use setNoteField1 / appendNoteField1 / clearNoteField1.\n\n"
    "GOOGLE SHEETS INTEGRATION:\n"
    "- Canvas items can be synced to Google Sheets (one row per item).\n"
    "- CRITICAL: You have backend tools for Google Sheets. ALWAYS call them:\n"
    "  - When asked to 'Create a new Google Sheet': CALL sheets_create_new\n"
    "  - When asked to 'Sync to sheets' or similar: CALL sheets_sync_all\n"
    "  - When asked for 'sheet URL' or 'link': CALL sheets_get_url\n"
    "  - When checking authentication: CALL sheets_check_auth\n"
    "- NEVER say 'authentication is required' without FIRST calling sheets_check_auth\n"
    "- NEVER say 'I cannot create' without FIRST calling sheets_create_new\n"
    "- These are BACKEND TOOLS - actually call them, don't just talk about them!\n"
    "- Examples of when to call backend tools:\n"
    "  - User: 'Create a new Google Sheet' → YOU: call sheets_create_new\n"
    "  - User: 'auth into google sheets' → YOU: call sheets_check_auth\n"
    "  - User: 'sync to sheets' → YOU: call sheets_sync_all\n"
    "  - User: 'what is the sheet URL?' → YOU: call sheets_get_url\n"
    "- The sheet contains: ID, Type, Name, Subtitle, Field1-4, Last Updated, and Raw Data columns.\n\n"
    "STRICT GROUNDING RULES:\n"
    "1) ONLY use shared state (items/globalTitle/globalDescription) as the source of truth.\n"
    "2) Before ANY read or write, assume values may have changed; always read the latest state.\n"
    "3) If a command doesn't specify which item to change, ask to clarify.\n"
)



# Create the base router directly
agentic_chat_router = get_ag_ui_workflow_router(
    llm=OpenAI(model="gpt-4.1"),
    # Provide frontend tool stubs so the model knows their names/signatures.
    frontend_tools=[
        createItem,
        deleteItem,
        setItemName,
        setItemSubtitleOrDescription,
        setGlobalTitle,
        setGlobalDescription,
        setNoteField1,
        appendNoteField1,
        clearNoteField1,
        setProjectField1,
        setProjectField2,
        setProjectField3,
        clearProjectField3,
        addProjectChecklistItem,
        setProjectChecklistItem,
        removeProjectChecklistItem,
        setEntityField1,
        setEntityField2,
        addEntityField3,
        removeEntityField3,
        addChartField1,
        setChartField1Label,
        setChartField1Value,
        clearChartField1Value,
        removeChartField1,
    ],
    backend_tools=[
        FunctionTool.from_defaults(fn=sheets_sync_all, name="sheets_sync_all"),
        FunctionTool.from_defaults(fn=sheets_get_url, name="sheets_get_url"),
        FunctionTool.from_defaults(fn=sheets_create_new, name="sheets_create_new"),
        FunctionTool.from_defaults(fn=sheets_check_auth, name="sheets_check_auth"),
    ],
    system_prompt=SYSTEM_PROMPT,
    initial_state={
        # Shared state synchronized with the frontend canvas
        "items": [],
        "globalTitle": "",
        "globalDescription": "",
        "lastAction": "",
        "itemsCreated": 0,
    },
)

# Initialize the global state
update_canvas_state({
    "items": [],
    "globalTitle": "",
    "globalDescription": "",
    "lastAction": "",
    "itemsCreated": 0,
})
