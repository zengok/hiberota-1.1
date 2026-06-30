"""Test settings."""

from __future__ import annotations

from .base import *  # noqa: F403
from .base import BASE_DIR, env_bool

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True

if env_bool("HIBEROTA_TEST_SQLITE", True):
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / ".test-db.sqlite3",
        }
    }

    CACHES = {  # noqa: F405
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "hiberota-tests",
        }
    }
