"""Tests for KoolnovaAPIRestClient: verbs, paths, parsing and the ban-avoidance cooldown."""

import logging
import unittest
from unittest.mock import MagicMock, patch

from koolnova_api.client import KoolnovaAPIRestClient
from koolnova_api.const import AUTH_FAILURE_COOLDOWN
from koolnova_api.exceptions import KoolnovaError

PROJECTS_PAYLOAD = {
    "data": [
        {
            "name": "Home",
            "topic": {
                "id": 42,
                "name": "Main topic",
                "mode": "1",
                "is_stop": False,
                "is_online": True,
                "eco": False,
                "last_sync": "2026-07-01T10:00:00Z",
            },
        }
    ]
}

SENSORS_PAYLOAD = {
    "data": [
        {
            "id": 7,
            "name": "Living room",
            "status": "00",
            "updated_at": "2026-07-01T10:00:00Z",
            "temperature": 23.4,
            "setpoint_temperature": 22.0,
            "speed": "2",
            "topic_info": {"id": 42, "rssi": -60, "is_online": True},
        }
    ]
}


class ClientTestCase(unittest.TestCase):
    """Base class wiring a client whose session is a mock."""

    def setUp(self):
        self.client = KoolnovaAPIRestClient("user@example.com", "secret")
        self.session = MagicMock()
        self.client.session = self.session
        # Pretend we authenticated just now so no login is attempted.
        self.session.token_created = float("inf")

    def _respond(self, payload):
        response = MagicMock()
        response.json.return_value = payload
        self.session.rest_request.return_value = response
        return response


class GetProjectTest(ClientTestCase):
    def test_requests_the_projects_endpoint_with_the_webapp_params(self):
        self._respond(PROJECTS_PAYLOAD)

        self.client.get_project()

        args, kwargs = self.session.rest_request.call_args
        self.assertEqual(args, ("GET", "projects/"))
        self.assertEqual(kwargs["params"]["page_size"], 25)
        self.assertEqual(kwargs["params"]["ordering"], "-start_date")
        self.assertIn("sec-ch-ua", kwargs["headers"])

    def test_flattens_the_topic_into_each_project(self):
        self._respond(PROJECTS_PAYLOAD)

        projects = self.client.get_project()

        self.assertEqual(len(projects), 1)
        self.assertEqual(
            projects[0],
            {
                "Project_Name": "Home",
                "Topic_Name": "Main topic",
                "Topic_id": 42,
                "Mode": "1",
                "is_stop": False,
                "is_online": True,
                "eco": False,
                "last_sync": "2026-07-01T10:00:00Z",
            },
        )

    def test_raises_when_the_api_returns_nothing(self):
        self._respond({})

        with self.assertRaises(KoolnovaError):
            self.client.get_project()

    def test_raises_when_there_are_no_projects(self):
        self._respond({"data": []})

        with self.assertRaises(KoolnovaError):
            self.client.get_project()

    def test_raises_instead_of_keyerror_when_data_is_missing(self):
        self._respond({"count": 0})

        with self.assertRaises(KoolnovaError):
            self.client.get_project()


class GetSensorsTest(ClientTestCase):
    def test_requests_the_sensors_endpoint(self):
        self._respond(SENSORS_PAYLOAD)

        self.client.get_sensors()

        args, _ = self.session.rest_request.call_args
        self.assertEqual(args, ("GET", "topics/sensors/"))

    def test_maps_room_fields_and_keeps_topic_info(self):
        self._respond(SENSORS_PAYLOAD)

        rooms = self.client.get_sensors()

        self.assertEqual(rooms[0]["Room_Name"], "Living room")
        self.assertEqual(rooms[0]["Room_id"], 7)
        self.assertEqual(rooms[0]["Room_actual_temp"], 23.4)
        self.assertEqual(rooms[0]["Room_setpoint_temp"], 22.0)
        self.assertEqual(rooms[0]["Topic_id"], 42)
        self.assertEqual(rooms[0]["topic_info"]["rssi"], -60)

    def test_topic_id_falls_back_when_topic_info_is_absent(self):
        payload = {"data": [dict(SENSORS_PAYLOAD["data"][0])]}
        del payload["data"][0]["topic_info"]
        self._respond(payload)

        rooms = self.client.get_sensors()

        self.assertEqual(rooms[0]["Topic_id"], "Unknown")
        self.assertEqual(rooms[0]["topic_info"], {})

    def test_raises_when_there_are_no_sensors(self):
        self._respond({"data": []})

        with self.assertRaises(KoolnovaError):
            self.client.get_sensors()


class UpdateTest(ClientTestCase):
    def test_updating_a_sensor_uses_put(self):
        """The sensors endpoint takes PUT; only topics takes PATCH."""
        self._respond({"ok": True})

        self.client.update_sensor(7, {"setpoint_temperature": 21.5})

        args, kwargs = self.session.rest_request.call_args
        self.assertEqual(args, ("PUT", "topics/sensors/7/"))
        self.assertEqual(kwargs["json"], {"setpoint_temperature": 21.5})
        self.assertEqual(kwargs["headers"]["content-type"], "application/json")

    def test_updating_a_project_uses_patch(self):
        self._respond({"ok": True})

        self.client.update_project(42, {"mode": "1"})

        args, kwargs = self.session.rest_request.call_args
        self.assertEqual(args, ("PATCH", "topics/42/"))
        self.assertEqual(kwargs["json"], {"mode": "1"})

    def test_the_response_body_is_parsed_once(self):
        response = self._respond({"ok": True})

        result = self.client.update_sensor(7, {"speed": "2"})

        self.assertEqual(result, {"ok": True})
        self.assertEqual(response.json.call_count, 1)


class AuthCooldownTest(unittest.TestCase):
    """Koolnova bans IPs that retry failed logins, so the client must back off."""

    def setUp(self):
        self.client = KoolnovaAPIRestClient("user@example.com", "secret")
        # These tests provoke login failures on purpose; keep the expected
        # error logging out of the test output.
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)

    def test_a_failed_login_is_recorded_and_reraised(self):
        with patch("koolnova_api.client.KoolnovaClientSession", side_effect=RuntimeError("nope")):
            with self.assertRaises(RuntimeError):
                self.client._get_session()

        self.assertIsNone(self.client.session)
        self.assertGreater(self.client._last_auth_failure, 0)

    def test_no_retry_during_the_cooldown_window(self):
        with patch("koolnova_api.client.KoolnovaClientSession", side_effect=RuntimeError("nope")):
            with self.assertRaises(RuntimeError):
                self.client._get_session()

            with patch("koolnova_api.client.KoolnovaClientSession") as session_cls:
                with self.assertRaises(KoolnovaError):
                    self.client._get_session()

                session_cls.assert_not_called()

    def test_retry_is_allowed_once_the_cooldown_has_elapsed(self):
        self.client._last_auth_failure = 1000.0

        with patch("koolnova_api.client.time.time", return_value=1000.0 + AUTH_FAILURE_COOLDOWN + 1):
            with patch("koolnova_api.client.KoolnovaClientSession") as session_cls:
                session_cls.return_value.token_created = float("inf")

                self.client._get_session()

                session_cls.assert_called_once()
        self.assertEqual(self.client._last_auth_failure, 0.0)

    def test_an_expired_token_triggers_a_new_session(self):
        stale = MagicMock()
        stale.token_created = 0.0
        self.client.session = stale

        self.assertFalse(self.client._is_session_valid())

    def test_a_fresh_token_is_reused(self):
        fresh = MagicMock()
        fresh.token_created = float("inf")
        self.client.session = fresh

        self.assertTrue(self.client._is_session_valid())


if __name__ == "__main__":
    unittest.main()
