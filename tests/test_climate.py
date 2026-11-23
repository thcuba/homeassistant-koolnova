"""Tests for the project entity's mode command, and for leaving the stopped state.

The project payload is the only place where the installation can be started or
stopped: ``is_stop`` is a flag, not a mode. Getting it wrong leaves the house
cold while Home Assistant reports the new mode, which is exactly the report that
produced ``fix/restart-after-stop``.
"""

import os
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _ensure_module(name, is_package=False):
    """Return the module from sys.modules, creating a stub if absent.

    Other test modules install their own partial stubs, so this has to be
    additive: whatever already exists is kept and only missing names are added.
    """
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    if is_package and not hasattr(module, "__path__"):
        module.__path__ = []
    return module


def _install_home_assistant_stubs():
    """Register the HA names koolnova.climate needs, without clobbering others."""
    from enum import IntFlag, StrEnum

    ha = _ensure_module("homeassistant", is_package=True)
    for sub in ("config_entries", "core", "exceptions", "helpers", "const"):
        _ensure_module(f"homeassistant.{sub}")

    config_entries = sys.modules["homeassistant.config_entries"]
    if not hasattr(config_entries, "ConfigEntry"):
        config_entries.ConfigEntry = MagicMock

    core = sys.modules["homeassistant.core"]
    if not hasattr(core, "HomeAssistant"):
        core.HomeAssistant = MagicMock

    exceptions = sys.modules["homeassistant.exceptions"]
    if not hasattr(exceptions, "ConfigEntryAuthFailed"):
        exceptions.ConfigEntryAuthFailed = type("ConfigEntryAuthFailed", (Exception,), {})

    class HVACMode(StrEnum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        HEAT_COOL = "heat_cool"
        AUTO = "auto"
        DRY = "dry"
        FAN_ONLY = "fan_only"

    class ClimateEntityFeature(IntFlag):
        TARGET_TEMPERATURE = 1
        TARGET_TEMPERATURE_RANGE = 2
        TARGET_HUMIDITY = 4
        FAN_MODE = 8
        PRESET_MODE = 16
        SWING_MODE = 32
        AUX_HEAT = 64
        TURN_ON = 128
        TURN_OFF = 256

    class ClimateEntity:
        """Stub ClimateEntity: only what the project entity touches."""

        _attr_should_poll = False
        _attr_name = None
        _attr_unique_id = None

        hass = None

        def async_write_ha_state(self):
            pass

    ha_const = sys.modules["homeassistant.const"]
    if not hasattr(ha_const, "Platform"):
        ha_const.Platform = MagicMock
    if not hasattr(ha_const, "UnitOfTemperature"):
        ha_const.UnitOfTemperature = type(
            "UnitOfTemperature", (), {"CELSIUS": "°C", "FAHRENHEIT": "°F"}
        )

    class _DataUpdateCoordinator:
        def __init__(self, hass, logger, **kwargs):
            self.hass = hass
            self.logger = logger
            self.update_interval = kwargs.get("update_interval")
            self.config_entry = kwargs.get("config_entry")
            self.data = {}

    uc = _ensure_module("homeassistant.helpers.update_coordinator")
    if not hasattr(uc, "DataUpdateCoordinator"):
        uc.DataUpdateCoordinator = _DataUpdateCoordinator
    if not hasattr(uc, "UpdateFailed"):
        uc.UpdateFailed = type("UpdateFailed", (Exception,), {})

    helpers = sys.modules["homeassistant.helpers"]
    helpers.update_coordinator = uc

    helpers_entity = _ensure_module("homeassistant.helpers.entity")
    if not hasattr(helpers_entity, "DeviceInfo"):
        helpers_entity.DeviceInfo = lambda **kwargs: kwargs
    helpers.entity = helpers_entity

    components = _ensure_module("homeassistant.components", is_package=True)

    climate = _ensure_module("homeassistant.components.climate")
    if not hasattr(climate, "HVACMode"):
        climate.HVACMode = HVACMode
    if not hasattr(climate, "ClimateEntity"):
        climate.ClimateEntity = ClimateEntity
    if not hasattr(climate, "ClimateEntityFeature"):
        climate.ClimateEntityFeature = ClimateEntityFeature
    for fan_const, fan_value in (
        ("FAN_LOW", "low"),
        ("FAN_MEDIUM", "medium"),
        ("FAN_HIGH", "high"),
        ("FAN_AUTO", "auto"),
    ):
        if not hasattr(climate, fan_const):
            setattr(climate, fan_const, fan_value)
    components.climate = climate

    persistent = _ensure_module("homeassistant.components.persistent_notification")
    if not hasattr(persistent, "async_create"):
        persistent.async_create = lambda *args, **kwargs: None
    components.persistent_notification = persistent


_install_home_assistant_stubs()

from custom_components.koolnova import const  # noqa: E402
from custom_components.koolnova.climate import KoolnovaProjectEntity  # noqa: E402
from homeassistant.components.climate import HVACMode  # noqa: E402


class ProjectModeCommandTest(unittest.IsolatedAsyncioTestCase):
    """What the project sends when a running mode is requested."""

    def _make_entity(self, is_stop, project_modes=None):
        """Build the project entity over a coordinator that records payloads."""
        self.project = {
            "Topic_id": 412217,
            "Project_Name": "Casa",
            "Topic_Name": "AC Casa",
            "Mode": "2",
            const.KOOLNOVA_PROJECT_STOP_KEY: is_stop,
            "Topic_modes": None,
            "is_online": True,
            "eco": False,
            "last_sync": "2026-11-23T19:41:55+00:00",
        }

        self.coordinator = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.data = {"projects": [self.project], "sensors": [], "hubs": []}
        self.coordinator.async_update_project_data = AsyncMock(return_value={"ok": True})

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_id"
        self.config_entry.data = {}
        self.config_entry.options = {
            const.CONF_HEAT_SOURCE: "air",
            const.CONF_PROJECT_HVAC_MODES: project_modes
            if project_modes is not None
            else ["cool", "heat", "off"],
        }

        entity = KoolnovaProjectEntity(self.coordinator, self.config_entry, self.project)
        entity.hass = MagicMock()
        entity.async_write_ha_state = MagicMock()
        return entity

    def _sent_payloads(self):
        """Bodies actually sent to the cloud, in order."""
        return [call.args[1] for call in self.coordinator.async_update_project_data.await_args_list]

    async def test_leaving_off_clears_the_flag_in_the_same_request(self):
        """From stopped, one request carries both the mode and is_stop false."""
        entity = self._make_entity(is_stop=True)

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        payloads = self._sent_payloads()
        self.assertEqual(len(payloads), 1, "the fix must stay a single request")
        self.assertEqual(
            payloads[0],
            {
                "mode": const.KOOLNOVA_PROJECT_MODE_CODE[(HVACMode.HEAT, "air")],
                const.KOOLNOVA_PROJECT_STOP_KEY: False,
            },
        )

    async def test_the_flag_is_sent_even_when_the_cache_still_says_running(self):
        """The cached is_stop may be an hour old: never let it suppress the flag.

        Projects are re-read only every ``project_update_frequency`` coordinator
        cycles, so the cache can claim the installation is running while the cloud
        has it stopped. Conditioning the flag on that cache sent ``{"mode": N}``
        alone and the installation stayed stopped with the mode merely set.
        """
        entity = self._make_entity(is_stop=False)

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        payloads = self._sent_payloads()
        self.assertEqual(len(payloads), 1)
        self.assertEqual(
            payloads[0].get(const.KOOLNOVA_PROJECT_STOP_KEY),
            False,
            "is_stop must be cleared regardless of what the cache believed",
        )
        self.assertIn("mode", payloads[0])

    async def test_off_sends_only_the_stop_flag(self):
        """Stopping is the flag alone: no mode code is involved."""
        entity = self._make_entity(is_stop=False)

        await entity.async_set_hvac_mode(HVACMode.OFF)

        payloads = self._sent_payloads()
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0], {const.KOOLNOVA_PROJECT_STOP_KEY: True})
        self.assertNotIn("mode", payloads[0])

    async def test_a_mode_the_options_do_not_offer_sends_nothing(self):
        """No request at all when the mode is not among the configured ones."""
        entity = self._make_entity(is_stop=True, project_modes=["heat", "off"])

        await entity.async_set_hvac_mode(HVACMode.COOL)

        self.assertEqual(self._sent_payloads(), [])


if __name__ == "__main__":
    unittest.main()
