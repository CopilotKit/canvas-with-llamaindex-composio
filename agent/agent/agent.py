from typing import Annotated, List, Optional, Dict, Any
import json
import os
from dotenv import load_dotenv

from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from llama_index.protocols.ag_ui.events import StateSnapshotWorkflowEvent
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router

# Load environment variables early to support local development via .env
load_dotenv()

# Google Sheets tools (via Composio)
GOOGLE_SHEETS_TOOLS: List[str] = [
    "GOOGLESHEETS_ADD_SHEET",
    "GOOGLESHEETS_AGGREGATE_COLUMN_DATA",
    "GOOGLESHEETS_APPEND_DIMENSION",
    "GOOGLESHEETS_BATCH_GET",
    "GOOGLESHEETS_BATCH_UPDATE",
    "GOOGLESHEETS_BATCH_UPDATE_VALUES_BY_DATA_FILTER",
    "GOOGLESHEETS_CLEAR_BASIC_FILTER",
    "GOOGLESHEETS_CLEAR_VALUES",
    "GOOGLESHEETS_CREATE_CHART",
    "GOOGLESHEETS_CREATE_GOOGLE_SHEET1",
    "GOOGLESHEETS_CREATE_SPREADSHEET_COLUMN",
    "GOOGLESHEETS_CREATE_SPREADSHEET_ROW",
    "GOOGLESHEETS_DELETE_DIMENSION",
    "GOOGLESHEETS_DELETE_SHEET",
    "GOOGLESHEETS_EXECUTE_SQL",
    "GOOGLESHEETS_FIND_WORKSHEET_BY_TITLE",
    "GOOGLESHEETS_FORMAT_CELL",
    "GOOGLESHEETS_GET_SHEET_NAMES",
    "GOOGLESHEETS_GET_SPREADSHEET_BY_DATA_FILTER",
    "GOOGLESHEETS_GET_SPREADSHEET_INFO",
    "GOOGLESHEETS_GET_TABLE_SCHEMA",
    "GOOGLESHEETS_INSERT_DIMENSION",
    "GOOGLESHEETS_LIST_TABLES",
    "GOOGLESHEETS_LOOKUP_SPREADSHEET_ROW",
    "GOOGLESHEETS_QUERY_TABLE",
    "GOOGLESHEETS_SEARCH_DEVELOPER_METADATA",
    "GOOGLESHEETS_SEARCH_SPREADSHEETS",
    "GOOGLESHEETS_SET_BASIC_FILTER",
    "GOOGLESHEETS_SHEET_FROM_JSON",
    "GOOGLESHEETS_SPREADSHEETS_SHEETS_COPY_TO",
    "GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
    "GOOGLESHEETS_SPREADSHEETS_VALUES_BATCH_CLEAR",
    "GOOGLESHEETS_SPREADSHEETS_VALUES_BATCH_CLEAR_BY_DATA_FILTER",
    "GOOGLESHEETS_SPREADSHEETS_VALUES_BATCH_GET_BY_DATA_FILTER",
    "GOOGLESHEETS_UPDATE_SHEET_PROPERTIES",
    "GOOGLESHEETS_UPDATE_SPREADSHEET_PROPERTIES",
]


def _load_composio_tools() -> List[Any]:
    """Load Composio Google Sheets tools (hardcoded) for use in the agent.

    Requires COMPOSIO_API_KEY to be configured. Uses COMPOSIO_USER_ID (defaults to
    "default") to scope the connected Google account.
    """
    try:
        from composio import Composio  # type: ignore
        from composio_llamaindex import LlamaIndexProvider  # type: ignore
    except Exception:
        return []

    user_id = os.getenv("COMPOSIO_USER_ID", "default")
    try:
        # First check if we have a connected Google Sheets account
        api_key = os.getenv("COMPOSIO_API_KEY", "").strip()
        auth_config_id = os.getenv("COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID", "").strip()
        if api_key and auth_config_id:
            # Use API client to check connections
            api_composio = Composio(api_key=api_key)
            result = api_composio.connected_accounts.list(auth_config_ids=[auth_config_id])  # type: ignore[attr-defined]
            # Access items property if it exists
            if hasattr(result, "items"):
                conns = result.items if result.items is not None else []
            elif isinstance(result, list):
                conns = result
            else:
                conns = []
            
            # Check for Google Sheets connection for this user
            # Since we're filtering by auth_config_id, these should all be Google Sheets connections
            has_google_sheets = False
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
                    
                    # Since we filtered by auth_config_id, this is a Google Sheets connection
                    has_google_sheets = True
                    break
            
            if not has_google_sheets:
                print("Warning: No Google Sheets connection found for user:", user_id)
                return []
        else:
            print("Warning: Missing COMPOSIO_API_KEY or COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID")
            return []
        
        # Load tools using the provider
        composio = Composio(provider=LlamaIndexProvider())
        tools = composio.tools.get(user_id=user_id, tools=GOOGLE_SHEETS_TOOLS)
        return list(tools) if tools is not None else []
    except Exception as e:
        print(f"Warning: Failed to load Composio tools: {e}")
        return []


def _get_composio_client():
    try:
        from composio import Composio  # type: ignore
        from composio_llamaindex import LlamaIndexProvider  # type: ignore
    except Exception as e:
        raise RuntimeError("Composio is not installed") from e
    composio = Composio(provider=LlamaIndexProvider())
    user_id = os.getenv("COMPOSIO_USER_ID", "default")
    return composio, user_id


async def syncCanvasSnapshotToGoogleSheets(
    ctx: Context,
    spreadsheetTitle: Annotated[Optional[str], "Optional title for the spreadsheet."] = None,
    sheetTitle: Annotated[Optional[str], "Sheet/tab title to use (default 'Canvas')."] = None,
) -> str:
    """Clear the sheet and write the current Canvas snapshot as rows.

    Behavior:
    - Create spreadsheet if missing; reuse otherwise.
    - Ensure a sheet/tab exists (default 'Canvas').
    - Clear all values in the sheet.
    - Write a header row + one row per item (id, type, name, subtitle, data_json).
    Returns the spreadsheet URL.
    """
    composio, user_id = _get_composio_client()
    
    # Check if Google Sheets is connected before proceeding
    try:
        from composio import Composio  # type: ignore
        api_key = os.getenv("COMPOSIO_API_KEY", "").strip()
        auth_config_id = os.getenv("COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID", "").strip()
        if api_key and auth_config_id:
            api_composio = Composio(api_key=api_key)
            result = api_composio.connected_accounts.list(auth_config_ids=[auth_config_id])  # type: ignore[attr-defined]
            # Access items property if it exists
            if hasattr(result, "items"):
                conns = result.items if result.items is not None else []
            elif isinstance(result, list):
                conns = result
            else:
                conns = []
            
            # Since we're filtering by auth_config_id, these should all be Google Sheets connections
            has_google_sheets = False
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
                    
                    # Since we filtered by auth_config_id, this is a Google Sheets connection
                    has_google_sheets = True
                    break
            
            if not has_google_sheets:
                raise RuntimeError("Google Sheets is not connected. Please connect Google Sheets first through the UI.")
        else:
            raise RuntimeError("Missing COMPOSIO_API_KEY or COMPOSIO_GOOGLESHEETS_AUTH_CONFIG_ID environment variables.")
    except Exception as e:
        if "not connected" in str(e).lower() or "missing composio" in str(e).lower():
            raise
        # If we can't check, proceed anyway and let the actual API call fail if needed
        pass
    
    title = (spreadsheetTitle or "AG-UI Canvas Snapshot").strip() or "AG-UI Canvas Snapshot"
    tab = (sheetTitle or "Canvas").strip() or "Canvas"

    # Persist spreadsheet metadata across calls in a side-channel store
    async with ctx.store.edit_state() as global_state:
        meta = global_state.get("googleSheets", {}) or {}

        spreadsheet_id = meta.get("spreadsheetId")
        # Create spreadsheet if missing
        if not spreadsheet_id:
            try:
                created = composio.tools.execute(
                    user_id=user_id,
                    tool="GOOGLESHEETS_CREATE_GOOGLE_SHEET1",
                    parameters={
                        "title": title,
                    },
                )
                # Try common shapes for result
                spreadsheet_id = (
                    created.get("response_data", {}).get("spreadsheetId")
                    or created.get("data", {}).get("spreadsheetId")
                    or created.get("spreadsheetId")
                )
            except Exception:
                spreadsheet_id = None

            if not spreadsheet_id:
                raise RuntimeError("Failed to create Google Spreadsheet. Please ensure Google Sheets is connected in Composio.")

            meta["spreadsheetId"] = spreadsheet_id
            meta["sheetTitle"] = tab
            global_state["googleSheets"] = meta

        # Ensure sheet/tab exists (create if missing)
        try:
            found = composio.tools.execute(
                user_id=user_id,
                tool="GOOGLESHEETS_FIND_WORKSHEET_BY_TITLE",
                parameters={
                    "spreadsheetId": spreadsheet_id,
                    "title": tab,
                },
            )
            # If not found, add sheet
            not_found = False
            if isinstance(found, dict):
                ok = (
                    found.get("response_data", {}).get("found", True)
                    or found.get("data", {}).get("found", True)
                )
                not_found = not ok
            if not_found:
                composio.tools.execute(
                    user_id=user_id,
                    tool="GOOGLESHEETS_ADD_SHEET",
                    parameters={
                        "spreadsheetId": spreadsheet_id,
                        "title": tab,
                    },
                )
        except Exception:
            # Best-effort: attempt to add the sheet
            composio.tools.execute(
                user_id=user_id,
                tool="GOOGLESHEETS_ADD_SHEET",
                parameters={
                    "spreadsheetId": spreadsheet_id,
                    "title": tab,
                },
            )

        # Read latest state snapshot
        state = await ctx.get("state", default={})
        items: List[Dict[str, Any]] = list(state.get("items", []) or [])

        # Build header + rows
        header = ["id", "type", "name", "subtitle", "data_json"]
        rows: List[List[str]] = [header]
        for it in items:
            data_json = json.dumps(it.get("data", {}), ensure_ascii=False)
            rows.append([
                str(it.get("id", "")),
                str(it.get("type", "")),
                str(it.get("name", "")),
                str(it.get("subtitle", "")),
                data_json,
            ])

        # Clear full sheet and write values anew
        try:
            composio.tools.execute(
                user_id=user_id,
                tool="GOOGLESHEETS_SPREADSHEETS_VALUES_BATCH_CLEAR",
                parameters={
                    "spreadsheetId": spreadsheet_id,
                    "ranges": [f"{tab}!A:ZZ"],
                },
            )
        except Exception:
            # Fallback clear values on a generous range
            composio.tools.execute(
                user_id=user_id,
                tool="GOOGLESHEETS_CLEAR_VALUES",
                parameters={
                    "spreadsheetId": spreadsheet_id,
                    "range": f"{tab}!A:ZZ",
                },
            )

        # Append all rows starting at A1
        composio.tools.execute(
            user_id=user_id,
            tool="GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
            parameters={
                "spreadsheetId": spreadsheet_id,
                "range": f"{tab}!A1",
                "valueInputOption": "RAW",
                "values": rows,
            },
        )

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"


# --- Backend tools (server-side) ---


# --- Frontend tool stubs (names/signatures only; execution happens in the UI) ---

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
    "You are a helpful AG-UI assistant.\n\n"
    + FIELD_SCHEMA +
    "\nMUTATION/TOOL POLICY:\n"
    "- When you claim to create/update/delete, you MUST call the corresponding tool(s) (frontend or backend).\n"
    "- To create new cards, call the frontend tool `createItem` with `type` in {project, entity, note, chart} and optional `name`.\n"
    "- After tools run, rely on the latest shared state (ground truth) when replying.\n"
    "- To set a card's subtitle (never the data fields): use setItemSubtitleOrDescription.\n\n"
    "DESCRIPTION MAPPING:\n"
    "- For project/entity/chart: treat 'description', 'overview', 'summary', 'caption', 'blurb' as the card subtitle; use setItemSubtitleOrDescription.\n"
    "- For notes: 'content', 'description', 'text', or 'note' refers to note content; use setNoteField1 / appendNoteField1 / clearNoteField1.\n\n"
    "STRICT GROUNDING RULES:\n"
    "1) ONLY use shared state (items/globalTitle/globalDescription) as the source of truth.\n"
    "2) Before ANY read or write, assume values may have changed; always read the latest state.\n"
    "3) If a command doesn't specify which item to change, ask to clarify.\n"
    "\nGOOGLE SHEETS SNAPSHOT SYNC POLICY:\n"
    "- Maintain a single Google Spreadsheet per session to mirror the current Canvas state.\n"
    "- If no spreadsheet exists yet, create one (e.g., name: 'AG-UI Canvas Snapshot').\n"
    "- Prefer a sheet/tab named 'Canvas'; create it if missing.\n"
    "- On each new state snapshot, CLEAR the sheet content, then WRITE a full snapshot:\n"
    "  - Recommended actions: GOOGLESHEETS_SPREADSHEETS_VALUES_BATCH_CLEAR (to clear)\n"
    "    followed by GOOGLESHEETS_SHEET_FROM_JSON (to populate from JSON).\n"
    "  - If SHEET_FROM_JSON is unavailable, write a header row + rows via GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND starting at A1.\n"
    "- Columns should include: id, type, name, subtitle, and a JSON string of data.\n"
    "- If the spreadsheet was deleted externally, create a new one and continue.\n"
)

_backend_tools = _load_composio_tools()

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
    backend_tools=_backend_tools + [syncCanvasSnapshotToGoogleSheets],
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
