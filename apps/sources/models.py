from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.institutions.models import Institution


class Source(TimeStampedModel):
    class SourceType(models.TextChoices):
        API = "api", "API"
        FEED = "feed", "Feed"
        SITEMAP = "sitemap", "Sitemap"
        HTML = "html", "HTML"
        HEADLESS = "headless", "Headless"
        MANUAL = "manual", "Manual"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        DEGRADED = "degraded", "Degraded"
        BLOCKED = "blocked", "Blocked"
        RETIRED = "retired", "Retired"
        MANUAL_ONLY = "manual_only", "Manual only"

    class RobotsStatus(models.TextChoices):
        ALLOWED = "allowed", "Allowed"
        RESTRICTED = "restricted", "Restricted"
        UNKNOWN = "unknown", "Unknown"

    class TermsStatus(models.TextChoices):
        REVIEWED = "reviewed", "Reviewed"
        RESTRICTED = "restricted", "Restricted"
        UNKNOWN = "unknown", "Unknown"

    institution = models.ForeignKey(Institution, on_delete=models.PROTECT, related_name="sources")
    source_key = models.SlugField(max_length=120, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    base_url = models.URLField(max_length=500)
    listing_url = models.URLField(max_length=500)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    adapter_key = models.SlugField(max_length=120)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    crawl_interval_minutes = models.PositiveIntegerField(default=60, validators=[MinValueValidator(15)])
    robots_status = models.CharField(max_length=20, choices=RobotsStatus.choices, default=RobotsStatus.UNKNOWN)
    terms_status = models.CharField(max_length=20, choices=TermsStatus.choices, default=TermsStatus.UNKNOWN)
    contact_url = models.URLField(max_length=500, blank=True)
    last_success_at = models.DateTimeField(blank=True, null=True)
    last_failure_at = models.DateTimeField(blank=True, null=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    health_score = models.PositiveSmallIntegerField(
        default=100, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    config_json = models.JSONField(default=dict, blank=True)
    config_version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["institution__name", "name"]
        constraints = [
            models.UniqueConstraint(fields=["institution", "name"], name="uniq_source_institution_name"),
            models.UniqueConstraint(fields=["adapter_key", "listing_url"], name="uniq_source_adapter_listing"),
        ]
        indexes = [
            models.Index(fields=["status", "source_type"], name="source_status_type_idx"),
            models.Index(fields=["adapter_key"], name="source_adapter_key_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.institution}: {self.name}"
