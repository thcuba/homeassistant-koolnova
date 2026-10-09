"""Tests for KoolnovaDataUpdateCoordinator methods, specifically async_update_all_sensors_status."""

import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure project root and custom_components are in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator


class TestKoolnovaCoordinatorStatus(unittest.IsolatedAsyncioTestCase):
    """Test suite for KoolnovaDataUpdateCoordinator.async_update_all_sensors_status."""

    def setUp(self):
        """Set up mock HomeAssistant and ConfigEntry for coordinator testing."""
        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.data = {
            "email": "test@example.com",
            "password": "secretpassword",
            "update_interval": 60,
            "project_update_frequency": 10,
        }
        self.config_entry.options = {}
        self.config_entry.entry_id = "test_entry_id"

        # Patch KoolnovaAPIRestClient during initialization so no network calls occur
        with patch("custom_components.koolnova.coordinator.KoolnovaAPIRestClient"):
            self.coordinator = KoolnovaDataUpdateCoordinator(
                self.hass, self.config_entry
            )

    async def test_async_update_all_sensors_status_all_sensors_success(self):
        """Test updating status for all sensors when topic_id is None."""
        self.coordinator.data = {
            "sensors": [
                {"Room_id": 1, "Room_Name": "Living Room", "Topic_id": 42},
                {"Room_id": 2, "Room_Name": "Bedroom", "Topic_id": 42},
            ]
        }

        self.coordinator.async_update_sensor_data = AsyncMock(
            return_value={"ok": True}
        )

        result = await self.coordinator.async_update_all_sensors_status("01", topic_id=None)

        self.assertEqual(result, {"updated": 2, "failed": 0})
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 2)
        self.coordinator.async_update_sensor_data.assert_any_call(1, {"status": "01"})
        self.coordinator.async_update_sensor_data.assert_any_call(2, {"status": "01"})

    async def test_async_update_all_sensors_status_filtered_by_topic_id(self):
        """Test updating status filtered by specific topic_id."""
        self.coordinator.data = {
            "sensors": [
                {"Room_id": 10, "Room_Name": "Room A", "Topic_id": 100},
                {"Room_id": 20, "Room_Name": "Room B", "Topic_id": 200},
                {"Room_id": 30, "Room_Name": "Room C", "Topic_id": 100},
            ]
        }

        self.coordinator.async_update_sensor_data = AsyncMock(
            return_value={"ok": True}
        )

        result = await self.coordinator.async_update_all_sensors_status("02", topic_id=100)

        self.assertEqual(result, {"updated": 2, "failed": 0})
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 2)
        self.coordinator.async_update_sensor_data.assert_any_call(10, {"status": "02"})
        self.coordinator.async_update_sensor_data.assert_any_call(30, {"status": "02"})

    async def test_async_update_all_sensors_status_partial_failure(self):
        """Test handling partial failures when updating individual sensors."""
        self.coordinator.data = {
            "sensors": [
                {"Room_id": 1, "Room_Name": "Room 1", "Topic_id": 10},
                {"Room_id": 2, "Room_Name": "Room 2", "Topic_id": 10},
            ]
        }

        async def _mock_update(sensor_id, payload):
            if sensor_id == 2:
                raise Exception("API failure")
            return {"ok": True}

        self.coordinator.async_update_sensor_data = AsyncMock(
            side_effect=_mock_update
        )

        result = await self.coordinator.async_update_all_sensors_status("00", topic_id=10)

        self.assertEqual(result, {"updated": 1, "failed": 1})
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 2)

    async def test_async_update_all_sensors_status_empty_sensors(self):
        """Test updating status when no sensors exist in coordinator data."""
        self.coordinator.data = {"sensors": []}
        self.coordinator.async_update_sensor_data = AsyncMock()

        result = await self.coordinator.async_update_all_sensors_status("00")

        self.assertEqual(result, {"updated": 0, "failed": 0})
        self.coordinator.async_update_sensor_data.assert_not_called()

    async def test_async_update_all_sensors_status_missing_room_id(self):
        """Test that sensors missing Room_id or with Room_id=None are skipped."""
        self.coordinator.data = {
            "sensors": [
                {"Room_Name": "Room No ID", "Topic_id": 10},
                {"Room_id": None, "Room_Name": "Room None ID", "Topic_id": 10},
                {"Room_id": 5, "Room_Name": "Valid Room", "Topic_id": 10},
            ]
        }

        self.coordinator.async_update_sensor_data = AsyncMock(
            return_value={"ok": True}
        )

        result = await self.coordinator.async_update_all_sensors_status("01", topic_id=10)

        self.assertEqual(result, {"updated": 1, "failed": 0})
        self.assertEqual(self.coordinator.async_update_sensor_data.call_count, 1)
        self.coordinator.async_update_sensor_data.assert_called_once_with(5, {"status": "01"})

    async def test_async_update_all_sensors_status_outer_exception_handling(self):
        """Test outer try-except block re-raises unexpected exceptions."""
        self.coordinator.data = None  # None.get("sensors") raises AttributeError

        with self.assertRaises(AttributeError):
            await self.coordinator.async_update_all_sensors_status("00")


if __name__ == "__main__":
    unittest.main()
