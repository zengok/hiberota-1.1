from __future__ import annotations

from io import BytesIO, StringIO
from types import TracebackType
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase


class FakeHttpResponse:
    def __init__(self, *, status: int, headers: dict[str, str], body: bytes) -> None:
        self.status = status
        self.headers = headers
        self._body = BytesIO(body)

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)


def fake_response(*, content_type: str, body: bytes, robots: str = "noindex, nofollow") -> FakeHttpResponse:
    return FakeHttpResponse(
        status=200,
        headers={
            "Content-Type": content_type,
            "X-Robots-Tag": robots,
        },
        body=body,
    )


class VerifyStagingSmokeCommandTests(SimpleTestCase):
    def test_command_passes_for_django_staging_responses(self) -> None:
        responses = [
            fake_response(content_type="application/json", body=b'{"status": "ok", "service": "hiberota"}'),
            fake_response(
                content_type="text/html; charset=utf-8",
                body=b'<html><head><link rel="canonical" href="https://staging.hiberota.com/"></head></html>',
            ),
        ]

        with patch(
            "apps.core.management.commands.verify_staging_smoke.urlopen",
            side_effect=responses,
        ):
            output = StringIO()
            call_command("verify_staging_smoke", stdout=output)

        self.assertIn("Staging smoke verification passed", output.getvalue())

    def test_command_fails_for_static_frontend_or_wrong_canonical(self) -> None:
        responses = [
            fake_response(content_type="text/html; charset=utf-8", body=b"<!doctype html><html></html>", robots=""),
            fake_response(
                content_type="text/html; charset=utf-8",
                body=b'<html><head><link rel="canonical" href="https://hiberota.com/"></head></html>',
                robots="",
            ),
        ]

        with patch(
            "apps.core.management.commands.verify_staging_smoke.urlopen",
            side_effect=responses,
        ):
            with self.assertRaises(CommandError):
                call_command("verify_staging_smoke")
