import unittest
from datetime import timedelta
from unittest.mock import MagicMock
from custom_components.koolnova.const import DEFAULT_UPDATE_INTERVAL, CONF_UPDATE_INTERVAL
from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator

class TestKoolnovaCoordinator(unittest.TestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.data = {
            "email": "test@example.com",
            "password": "password",
            CONF_UPDATE_INTERVAL: 10
        }
        self.config_entry.options = {
            CONF_UPDATE_INTERVAL: 20
        }
        self.config_entry.entry_id = "test_entry_id"

    def test_update_interval_initialization(self):
        """Test that the update interval is initialized from options."""
        coordinator = KoolnovaDataUpdateCoordinator(self.hass, self.config_entry)
        self.assertEqual(coordinator.update_interval, timedelta(seconds=20))

    def test_async_options_updated_changes_interval(self):
        """Test that async_options_updated correctly changes the update interval."""
        coordinator = KoolnovaDataUpdateCoordinator(self.hass, self.config_entry)

        # Change options to a different interval
        self.config_entry.options = {
            CONF_UPDATE_INTERVAL: 60,
            "project_update_frequency": 20
        }

        # Call async_options_updated
        import asyncio
        asyncio.run(coordinator.async_options_updated())

        self.assertEqual(coordinator.update_interval, timedelta(seconds=60))
        self.assertEqual(coordinator._project_update_frequency, 20)

if __name__ == "__main__":
    unittest.main()
