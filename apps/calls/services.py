from __future__ import annotations

from datetime import datetime, timedelta

from django.utils import timezone

from apps.calls.models import GrantCall


def calculate_availability_status(
    *,
    application_open_at: datetime | None = None,
    deadline_at: datetime | None = None,
    now: datetime | None = None,
    closing_soon_window: timedelta = timedelta(days=7),
) -> str:
    current_time = now or timezone.now()

    if deadline_at is None and application_open_at is None:
        return GrantCall.AvailabilityStatus.UNKNOWN

    if application_open_at is not None and application_open_at > current_time:
        return GrantCall.AvailabilityStatus.UPCOMING

    if deadline_at is None:
        return GrantCall.AvailabilityStatus.UNKNOWN

    if deadline_at < current_time:
        return GrantCall.AvailabilityStatus.CLOSED

    if deadline_at <= current_time + closing_soon_window:
        return GrantCall.AvailabilityStatus.CLOSING_SOON

    return GrantCall.AvailabilityStatus.OPEN


def apply_availability_status(call: GrantCall, *, now: datetime | None = None) -> GrantCall:
    call.availability_status = calculate_availability_status(
        application_open_at=call.application_open_at,
        deadline_at=call.deadline_at,
        now=now,
    )
    return call
