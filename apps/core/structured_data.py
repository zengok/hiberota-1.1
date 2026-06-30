from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest


def structured_data_json(items: list[dict[str, Any]]) -> str:
    payload = items[0] if len(items) == 1 else items
    return (
        json.dumps(payload, cls=DjangoJSONEncoder, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003C")
        .replace(">", "\\u003E")
        .replace("&", "\\u0026")
    )


def website_schema(request: HttpRequest) -> dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "HibeRota",
        "url": request.build_absolute_uri("/"),
        "inLanguage": "tr-TR",
    }


def organization_schema(request: HttpRequest) -> dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "HibeRota",
        "url": request.build_absolute_uri("/"),
    }


def breadcrumb_schema(request: HttpRequest, crumbs: list[tuple[str, str]]) -> dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": request.build_absolute_uri(path),
            }
            for index, (name, path) in enumerate(crumbs, start=1)
        ],
    }


def institution_schema(
    request: HttpRequest,
    *,
    name: str,
    path: str,
    country: str,
    website_url: str = "",
) -> dict[str, Any]:
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
        "url": request.build_absolute_uri(path),
        "areaServed": country,
    }
    if website_url:
        schema["sameAs"] = website_url
    return schema


def blog_posting_schema(
    request: HttpRequest,
    *,
    title: str,
    path: str,
    description: str,
    author_name: str,
    published_at: datetime | None,
    modified_at: datetime,
) -> dict[str, Any]:
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": description,
        "url": request.build_absolute_uri(path),
        "author": {"@type": "Person", "name": author_name},
        "publisher": {"@type": "Organization", "name": "HibeRota"},
        "dateModified": modified_at,
        "inLanguage": "tr-TR",
    }
    if published_at:
        schema["datePublished"] = published_at
    return schema
