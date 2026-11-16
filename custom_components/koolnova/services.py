"""Services for the Koolnova integration.

Only one service lives here: the "set every zone at once" action that used to hide
in the preset slot of the project entity. Presets now carry the entries the official
app offers (cool air, hot air, heat floor, ...), which is what a user needs to pick
from, so the bulk zone command moved here instead of being dropped.
"""
import logging

from homeassistant.components.climate import HVACMode
from homeassistant.core import HomeAssistant, ServiceCall, callback

from .const import DOMAIN, HVAC_TO_KOOLNOVA_ZONE_STATUS

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_ALL_ZONES_MODE = "set_all_zones_mode"
ATTR_MODE = "mode"
ZONE_MODES = ("cool", "heat", "off", "auto")


async def _async_set_all_zones_mode(hass: HomeAssistant, call: ServiceCall) -> None:
    """Set the HVAC mode of every zone in every project."""
    mode = call.data[ATTR_MODE]
    try:
        status_code = HVAC_TO_KOOLNOVA_ZONE_STATUS.get(HVACMode(mode))
    except ValueError:
        status_code = None

    if not status_code:
        _LOGGER.error(
            "Unsupported zone mode %s. Available: %s",
            mode,
            ", ".join(sorted(m.value for m in HVAC_TO_KOOLNOVA_ZONE_STATUS)),
        )
        return

    updated = 0
    failed = 0
    for coordinator in hass.data.get(DOMAIN, {}).values():
        try:
            result = await coordinator.async_update_all_sensors_status(status_code)
            updated += result.get("updated", 0)
            failed += result.get("failed", 0)
        except Exception as err:  # noqa: BLE001 - one project must not stop the others
            _LOGGER.error("Error setting all zones to %s: %s", mode, err)
            failed += 1

    _LOGGER.info("All zones set to %s: %s updated, %s failed", mode, updated, failed)


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register the integration services, once per Home Assistant instance."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_ALL_ZONES_MODE):
        return

    # Imported here rather than at module level: the package has to stay importable
    # where the Home Assistant dependencies are absent, which is the case in the
    # unit tests, and a module-level import would break every test module.
    import voluptuous as vol

    schema = vol.Schema({vol.Required(ATTR_MODE): vol.In(list(ZONE_MODES))})

    async def handle_set_all_zones_mode(call: ServiceCall) -> None:
        await _async_set_all_zones_mode(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ALL_ZONES_MODE,
        handle_set_all_zones_mode,
        schema=schema,
    )
