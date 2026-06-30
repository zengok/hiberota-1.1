from __future__ import annotations

from typing import Any

from apps.calls.detail import build_call_detail_path, published_call_queryset
from apps.calls.models import GrantCall

MAX_FAVORITE_RESOLVE_IDS = 200


def parse_favorite_ids(raw_ids: str) -> list[int]:
    parsed_ids = []
    for raw_id in raw_ids.split(","):
        try:
            call_id = int(raw_id.strip())
        except ValueError:
            continue
        if call_id > 0 and call_id not in parsed_ids:
            parsed_ids.append(call_id)
    return parsed_ids[:MAX_FAVORITE_RESOLVE_IDS]


def resolve_favorite_calls(raw_ids: str) -> list[dict[str, Any]]:
    favorite_ids = parse_favorite_ids(raw_ids)
    if not favorite_ids:
        return []

    calls_by_id = {call.id: call for call in published_call_queryset().filter(id__in=favorite_ids)}
    return [serialize_favorite_call(calls_by_id[call_id]) for call_id in favorite_ids if call_id in calls_by_id]


def serialize_favorite_call(call: GrantCall) -> dict[str, Any]:
    return {
        "id": call.id,
        "title": call.title,
        "institution": str(call.institution),
        "url": build_call_detail_path(call),
        "deadline": call.deadline_at.strftime("%d.%m.%Y") if call.deadline_at else "",
        "status": call.availability_status,
    }
