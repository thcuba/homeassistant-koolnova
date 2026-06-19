"""Sensor entities for Koolnova."""
import logging
from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Koolnova sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Single connectivity sensor for the whole system
    entities.append(KoolnovaConnectivitySensor(coordinator, entry))

    async_add_entities(entities, update_before_add=False)

class KoolnovaConnectivitySensor(BinarySensorEntity):
    """Connectivity sensor for the Koolnova system."""

    _attr_has_entity_name = True
    _attr_translation_key = "connectivity_status"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_should_poll = False

    def __init__(self, coordinator, config_entry):
        """Initialize the connectivity sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_connectivity_status"

        # Device info based on the first project or generic
        project_id = "global"
        if coordinator.data.get("projects"):
            project_id = coordinator.data["projects"][0].get("Topic_id", "global")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.entry_id}_{project_id}")},
            name="Koolnova System",
            manufacturer="Koolnova",
            model="REST API Gateway",
        )

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self):
        """Return true if system is online."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return False

        topic_info = sensors[0].get("topic_info", {})
        return topic_info.get("is_online", False)

    @property
    def extra_state_attributes(self):
        """Return connectivity attributes in English snake_case."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return {}

        topic_info = sensors[0].get("topic_info", {})
        attrs = {
            "wifi_signal": topic_info.get("rssi"),
            "online_status": topic_info.get("is_online"),
        }

        system_last_sync = topic_info.get("last_sync")
        if system_last_sync:
            try:
                attrs["system_last_sync"] = datetime.fromisoformat(system_last_sync)
            except (ValueError, TypeError):
                attrs["system_last_sync"] = system_last_sync

        # Room sync times
        room_sync_times = {}
        for sensor in sensors:
            room_name = sensor.get("Room_Name", f"room_{sensor.get('Room_id')}")
            sensor_topic_info = sensor.get("topic_info", {})
            room_last_sync = sensor_topic_info.get("last_sync")
            if room_last_sync:
                room_sync_times[room_name.lower().replace(" ", "_")] = room_last_sync

        if room_sync_times:
            attrs["room_sync_times"] = room_sync_times

        return attrs
