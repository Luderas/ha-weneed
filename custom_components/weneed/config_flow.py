"""Config flow for WeNeed integration."""

import logging
import voluptuous as vol

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .api import WeNeedApi
from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_LIST_ID,
    CONF_LIST_NAME,
)

_LOGGER = logging.getLogger(__name__)

STEP_AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


class WeNeedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WeNeed."""

    VERSION = 1

    def __init__(self):
        self._email = None
        self._password = None
        self._available_lists = []

    async def async_step_user(self, user_input=None):
        """Handle the initial authentication step."""
        errors = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]

            api = WeNeedApi(self._email, self._password)
            try:
                await self.hass.async_add_executor_job(api.authenticate)
                self._available_lists = await self.hass.async_add_executor_job(
                    api.get_shopping_lists
                )
            except Exception as err:
                _LOGGER.error("Failed to authenticate with WeNeed: %s", err)
                errors["base"] = "invalid_auth"
            else:
                if len(self._available_lists) == 1:
                    # Exactly one list found, configure automatically
                    single_list = self._available_lists[0]
                    list_id = single_list["id"]
                    list_name = single_list["name"]
                    await self.async_set_unique_id(f"weneed_{list_id}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=list_name,
                        data={
                            CONF_EMAIL: self._email,
                            CONF_PASSWORD: self._password,
                            CONF_LIST_ID: list_id,
                            CONF_LIST_NAME: list_name,
                        },
                    )
                # Show list selection step
                return await self.async_step_select_list()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_AUTH_SCHEMA,
            errors=errors,
        )

    async def async_step_select_list(self, user_input=None):
        """Handle selecting from discovered lists or entering ID manually."""
        errors = {}

        if user_input is not None:
            list_id = user_input[CONF_LIST_ID]
            list_name = user_input.get(CONF_LIST_NAME, "Einkaufsliste")

            # If user selected from dropdown, look up the list name
            for item in self._available_lists:
                if item["id"] == list_id:
                    list_name = item["name"]
                    break

            await self.async_set_unique_id(f"weneed_{list_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=list_name,
                data={
                    CONF_EMAIL: self._email,
                    CONF_PASSWORD: self._password,
                    CONF_LIST_ID: list_id,
                    CONF_LIST_NAME: list_name,
                },
            )

        if self._available_lists:
            # Build dropdown options
            options = {
                item["id"]: f"{item['name']} ({item['item_count']} Artikel)"
                for item in self._available_lists
            }
            schema = vol.Schema(
                {
                    vol.Required(CONF_LIST_ID): vol.In(options),
                }
            )
        else:
            # Fallback to manual entry if no lists were discovered
            schema = vol.Schema(
                {
                    vol.Required(CONF_LIST_ID): cv.string,
                    vol.Optional(CONF_LIST_NAME, default="Einkaufsliste"): cv.string,
                }
            )

        return self.async_show_form(
            step_id="select_list",
            data_schema=schema,
            errors=errors,
        )
