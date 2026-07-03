"""Config flow for Garage IR Tuya integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_COVER_NAME,
    CONF_OPEN_ENTITY,
    CONF_CLOSE_ENTITY,
    CONF_STOP_ENTITY,
    CONF_DURATION,
    CONF_FORCE_STATE,
    DEFAULT_NAME,
    DEFAULT_DURATION,
    FORCE_STATE_NO_CHANGE,
    FORCE_STATE_OPEN,
    FORCE_STATE_CLOSED,
)

# Entity selector for scenes, scripts, and buttons
ENTITY_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["scene", "script", "button"])
)

ENTITY_SELECTOR_OPTIONAL = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["scene", "script", "button"])
)

DURATION_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=5, max=120, step=1, unit_of_measurement="s", mode="slider"
    )
)


def _build_setup_schema(
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    """Build the schema for initial setup."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_COVER_NAME,
                default=defaults.get(CONF_COVER_NAME, DEFAULT_NAME),
            ): selector.TextSelector(),
            vol.Required(
                CONF_OPEN_ENTITY,
                default=defaults.get(CONF_OPEN_ENTITY),
            ): ENTITY_SELECTOR,
            vol.Required(
                CONF_CLOSE_ENTITY,
                default=defaults.get(CONF_CLOSE_ENTITY),
            ): ENTITY_SELECTOR,
            vol.Optional(
                CONF_STOP_ENTITY,
                description={"suggested_value": defaults.get(CONF_STOP_ENTITY)},
            ): ENTITY_SELECTOR_OPTIONAL,
            vol.Required(
                CONF_DURATION,
                default=defaults.get(CONF_DURATION, DEFAULT_DURATION),
            ): DURATION_SELECTOR,
        }
    )


def _build_options_schema(
    current: dict[str, Any],
) -> vol.Schema:
    """Build the schema for options flow (same fields + force state)."""
    return vol.Schema(
        {
            vol.Required(
                CONF_OPEN_ENTITY,
                default=current.get(CONF_OPEN_ENTITY),
            ): ENTITY_SELECTOR,
            vol.Required(
                CONF_CLOSE_ENTITY,
                default=current.get(CONF_CLOSE_ENTITY),
            ): ENTITY_SELECTOR,
            vol.Optional(
                CONF_STOP_ENTITY,
                description={"suggested_value": current.get(CONF_STOP_ENTITY)},
            ): ENTITY_SELECTOR_OPTIONAL,
            vol.Required(
                CONF_DURATION,
                default=current.get(CONF_DURATION, DEFAULT_DURATION),
            ): DURATION_SELECTOR,
            vol.Required(
                CONF_FORCE_STATE,
                default=FORCE_STATE_NO_CHANGE,
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=FORCE_STATE_NO_CHANGE,
                            label="no_change",
                        ),
                        selector.SelectOptionDict(
                            value=FORCE_STATE_OPEN,
                            label="open",
                        ),
                        selector.SelectOptionDict(
                            value=FORCE_STATE_CLOSED,
                            label="closed",
                        ),
                    ],
                    translation_key=CONF_FORCE_STATE,
                    mode="dropdown",
                )
            ),
        }
    )


class GarageIRTuyaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Garage IR Tuya."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step — configure the garage door."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate that open and close entities are different
            if user_input[CONF_OPEN_ENTITY] == user_input[CONF_CLOSE_ENTITY]:
                errors["base"] = "same_entity"
            else:
                # Use the cover name as the entry title
                title = user_input.get(CONF_COVER_NAME, DEFAULT_NAME)
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_setup_schema(),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> GarageIRTuyaOptionsFlow:
        """Get the options flow handler."""
        return GarageIRTuyaOptionsFlow(config_entry)


class GarageIRTuyaOptionsFlow(OptionsFlow):
    """Handle options flow for Garage IR Tuya."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options — modify entities, duration, or force state."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input[CONF_OPEN_ENTITY] == user_input[CONF_CLOSE_ENTITY]:
                errors["base"] = "same_entity"
            else:
                return self.async_create_entry(title="", data=user_input)

        # Merge data and options for current values
        current = {**self._config_entry.data, **self._config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=_build_options_schema(current),
            errors=errors,
        )
