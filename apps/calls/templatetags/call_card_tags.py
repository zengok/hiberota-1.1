from __future__ import annotations

from datetime import datetime

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def days_until(value: datetime | None) -> int | None:
    if value is None:
        return None
    deadline = timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    return (deadline - timezone.localdate()).days
