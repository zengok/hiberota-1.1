from __future__ import annotations

from django.core.cache import cache
from django.http import HttpRequest

from apps.calls.detail import build_call_detail_path
from apps.calls.models import GrantCall

EMBED_RATE_LIMIT = 120
EMBED_RATE_WINDOW_SECONDS = 60


def build_call_embed_path(call: GrantCall) -> str:
    return f"{build_call_detail_path(call)}embed/"


def is_embed_rate_limited(request: HttpRequest, call_id: int) -> bool:
    client_ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"calls:embed:{call_id}:{client_ip}"
    count = cache.get(key, 0)
    if count >= EMBED_RATE_LIMIT:
        return True
    if count == 0:
        cache.set(key, 1, timeout=EMBED_RATE_WINDOW_SECONDS)
    else:
        cache.incr(key)
    return False


def embed_csp_header() -> str:
    return (
        "default-src 'none'; "
        "style-src 'unsafe-inline'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "frame-ancestors https: http://localhost:* http://127.0.0.1:*"
    )
