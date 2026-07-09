import unittest
from unittest.mock import MagicMock
from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator

class TestKoolnovaMultiProject(unittest.TestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.data = {
            "email": "test@example.com",
            "password": "password",
            "update_interval": 60
        }
        self.config_entry.options = {}
        self.config_entry.entry_id = "test_entry_id"

    def test_global_update_filtering(self):
        """Test that global update methods correctly filter by topic_id."""
        coordinator = KoolnovaDataUpdateCoordinator(self.hass, self.config_entry)

        # Mock data with two projects
        coordinator.data = {
            "projects": [
                {"Topic_id": 1, "Project_Name": "Project 1"},
                {"Topic_id": 2, "Project_Name": "Project 2"}
            ],
            "sensors": [
                {"Room_id": 101, "Topic_id": 1, "Room_Name": "P1 Room 1"},
                {"Room_id": 102, "Topic_id": 1, "Room_Name": "P1 Room 2"},
                {"Room_id": 201, "Topic_id": 2, "Room_Name": "P2 Room 1"}
            ]
        }

        # Mock async_update_sensor_data
        coordinator.async_update_sensor_data = MagicMock(side_effect=lambda sid, payload: payload)

        # Test temperature update for Project 1
        import asyncio
        asyncio.run(coordinator.async_update_all_sensors_temperature(25.0, topic_id=1))

        # Should have called async_update_sensor_data for 101 and 102, but not 201
        self.assertEqual(coordinator.async_update_sensor_data.call_count, 2)
        called_ids = [call.args[0] for call in coordinator.async_update_sensor_data.call_args_list]
        self.assertIn(101, called_ids)
        self.assertIn(102, called_ids)
        self.assertNotIn(201, called_ids)

        # Reset mock
        coordinator.async_update_sensor_data.reset_mock()

        # Test temperature update for Project 2
        asyncio.run(coordinator.async_update_all_sensors_temperature(22.0, topic_id=2))
        self.assertEqual(coordinator.async_update_sensor_data.call_count, 1)
        self.assertEqual(coordinator.async_update_sensor_data.call_args[0][0], 201)

if __name__ == "__main__":
    unittest.main()
