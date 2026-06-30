from __future__ import annotations

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel
from apps.institutions.models import Country, Institution
from apps.sources.models import Source
from apps.taxonomy.models import AudienceType, OrganizationSize, ProgramType, Region, Sector, Theme


class GrantCall(TimeStampedModel):
    class WorkflowStatus(models.TextChoices):
        DISCOVERED = "discovered", "Discovered"
        REVIEW = "review", "Review"
        PUBLISHED = "published", "Published"
        REJECTED = "rejected", "Rejected"
        ARCHIVED = "archived", "Archived"

    class AvailabilityStatus(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        OPEN = "open", "Open"
        CLOSING_SOON = "closing_soon", "Closing soon"
        CLOSED = "closed", "Closed"
        UNKNOWN = "unknown", "Unknown"

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320)
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="grant_calls")
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT, related_name="grant_calls")
    external_id = models.CharField(max_length=200, blank=True)
    official_url = models.URLField(max_length=700)
    canonical_source_url = models.URLField(max_length=700)
    fingerprint = models.CharField(max_length=128, unique=True)

    summary = models.TextField(blank=True)
    purpose = models.TextField(blank=True)
    eligibility_text = models.TextField(blank=True)
    conditions_text = models.TextField(blank=True)
    duration_text = models.TextField(blank=True)
    funding_text = models.TextField(blank=True)
    application_process_text = models.TextField(blank=True)
    contact_text = models.TextField(blank=True)

    source_published_at = models.DateTimeField(blank=True, null=True)
    application_open_at = models.DateTimeField(blank=True, null=True)
    deadline_at = models.DateTimeField(blank=True, null=True)
    deadline_timezone = models.CharField(max_length=64, blank=True, default="UTC")
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField(blank=True, null=True)
    last_verified_at = models.DateTimeField(blank=True, null=True)
    duration_min_months = models.PositiveSmallIntegerField(blank=True, null=True)
    duration_max_months = models.PositiveSmallIntegerField(blank=True, null=True)
    funding_min = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    funding_max = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True)
    funding_rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )

    workflow_status = models.CharField(
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DISCOVERED,
    )
    availability_status = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.UNKNOWN,
    )
    confidence_score = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    title_confidence = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    deadline_confidence = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    eligibility_confidence = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    funding_confidence = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])

    countries = models.ManyToManyField(Country, related_name="grant_calls", blank=True)
    audiences = models.ManyToManyField(AudienceType, related_name="grant_calls", blank=True)
    sectors = models.ManyToManyField(Sector, related_name="grant_calls", blank=True)
    themes = models.ManyToManyField(Theme, related_name="grant_calls", blank=True)
    program_types = models.ManyToManyField(ProgramType, related_name="grant_calls", blank=True)
    organization_sizes = models.ManyToManyField(OrganizationSize, related_name="grant_calls", blank=True)
    regions = models.ManyToManyField(Region, related_name="grant_calls", blank=True)

    class Meta:
        ordering = ["-published_at", "-first_seen_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(funding_min__isnull=True)
                    | Q(funding_max__isnull=True)
                    | Q(funding_min__lte=models.F("funding_max"))
                ),
                name="call_funding_min_lte_max",
            ),
            models.CheckConstraint(
                condition=Q(duration_min_months__isnull=True)
                | Q(duration_max_months__isnull=True)
                | Q(duration_min_months__lte=models.F("duration_max_months")),
                name="call_duration_min_lte_max",
            ),
            models.UniqueConstraint(
                fields=["source", "external_id"],
                condition=~Q(external_id=""),
                name="uniq_call_source_external_id",
            ),
            models.UniqueConstraint(fields=["canonical_source_url"], name="uniq_call_canonical_source_url"),
        ]
        indexes = [
            models.Index(fields=["deadline_at"], name="call_deadline_idx"),
            models.Index(fields=["first_seen_at"], name="call_first_seen_idx"),
            models.Index(fields=["published_at"], name="call_published_idx"),
            models.Index(fields=["workflow_status"], name="call_workflow_idx"),
            models.Index(fields=["availability_status"], name="call_availability_idx"),
            models.Index(fields=["institution"], name="call_institution_idx"),
            models.Index(fields=["source"], name="call_source_idx"),
        ]

    def __str__(self) -> str:
        return self.title
