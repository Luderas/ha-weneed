"""WeNeed TodoList entity for Home Assistant."""

from datetime import timedelta
import logging
from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import WeNeedApi
from .const import DOMAIN, CONF_LIST_ID, CONF_LIST_NAME, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

# Poll WeNeed every 20 seconds for external changes (e.g. from the mobile app)
SCAN_INTERVAL = timedelta(seconds=20)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WeNeed Todo platform from a config entry."""
    api: WeNeedApi = hass.data[DOMAIN][entry.entry_id]
    list_id = entry.data[CONF_LIST_ID]
    list_name = entry.data.get(CONF_LIST_NAME, DEFAULT_NAME)

    entity = WeNeedTodoListEntity(hass, api, list_id, list_name)
    async_add_entities([entity], update_before_add=True)


class WeNeedTodoListEntity(TodoListEntity):
    """Representation of a WeNeed Shopping List."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(
        self,
        hass: HomeAssistant,
        api: WeNeedApi,
        list_id: str,
        name: str,
    ) -> None:
        """Initialize the WeNeed entity."""
        self.hass = hass
        self._api = api
        self._list_id = list_id
        self._attr_name = name
        self._attr_unique_id = f"weneed_{list_id}"
        self._todo_items: list[TodoItem] = []

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return the items on the shopping list."""
        return self._todo_items

    async def async_update(self) -> None:
        """Fetch items from WeNeed API."""
        try:
            items_data = await self.hass.async_add_executor_job(self._api.get_items)
            self._todo_items = [
                TodoItem(
                    uid=item["uid"],
                    summary=item["name"],
                    status=(
                        TodoItemStatus.COMPLETED
                        if item["checked"]
                        else TodoItemStatus.NEEDS_ACTION
                    ),
                )
                for item in items_data
            ]
        except Exception as err:
            _LOGGER.error("Error updating WeNeed list: %s", err)

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new item on the WeNeed list with fast optimistic response."""
        item_id = await self.hass.async_add_executor_job(self._api.add_item, item.summary)
        # Optimistically add item to local state for instant voice/UI response
        self._todo_items.append(
            TodoItem(
                uid=item_id,
                summary=item.summary,
                status=TodoItemStatus.NEEDS_ACTION,
            )
        )
        self.async_write_ha_state()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item status (check / uncheck) with optimistic response."""
        # Optimistic update in memory
        for idx, existing in enumerate(self._todo_items):
            if existing.uid == item.uid:
                self._todo_items[idx] = item
                break
        self.async_write_ha_state()

        is_completed = item.status == TodoItemStatus.COMPLETED
        await self.hass.async_add_executor_job(
            self._api.update_item_status, item.uid, is_completed
        )

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete items permanently with optimistic response."""
        # Optimistic deletion in memory
        self._todo_items = [
            item for item in self._todo_items if item.uid not in uids
        ]
        self.async_write_ha_state()

        for uid in uids:
            await self.hass.async_add_executor_job(self._api.delete_item, uid)
