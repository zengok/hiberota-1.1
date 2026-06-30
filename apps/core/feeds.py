from __future__ import annotations

from email.utils import format_datetime
from html import escape

from django.http import HttpRequest

from apps.calls.detail import build_call_detail_path, published_call_queryset

RSS_LIMIT = 20


def latest_calls_rss(request: HttpRequest) -> bytes:
    items = []
    for call in published_call_queryset().order_by("-published_at", "-first_seen_at")[:RSS_LIMIT]:
        url = request.build_absolute_uri(build_call_detail_path(call))
        published_at = call.published_at or call.first_seen_at
        items.append(
            "".join(
                [
                    "<item>",
                    f"<title>{_xml_escape(call.title)}</title>",
                    f"<link>{_xml_escape(url)}</link>",
                    f'<guid isPermaLink="true">{_xml_escape(url)}</guid>',
                    f"<description>{_xml_escape(call.summary or str(call.institution))}</description>",
                    f"<pubDate>{format_datetime(published_at)}</pubDate>",
                    "</item>",
                ]
            )
        )
    channel = "".join(
        [
            "<channel>",
            "<title>HibeRota çağrıları</title>",
            f"<link>{_xml_escape(request.build_absolute_uri('/'))}</link>",
            "<description>HibeRota üzerinde yayınlanan son hibe, fon ve proje çağrıları.</description>",
            "<language>tr-TR</language>",
            *items,
            "</channel>",
        ]
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">{channel}</rss>'.encode()


def _xml_escape(value: str) -> str:
    return escape(value, quote=True)
