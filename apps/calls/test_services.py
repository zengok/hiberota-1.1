from __future__ import annotations

from datetime import timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.calls.services import calculate_availability_status


class AvailabilityStatusTests(SimpleTestCase):
    def test_unknown_when_dates_are_missing(self) -> None:
        status = calculate_availability_status(now=timezone.now())

        self.assertEqual(status, GrantCall.AvailabilityStatus.UNKNOWN)

    def test_upcoming_when_open_date_is_future(self) -> None:
        now = timezone.now()

        status = calculate_availability_status(
            application_open_at=now + timedelta(days=2),
            deadline_at=now + timedelta(days=30),
            now=now,
        )

        self.assertEqual(status, GrantCall.AvailabilityStatus.UPCOMING)

    def test_closed_when_deadline_has_passed(self) -> None:
        now = timezone.now()

        status = calculate_availability_status(deadline_at=now - timedelta(minutes=1), now=now)

        self.assertEqual(status, GrantCall.AvailabilityStatus.CLOSED)

    def test_closing_soon_inside_window(self) -> None:
        now = timezone.now()

        status = calculate_availability_status(deadline_at=now + timedelta(days=3), now=now)

        self.assertEqual(status, GrantCall.AvailabilityStatus.CLOSING_SOON)

    def test_open_when_deadline_is_beyond_window(self) -> None:
        now = timezone.now()

        status = calculate_availability_status(deadline_at=now + timedelta(days=30), now=now)

        self.assertEqual(status, GrantCall.AvailabilityStatus.OPEN)
