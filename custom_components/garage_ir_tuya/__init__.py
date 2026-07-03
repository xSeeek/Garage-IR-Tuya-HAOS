"""The Garage IR Tuya integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, CONF_FORCE_STATE, FORCE_STATE_NO_CHANGE

_LOGGER = logging.getLogger(__name__)

type GarageIRTuyaConfigEntry = ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant, entry: GarageIRTuyaConfigEntry
) -> bool:
    """Set up Garage IR Tuya from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def _async_update_options(
    hass: HomeAssistant, entry: GarageIRTuyaConfigEntry
) -> None:
    """Handle options update — applies force_state if set, then reloads."""
    force_state = entry.options.get(CONF_FORCE_STATE, FORCE_STATE_NO_CHANGE)

    if force_state != FORCE_STATE_NO_CHANGE:
        # Store the forced state for the cover to pick up after reload
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][f"{entry.entry_id}_force_state"] = force_state

        # Remove force_state from options so it doesn't re-apply on future reloads
        new_options = {
            k: v for k, v in entry.options.items() if k != CONF_FORCE_STATE
        }
        hass.config_entries.async_update_entry(entry, options=new_options)

        _LOGGER.info(
            "Garage IR Tuya: Forcing state to '%s' for entry %s",
            force_state,
            entry.entry_id,
        )

    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: GarageIRTuyaConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
