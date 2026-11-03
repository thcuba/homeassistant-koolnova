"""Tests for Koolnova sensor entities (humidity sensor and setup)."""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _install_home_assistant_stubs():
    """Register minimal stubs for HA modules required by sensor.py if HA is not installed."""
    if "homeassistant.components.sensor" in sys.modules:
        return

    from enum import StrEnum

    # ---- homeassistant.const ----
    ha_const = sys.modules.get("homeassistant.const")
    if ha_const is None:
        ha_const = types.ModuleType("homeassistant.const")
        sys.modules["homeassistant.const"] = ha_const

    if not hasattr(ha_const, "PERCENTAGE"):
        setattr(ha_const, "PERCENTAGE", "%")
    if not hasattr(ha_const, "Platform"):
        class Platform(StrEnum):
            CLIMATE = "climate"
            BINARY_SENSOR = "binary_sensor"
            SWITCH = "switch"
            SENSOR = "sensor"
        setattr(ha_const, "Platform", Platform)

    # ---- homeassistant.components.climate ----
    class HVACMode(StrEnum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        HEAT_COOL = "heat_cool"
        AUTO = "auto"
        DRY = "dry"
        FAN_ONLY = "fan_only"

    climate_mod = types.ModuleType("homeassistant.components.climate")
    climate_mod.HVACMode = HVACMode
    climate_mod.FAN_LOW = "low"
    climate_mod.FAN_MEDIUM = "medium"
    climate_mod.FAN_HIGH = "high"
    climate_mod.FAN_AUTO = "auto"

    # ---- homeassistant.components.sensor ----
    class SensorDeviceClass(StrEnum):
        HUMIDITY = "humidity"

    class SensorStateClass(StrEnum):
        MEASUREMENT = "measurement"

    class SensorEntity:
        """Stub SensorEntity simulating Home Assistant Entity property behavior."""
        _attr_has_entity_name = False
        _attr_device_class = None
        _attr_state_class = None
        _attr_native_unit_of_measurement = None
        _attr_should_poll = True
        _attr_name = None
        _attr_unique_id = None
        _attr_device_info = None

        @property
        def name(self):
            return self._attr_name

        @property
        def unique_id(self):
            return self._attr_unique_id

        @property
        def should_poll(self):
            return self._attr_should_poll

        @property
        def device_info(self):
            return self._attr_device_info

        async def async_added_to_hass(self):
            pass

        def async_on_remove(self, func):
            pass

        def async_write_ha_state(self):
            pass

    sensor_mod = types.ModuleType("homeassistant.components.sensor")
    sensor_mod.SensorDeviceClass = SensorDeviceClass
    sensor_mod.SensorStateClass = SensorStateClass
    sensor_mod.SensorEntity = SensorEntity

    # ---- homeassistant.helpers.entity ----
    def DeviceInfo(**kwargs):
        return kwargs

    entity_mod = types.ModuleType("homeassistant.helpers.entity")
    entity_mod.DeviceInfo = DeviceInfo

    # ---- homeassistant.helpers.update_coordinator ----
    class _DataUpdateCoordinator:
        def __init__(self, hass, logger, **kwargs):
            self.hass = hass
            self.update_interval = kwargs.get("update_interval")
            self.data = {}

    uc = types.ModuleType("homeassistant.helpers.update_coordinator")
    uc.DataUpdateCoordinator = _DataUpdateCoordinator
    uc.UpdateFailed = type("UpdateFailed", (Exception,), {})

    # ---- homeassistant.config_entries ----
    config_entries = sys.modules.get("homeassistant.config_entries")
    if config_entries is None:
        config_entries = types.ModuleType("homeassistant.config_entries")
        config_entries.ConfigEntry = MagicMock
        sys.modules["homeassistant.config_entries"] = config_entries

    # ---- homeassistant.core ----
    core = sys.modules.get("homeassistant.core")
    if core is None:
        core = types.ModuleType("homeassistant.core")
        core.HomeAssistant = MagicMock
        sys.modules["homeassistant.core"] = core

    # ---- homeassistant.exceptions ----
    exceptions = sys.modules.get("homeassistant.exceptions")
    if exceptions is None:
        exceptions = types.ModuleType("homeassistant.exceptions")
        exceptions.ConfigEntryAuthFailed = type("ConfigEntryAuthFailed", (Exception,), {})
        sys.modules["homeassistant.exceptions"] = exceptions

    # ---- Wire the package tree ----
    ha = sys.modules.get("homeassistant")
    if ha is None:
        ha = types.ModuleType("homeassistant")
        ha.__path__ = []
        sys.modules["homeassistant"] = ha

    ha.const = ha_const
    ha.config_entries = config_entries
    ha.core = core
    ha.exceptions = exceptions

    components = sys.modules.get("homeassistant.components")
    if components is None:
        components = types.ModuleType("homeassistant.components")
        components.__path__ = []
        sys.modules["homeassistant.components"] = components
        setattr(ha, "components", components)

    helpers = sys.modules.get("homeassistant.helpers")
    if helpers is None:
        helpers = types.ModuleType("homeassistant.helpers")
        helpers.__path__ = []
        sys.modules["homeassistant.helpers"] = helpers
        setattr(ha, "helpers", helpers)

    components.sensor = sensor_mod
    components.climate = climate_mod
    helpers.entity = entity_mod
    helpers.update_coordinator = uc

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.const"] = ha_const
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.exceptions"] = exceptions
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.climate"] = climate_mod
    sys.modules["homeassistant.components.sensor"] = sensor_mod
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.update_coordinator"] = uc
    sys.modules["homeassistant.helpers.entity"] = entity_mod


_install_home_assistant_stubs()

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from custom_components.koolnova.const import DOMAIN
from custom_components.koolnova.sensor import (
    KoolnovaHumiditySensor,
    async_setup_entry,
)


class TestAsyncSetupEntry(unittest.IsolatedAsyncioTestCase):
    """Test suite for sensor platform async_setup_entry."""

    async def test_async_setup_entry_with_humidity_sensors(self):
        """Test entity creation when sensors report Room_humidity."""
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.entry_id = "entry_humidity_1"

        coordinator = MagicMock()
        coordinator.data = {
            "projects": [{"Topic_id": 10, "Project_Name": "Main Residence"}],
            "sensors": [
                {
                    "Room_id": 1,
                    "Room_Name": "Living Room",
                    "Room_humidity": 45,
                    "Topic_id": 10,
                },
                {
                    "Room_id": 2,
                    "Room_Name": "Hallway",
                    # No Room_humidity key
                    "Topic_id": 10,
                },
                {
                    "Room_id": 3,
                    "Room_Name": "Bedroom",
                    "Room_humidity": None,  # Explicitly None
                    "Topic_id": 10,
                },
                {
                    "Room_id": 4,
                    "Room_Name": "Kitchen",
                    "Room_humidity": 55,
                    "Topic_id": 10,
                },
            ],
        }
        hass.data = {DOMAIN: {config_entry.entry_id: coordinator}}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        update_before_add = async_add_entities.call_args.kwargs.get("update_before_add")

        self.assertFalse(update_before_add)
        self.assertEqual(len(entities), 2)
        self.assertIsInstance(entities[0], KoolnovaHumiditySensor)
        self.assertIsInstance(entities[1], KoolnovaHumiditySensor)
        self.assertEqual(entities[0].name, "Living Room Humidity")
        self.assertEqual(entities[1].name, "Kitchen Humidity")
        self.assertEqual(entities[0].native_value, 45)
        self.assertEqual(entities[1].native_value, 55)

    async def test_async_setup_entry_no_humidity_sensors(self):
        """Test async_add_entities is not called when no sensor has Room_humidity."""
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.entry_id = "entry_no_humidity"

        coordinator = MagicMock()
        coordinator.data = {
            "projects": [],
            "sensors": [
                {"Room_id": 1, "Room_Name": "Room 1"},
                {"Room_id": 2, "Room_Name": "Room 2", "Room_humidity": None},
            ],
        }
        hass.data = {DOMAIN: {config_entry.entry_id: coordinator}}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_not_called()

    async def test_async_setup_entry_empty_sensors(self):
        """Test async_add_entities is not called when sensors list is empty or absent."""
        hass = MagicMock()
        config_entry = MagicMock()
        config_entry.entry_id = "entry_empty"

        coordinator = MagicMock()
        coordinator.data = {}
        hass.data = {DOMAIN: {config_entry.entry_id: coordinator}}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_not_called()


class TestKoolnovaHumiditySensor(unittest.IsolatedAsyncioTestCase):
    """Test suite for KoolnovaHumiditySensor entity properties and behavior."""

    def setUp(self):
        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_id"

        self.coordinator = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.async_add_listener = MagicMock()

        self.sensor_data = {
            "Room_id": 1,
            "Room_Name": "Master Bedroom",
            "Room_humidity": 50,
            "Topic_id": 101,
        }

        self.coordinator.data = {
            "projects": [
                {"Topic_id": 101, "Project_Name": "Villa Sunset"},
                {"Topic_id": 102, "Project_Name": "Guest House"},
            ],
            "sensors": [self.sensor_data],
        }

        self.sensor = KoolnovaHumiditySensor(
            self.coordinator, self.config_entry, self.sensor_data
        )
        self.sensor.async_write_ha_state = MagicMock()

    def test_init_and_properties_with_project(self):
        """Test sensor initialization and attributes when project data matches."""
        self.assertTrue(self.sensor._attr_has_entity_name)
        self.assertEqual(self.sensor._attr_device_class, SensorDeviceClass.HUMIDITY)
        self.assertEqual(self.sensor._attr_state_class, SensorStateClass.MEASUREMENT)
        self.assertEqual(self.sensor._attr_native_unit_of_measurement, PERCENTAGE)
        self.assertFalse(self.sensor.should_poll)
        self.assertEqual(self.sensor.name, "Master Bedroom Humidity")
        self.assertEqual(
            self.sensor.unique_id,
            "test_entry_id_zone_1_humidity",
        )
        self.assertEqual(
            self.sensor.device_info["identifiers"],
            {(DOMAIN, "test_entry_id_101")},
        )
        self.assertEqual(self.sensor.device_info["name"], "Koolnova Villa Sunset")
        self.assertEqual(self.sensor.device_info["manufacturer"], "Koolnova")
        self.assertEqual(self.sensor.device_info["model"], "REST API Gateway")

    def test_init_and_properties_fallback_project(self):
        """Test fallback project name and Topic_id when sensor has no or unmatched Topic_id."""
        # Case 1: Topic_id is missing from sensor, projects list is empty
        coordinator_fallback = MagicMock()
        coordinator_fallback.data = {"projects": [], "sensors": []}

        sensor_no_topic = {
            "Room_id": 2,
            "Room_Name": "Attic",
            "Room_humidity": 60,
        }
        sensor_entity = KoolnovaHumiditySensor(
            coordinator_fallback, self.config_entry, sensor_no_topic
        )

        self.assertEqual(
            sensor_entity.device_info["identifiers"],
            {(DOMAIN, "test_entry_id_global")},
        )
        self.assertEqual(sensor_entity.device_info["name"], "Koolnova System")

        # Case 2: Topic_id present in sensor but not matched in projects
        sensor_unmatched_topic = {
            "Room_id": 3,
            "Room_Name": "Basement",
            "Room_humidity": 70,
            "Topic_id": 999,
        }
        sensor_entity_2 = KoolnovaHumiditySensor(
            coordinator_fallback, self.config_entry, sensor_unmatched_topic
        )
        self.assertEqual(
            sensor_entity_2.device_info["identifiers"],
            {(DOMAIN, "test_entry_id_999")},
        )
        self.assertEqual(sensor_entity_2.device_info["name"], "Koolnova System")

    async def test_async_added_to_hass(self):
        """Test that sensor registers listener with coordinator on add."""
        self.sensor.async_on_remove = MagicMock()

        await self.sensor.async_added_to_hass()

        self.coordinator.async_add_listener.assert_called_once_with(
            self.sensor.async_write_ha_state
        )
        self.sensor.async_on_remove.assert_called_once()

    def test_availability(self):
        """Test sensor availability reflects coordinator.last_update_success."""
        self.coordinator.last_update_success = True
        self.assertTrue(self.sensor.available)

        self.coordinator.last_update_success = False
        self.assertFalse(self.sensor.available)

    def test_native_value_and_update_sensor_data(self):
        """Test native_value reflects initial and updated coordinator sensor data."""
        # Initial value
        self.assertEqual(self.sensor.native_value, 50)

        # Update humidity in coordinator data
        updated_sensor = {
            "Room_id": 1,
            "Room_Name": "Master Bedroom",
            "Room_humidity": 58,
            "Topic_id": 101,
        }
        self.coordinator.data = {
            "projects": [{"Topic_id": 101, "Project_Name": "Villa Sunset"}],
            "sensors": [updated_sensor],
        }

        self.assertEqual(self.sensor.native_value, 58)

    def test_native_value_zero(self):
        """Test native_value handles 0% humidity properly."""
        updated_sensor = {
            "Room_id": 1,
            "Room_Name": "Master Bedroom",
            "Room_humidity": 0,
            "Topic_id": 101,
        }
        self.coordinator.data = {"sensors": [updated_sensor]}

        self.assertEqual(self.sensor.native_value, 0)

    def test_update_sensor_data_sensor_not_in_coordinator(self):
        """Test _update_sensor_data retains previous sensor when Room_id is not in coordinator."""
        self.assertEqual(self.sensor.native_value, 50)

        # Coordinator data without this room
        self.coordinator.data = {
            "sensors": [{"Room_id": 99, "Room_humidity": 30}]
        }

        # Should retain previous sensor data and humidity
        self.assertEqual(self.sensor.native_value, 50)


if __name__ == "__main__":
    unittest.main()
