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
            {"1": "cool", "2": "heat", "3": "heat", "5": "cool", "6": "heat"},
        )

    def test_project_mode_code_is_chosen_by_mode_and_heat_source(self):
        self.assertEqual(
            const.KOOLNOVA_PROJECT_MODE_CODE,
            {
                ("cool", "air"): "1",
                ("cool", "both"): "5",
                ("heat", "air"): "2",
                ("heat", "floor"): "3",
                ("heat", "both"): "6",
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
        """1 and 2 drive the air circuit, 3 the floor, 5 and 6 both together."""
        self.assertEqual(
            const.KOOLNOVA_MODE_TO_HEAT_SOURCE,
            {
                "1": const.HEAT_SOURCE_AIR,
                "2": const.HEAT_SOURCE_AIR,
                "3": const.HEAT_SOURCE_FLOOR,
                "5": const.HEAT_SOURCE_BOTH,
                "6": const.HEAT_SOURCE_BOTH,
            },
        )

    def test_stopping_is_a_flag_not_a_mode(self):
        """No mode code reads back as off: the installation stops via is_stop."""
        self.assertNotIn("off", const.KOOLNOVA_TO_HVAC_MODE.values())
        self.assertEqual(const.KOOLNOVA_PROJECT_STOP_KEY, "is_stop")
        for (mode, _source) in const.KOOLNOVA_PROJECT_MODE_CODE:
            with self.subTest(mode=mode):
                self.assertNotEqual(mode, "off")

    def test_heat_both_is_code_6_not_auto(self):
        """What looked like AUTO is the 'heat floor + hot air' combination."""
        self.assertEqual(const.KOOLNOVA_TO_HVAC_MODE["6"], "heat")
        self.assertEqual(const.KOOLNOVA_MODE_HEAT_BOTH, "6")
        self.assertEqual(const.KOOLNOVA_MODE_TO_HEAT_SOURCE["6"], const.HEAT_SOURCE_BOTH)

    def test_there_is_no_auto_code(self):
        """The app has no auto entry: nothing may be read or written as auto."""
        self.assertNotIn("auto", const.KOOLNOVA_TO_HVAC_MODE.values())
        for (mode, _source) in const.KOOLNOVA_PROJECT_MODE_CODE:
            with self.subTest(mode=mode):
                self.assertNotEqual(mode, "auto")

    def test_code_4_is_left_unmapped(self):
        """Code 4 appears in the app's list but is not identified yet: guessing is
        worse than logging it, so it must stay out of the table."""
        self.assertNotIn("4", const.KOOLNOVA_TO_HVAC_MODE)
        self.assertNotIn("4", const.KOOLNOVA_MODE_TO_HEAT_SOURCE)

    def test_default_heat_source_is_selectable(self):
        self.assertIn(const.DEFAULT_HEAT_SOURCE, const.AVAILABLE_HEAT_SOURCES)
        self.assertEqual(len(const.AVAILABLE_HEAT_SOURCES), 3)


class ProjectPresetsTest(unittest.TestCase):
    def test_presets_are_the_five_known_entries(self):
        self.assertEqual(
            const.KOOLNOVA_PRESET_CODES,
            {
                "cool_air": "1",
                "hot_air": "2",
                "heat_floor": "3",
                "cool_both": "5",
                "heat_both": "6",
            },
        )

    def test_every_preset_maps_to_a_known_code(self):
        for name, code in const.KOOLNOVA_PRESET_CODES.items():
            with self.subTest(preset=name):
                self.assertIn(code, const.KOOLNOVA_TO_HVAC_MODE)

    def test_preset_reverse_mapping_round_trips(self):
        for name, code in const.KOOLNOVA_PRESET_CODES.items():
            with self.subTest(preset=name):
                self.assertEqual(const.KOOLNOVA_MODE_TO_PRESET[code], name)

    def test_unmapped_and_missing_codes_have_no_preset(self):
        """Off is a flag and code 4 is unknown: neither may claim a preset."""
        self.assertEqual(len(const.KOOLNOVA_MODE_TO_PRESET), len(const.KOOLNOVA_PRESET_CODES))
        self.assertNotIn("4", const.KOOLNOVA_MODE_TO_PRESET)


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
        """Cooling on air or both, heating on air, floor or both."""
        for combination in (
            ("cool", const.HEAT_SOURCE_AIR),
            ("cool", const.HEAT_SOURCE_BOTH),
            ("heat", const.HEAT_SOURCE_AIR),
            ("heat", const.HEAT_SOURCE_FLOOR),
            ("heat", const.HEAT_SOURCE_BOTH),
        ):
            with self.subTest(combination=combination):
                self.assertIn(combination, const.KOOLNOVA_PROJECT_MODE_CODE)

    def test_off_and_auto_have_no_project_code(self):
        """OFF is the is_stop flag and the app has no auto entry."""
        for source in const.AVAILABLE_HEAT_SOURCES:
            for mode in ("off", "auto"):
                with self.subTest(mode=mode, source=source):
                    self.assertNotIn((mode, source), const.KOOLNOVA_PROJECT_MODE_CODE)

    def test_default_precision_is_selectable(self):
        self.assertIn(const.DEFAULT_TEMP_PRECISION, const.AVAILABLE_TEMP_PRECISIONS)


class PlatformsTest(unittest.TestCase):
    def test_domain_and_platforms(self):
        self.assertEqual(const.DOMAIN, "koolnova")
        self.assertEqual(const.PLATFORMS, ["climate", "binary_sensor", "switch", "sensor"])


class ProjectModeSelectionTest(unittest.TestCase):
    """Le modalita' offerte per il progetto devono essere quelle che il progetto esegue.

    Offrire `auto` non era innocuo: non esiste un codice `auto` nel payload del progetto, quindi
    sceglierlo non mandava nulla e l'unica traccia era una riga di log (issue #96, provato da
    @DaniCai130 nell'app: "auto -> no effect").
    """

    def test_the_project_offers_only_modes_it_can_execute(self):
        values = [mode.value for mode in const.PROJECT_HVAC_MODES]
        self.assertEqual(values, ["cool", "heat", "off"])
        self.assertNotIn("auto", values)

    def test_every_offered_mode_but_off_has_a_code(self):
        """Se una modalita' appare nella lista, deve esistere una combinazione che la scriva."""
        codable = {mode for mode, _source in const.KOOLNOVA_PROJECT_MODE_CODE}
        for mode in const.PROJECT_HVAC_MODES:
            if mode == const.HVACMode.OFF:
                continue
            self.assertIn(mode, codable, f"{mode} e' offerta ma non ha nessun codice")

    def test_auto_is_dropped_from_saved_options(self):
        kept = const.filter_project_hvac_modes(["auto", "cool"])
        self.assertEqual([mode.value for mode in kept], ["cool"])

    def test_options_with_nothing_valid_fall_back_to_the_default(self):
        """Un'entita' senza modalita' sarebbe peggio di un default: si ricade sul default."""
        kept = const.filter_project_hvac_modes(["auto"])
        self.assertEqual(
            [mode.value for mode in kept],
            [mode.value for mode in const.DEFAULT_PROJECT_HVAC_MODES],
        )

    def test_duplicates_and_unknown_values_do_not_break_the_list(self):
        kept = const.filter_project_hvac_modes(["heat", "heat", "boh", "off"])
        self.assertEqual([mode.value for mode in kept], ["heat", "off"])

    def test_the_order_is_stable_regardless_of_how_the_options_are_saved(self):
        kept = const.filter_project_hvac_modes(["off", "heat", "cool"])
        self.assertEqual([mode.value for mode in kept], ["cool", "heat", "off"])

    def test_zones_still_offer_auto(self):
        """Il taglio riguarda il solo progetto: lo status 03 delle zone esiste davvero."""
        self.assertIn(const.HVACMode.AUTO, const.AVAILABLE_HVAC_MODES)

    def test_the_fan_auto_is_untouched(self):
        """`auto` come velocita' ventola e' un'altra cosa e funziona.

        Chiarito da @DaniCai130: nell'app Koolnova "Auto" e' una velocita' della ventola.
        Questi test esistono perche' un domani nessuno "ripulisca" auto anche dalle ventole
        dopo averlo tolto dalle modalita' del progetto.
        """
        self.assertEqual(const.KOOLNOVA_TO_FAN["4"], const.FAN_AUTO)
        self.assertEqual(const.FAN_TO_KOOLNOVA[const.FAN_AUTO], "4")

    def test_an_empty_selection_is_handled(self):
        self.assertEqual(
            [mode.value for mode in const.filter_project_hvac_modes(None)],
            [mode.value for mode in const.DEFAULT_PROJECT_HVAC_MODES],
        )


class TopicModesTest(unittest.TestCase):
    """`TopicModes` is the topic configuration listing which mode codes are enabled.

    The string is positional: the character at index N is the flag for code N, so
    "0110011" enables 1, 2, 5 and 6 - the four codes this integration maps. Its length is
    whatever the installation reports, so positions past the known codes are ignored
    rather than treated as a contradiction.
    """

    def test_the_enabled_codes_come_from_the_positions_set_to_one(self):
        self.assertEqual(const.enabled_mode_codes("0110011"), ["1", "2", "5", "6"])

    def test_positions_holding_a_code_this_table_lacks_are_skipped(self):
        """Indexes 4 and 7 are set here and mean nothing yet, so they never become codes."""
        self.assertEqual(const.enabled_mode_codes("01101011"), ["1", "2", "6"])

    def test_a_missing_value_enables_nothing(self):
        """Nothing is known, so nothing is guessed here - see the helpers below."""
        for value in (None, "", 0, ["1"]):
            with self.subTest(value=value):
                self.assertEqual(const.enabled_mode_codes(value), [])

    def test_the_enabled_hvac_modes_follow_the_codes(self):
        self.assertEqual(
            [mode.value for mode in const.enabled_project_hvac_modes("0110011")],
            ["cool", "heat"],
        )

    def test_a_cool_only_installation_does_not_enable_heating(self):
        """Codes 1 and 5 only: no heating code is set."""
        self.assertEqual(
            [mode.value for mode in const.enabled_project_hvac_modes("0100010")],
            ["cool"],
        )

    def test_fan_only_is_never_offered_as_a_project_mode(self):
        """Position 0 is enabled by some installations, but fan_only is not a direction."""
        values = [mode.value for mode in const.enabled_project_hvac_modes("1100010")]
        self.assertNotIn("fan_only", values)

    def test_a_value_mapping_nothing_is_treated_as_unknown(self):
        self.assertIsNone(const.enabled_project_hvac_modes("1000000"))

    def test_an_unknown_installation_does_not_narrow_the_selection(self):
        """Senza TopicModes non si indovina: la selezione salvata resta quella scelta."""
        kept = const.filter_project_hvac_modes(["cool", "heat", "off"], None)
        self.assertEqual([mode.value for mode in kept], ["cool", "heat", "off"])

    def test_the_selection_is_narrowed_to_what_the_installation_enables(self):
        kept = const.filter_project_hvac_modes(["cool", "heat", "off"], "0100010")
        self.assertEqual([mode.value for mode in kept], ["cool", "off"])

    def test_off_survives_the_narrowing(self):
        """`off` is the is_stop flag, not a code, so no TopicModes value can remove it."""
        kept = const.filter_project_hvac_modes(["off"], "0100010")
        self.assertEqual([mode.value for mode in kept], ["off"])

    def test_a_contradicting_value_never_leaves_the_entity_without_a_mode(self):
        kept = const.filter_project_hvac_modes(["heat"], "0100010")
        self.assertEqual([mode.value for mode in kept], ["heat"])

    def test_the_configured_code_wins_when_the_installation_enables_it(self):
        self.assertEqual(const.mode_code_for("heat", "floor", "0111011"), "3")

    def test_a_disabled_code_falls_back_to_an_enabled_one_in_the_same_direction(self):
        """Code 3 is off here, so heating uses another circuit that is enabled."""
        self.assertEqual(const.mode_code_for("heat", "floor", "0110011"), "2")

    def test_a_direction_the_installation_cannot_run_has_no_code(self):
        self.assertIsNone(const.mode_code_for("heat", "air", "0100010"))

    def test_nothing_is_known_without_a_topic_modes_value(self):
        """Senza dato si tiene il codice storico: nessuna regressione per chi non ce l'ha."""
        self.assertEqual(const.mode_code_for("heat", "floor"), const.KOOLNOVA_MODE_HEAT_FLOOR)

    def test_cooling_on_the_underfloor_only_still_has_no_code(self):
        self.assertIsNone(const.mode_code_for("cool", "floor", "0111011"))


if __name__ == "__main__":
    unittest.main()
