"""Tests for the Koolnova <-> Home Assistant code tables.

`const.py` imports from Home Assistant, which is not installed here, so a minimal stub
of `homeassistant.components.climate` is registered before importing it. The stub uses
Home Assistant's real string values, which is what the mappings ultimately produce.

These tables are easy to get subtly wrong — the project modes 4 and 6 were documented
swapped for a long time — and a wrong entry silently heats the house when asked to cool.
"""

import importlib.util
import sys
import types
import unittest
from enum import StrEnum
from pathlib import Path


def _install_home_assistant_stub():
    """Register a stand-in for the parts of Home Assistant that const.py imports."""
    if "homeassistant.components.climate" in sys.modules:
        return

    class HVACMode(StrEnum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        HEAT_COOL = "heat_cool"
        AUTO = "auto"
        DRY = "dry"
        FAN_ONLY = "fan_only"

    climate = types.ModuleType("homeassistant.components.climate")
    climate.HVACMode = HVACMode
    climate.FAN_LOW = "low"
    climate.FAN_MEDIUM = "medium"
    climate.FAN_HIGH = "high"
    climate.FAN_AUTO = "auto"

    homeassistant = types.ModuleType("homeassistant")
    components = types.ModuleType("homeassistant.components")
    components.climate = climate
    homeassistant.components = components

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.climate"] = climate


def _load_const():
    _install_home_assistant_stub()
    path = Path(__file__).resolve().parent.parent / "custom_components" / "koolnova" / "const.py"
    spec = importlib.util.spec_from_file_location("koolnova_const", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


const = _load_const()


class ProjectModeTest(unittest.TestCase):
    def test_project_mode_codes(self):
        self.assertEqual(
            const.KOOLNOVA_TO_HVAC_MODE,
            {"1": "cool", "2": "heat", "3": "heat", "4": "heat", "5": "cool", "6": "auto"},
        )

    def test_project_mode_code_is_chosen_by_mode_and_heat_source(self):
        self.assertEqual(
            const.KOOLNOVA_PROJECT_MODE_CODE,
            {
                ("cool", "air"): "1",
                ("cool", "both"): "5",
                ("heat", "air"): "2",
                ("heat", "floor"): "3",
                ("heat", "both"): "4",
                ("auto", "air"): "6",
                ("auto", "floor"): "6",
                ("auto", "both"): "6",
            },
        )

    def test_every_code_sent_reads_back_as_the_requested_mode(self):
        """A command must never come back as something else.

        This is the regression that made 'off' switch the heating on: the old table
        mapped 'off' to 2, which the app labels 'hot air'.
        """
        for (mode, _source), code in const.KOOLNOVA_PROJECT_MODE_CODE.items():
            with self.subTest(mode=mode, code=code):
                self.assertEqual(const.KOOLNOVA_TO_HVAC_MODE[code], mode)

    def test_cool_floor_alone_has_no_code(self):
        """The app has no cool-floor-only entry, so it must fail loudly."""
        self.assertNotIn(("cool", const.HEAT_SOURCE_FLOOR), const.KOOLNOVA_PROJECT_MODE_CODE)

    def test_cool_and_heat_never_share_a_code(self):
        for source in const.AVAILABLE_HEAT_SOURCES:
            cooling = const.KOOLNOVA_PROJECT_MODE_CODE.get(("cool", source))
            heating = const.KOOLNOVA_PROJECT_MODE_CODE.get(("heat", source))
            if cooling is None or heating is None:
                continue
            with self.subTest(source=source):
                self.assertNotEqual(cooling, heating)

    def test_heat_source_mapping_matches_the_code_table(self):
        """1 and 2 drive the air circuit, 3 the floor, 4 and 5 both together."""
        self.assertEqual(
            const.KOOLNOVA_MODE_TO_HEAT_SOURCE,
            {
                "1": const.HEAT_SOURCE_AIR,
                "2": const.HEAT_SOURCE_AIR,
                "3": const.HEAT_SOURCE_FLOOR,
                "4": const.HEAT_SOURCE_BOTH,
                "5": const.HEAT_SOURCE_BOTH,
            },
        )

    def test_stopping_is_a_flag_not_a_mode(self):
        """No mode code reads back as off: the installation stops via is_stop."""
        self.assertNotIn("off", const.KOOLNOVA_TO_HVAC_MODE.values())
        self.assertEqual(const.KOOLNOVA_PROJECT_STOP_KEY, "is_stop")
        for (mode, _source) in const.KOOLNOVA_PROJECT_MODE_CODE:
            with self.subTest(mode=mode):
                self.assertNotEqual(mode, "off")

    def test_auto_is_code_6_and_ignores_the_circuit(self):
        """AUTO exists (code 6) and carries the same code on every source."""
        self.assertEqual(const.KOOLNOVA_TO_HVAC_MODE["6"], "auto")
        for source in const.AVAILABLE_HEAT_SOURCES:
            with self.subTest(source=source):
                self.assertEqual(
                    const.KOOLNOVA_PROJECT_MODE_CODE[("auto", source)],
                    const.KOOLNOVA_MODE_AUTO,
                )

    def test_auto_has_no_heat_source(self):
        self.assertNotIn(const.KOOLNOVA_MODE_AUTO, const.KOOLNOVA_MODE_TO_HEAT_SOURCE)

    def test_default_heat_source_is_selectable(self):
        self.assertIn(const.DEFAULT_HEAT_SOURCE, const.AVAILABLE_HEAT_SOURCES)
        self.assertEqual(len(const.AVAILABLE_HEAT_SOURCES), 3)


class ZoneStatusTest(unittest.TestCase):
    def test_zone_status_codes(self):
        self.assertEqual(
            const.KOOLNOVA_ZONE_STATUS_TO_HVAC,
            {"00": "cool", "01": "heat", "02": "off", "03": "auto"},
        )

    def test_zone_status_inverse_round_trips(self):
        for code, mode in const.KOOLNOVA_ZONE_STATUS_TO_HVAC.items():
            with self.subTest(code=code):
                self.assertEqual(const.HVAC_TO_KOOLNOVA_ZONE_STATUS[mode], code)

    def test_zone_and_project_encodings_stay_distinct(self):
        """Zone codes are zero-padded pairs, project codes are single digits."""
        self.assertTrue(all(len(code) == 2 for code in const.KOOLNOVA_ZONE_STATUS_TO_HVAC))
        self.assertTrue(all(len(code) == 1 for code in const.KOOLNOVA_TO_HVAC_MODE))


class FanSpeedTest(unittest.TestCase):
    def test_fan_speed_codes(self):
        self.assertEqual(
            const.KOOLNOVA_TO_FAN,
            {"1": "low", "2": "medium", "3": "high", "4": "auto"},
        )

    def test_fan_inverse_round_trips(self):
        for code, speed in const.KOOLNOVA_TO_FAN.items():
            with self.subTest(code=code):
                self.assertEqual(const.FAN_TO_KOOLNOVA[speed], code)


class LimitsTest(unittest.TestCase):
    def test_polling_never_goes_below_the_koolnova_ban_threshold(self):
        """Koolnova bans IPs polled more often than once every 30 s."""
        self.assertGreaterEqual(const.MIN_UPDATE_INTERVAL, 30)
        self.assertGreaterEqual(const.DEFAULT_UPDATE_INTERVAL, const.MIN_UPDATE_INTERVAL)

    def test_interval_bounds_are_ordered(self):
        self.assertLess(const.MIN_UPDATE_INTERVAL, const.MAX_UPDATE_INTERVAL)
        self.assertLessEqual(const.DEFAULT_UPDATE_INTERVAL, const.MAX_UPDATE_INTERVAL)

    def test_project_update_frequency_bounds_are_ordered(self):
        self.assertLessEqual(const.MIN_PROJECT_UPDATE_FREQUENCY, const.DEFAULT_PROJECT_UPDATE_FREQUENCY)
        self.assertLessEqual(const.DEFAULT_PROJECT_UPDATE_FREQUENCY, const.MAX_PROJECT_UPDATE_FREQUENCY)

    def test_temperature_defaults_sit_inside_the_configurable_range(self):
        self.assertLess(const.DEFAULT_MIN_TEMP, const.DEFAULT_MAX_TEMP)
        self.assertGreaterEqual(const.DEFAULT_MIN_TEMP, const.MIN_CONFIGURABLE_TEMP)
        self.assertLessEqual(const.DEFAULT_MAX_TEMP, const.MAX_CONFIGURABLE_TEMP)

    def test_default_modes_are_offered_by_the_config_flow(self):
        for mode in const.DEFAULT_PROJECT_HVAC_MODES + const.DEFAULT_ZONE_HVAC_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, const.AVAILABLE_HVAC_MODES)

    def test_every_available_zone_mode_can_be_encoded(self):
        for mode in const.AVAILABLE_HVAC_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, const.HVAC_TO_KOOLNOVA_ZONE_STATUS)

    def test_supported_combinations_are_encodable(self):
        """Cooling on air or both, heating on air, floor or both, plus auto."""
        for combination in (
            ("cool", const.HEAT_SOURCE_AIR),
            ("cool", const.HEAT_SOURCE_BOTH),
            ("heat", const.HEAT_SOURCE_AIR),
            ("heat", const.HEAT_SOURCE_FLOOR),
            ("heat", const.HEAT_SOURCE_BOTH),
            ("auto", const.HEAT_SOURCE_AIR),
        ):
            with self.subTest(combination=combination):
                self.assertIn(combination, const.KOOLNOVA_PROJECT_MODE_CODE)

    def test_off_has_no_project_code(self):
        """OFF is the is_stop flag, not a mode."""
        for source in const.AVAILABLE_HEAT_SOURCES:
            with self.subTest(source=source):
                self.assertNotIn(("off", source), const.KOOLNOVA_PROJECT_MODE_CODE)

    def test_default_precision_is_selectable(self):
        self.assertIn(const.DEFAULT_TEMP_PRECISION, const.AVAILABLE_TEMP_PRECISIONS)


class PlatformsTest(unittest.TestCase):
    def test_domain_and_platforms(self):
        self.assertEqual(const.DOMAIN, "koolnova")
        self.assertEqual(const.PLATFORMS, ["climate", "binary_sensor", "switch", "sensor"])


if __name__ == "__main__":
    unittest.main()
