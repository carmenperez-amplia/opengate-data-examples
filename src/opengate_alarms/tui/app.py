from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Button, ListView, ListItem, Label, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical

from textual.screen import Screen
from textual import on
from typing import Any, List, Optional
import asyncio
from datetime import datetime

from ..client import OpenGateAlarmClient
from ..og_data import OpenGateDataHelper
from ..models import Alarm, SearchRequest
import json
import os
import logging
from pathlib import Path


logger = logging.getLogger("opengate_alarms.tui")



class AlarmDetailScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def __init__(self, alarm: Alarm):
        super().__init__()
        self.alarm = alarm

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"ID: {self.alarm.id}"),
            Static(f"Entity: {self.alarm.entity_id}"),
            Static(f"Name: {self.alarm.name}"),
            Static(f"Severity: {self.alarm.severity}"),
            Static(f"Status: {self.alarm.status}"),
            Static(f"Date: {self.alarm.creation_date}"),
            Static(f"Rule: {self.alarm.rule or 'N/A'}"),
            Static(f"Description: {self.alarm.description or 'No description'}"),
            classes="detail-container"
        )
        yield Footer()

class OpenGateApp(App):
    CSS = """
    .detail-container {
        padding: 1 2;
        border: solid green;
    }
    DataTable {
        height: 1fr;
        width: 1fr;
    }
    #sidebar-alarms, #sidebar-entities {
        width: 30;
        height: 1fr;
        border-right: solid green;
        padding: 1;
    }
    .sidebar-title {
        text-align: center;
        background: green;
        color: white;
        margin-bottom: 1;
    }
    TabbedContent {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.client = OpenGateAlarmClient()
        self.entities_helper = OpenGateDataHelper()
        # Mock mode if no API key
        self.mock_mode = not self.client.api_key

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Alarms", id="alarms-tab"):
                with Horizontal():
                    with Vertical(id="sidebar-alarms"):
                        yield Label("ALARM FILTERS", classes="sidebar-title")
                        yield ListView(id="alarm-filter-list")
                    yield DataTable(id="alarms-table")
            with TabPane("Entities", id="entities-tab"):
                with Horizontal():
                    with Vertical(id="sidebar-entities"):
                        yield Label("ENTITY FILTERS", classes="sidebar-title")
                        yield ListView(id="entity-filter-list")
                    yield DataTable(id="entities-table")
        yield Footer()



    async def on_mount(self) -> None:
        # Initialize Alarm table
        alarm_table = self.query_one("#alarms-table", DataTable)
        alarm_table.add_columns("ID", "Entity", "Name", "Severity", "Status", "Date")
        alarm_table.cursor_type = "row"
        
        # Initialize Entity table
        entity_table = self.query_one("#entities-table", DataTable)
        entity_table.cursor_type = "row"

        await self.load_all_filters()
        await self.refresh_alarms()
        await self.refresh_entities()

    async def load_all_filters(self) -> None:
        from ..filters import ALARM_FILTERS, ENTITY_FILTERS
        await self.load_filters_into_list("#alarm-filter-list", list(ALARM_FILTERS.keys()))
        await self.load_filters_into_list("#entity-filter-list", list(ENTITY_FILTERS.keys()))

    async def load_filters_into_list(self, list_id: str, keys: List[str]) -> None:
        filter_list = self.query_one(list_id, ListView)
            
        await filter_list.clear()
        
        for k in sorted(keys):
            item = ListItem(Label(k), id=k)
            await filter_list.append(item)
        
        if keys:
            filter_list.index = 0

    @on(ListView.Selected)
    async def on_filter_selected(self, event: ListView.Selected) -> None:
        if not event.item or not event.item.id:
            return
            
        filter_key = event.item.id
        # Determine which list triggered the event
        if event.list_view.id == "alarm-filter-list":
            await self.refresh_alarms(filter_key=filter_key)
        elif event.list_view.id == "entity-filter-list":
            await self.refresh_entities(filter_key=filter_key)

    async def action_refresh(self) -> None:
        # Determine active tab
        tabbed_content = self.query_one(TabbedContent)
        active_tab = tabbed_content.active
        
        if active_tab == "alarms-tab":
            filter_list = self.query_one("#alarm-filter-list", ListView)
            if filter_list.index is not None:
                filter_key = filter_list.children[filter_list.index].id
                await self.refresh_alarms(filter_key=filter_key)
            else:
                await self.refresh_alarms()
        elif active_tab == "entities-tab":
            filter_list = self.query_one("#entity-filter-list", ListView)
            if filter_list.index is not None:
                filter_key = filter_list.children[filter_list.index].id
                await self.refresh_entities(filter_key=filter_key)
            else:
                await self.refresh_entities()

    async def refresh_alarms(self, filter_key: Optional[str] = None) -> None:
        from ..filters import ALARM_FILTERS
        table = self.query_one("#alarms-table", DataTable)
        table.clear()
        
        search_req = SearchRequest()
        if filter_key and filter_key in ALARM_FILTERS:
            try:
                filter_data = ALARM_FILTERS[filter_key]
                logger.info(f"Loaded alarm filter {filter_key}: {filter_data}")
                if "filter" in filter_data:
                    search_req.filter = filter_data["filter"]
                elif filter_data:
                    search_req.filter = filter_data
            except Exception as e:
                logger.error(f"Error loading alarm filter {filter_key}: {e}")
                self.notify(f"Error loading alarm filter {filter_key}: {e}", severity="error")

        if self.mock_mode:
            alarms = [
                Alarm(id="AL-001", entity_id="DEV-01", name="Mock Alarm", severity="CRITICAL", status="OPEN", creation_date=datetime.now())
            ]
        else:
            try:
                alarms = await self.client.query_alarms(search_req)
            except Exception as e:
                logger.error(f"Error loading alarms: {e}")
                self.notify(f"Error loading alarms: {e}", severity="error")
                return

        for alarm in alarms:
            table.add_row(alarm.id, alarm.entity_id, alarm.name, alarm.severity, alarm.status, str(alarm.creation_date))

    async def refresh_entities(self, filter_key: Optional[str] = None) -> None:
        from ..filters import ENTITY_FILTERS
        table = self.query_one("#entities-table", DataTable)
        table.clear()
        
        search_req = {
            "limit": {"size": 25, "start": 1}
        }
        # Default column mapping: list of (Header, DataPath)
        column_map = [("ID", ["id"]), ("NAME", ["name"]), ("TYPE", ["resourceType"])]
        
        if filter_key and filter_key in ENTITY_FILTERS:
            try:
                filter_data = ENTITY_FILTERS[filter_key]
                logger.info(f"Loaded entity filter {filter_key}: {filter_data}")
                search_req = filter_data
                if "select" in filter_data:
                    column_map = self.parse_complex_select(filter_data["select"])
            except Exception as e:
                logger.error(f"Error loading entity filter {filter_key}: {e}")
                self.notify(f"Error loading entity filter {filter_key}: {e}", severity="error")

        # Update columns dynamically
        table.clear(columns=True)
        table.add_columns(*[col[0].upper() for col in column_map])

        try:
            entities = await asyncio.to_thread(self.entities_helper.search_entities, search_req)
            for entity in entities:
                row = []
                for header, path in column_map:
                    val = self.get_nested_value(entity, path)
                    row.append(str(val) if val is not None else "N/A")
                table.add_row(*row)
        except Exception as e:
            logger.error(f"Error loading entities: {e}")
            self.notify(f"Error loading entities: {e}", severity="error")

    def parse_complex_select(self, select_list: List[Any]) -> List[tuple]:
        """Parse complex select structure into (Header, DataPath) pairs."""
        columns = []
        for item in select_list:
            if isinstance(item, str):
                columns.append((item, item.split(".")))
            elif isinstance(item, dict):
                base_name = item.get("name", "")
                base_path = base_name.replace("[]", "").split(".")
                fields = item.get("fields", [])
                if not fields:
                    columns.append((base_name, base_path))
                else:
                    for f in fields:
                        field_path = f.get("field", "").split(".")
                        alias = f.get("alias", f.get("field", base_name))
                        columns.append((alias, base_path + field_path))
        return columns

    def get_nested_value(self, data: Any, path: List[str]) -> Any:
        """Navigate nested dictionary/list using path, handling OpenGate structures."""
        current = data
        for i, part in enumerate(path):
            if current is None:
                return None
            
            if isinstance(current, dict):
                # 1. Try direct match
                if part in current:
                    current = current[part]
                # 2. Skip 'provision' at start if missing
                elif i == 0 and part == "provision":
                    continue
                # 3. Handle 'current' or '_current' wrapper
                elif "current" in current and isinstance(current["current"], dict) and part in current["current"]:
                    current = current["current"][part]
                elif "_current" in current and isinstance(current["_current"], dict) and part in current["_current"]:
                    current = current["_current"][part]
                else:
                    return None
            elif isinstance(current, list) and current:
                # Take first element and re-try the same part if it's the root or continue
                current = current[0]
                # If after taking first element we are in a dict, we still need to find 'part'
                if isinstance(current, dict):
                    if part in current:
                        current = current[part]
                    elif "current" in current and isinstance(current["current"], dict) and part in current["current"]:
                        current = current["current"][part]
                    elif "_current" in current and isinstance(current["_current"], dict) and part in current["_current"]:
                        current = current["_current"][part]
                    else:
                        return None
            else:
                return None
        return current


    @on(DataTable.RowSelected)
    async def on_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "alarms-table":
            return
            
        row_key = event.row_key
        row_values = self.query_one("#alarms-table", DataTable).get_row(row_key)
        
        alarm = Alarm(
            id=row_values[0],
            entity_id=row_values[1],
            name=row_values[2],
            severity=row_values[3],
            status=row_values[4],
            creation_date=datetime.fromisoformat(row_values[5]) if isinstance(row_values[5], str) else row_values[5]
        )
        self.push_screen(AlarmDetailScreen(alarm))



def run():
    app = OpenGateApp()
    app.run()

if __name__ == "__main__":
    run()

