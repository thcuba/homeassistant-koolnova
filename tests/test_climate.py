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
from custom_components.koolnova.coordinator import (  # noqa: E402
    command_was_applied,
    payload_changes_project,
)
from homeassistant.components.climate import HVACMode  # noqa: E402

HEAT_AIR_CODE = const.KOOLNOVA_PROJECT_MODE_CODE[(HVACMode.HEAT, "air")]
COOL_AIR_CODE = const.KOOLNOVA_PROJECT_MODE_CODE[(HVACMode.COOL, "air")]
STOP_KEY = const.KOOLNOVA_PROJECT_STOP_KEY


class ProjectModeCommandTest(unittest.IsolatedAsyncioTestCase):
    """What the project sends when a running mode is requested."""

    def _make_entity(self, is_stop, mode="2", project_modes=None):
        """Build the project entity over a coordinator that records payloads."""
        self.project = {
            "Topic_id": 412217,
            "Project_Name": "Casa",
            "Topic_Name": "AC Casa",
            "Mode": mode,
            STOP_KEY: is_stop,
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

    async def test_the_flag_travels_alone_when_the_mode_is_unchanged(self):
        """Leaving off with the stored mode: the flag alone, as the app's Start does."""
        entity = self._make_entity(is_stop=True, mode=str(HEAT_AIR_CODE))

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        payloads = self._sent_payloads()
        self.assertEqual(len(payloads), 1, "the fix must stay a single request")
        self.assertEqual(payloads[0], {STOP_KEY: False})

    async def test_the_mode_and_the_flag_travel_together_when_the_mode_changes(self):
        """A real mode change keeps both in one request."""
        entity = self._make_entity(is_stop=True, mode=str(COOL_AIR_CODE))

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        payloads = self._sent_payloads()
        self.assertEqual(len(payloads), 1, "the fix must stay a single request")
        self.assertEqual(payloads[0], {"mode": HEAT_AIR_CODE, STOP_KEY: False})

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


class CommandApplicationTest(unittest.TestCase):
    """Whether the cloud applied a command, decided from last_sync."""

    def test_a_moved_last_sync_means_applied(self):
        self.assertTrue(
            command_was_applied(
                "2026-11-23T12:08:29Z",
                {"last_sync": "2026-11-23T12:16:19Z", "is_stop": False},
                {"mode": "2", STOP_KEY: False},
                {"Mode": "2", STOP_KEY: True},
            )
        )

    def test_an_unchanged_last_sync_means_the_command_was_dropped(self):
        """The measured case: 200, the flag echoed back, last_sync untouched."""
        self.assertFalse(
            command_was_applied(
                "2026-11-23T12:08:29Z",
                {"last_sync": "2026-11-23T12:08:29Z", "is_stop": False},
                {"mode": "2", STOP_KEY: False},
                {"Mode": "2", STOP_KEY: True},
            ),
            "a 200 with the flag echoed back is not proof of anything",
        )

    def test_nothing_to_apply_is_not_a_failure(self):
        """A payload identical to the cached state is not expected to move last_sync."""
        self.assertTrue(
            command_was_applied(
                "2026-11-23T12:08:29Z",
                {"last_sync": "2026-11-23T12:08:29Z"},
                {"mode": "2", STOP_KEY: False},
                {"Mode": "2", STOP_KEY: False},
            )
        )

    def test_a_response_without_last_sync_keeps_the_old_behaviour(self):
        """Nothing to compare: assume applied rather than break callers."""
        self.assertTrue(command_was_applied("whatever", {"is_stop": False}, {STOP_KEY: False}, {}))
        self.assertTrue(command_was_applied("whatever", "not a dict", {STOP_KEY: False}, {}))

    def test_payload_changes_project_tells_the_two_cases_apart(self):
        self.assertTrue(payload_changes_project({"mode": "2"}, {"Mode": "1"}))
        self.assertTrue(payload_changes_project({"mode": "2"}, {}))
        self.assertTrue(payload_changes_project({STOP_KEY: False}, {STOP_KEY: True}))
        self.assertTrue(payload_changes_project({STOP_KEY: True}, {}))
        self.assertFalse(payload_changes_project({"mode": "2"}, {"Mode": "2"}))
        self.assertFalse(
            payload_changes_project(
                {"mode": "2", STOP_KEY: False}, {"Mode": "2", STOP_KEY: False}
            )
        )


class UnappliedCommandTest(unittest.IsolatedAsyncioTestCase):
    """The entity must never report a state the installation is not running."""

    async def test_a_dropped_command_is_not_believed(self):
        """A cache the coordinator left untouched means the command was dropped."""
        project = {
            "Topic_id": 412217,
            "Project_Name": "Casa",
            "Topic_Name": "AC Casa",
            "Mode": str(HEAT_AIR_CODE),
            STOP_KEY: True,
            "Topic_modes": None,
        }

        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.data = {"projects": [project], "sensors": [], "hubs": []}

        async def _dropped(topic_id, payload):
            # The coordinator refuses to refresh the cache when last_sync did not move,
            # so the project dict above stays exactly as it was.
            return {"last_sync": "unchanged", "is_stop": False}

        coordinator.async_update_project_data = _dropped

        config_entry = MagicMock()
        config_entry.entry_id = "test_entry_id"
        config_entry.data = {}
        config_entry.options = {
            const.CONF_HEAT_SOURCE: "air",
            const.CONF_PROJECT_HVAC_MODES: ["cool", "heat", "off"],
        }

        entity = KoolnovaProjectEntity(coordinator, config_entry, project)
        entity.hass = MagicMock()
        entity.async_write_ha_state = MagicMock()

        notified = []
        import custom_components.koolnova.climate as climate_mod

        original = climate_mod.async_create
        climate_mod.async_create = lambda hass, message, **kwargs: notified.append(message)
        try:
            await entity.async_set_hvac_mode(HVACMode.HEAT)
        finally:
            climate_mod.async_create = original

        self.assertEqual(
            project.get(STOP_KEY),
            True,
            "the cached state must not be replaced by what the server echoed back",
        )
        self.assertEqual(len(notified), 1, "the user has to be told the command was dropped")
        self.assertIn("did not apply", notified[0])


if __name__ == "__main__":
    unittest.main()
