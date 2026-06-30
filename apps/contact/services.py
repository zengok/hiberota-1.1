from __future__ import annotations

import hashlib
import hmac
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest

from apps.contact.models import ContactMessage

RATE_LIMIT = 5
RATE_LIMIT_SECONDS = 3600


def hash_contact_key(value: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), value.strip().lower().encode(), hashlib.sha256).hexdigest()


def client_ip_hash(request: HttpRequest) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    client_ip = forwarded_for.split(",", 1)[0].strip() or request.META.get("REMOTE_ADDR", "")
    return hash_contact_key(client_ip)


def is_rate_limited(request: HttpRequest, email: str) -> bool:
    keys = [f"contact:ip:{client_ip_hash(request)}", f"contact:email:{hash_contact_key(email)}"]
    limited = False
    for key in keys:
        if cache.add(key, 1, timeout=RATE_LIMIT_SECONDS):
            continue
        count = cache.incr(key)
        if count > RATE_LIMIT:
            limited = True
    return limited


def create_contact_message(request: HttpRequest, cleaned_data: dict[str, Any]) -> ContactMessage:
    return ContactMessage.objects.create(
        name=cleaned_data["name"].strip(),
        email=cleaned_data["email"],
        subject=cleaned_data["subject"].strip(),
        message=cleaned_data["message"].strip(),
        privacy_accepted=cleaned_data["privacy_accepted"],
        ip_hash=client_ip_hash(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )
