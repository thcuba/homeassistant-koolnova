"""Binary sensor entities for Koolnova."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Koolnova binary sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    projects = coordinator.data.get("projects", [])
    if projects:
        for project in projects:
            entities.append(KoolnovaConnectivitySensor(coordinator, entry, project))
    else:
        entities.append(KoolnovaConnectivitySensor(coordinator, entry))

    async_add_entities(entities, update_before_add=False)


class KoolnovaConnectivitySensor(BinarySensorEntity):
    """Online/offline binary sensor for a Koolnova project."""

    _attr_has_entity_name = True
    _attr_translation_key = "connectivity_status"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_should_poll = False  # coordinator pushes updates via listener

    def __init__(self, coordinator, config_entry, project=None):
        """Initialize the connectivity sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._project = project

        topic_id = project.get("Topic_id", "global") if project else "global"
        project_name = project.get("Project_Name", "System") if project else "System"

        self._attr_unique_id = f"{config_entry.entry_id}_connectivity_{topic_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.entry_id}_{topic_id}")},
            name=f"Koolnova {project_name}",
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
        """Return true when the system is online."""
        topic_id = self._project.get("Topic_id") if self._project else None
        all_sensors = self.coordinator.data.get("sensors", [])

        sensors = all_sensors
        if topic_id is not None:
            sensors = [s for s in all_sensors if s.get("Topic_id") == topic_id]

        if not sensors:
            return False

        topic_info = sensors[0].get("topic_info", {})
        return bool(topic_info.get("is_online"))
