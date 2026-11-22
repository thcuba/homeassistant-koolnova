"""Tests for the configured temperature step exposed by the climate entities.

Home Assistant is not installed in CI, so minimal stubs are registered before
``climate.py`` is imported (it pulls in ``coordinator.py`` and the HA symbols
the entities use). The step is reported through ``target_temperature_step``:
``ClimateEntity.precision`` is deprecated and is no longer set.
"""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent


def _install_home_assistant_stubs():
    """Register the HA symbols imported by ``climate.py`` and ``coordinator.py``.

    Other test modules in the suite install narrower stubs first, so this must
    complete whatever is already registered instead of trusting it wholesale.
    """
    from enum import StrEnum

    class HVACMode(StrEnum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        HEAT_COOL = "heat_cool"
        AUTO = "auto"
        DRY = "dry"
        FAN_ONLY = "fan_only"

    class ClimateEntityFeature(StrEnum):
        TARGET_TEMPERATURE = "target_temperature"

    class ClimateEntity:
        _attr_should_poll = True

        def __init__(self, coordinator, config_entry):
            self.coordinator = coordinator
            self.config_entry = config_entry

    class UnitOfTemperature(StrEnum):
        CELSIUS = "°C"

    ha = sys.modules.get("homeassistant")
    if ha is None:
        ha = types.ModuleType("homeassistant")
        ha.__path__ = []
        sys.modules["homeassistant"] = ha

    components = sys.modules.get("homeassistant.components")
    if components is None:
        components = types.ModuleType("homeassistant.components")
        components.__path__ = []
        sys.modules["homeassistant.components"] = components
    ha.components = components

    climate = sys.modules.get("homeassistant.components.climate")
    if climate is None:
        climate = types.ModuleType("homeassistant.components.climate")
        sys.modules["homeassistant.components.climate"] = climate
        components.climate = climate
    climate.ClimateEntity = getattr(climate, "ClimateEntity", ClimateEntity)
    climate.HVACMode = getattr(climate, "HVACMode", HVACMode)
    climate.ClimateEntityFeature = getattr(
        climate, "ClimateEntityFeature", ClimateEntityFeature
    )
    for fan in ("FAN_LOW", "FAN_MEDIUM", "FAN_HIGH", "FAN_AUTO"):
        if not hasattr(climate, fan):
            setattr(climate, fan, fan.lower().replace("fan_", ""))

    notifications = sys.modules.get("homeassistant.components.persistent_notification")
    if notifications is None:
        notifications = types.ModuleType(
            "homeassistant.components.persistent_notification"
        )
        sys.modules["homeassistant.components.persistent_notification"] = notifications
        components.persistent_notification = notifications
    if not hasattr(notifications, "async_create"):
        notifications.async_create = MagicMock()

    helpers = sys.modules.get("homeassistant.helpers")
    if helpers is None:
        helpers = types.ModuleType("homeassistant.helpers")
        helpers.__path__ = []
        sys.modules["homeassistant.helpers"] = helpers
    ha.helpers = helpers

    entity = sys.modules.get("homeassistant.helpers.entity")
    if entity is None:
        entity = types.ModuleType("homeassistant.helpers.entity")
        sys.modules["homeassistant.helpers.entity"] = entity
        helpers.entity = entity
    if not hasattr(entity, "DeviceInfo"):
        entity.DeviceInfo = dict

    class _DataUpdateCoordinator:
        def __init__(self, hass, logger, **kwargs):
            self.hass = hass
            self.data = {}

    update_coordinator = sys.modules.get("homeassistant.helpers.update_coordinator")
    if update_coordinator is None:
        update_coordinator = types.ModuleType(
            "homeassistant.helpers.update_coordinator"
        )
        sys.modules["homeassistant.helpers.update_coordinator"] = update_coordinator
        helpers.update_coordinator = update_coordinator
    for name, value in (
        ("DataUpdateCoordinator", _DataUpdateCoordinator),
        ("UpdateFailed", type("UpdateFailed", (Exception,), {})),
    ):
        if not hasattr(update_coordinator, name):
            setattr(update_coordinator, name, value)

    ha_const = sys.modules.get("homeassistant.const")
    if ha_const is None:
        ha_const = types.ModuleType("homeassistant.const")
        sys.modules["homeassistant.const"] = ha_const
        ha.const = ha_const
    if not hasattr(ha_const, "UnitOfTemperature"):
        ha_const.UnitOfTemperature = UnitOfTemperature
    if not hasattr(ha_const, "Platform"):
        ha_const.Platform = MagicMock

    core = sys.modules.get("homeassistant.core")
    if core is None:
        core = types.ModuleType("homeassistant.core")
        sys.modules["homeassistant.core"] = core
        ha.core = core
    if not hasattr(core, "HomeAssistant"):
        core.HomeAssistant = MagicMock

    config_entries = sys.modules.get("homeassistant.config_entries")
    if config_entries is None:
        config_entries = types.ModuleType("homeassistant.config_entries")
        sys.modules["homeassistant.config_entries"] = config_entries
        ha.config_entries = config_entries
    if not hasattr(config_entries, "ConfigEntry"):
        config_entries.ConfigEntry = MagicMock

    exceptions = sys.modules.get("homeassistant.exceptions")
    if exceptions is None:
        exceptions = types.ModuleType("homeassistant.exceptions")
        sys.modules["homeassistant.exceptions"] = exceptions
        ha.exceptions = exceptions
    if not hasattr(exceptions, "ConfigEntryAuthFailed"):
        exceptions.ConfigEntryAuthFailed = type(
            "ConfigEntryAuthFailed", (Exception,), {}
        )


_install_home_assistant_stubs()

sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "custom_components"))

for mod_name in [
    "custom_components.koolnova.koolnova_api.exceptions",
    "custom_components.koolnova.koolnova_api.const",
    "custom_components.koolnova.koolnova_api.session",
    "custom_components.koolnova.koolnova_api.client",
]:
    importlib.import_module(mod_name)

const = importlib.import_module("custom_components.koolnova.const")
coordinator = importlib.import_module("custom_components.koolnova.coordinator")
climate = importlib.import_module("custom_components.koolnova.climate")

KoolnovaConfigMixin = climate.KoolnovaConfigMixin
CONF_TEMP_PRECISION = const.CONF_TEMP_PRECISION
DEFAULT_TEMP_PRECISION = const.DEFAULT_TEMP_PRECISION


class _ConfigHolder(KoolnovaConfigMixin):
    """Bare mixin host: only the config lookups are exercised."""

    def __init__(self, options=None, data=None):
        entry = MagicMock()
        entry.options = {} if options is None else options
        entry.data = {} if data is None else data
        self.config_entry = entry


class TempPrecisionTest(unittest.TestCase):
    def test_default_when_unset(self):
        self.assertEqual(
            _ConfigHolder()._get_temp_precision(), DEFAULT_TEMP_PRECISION
        )

    def test_string_option_is_accepted(self):
        """The config flow stores the select value as a string."""
        self.assertEqual(
            _ConfigHolder({CONF_TEMP_PRECISION: "1.0"})._get_temp_precision(), 1.0
        )

    def test_option_overrides_data(self):
        holder = _ConfigHolder(
            {CONF_TEMP_PRECISION: 1.0}, {CONF_TEMP_PRECISION: 0.5}
        )
        self.assertEqual(holder._get_temp_precision(), 1.0)

    def test_data_is_used_when_option_missing(self):
        self.assertEqual(
            _ConfigHolder({}, {CONF_TEMP_PRECISION: "1.0"})._get_temp_precision(), 1.0
        )

    def test_unsupported_values_fall_back_to_default(self):
        """A step HA cannot render must not reach the UI."""
        for invalid in (0.1, 2.0, "0.2", "abc", None):
            with self.subTest(invalid=invalid):
                self.assertEqual(
                    _ConfigHolder({CONF_TEMP_PRECISION: invalid})._get_temp_precision(),
                    DEFAULT_TEMP_PRECISION,
                )


class DeprecatedPrecisionTest(unittest.TestCase):
    """``precision`` is deprecated in HA; the step must come from the step property."""

    def test_entities_expose_target_temperature_step(self):
        for entity in (climate.KoolnovaProjectEntity, climate.KoolnovaZoneEntity):
            with self.subTest(entity=entity.__name__):
                self.assertIn("target_temperature_step", vars(entity))
                self.assertNotIn("precision", vars(entity))


if __name__ == "__main__":
    unittest.main()
