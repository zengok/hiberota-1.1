from __future__ import annotations

import hashlib
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from django.utils import timezone

from apps.security.models import AdminTOTPDevice
from apps.security.totp import verify_totp_token

GENERIC_ADMIN_LOGIN_ERROR = "Yönetici oturumu açılamadı. Bilgileri kontrol edip tekrar deneyin."


def admin_login_is_locked(request: HttpRequest, username: str) -> bool:
    return cache.get(_lock_key(request, username)) is True


def record_failed_admin_login(request: HttpRequest, username: str) -> None:
    attempts_key = _attempts_key(request, username)
    attempts = cache.get(attempts_key, 0) + 1
    cache.set(attempts_key, attempts, timeout=settings.ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    if attempts >= settings.ADMIN_LOGIN_RATE_LIMIT_ATTEMPTS:
        cache.set(_lock_key(request, username), True, timeout=settings.ADMIN_LOGIN_RATE_LIMIT_LOCKOUT_SECONDS)


def reset_admin_login_attempts(request: HttpRequest, username: str) -> None:
    cache.delete(_attempts_key(request, username))
    cache.delete(_lock_key(request, username))


def verify_admin_totp(user: Any, token: str) -> bool:
    if not getattr(settings, "ADMIN_TOTP_REQUIRED", True):
        return True
    if not user.is_staff:
        return False

    try:
        device = AdminTOTPDevice.objects.get(user=user, is_active=True)
    except AdminTOTPDevice.DoesNotExist:
        return False

    is_valid, counter = verify_totp_token(device.secret_key, token, last_counter=device.last_counter)
    if not is_valid or counter is None:
        return False

    device.last_counter = counter
    device.last_used_at = timezone.now()
    device.save(update_fields=["last_counter", "last_used_at", "updated_at"])
    return True


def _attempts_key(request: HttpRequest, username: str) -> str:
    return f"admin-login-attempts:{_fingerprint(request, username)}"


def _lock_key(request: HttpRequest, username: str) -> str:
    return f"admin-login-lock:{_fingerprint(request, username)}"


def _fingerprint(request: HttpRequest, username: str) -> str:
    client_ip = request.META.get("REMOTE_ADDR", "unknown")
    raw_value = f"{client_ip}:{username.strip().lower()}"
    return hashlib.sha256(raw_value.encode()).hexdigest()
