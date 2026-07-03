"""Constants for the Garage IR Tuya integration."""

DOMAIN = "garage_ir_tuya"
PLATFORMS = ["cover"]

# --- Configuration Keys ---
CONF_COVER_NAME = "name"
CONF_OPEN_ENTITY = "open_entity"
CONF_CLOSE_ENTITY = "close_entity"
CONF_STOP_ENTITY = "stop_entity"
CONF_DURATION = "duration"
CONF_FORCE_STATE = "force_state"

# --- Defaults ---
DEFAULT_NAME = "Puerta del Garage"
DEFAULT_DURATION = 15  # seconds

# --- Safeguard ---
SAFEGUARD_DELAY = 2  # seconds between double-press

# --- Force State Options ---
FORCE_STATE_NO_CHANGE = "no_change"
FORCE_STATE_OPEN = "open"
FORCE_STATE_CLOSED = "closed"
