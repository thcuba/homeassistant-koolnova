import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator
from custom_components.koolnova.const import CONF_UPDATE_INTERVAL

class TestKoolnovaMultiProject(unittest.TestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.data = {
            "email": "test@example.com",
            "password": "password",
            CONF_UPDATE_INTERVAL: 60
        }
        self.config_entry.options = {}
        self.config_entry.entry_id = "test_entry_id"

        with patch('custom_components.koolnova.coordinator.KoolnovaAPIRestClient'):
            self.coordinator = KoolnovaDataUpdateCoordinator(self.hass, self.config_entry)

        self.coordinator.data = {
            "projects": [
                {"Topic_id": 1, "Project_Name": "Project 1"},
                {"Topic_id": 2, "Project_Name": "Project 2"}
            ],
            "sensors": [
                {"Room_id": 101, "Topic_id": 1, "Room_Name": "Room 1.1"},
                {"Room_id": 102, "Topic_id": 1, "Room_Name": "Room 1.2"},
                {"Room_id": 201, "Topic_id": 2, "Room_Name": "Room 2.1"}
            ]
        }

    def test_async_update_all_sensors_temperature_filtered(self):
        """Test filtering by topic_id in async_update_all_sensors_temperature."""
        self.coordinator.async_update_sensor_data = AsyncMock()

        asyncio.run(self.coordinator.async_update_all_sensors_temperature(22.5, topic_id=1))

        # Should only call for sensors in Topic 1
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 2)
        called_ids = [call.args[0] for call in self.coordinator.async_update_sensor_data.call_args_list]
        self.assertIn(101, called_ids)
        self.assertIn(102, called_ids)
        self.assertNotIn(201, called_ids)

    def test_async_update_all_sensors_status_filtered(self):
        """Test filtering by topic_id in async_update_all_sensors_status."""
        self.coordinator.async_update_sensor_data = AsyncMock()

        asyncio.run(self.coordinator.async_update_all_sensors_status("01", topic_id=2))

        # Should only call for sensors in Topic 2
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 1)
        self.coordinator.async_update_sensor_data.assert_called_once_with(201, {"status": "01"})

if __name__ == "__main__":
    unittest.main()
