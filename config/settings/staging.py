"""Staging settings for hiberota.com pre-production validation."""

from __future__ import annotations

from .base import env_bool
from .production import *  # noqa: F403

STAGING_ROBOTS_NOINDEX = env_bool("STAGING_ROBOTS_NOINDEX", True)
SECURE_HSTS_PRELOAD = False
SOURCE_SCHEDULER_ENABLED = env_bool("SOURCE_SCHEDULER_ENABLED", False)
