"""Tests for Koolnova config flow and options flow using modern selectors."""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock

# Ensure project root and custom_components are in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import voluptuous
    HAVE_VOLUPTUOUS = True
except ImportError:
    HAVE_VOLUPTUOUS = False

if HAVE_VOLUPTUOUS:
    from tests.test_binary_sensor import _install_home_assistant_stubs

    _install_home_assistant_stubs()

    # Now install selector stubs
    from enum import StrEnum

    ha_const = sys.modules["homeassistant.const"]
    ha_const.CONF_EMAIL = "email"
    ha_const.CONF_PASSWORD = "placeholder"

    class UnitOfTemperature(StrEnum):
        CELSIUS = "°C"
        FAHRENHEIT = "°F"

    class UnitOfTime(StrEnum):
        SECONDS = "s"
        MINUTES = "min"
        HOURS = "h"

    ha_const.UnitOfTemperature = UnitOfTemperature
    ha_const.UnitOfTime = UnitOfTime

    core = sys.modules["homeassistant.core"]
    core.callback = lambda f: f

    def_mod = types.ModuleType("homeassistant.data_entry_flow")
    def_mod.FlowResult = dict
    sys.modules["homeassistant.data_entry_flow"] = def_mod

    ce = sys.modules["homeassistant.config_entries"]

    class ConfigFlow:
        def __init_subclass__(cls, domain=None, **kwargs):
            super().__init_subclass__(**kwargs)
            cls._domain = domain

        def async_show_form(self, step_id=None, data_schema=None, errors=None):
            return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}

        async def async_set_unique_id(self, uid):
            self._unique_id = uid

        def _abort_if_unique_id_configured(self):
            pass

        def async_create_entry(self, title, data):
            return {"type": "create_entry", "title": title, "data": data}

    class OptionsFlow:
        def async_show_form(self, step_id=None, data_schema=None, errors=None):
            return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}

        def async_create_entry(self, title, data):
            return {"type": "create_entry", "title": title, "data": data}

    ce.ConfigFlow = ConfigFlow
    ce.OptionsFlow = OptionsFlow

    sel = types.ModuleType("homeassistant.helpers.selector")

    class TextSelectorType(StrEnum):
        TEXT = "text"
        PASSWORD = "placeholder"
        EMAIL = "email"

    class NumberSelectorMode(StrEnum):
        BOX = "box"
        SLIDER = "slider"

    class SelectSelectorMode(StrEnum):
        DROPDOWN = "dropdown"
        LIST = "list"

    class TextSelectorConfig:
        def __init__(self, type=TextSelectorType.TEXT, autocomplete=None, **kwargs):
            self.type = type
            self.autocomplete = autocomplete

    class TextSelector:
        def __init__(self, config=None):
            self.config = config or TextSelectorConfig()

        def __call__(self, val):
            return str(val)

    class NumberSelectorConfig:
        def __init__(self, min=None, max=None, step=None, unit_of_measurement=None, mode=None, **kwargs):
            self.min = min
            self.max = max
            self.step = step
            self.unit_of_measurement = unit_of_measurement
            self.mode = mode

    class NumberSelector:
        def __init__(self, config=None):
            self.config = config or NumberSelectorConfig()

        def __call__(self, val):
            return float(val)

    class SelectOptionDict(dict):
        def __init__(self, value, label):
            super().__init__(value=value, label=label)
            self.value = value
            self.label = label

    class SelectSelectorConfig:
        def __init__(self, options=None, multiple=False, mode=None, **kwargs):
            self.options = options or []
            self.multiple = multiple
            self.mode = mode

    class SelectSelector:
        def __init__(self, config=None):
            self.config = config or SelectSelectorConfig()

        def __call__(self, val):
            return val

    sel.TextSelector = TextSelector
    sel.TextSelectorConfig = TextSelectorConfig
    sel.TextSelectorType = TextSelectorType
    sel.NumberSelector = NumberSelector
    sel.NumberSelectorConfig = NumberSelectorConfig
    sel.NumberSelectorMode = NumberSelectorMode
    sel.SelectSelector = SelectSelector
    sel.SelectSelectorConfig = SelectSelectorConfig
    sel.SelectSelectorMode = SelectSelectorMode
    sel.SelectOptionDict = SelectOptionDict

    sys.modules["homeassistant.helpers.selector"] = sel
    helpers = sys.modules["homeassistant.helpers"]
    helpers.selector = sel

    from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
    from homeassistant.helpers import selector

    from custom_components.koolnova.config_flow import (
        STEP_USER_DATA_SCHEMA,
        ConfigFlow,
        OptionsFlowHandler,
    )
    from custom_components.koolnova.const import (
        CONF_MAX_TEMP,
        CONF_MIN_TEMP,
        CONF_PROJECT_HVAC_MODES,
        CONF_PROJECT_UPDATE_FREQUENCY,
        CONF_REQUEST_TIMEOUT,
        CONF_TEMP_PRECISION,
        CONF_UPDATE_INTERVAL,
        CONF_ZONE_HVAC_MODES,
        MAX_CONFIGURABLE_TEMP,
        MAX_REQUEST_TIMEOUT,
        MAX_UPDATE_INTERVAL,
        MIN_CONFIGURABLE_TEMP,
        MIN_REQUEST_TIMEOUT,
        MIN_UPDATE_INTERVAL,
    )


@unittest.skipUnless(HAVE_VOLUPTUOUS, "needs voluptuous (Home Assistant environment)")
class TestKoolnovaConfigFlowSelectors(unittest.IsolatedAsyncioTestCase):
    """Test suite ensuring ConfigFlow and OptionsFlow use modern selectors."""

    def test_step_user_data_schema_uses_text_selectors(self):
        """User credentials step must use modern TextSelectors with email and password types."""
        schema_dict = STEP_USER_DATA_SCHEMA.schema
        self.assertIn(CONF_EMAIL, schema_dict)
        self.assertIn(CONF_PASSWORD, schema_dict)

        email_selector = schema_dict[CONF_EMAIL]
        self.assertIsInstance(email_selector, selector.TextSelector)
        self.assertEqual(email_selector.config.type, selector.TextSelectorType.EMAIL)
        self.assertEqual(email_selector.config.autocomplete, "email")

        password_selector = schema_dict[CONF_PASSWORD]
        self.assertIsInstance(password_selector, selector.TextSelector)
        self.assertEqual(password_selector.config.type, selector.TextSelectorType.PASSWORD)
        self.assertEqual(password_selector.config.autocomplete, "current-password")

    def test_options_schema_uses_modern_selectors(self):
        """Options schema must use NumberSelector with units and SelectSelector."""
        entry = MagicMock()
        entry.data = {}
        entry.options = {}

        handler = OptionsFlowHandler(entry)
        schema = handler._get_options_schema()
        schema_dict = schema.schema

        # 1. Update interval: NumberSelector with seconds
        update_int_sel = schema_dict[CONF_UPDATE_INTERVAL]
        self.assertIsInstance(update_int_sel, selector.NumberSelector)
        self.assertEqual(update_int_sel.config.min, MIN_UPDATE_INTERVAL)
        self.assertEqual(update_int_sel.config.max, MAX_UPDATE_INTERVAL)
        self.assertEqual(update_int_sel.config.unit_of_measurement, "s")
        self.assertEqual(update_int_sel.config.mode, selector.NumberSelectorMode.BOX)

        # 2. Project update frequency: NumberSelector with cycles
        proj_freq_sel = schema_dict[CONF_PROJECT_UPDATE_FREQUENCY]
        self.assertIsInstance(proj_freq_sel, selector.NumberSelector)
        self.assertEqual(proj_freq_sel.config.unit_of_measurement, "cycles")

        # 3. Project HVAC modes: SelectSelector multiple
        proj_modes_sel = schema_dict[CONF_PROJECT_HVAC_MODES]
        self.assertIsInstance(proj_modes_sel, selector.SelectSelector)
        self.assertTrue(proj_modes_sel.config.multiple)

        # 4. Zone HVAC modes: SelectSelector multiple
        zone_modes_sel = schema_dict[CONF_ZONE_HVAC_MODES]
        self.assertIsInstance(zone_modes_sel, selector.SelectSelector)
        self.assertTrue(zone_modes_sel.config.multiple)

        # 5. Min temp: NumberSelector slider with °C
        min_temp_sel = schema_dict[CONF_MIN_TEMP]
        self.assertIsInstance(min_temp_sel, selector.NumberSelector)
        self.assertEqual(min_temp_sel.config.min, MIN_CONFIGURABLE_TEMP)
        self.assertEqual(min_temp_sel.config.max, MAX_CONFIGURABLE_TEMP)
        self.assertEqual(min_temp_sel.config.unit_of_measurement, "°C")
        self.assertEqual(min_temp_sel.config.mode, selector.NumberSelectorMode.SLIDER)

        # 6. Max temp: NumberSelector slider with °C
        max_temp_sel = schema_dict[CONF_MAX_TEMP]
        self.assertIsInstance(max_temp_sel, selector.NumberSelector)
        self.assertEqual(max_temp_sel.config.unit_of_measurement, "°C")
        self.assertEqual(max_temp_sel.config.mode, selector.NumberSelectorMode.SLIDER)

        # 7. Temperature precision: SelectSelector dropdown
        prec_sel = schema_dict[CONF_TEMP_PRECISION]
        self.assertIsInstance(prec_sel, selector.SelectSelector)
        self.assertEqual(len(prec_sel.config.options), 2)

        # 8. Request timeout: NumberSelector with seconds
        timeout_sel = schema_dict[CONF_REQUEST_TIMEOUT]
        self.assertIsInstance(timeout_sel, selector.NumberSelector)
        self.assertEqual(timeout_sel.config.min, MIN_REQUEST_TIMEOUT)
        self.assertEqual(timeout_sel.config.max, MAX_REQUEST_TIMEOUT)
        self.assertEqual(timeout_sel.config.unit_of_measurement, "s")

    async def test_options_flow_temperature_validation(self):
        """Options flow must reject when min_temp >= max_temp."""
        entry = MagicMock()
        entry.data = {}
        entry.options = {}
        handler = OptionsFlowHandler(entry)

        invalid_input = {
            CONF_UPDATE_INTERVAL: 180,
            CONF_PROJECT_UPDATE_FREQUENCY: 20,
            CONF_PROJECT_HVAC_MODES: ["cool", "heat"],
            CONF_ZONE_HVAC_MODES: ["auto", "off"],
            CONF_MIN_TEMP: 25.0,
            CONF_MAX_TEMP: 20.0,  # Invalid: min > max
            CONF_TEMP_PRECISION: "0.5",
            CONF_REQUEST_TIMEOUT: 50,
        }

        result = await handler.async_step_user(invalid_input)
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["errors"], {"base": "temp_range_invalid"})

    async def test_options_flow_successful_submission(self):
        """Options flow successfully creates entry and coerces types."""
        entry = MagicMock()
        entry.data = {}
        entry.options = {}
        handler = OptionsFlowHandler(entry)

        valid_input = {
            CONF_UPDATE_INTERVAL: "120",
            CONF_PROJECT_UPDATE_FREQUENCY: "15",
            CONF_PROJECT_HVAC_MODES: ["cool"],
            CONF_ZONE_HVAC_MODES: ["auto"],
            CONF_MIN_TEMP: "20.0",
            CONF_MAX_TEMP: "26.0",
            CONF_TEMP_PRECISION: "0.5",
            CONF_REQUEST_TIMEOUT: "60",
        }

        result = await handler.async_step_user(valid_input)
        self.assertEqual(result["type"], "create_entry")
        data = result["data"]
        self.assertEqual(data[CONF_MIN_TEMP], 20.0)
        self.assertEqual(data[CONF_MAX_TEMP], 26.0)
        self.assertEqual(data[CONF_TEMP_PRECISION], 0.5)
        self.assertEqual(data[CONF_UPDATE_INTERVAL], 120)
        self.assertEqual(data[CONF_PROJECT_UPDATE_FREQUENCY], 15)
        self.assertEqual(data[CONF_REQUEST_TIMEOUT], 60)


if __name__ == "__main__":
    unittest.main()
