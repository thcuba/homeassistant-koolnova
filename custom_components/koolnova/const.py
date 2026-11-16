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

# Heat source for the project circuit. The Koolnova cloud drives two independent
# circuits (air and underfloor) and encodes the four combinations - cool/hot times
# air/floor - with four distinct "mode" codes, so "heat" alone is ambiguous.
HEAT_SOURCE_AIR = "air"
HEAT_SOURCE_FLOOR = "floor"
AVAILABLE_HEAT_SOURCES = [HEAT_SOURCE_AIR, HEAT_SOURCE_FLOOR]
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

# Project "mode" codes, as the official app labels them:
#   1 cool air · 2 hot air · 3 off · 4 heat floor · 5 cool floor
# Codes 1, 2, 4 and 5 are the four entries the app offers. The value used for
# "off" is reported as 3, inferred from the gap in that sequence: it has not been
# confirmed against the cloud yet, so the raw mode is exposed in the entity
# attributes as `project_mode_raw` and an unmapped code logs a warning instead of
# being silently treated as off.
KOOLNOVA_MODE_COOL_AIR = "1"
KOOLNOVA_MODE_HOT_AIR = "2"
KOOLNOVA_MODE_OFF = "3"
KOOLNOVA_MODE_HEAT_FLOOR = "4"
KOOLNOVA_MODE_COOL_FLOOR = "5"

# Forward mapping: what each code means. Unlike the zone statuses this is NOT
# invertible, because two codes collapse onto each of cool and heat. Going the
# other way requires KOOLNOVA_PROJECT_MODE_CODE, since the code to send also
# depends on the configured heat source.
KOOLNOVA_TO_HVAC_MODE = {
    KOOLNOVA_MODE_COOL_AIR: HVACMode.COOL,
    KOOLNOVA_MODE_HOT_AIR: HVACMode.HEAT,
    KOOLNOVA_MODE_OFF: HVACMode.OFF,
    KOOLNOVA_MODE_HEAT_FLOOR: HVACMode.HEAT,
    KOOLNOVA_MODE_COOL_FLOOR: HVACMode.COOL,
}

# Which circuit each code drives. "off" has no circuit, so it is absent on purpose.
KOOLNOVA_MODE_TO_HEAT_SOURCE = {
    KOOLNOVA_MODE_COOL_AIR: HEAT_SOURCE_AIR,
    KOOLNOVA_MODE_HOT_AIR: HEAT_SOURCE_AIR,
    KOOLNOVA_MODE_HEAT_FLOOR: HEAT_SOURCE_FLOOR,
    KOOLNOVA_MODE_COOL_FLOOR: HEAT_SOURCE_FLOOR,
}

# Code to send to the cloud, keyed by (Home Assistant mode, heat source).
KOOLNOVA_PROJECT_MODE_CODE = {
    (HVACMode.COOL, HEAT_SOURCE_AIR): KOOLNOVA_MODE_COOL_AIR,
    (HVACMode.COOL, HEAT_SOURCE_FLOOR): KOOLNOVA_MODE_COOL_FLOOR,
    (HVACMode.HEAT, HEAT_SOURCE_AIR): KOOLNOVA_MODE_HOT_AIR,
    (HVACMode.HEAT, HEAT_SOURCE_FLOOR): KOOLNOVA_MODE_HEAT_FLOOR,
    (HVACMode.OFF, HEAT_SOURCE_AIR): KOOLNOVA_MODE_OFF,
    (HVACMode.OFF, HEAT_SOURCE_FLOOR): KOOLNOVA_MODE_OFF,
}

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
