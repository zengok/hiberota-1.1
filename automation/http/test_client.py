from __future__ import annotations

from django.test import SimpleTestCase

from automation.http.client import SafeHttpRequest, UnsafeUrlError, is_robots_allowed, validate_target_url


def public_resolver(host: str, port: int) -> list[str]:
    return ["93.184.216.34"]


def private_resolver(host: str, port: int) -> list[str]:
    return ["127.0.0.1"]


class SafeHttpClientTests(SimpleTestCase):
    def test_allows_public_allowlisted_https_url(self) -> None:
        parsed = validate_target_url(
            "https://example.org/calls",
            frozenset({"example.org"}),
            resolver=public_resolver,
        )

        self.assertEqual(parsed.hostname, "example.org")

    def test_rejects_non_allowlisted_host(self) -> None:
        with self.assertRaises(UnsafeUrlError):
            validate_target_url(
                "https://evil.example/calls",
                frozenset({"example.org"}),
                resolver=public_resolver,
            )

    def test_rejects_private_ip_resolution(self) -> None:
        with self.assertRaises(UnsafeUrlError):
            validate_target_url(
                "https://example.org/calls",
                frozenset({"example.org"}),
                resolver=private_resolver,
            )

    def test_rejects_userinfo(self) -> None:
        with self.assertRaises(UnsafeUrlError):
            validate_target_url(
                "https://user:pass@example.org/calls",
                frozenset({"example.org"}),
                resolver=public_resolver,
            )

    def test_request_defaults_are_conservative(self) -> None:
        request = SafeHttpRequest(
            url="https://example.org/calls",
            allowed_hosts=frozenset({"example.org"}),
            user_agent="HibeRotaBot/1.0",
            contact_email="security@example.invalid",
        )

        self.assertEqual(request.max_redirects, 3)
        self.assertLessEqual(request.max_response_bytes, 2_000_000)

    def test_robots_rules_can_disallow_path(self) -> None:
        robots_txt = "User-agent: *\nDisallow: /private\n"

        self.assertFalse(is_robots_allowed(robots_txt, "HibeRotaBot/1.0", "https://example.org/private/call"))
        self.assertTrue(is_robots_allowed(robots_txt, "HibeRotaBot/1.0", "https://example.org/public/call"))
