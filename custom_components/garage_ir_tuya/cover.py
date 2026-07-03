"""Cover platform for Garage IR Tuya integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_COVER_NAME,
    CONF_OPEN_ENTITY,
    CONF_CLOSE_ENTITY,
    CONF_STOP_ENTITY,
    CONF_DURATION,
    DEFAULT_DURATION,
    DEFAULT_NAME,
    SAFEGUARD_DELAY,
    FORCE_STATE_OPEN,
)

_LOGGER = logging.getLogger(__name__)

# Cover states (using string literals to match HA convention)
STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_OPENING = "opening"
STATE_CLOSING = "closing"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Garage IR Tuya cover from a config entry."""
    async_add_entities([GarageIRTuyaCover(hass, entry)])


class GarageIRTuyaCover(CoverEntity, RestoreEntity):
    """A garage door cover controlled via Tuya IR/RF scenes.

    Features:
    - Safeguard double-press: When interrupting a movement (e.g., closing
      while opening), sends the command twice with a delay to handle
      the motor's stop-then-act behavior.
    - Timer-based state: Tracks state using a timer since there's no
      physical sensor. After the configured duration, the state
      transitions from opening→open or closing→closed.
    - RestoreEntity: Persists state across HA restarts. Transitional
      states (opening/closing) are resolved to their target state.
    - Force State: Supports overriding the current state from the
      options flow when the state gets out of sync.
    """

    _attr_device_class = CoverDeviceClass.GARAGE
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the cover."""
        self._entry = entry
        self._hass = hass

        # Unique ID and name
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_name = self._get_config(CONF_COVER_NAME, DEFAULT_NAME)

        # Configuration — options take precedence over data
        self._open_entity: str = self._get_config(CONF_OPEN_ENTITY)
        self._close_entity: str = self._get_config(CONF_CLOSE_ENTITY)
        self._stop_entity: str | None = self._get_config(CONF_STOP_ENTITY)
        self._duration: int = self._get_config(CONF_DURATION, DEFAULT_DURATION)

        # Internal state
        self._state: str = STATE_CLOSED
        self._timer_unsub: callback | None = None

        # Supported features
        features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        if self._stop_entity:
            features |= CoverEntityFeature.STOP
        self._attr_supported_features = features

        # Device info — groups the cover under a device in HA UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": self._get_config(CONF_COVER_NAME, DEFAULT_NAME),
            "manufacturer": "Tuya (IR/RF Bridge)",
            "model": "Garage Door Controller",
            "sw_version": "1.0.0",
        }

    def _get_config(self, key: str, default: any = None) -> any:
        """Get a config value, preferring options over data."""
        return self._entry.options.get(key, self._entry.data.get(key, default))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Restore state on startup or apply forced state."""
        await super().async_added_to_hass()

        # Check for a forced state (set via options flow)
        force_key = f"{self._entry.entry_id}_force_state"
        domain_data = self._hass.data.get(DOMAIN, {})
        forced = domain_data.pop(force_key, None)

        if forced:
            self._state = STATE_OPEN if forced == FORCE_STATE_OPEN else STATE_CLOSED
            _LOGGER.info(
                "Garage IR Tuya: State forced to '%s'", self._state
            )
            return

        # Normal restore from last known state
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in (
            STATE_OPEN,
            STATE_CLOSED,
            STATE_OPENING,
            STATE_CLOSING,
        ):
            # If HA restarted mid-movement, assume the movement completed
            if last_state.state == STATE_OPENING:
                self._state = STATE_OPEN
            elif last_state.state == STATE_CLOSING:
                self._state = STATE_CLOSED
            else:
                self._state = last_state.state

            _LOGGER.debug(
                "Garage IR Tuya: Restored state to '%s' (was '%s')",
                self._state,
                last_state.state,
            )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up timer on removal."""
        self._cancel_timer()

    # ------------------------------------------------------------------
    # State properties
    # ------------------------------------------------------------------

    @property
    def is_closed(self) -> bool | None:
        """Return True if the cover is closed."""
        if self._state == STATE_CLOSED:
            return True
        if self._state == STATE_OPEN:
            return False
        # During transition, state is unknown
        return None

    @property
    def is_opening(self) -> bool:
        """Return True if the cover is opening."""
        return self._state == STATE_OPENING

    @property
    def is_closing(self) -> bool:
        """Return True if the cover is closing."""
        return self._state == STATE_CLOSING

    # ------------------------------------------------------------------
    # Cover actions
    # ------------------------------------------------------------------

    async def async_open_cover(self, **kwargs) -> None:
        """Open the garage door.

        If the door is currently closing, applies the safeguard:
        sends open twice with a delay (first to stop, second to open).
        """
        if self._state in (STATE_OPEN, STATE_OPENING):
            _LOGGER.debug("Garage IR Tuya: Already open/opening, ignoring")
            return

        if self._state == STATE_CLOSING:
            # Safeguard: door is closing → stop it, then open
            _LOGGER.info("Garage IR Tuya: Safeguard — interrupting close to open")
            await self._activate_entity(self._open_entity)
            await asyncio.sleep(SAFEGUARD_DELAY)
            await self._activate_entity(self._open_entity)
        else:
            # Normal open from closed state
            await self._activate_entity(self._open_entity)

        self._state = STATE_OPENING
        self._start_timer(STATE_OPEN)
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs) -> None:
        """Close the garage door.

        If the door is currently opening, applies the safeguard:
        sends close twice with a delay (first to stop, second to close).
        """
        if self._state in (STATE_CLOSED, STATE_CLOSING):
            _LOGGER.debug("Garage IR Tuya: Already closed/closing, ignoring")
            return

        if self._state == STATE_OPENING:
            # Safeguard: door is opening → stop it, then close
            _LOGGER.info("Garage IR Tuya: Safeguard — interrupting open to close")
            await self._activate_entity(self._close_entity)
            await asyncio.sleep(SAFEGUARD_DELAY)
            await self._activate_entity(self._close_entity)
        else:
            # Normal close from open state
            await self._activate_entity(self._close_entity)

        self._state = STATE_CLOSING
        self._start_timer(STATE_CLOSED)
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs) -> None:
        """Stop the garage door movement.

        Sends the opposite command to halt movement. If a dedicated
        stop entity is configured, uses that instead.
        The state is set to 'open' since the door is partially open.
        """
        if self._state not in (STATE_OPENING, STATE_CLOSING):
            _LOGGER.debug("Garage IR Tuya: Not moving, nothing to stop")
            return

        if self._stop_entity:
            # Use dedicated stop entity
            await self._activate_entity(self._stop_entity)
        elif self._state == STATE_OPENING:
            # Send close to stop opening
            await self._activate_entity(self._close_entity)
        else:
            # Send open to stop closing
            await self._activate_entity(self._open_entity)

        self._cancel_timer()
        self._state = STATE_OPEN  # Partially open
        self.async_write_ha_state()

        _LOGGER.info("Garage IR Tuya: Movement stopped, state set to 'open'")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _activate_entity(self, entity_id: str) -> None:
        """Activate a scene, script, or button entity."""
        domain = entity_id.split(".")[0]

        if domain == "scene":
            await self._hass.services.async_call(
                "scene", "turn_on", {"entity_id": entity_id}
            )
        elif domain == "script":
            await self._hass.services.async_call(
                "script", "turn_on", {"entity_id": entity_id}
            )
        elif domain == "button":
            await self._hass.services.async_call(
                "button", "press", {"entity_id": entity_id}
            )
        else:
            # Fallback: generic activation
            await self._hass.services.async_call(
                "homeassistant", "turn_on", {"entity_id": entity_id}
            )

        _LOGGER.debug("Garage IR Tuya: Activated entity '%s'", entity_id)

    def _cancel_timer(self) -> None:
        """Cancel the movement completion timer."""
        if self._timer_unsub is not None:
            self._timer_unsub()
            self._timer_unsub = None

    def _start_timer(self, target_state: str) -> None:
        """Start a timer that transitions to target_state when it expires."""
        self._cancel_timer()

        @callback
        def _timer_finished(_now) -> None:
            """Handle timer expiration — movement is complete."""
            self._state = target_state
            self._timer_unsub = None
            self.async_write_ha_state()
            _LOGGER.info(
                "Garage IR Tuya: Movement complete, state is now '%s'",
                target_state,
            )

        self._timer_unsub = async_call_later(
            self._hass, self._duration, _timer_finished
        )

        _LOGGER.debug(
            "Garage IR Tuya: Timer started — %ds until '%s'",
            self._duration,
            target_state,
        )
