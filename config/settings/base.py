"""Shared Django settings for HibeRota."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(item.strip() for item in os.environ.get(name, default).split(",") if item.strip())


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-secret-key")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = [host.strip() for host in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
]

PROJECT_APPS = [
    "apps.calls",
    "apps.institutions",
    "apps.taxonomy",
    "apps.sources",
    "apps.ingestion",
    "apps.search",
    "apps.blog",
    "apps.survey",
    "apps.newsletter",
    "apps.contact",
    "apps.analytics",
    "apps.security.apps.SecurityConfig",
]

INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.security.headers.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.analytics.context_processors.analytics_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "hiberota"),
        "USER": env("POSTGRES_USER", "hiberota"),
        "PASSWORD": env("POSTGRES_PASSWORD", "hiberota_dev_password"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(env("DATABASE_CONN_MAX_AGE", "60")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "tr-tr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
SITE_BASE_URL = env("SITE_BASE_URL", "http://localhost:8000")
SECURITY_CONTACT_EMAIL = env("SECURITY_CONTACT_EMAIL", "security@example.invalid")
SECURITY_TXT_CONTACT = env("SECURITY_TXT_CONTACT", f"mailto:{SECURITY_CONTACT_EMAIL}")
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", "25"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = int(env("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "no-reply@example.invalid")
GA4_MEASUREMENT_ID = env("GA4_MEASUREMENT_ID", "")
CMP_ENABLED = env_bool("CMP_ENABLED", False)
CMP_PROVIDER_NAME = env("CMP_PROVIDER_NAME", "")
CMP_SCRIPT_URL = env("CMP_SCRIPT_URL", "")
ADSENSE_ENABLED = env_bool("ADSENSE_ENABLED", False)
ADSENSE_PUBLISHER_ID = env("ADSENSE_PUBLISHER_ID", "")
ADSENSE_CLIENT_ID = env("ADSENSE_CLIENT_ID", "")
ADSENSE_SLOT_CALL_LIST_TOP = env("ADSENSE_SLOT_CALL_LIST_TOP", "")
ADSENSE_SLOT_CALL_DETAIL_INLINE = env("ADSENSE_SLOT_CALL_DETAIL_INLINE", "")
GOOGLE_SITE_VERIFICATION = env("GOOGLE_SITE_VERIFICATION", "")
BING_SITE_VERIFICATION = env("BING_SITE_VERIFICATION", "")
SECURITY_HEADERS_ENABLED = env_bool("SECURITY_HEADERS_ENABLED", True)
SECURITY_CSP_REPORT_ONLY = env_bool("SECURITY_CSP_REPORT_ONLY", False)
SECURITY_CSP_UPGRADE_INSECURE_REQUESTS = env_bool("SECURITY_CSP_UPGRADE_INSECURE_REQUESTS", not DEBUG)
ADMIN_TOTP_REQUIRED = env_bool("ADMIN_TOTP_REQUIRED", True)
ADMIN_LOGIN_RATE_LIMIT_ATTEMPTS = int(env("ADMIN_LOGIN_RATE_LIMIT_ATTEMPTS", "5"))
ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(env("ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300"))
ADMIN_LOGIN_RATE_LIMIT_LOCKOUT_SECONDS = int(env("ADMIN_LOGIN_RATE_LIMIT_LOCKOUT_SECONDS", "900"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL", "redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
SOURCE_SCHEDULER_ENABLED = env_bool("SOURCE_SCHEDULER_ENABLED", True)
SOURCE_SCHEDULER_ROLLBACK_PAUSED = env_bool("SOURCE_SCHEDULER_ROLLBACK_PAUSED", False)
SOURCE_SCHEDULER_ALLOWLIST = env_csv("SOURCE_SCHEDULER_ALLOWLIST", "")
SOURCE_SCHEDULER_REQUIRE_ALLOWLIST = env_bool("SOURCE_SCHEDULER_REQUIRE_ALLOWLIST", False)
SOURCE_SCHEDULER_MAX_DUE_SOURCES = int(env("SOURCE_SCHEDULER_MAX_DUE_SOURCES", "5"))
CELERY_BEAT_SCHEDULE = {
    "schedule-due-sources": {
        "task": "sources.schedule_due_sources",
        "schedule": 300.0,
    },
    "send-weekly-newsletter-digest": {
        "task": "newsletter.send_due_newsletter_digest",
        "schedule": 3600.0,
        "args": ("WEEKLY",),
    },
    "send-monthly-newsletter-digest": {
        "task": "newsletter.send_due_newsletter_digest",
        "schedule": 3600.0,
        "args": ("MONTHLY",),
    },
}

LOG_LEVEL = env("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "apps.core.logging.JsonLogFormatter",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
