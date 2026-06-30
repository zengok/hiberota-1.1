"""Production settings loaded by Docker/Gunicorn."""

from __future__ import annotations

from .base import *  # noqa: F403
from .base import env, env_bool

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = False
SOURCE_SCHEDULER_REQUIRE_ALLOWLIST = env_bool("SOURCE_SCHEDULER_REQUIRE_ALLOWLIST", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env("DJANGO_SECURE_SSL_REDIRECT", "true").lower() in {"1", "true", "yes", "on"}
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_HSTS_SECONDS = int(env("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
SECURE_HSTS_PRELOAD = env("DJANGO_SECURE_HSTS_PRELOAD", "false").lower() in {"1", "true", "yes", "on"}
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
