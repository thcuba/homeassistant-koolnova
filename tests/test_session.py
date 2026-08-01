"""Tests for the login request.

The login payload field is the single most fragile detail in this integration: v1.3.0
switched it from `email` to `username` and broke authentication for everyone, and
v1.3.1 had to revert it. These tests pin that behaviour down.
"""

import unittest
from unittest.mock import patch

from koolnova_api.session import KoolnovaClientSession


def _ok_response(payload=None, status=200):
    """Build a stand-in for requests.Response with just what the code touches."""

    class _Response:
        status_code = status
        headers = {}
        text = "{}"

        def json(self):
            return payload if payload is not None else {"access_token": "tok"}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    return _Response()


class LoginPayloadTest(unittest.TestCase):
    """What we send to /auth/v2/login/."""

    def _login(self, *args, **kwargs):
        with patch("requests.Session.request", return_value=_ok_response()) as request:
            KoolnovaClientSession(*args, **kwargs)
        return request.call_args

    def test_credentials_are_sent_under_email_not_username(self):
        """Regression guard for v1.3.0: 'username' makes the API answer 400."""
        _, kwargs = self._login("user@example.com", "secret")

        self.assertEqual(kwargs["json"], {"email": "user@example.com", "password": "secret"})
        self.assertNotIn("username", kwargs["json"])

    def test_explicit_email_argument_wins_over_username(self):
        _, kwargs = self._login("someone", "secret", email="real@example.com")

        self.assertEqual(kwargs["json"]["email"], "real@example.com")

    def test_posts_to_the_v2_login_endpoint(self):
        args, _ = self._login("user@example.com", "secret")

        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "https://api.koolnova.com/auth/v2/login/")

    def test_sends_browser_headers(self):
        """Regression guard for issue #4: without these the API answers 404."""
        _, kwargs = self._login("user@example.com", "secret")
        headers = kwargs["headers"]

        self.assertIn("Chrome/", headers["user-agent"])
        self.assertIn("sec-ch-ua", headers)
        self.assertIn("sec-fetch-mode", headers)
        self.assertEqual(headers["origin"], "https://app.koolnova.com")
        self.assertEqual(headers["content-type"], "application/json")


class TokenHandlingTest(unittest.TestCase):
    """What we do with the response."""

    def test_accepts_the_documented_token_field_names(self):
        for field in ("access_token", "token", "accessToken"):
            with self.subTest(field=field):
                with patch("requests.Session.request", return_value=_ok_response({field: "abc123"})):
                    session = KoolnovaClientSession("user@example.com", "secret")

                self.assertEqual(session.bearerToken, "abc123")

    def test_raises_when_the_response_carries_no_token(self):
        with patch("requests.Session.request", return_value=_ok_response({"detail": "nope"})):
            with self.assertRaises(RuntimeError):
                KoolnovaClientSession("user@example.com", "secret")

    def test_raises_on_a_rejected_login(self):
        with patch("requests.Session.request", return_value=_ok_response(status=400)):
            with self.assertRaises(RuntimeError):
                KoolnovaClientSession("user@example.com", "secret")

    def test_authenticated_requests_carry_the_bearer_token(self):
        with patch("requests.Session.request", return_value=_ok_response()):
            session = KoolnovaClientSession("user@example.com", "secret")

        with patch("requests.Session.request", return_value=_ok_response()) as request:
            session.rest_request("GET", "projects/")

        headers = request.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer tok")
        self.assertIn("Chrome/", headers["User-Agent"])

    def test_rest_request_builds_the_url_from_the_api_host(self):
        with patch("requests.Session.request", return_value=_ok_response()):
            session = KoolnovaClientSession("user@example.com", "secret")

        with patch("requests.Session.request", return_value=_ok_response()) as request:
            session.rest_request("GET", "topics/sensors/")

        self.assertEqual(request.call_args.args[1], "https://api.koolnova.com/topics/sensors/")


if __name__ == "__main__":
    unittest.main()
