from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

from apps.calls.models import GrantCall

RELATED_CALL_LIMIT = 3


def published_call_queryset() -> QuerySet[GrantCall]:
    return (
        GrantCall.objects.filter(workflow_status=GrantCall.WorkflowStatus.PUBLISHED)
        .select_related("institution", "source")
        .prefetch_related("countries", "audiences", "sectors", "themes", "program_types")
    )


def build_call_detail_context(call: GrantCall) -> dict[str, Any]:
    return {
        "page_title": f"{call.title} | HibeRota",
        "meta_description": _meta_description(call),
        "canonical_path": build_call_detail_path(call),
        "robots": "index,follow",
        "call": call,
        "related_calls": related_calls(call),
    }


def build_call_detail_path(call: GrantCall) -> str:
    return f"/cagrilar/{call.slug}-{call.id}/"


def related_calls(call: GrantCall) -> QuerySet[GrantCall]:
    return (
        published_call_queryset()
        .filter(institution=call.institution)
        .exclude(id=call.id)
        .order_by("-first_seen_at")[:RELATED_CALL_LIMIT]
    )


def _meta_description(call: GrantCall) -> str:
    if call.summary:
        return call.summary[:155]
    return f"{call.institution} tarafından yayımlanan hibe ve fon çağrısını resmi kaynak bağlantısıyla inceleyin."
