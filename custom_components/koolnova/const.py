"""Constants for the Koolnova integration."""

from datetime import timedelta
from homeassistant.components.climate import (
    HVACMode,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO
)

DOMAIN = "koolnova"
PLATFORMS = ["climate", "binary_sensor", "switch", "sensor"]

# CONFIGURABLE: defaults and limits.
# IMPORTANT: Koolnova bans IPs automatically when the API is polled more than
# once every 30 seconds (confirmed by their support, see issue #4).
# Defaults favour a home install: 180 s between polls, with a full
# (projects+modules+hubs) refresh once every 20 cycles (~1/h). This keeps the
# cloud traffic low (~20+ requests/hour) while the zone temperatures stay
# fresh enough for a thermostat.
DEFAULT_UPDATE_INTERVAL = 180  # seconds
MIN_UPDATE_INTERVAL = 30      # configurable minimum (limit imposed by Koolnova)
MAX_UPDATE_INTERVAL = 3600    # configurable maximum
DEFAULT_PROJECT_UPDATE_FREQUENCY = 20  # refresh projects every N updates
MIN_PROJECT_UPDATE_FREQUENCY = 1      # configurable minimum (always refresh)
MAX_PROJECT_UPDATE_FREQUENCY = 300    # configurable maximum

# Per-request HTTP timeout for Koolnova API calls (seconds).
# 45s is the minimum recommended by Koolnova support; never go below it.
DEFAULT_REQUEST_TIMEOUT = 50   # seconds
MIN_REQUEST_TIMEOUT = 45       # configurable minimum — never below 45s for cloud
MAX_REQUEST_TIMEOUT = 300      # configurable maximum

DEFAULT_PROJECT_HVAC_MODES = [HVACMode.COOL, HVACMode.HEAT]
DEFAULT_ZONE_HVAC_MODES = [HVACMode.OFF, HVACMode.AUTO]

DEFAULT_MIN_TEMP = 21.0       # default value
MIN_CONFIGURABLE_TEMP = 15.0  # customizable minimum
DEFAULT_MAX_TEMP = 27.0       # default value
MAX_CONFIGURABLE_TEMP = 35.0  # customizable maximum
DEFAULT_TEMP_PRECISION = 0.5

# Available options for HVAC modes
AVAILABLE_HVAC_MODES = [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF, HVACMode.AUTO]
AVAILABLE_TEMP_PRECISIONS = [0.5, 1.0]

# Heat source for the project circuit. The Koolnova cloud drives two circuits — air
# and underfloor — and the app lists their combinations as separate entries, so
# "heat" and "cool" on their own are ambiguous.
HEAT_SOURCE_AIR = "air"
HEAT_SOURCE_FLOOR = "floor"
HEAT_SOURCE_BOTH = "both"
AVAILABLE_HEAT_SOURCES = [HEAT_SOURCE_AIR, HEAT_SOURCE_FLOOR, HEAT_SOURCE_BOTH]
DEFAULT_HEAT_SOURCE = HEAT_SOURCE_AIR

# Configuration keys
CONF_UPDATE_INTERVAL = "update_interval"
CONF_PROJECT_UPDATE_FREQUENCY = "project_update_frequency"
CONF_PROJECT_HVAC_MODES = "project_hvac_modes"
CONF_ZONE_HVAC_MODES = "zone_hvac_modes"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_TEMP_PRECISION = "temp_precision"
CONF_REQUEST_TIMEOUT = "request_timeout"
CONF_HEAT_SOURCE = "heat_source"

# Project "mode" codes. Confirmed on a real installation:
#   1 cool air · 2 hot air · 3 heat floor · 5 cool floor + cool air
#   6 heat floor + hot air
# Code 4 shows up in the app's list but has not been identified yet, so it is left
# unmapped on purpose: an unmapped code logs a warning carrying its value instead
# of being silently read as off.
# There is neither an "auto" nor an "off" code: stopping is the `is_stop` flag.
KOOLNOVA_MODE_COOL_AIR = "1"
KOOLNOVA_MODE_HOT_AIR = "2"
KOOLNOVA_MODE_HEAT_FLOOR = "3"
KOOLNOVA_MODE_COOL_BOTH = "5"
KOOLNOVA_MODE_HEAT_BOTH = "6"

# Payload key used to switch the whole installation off.
KOOLNOVA_PROJECT_STOP_KEY = "is_stop"

# Forward mapping: what each code means. It is NOT invertible, because several
# codes collapse onto heat and onto cool: writing requires
# KOOLNOVA_PROJECT_MODE_CODE, keyed by (hvac mode, heat source).
KOOLNOVA_TO_HVAC_MODE = {
    KOOLNOVA_MODE_COOL_AIR: HVACMode.COOL,
    KOOLNOVA_MODE_HOT_AIR: HVACMode.HEAT,
    KOOLNOVA_MODE_HEAT_FLOOR: HVACMode.HEAT,
    KOOLNOVA_MODE_COOL_BOTH: HVACMode.COOL,
    KOOLNOVA_MODE_HEAT_BOTH: HVACMode.HEAT,
}

# Which circuit(s) each code drives.
KOOLNOVA_MODE_TO_HEAT_SOURCE = {
    KOOLNOVA_MODE_COOL_AIR: HEAT_SOURCE_AIR,
    KOOLNOVA_MODE_HOT_AIR: HEAT_SOURCE_AIR,
    KOOLNOVA_MODE_HEAT_FLOOR: HEAT_SOURCE_FLOOR,
    KOOLNOVA_MODE_COOL_BOTH: HEAT_SOURCE_BOTH,
    KOOLNOVA_MODE_HEAT_BOTH: HEAT_SOURCE_BOTH,
}

# Code to send to the cloud, keyed by (Home Assistant mode, heat source).
# (cool, floor) is absent on purpose: the app has no cool-floor-only entry, so that
# combination must fail loudly instead of falling back to another circuit.
KOOLNOVA_PROJECT_MODE_CODE = {
    (HVACMode.COOL, HEAT_SOURCE_AIR): KOOLNOVA_MODE_COOL_AIR,
    (HVACMode.COOL, HEAT_SOURCE_BOTH): KOOLNOVA_MODE_COOL_BOTH,
    (HVACMode.HEAT, HEAT_SOURCE_AIR): KOOLNOVA_MODE_HOT_AIR,
    (HVACMode.HEAT, HEAT_SOURCE_FLOOR): KOOLNOVA_MODE_HEAT_FLOOR,
    (HVACMode.HEAT, HEAT_SOURCE_BOTH): KOOLNOVA_MODE_HEAT_BOTH,
}

# The modes the project can actually execute: the directions that map to a code, plus `off`,
# which is not a code but the `is_stop` flag. `auto` is deliberately absent - the project
# payload has no code that represents it, so offering it in `hvac_modes` gives the user a
# command that silently does nothing (reported by @DaniCai130 after trying it in the app).
# Derived from KOOLNOVA_PROJECT_MODE_CODE so a new mapping shows up here by itself.
PROJECT_HVAC_MODES = [
    mode
    for mode in (HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF)
    if mode is HVACMode.OFF or any(hvac == mode for hvac, _source in KOOLNOVA_PROJECT_MODE_CODE)
]


def filter_project_hvac_modes(values):
    """Keep only the modes the project can execute, in a stable order.

    Saved options can carry values the project cannot run - `auto` from an older
    configuration, or something typed by hand. Exposing them in `hvac_modes` would show a
    command that does nothing, so they are dropped. When nothing valid is left the default is
    returned instead of leaving the entity without a single mode to offer.
    """
    kept = []
    for value in values or []:
        try:
            mode = HVACMode(value)
        except ValueError:
            continue  # valore sconosciuto: scartato, non deve rompere l'entita'
        if mode in PROJECT_HVAC_MODES and mode not in kept:
            kept.append(mode)
    order = {mode: index for index, mode in enumerate(PROJECT_HVAC_MODES)}
    return sorted(kept, key=order.__getitem__) if kept else list(DEFAULT_PROJECT_HVAC_MODES)


# Presets exposed on the project entity: the five entries the app offers. Each is a
# (mode, circuit) pair, so picking one sends its code directly instead of having to
# set a global heat source first. Names are the stable keys used by the translations.
KOOLNOVA_PRESET_CODES = {
    "cool_air": KOOLNOVA_MODE_COOL_AIR,
    "hot_air": KOOLNOVA_MODE_HOT_AIR,
    "heat_floor": KOOLNOVA_MODE_HEAT_FLOOR,
    "cool_both": KOOLNOVA_MODE_COOL_BOTH,
    "heat_both": KOOLNOVA_MODE_HEAT_BOTH,
}

# Which preset a raw mode corresponds to. Off, auto and unmapped codes have none.
KOOLNOVA_MODE_TO_PRESET = {code: name for name, code in KOOLNOVA_PRESET_CODES.items()}

# Status mappings for sensors/zones - only the forward definition is written by hand
KOOLNOVA_ZONE_STATUS_TO_HVAC = {
    "00": HVACMode.COOL,
    "01": HVACMode.HEAT,
    "02": HVACMode.OFF,
    "03": HVACMode.AUTO
}

# Inverse mapping, generated automatically, for zone status
HVAC_TO_KOOLNOVA_ZONE_STATUS = {v: k for k, v in KOOLNOVA_ZONE_STATUS_TO_HVAC.items()}

# Fan mode mappings - only the forward definition is written by hand
KOOLNOVA_TO_FAN = {
    "1": FAN_LOW,
    "2": FAN_MEDIUM,
    "3": FAN_HIGH,
    "4": FAN_AUTO
}

# Inverse mapping, generated automatically, for fan speed
FAN_TO_KOOLNOVA = {v: k for k, v in KOOLNOVA_TO_FAN.items()}

# Fan Mode mappings
