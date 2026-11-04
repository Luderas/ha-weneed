"""The WeNeed Shopping List integration."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import WeNeedApi
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD, CONF_LIST_ID

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.TODO]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the component from YAML (not used if config flow is used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WeNeed from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api = WeNeedApi(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        list_id=entry.data[CONF_LIST_ID],
    )

    hass.data[DOMAIN][entry.entry_id] = api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
