from __future__ import annotations

from django.core.validators import MaxValueValidator
from django.db import models

from apps.calls.models import GrantCall
from apps.core.models import TimeStampedModel
from apps.sources.models import Source


class CrawlRun(TimeStampedModel):
    class TriggerType(models.TextChoices):
        SCHEDULE = "schedule", "Schedule"
        MANUAL = "manual", "Manual"
        RETRY = "retry", "Retry"
        BACKFILL = "backfill", "Backfill"

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="crawl_runs")
    trigger_type = models.CharField(max_length=20, choices=TriggerType.choices, default=TriggerType.SCHEDULE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    discovered_count = models.PositiveIntegerField(default=0)
    fetched_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    http_status_summary = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=80, blank=True)
    error_summary = models.TextField(blank=True)
    worker_id = models.CharField(max_length=120, blank=True)
    config_version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["source", "status"], name="crawl_run_source_status_idx"),
            models.Index(fields=["started_at"], name="crawl_run_started_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.source_id}:{self.trigger_type}:{self.status}"


class CrawlItem(TimeStampedModel):
    class Status(models.TextChoices):
        DISCOVERED = "discovered", "Discovered"
        FETCHED = "fetched", "Fetched"
        PARSED = "parsed", "Parsed"
        FAILED = "failed", "Failed"
        DUPLICATE = "duplicate", "Duplicate"

    crawl_run = models.ForeignKey(CrawlRun, on_delete=models.CASCADE, related_name="items")
    source_url = models.URLField(max_length=700)
    normalized_url = models.URLField(max_length=700)
    external_id = models.CharField(max_length=200, blank=True)
    content_hash = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DISCOVERED)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    http_status = models.PositiveSmallIntegerField(blank=True, null=True)
    parser_version = models.CharField(max_length=80, blank=True)
    raw_metadata_json = models.JSONField(default=dict, blank=True)
    grant_call = models.ForeignKey(
        GrantCall,
        on_delete=models.SET_NULL,
        related_name="crawl_items",
        blank=True,
        null=True,
    )
    error_code = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["crawl_run", "id"]
        indexes = [
            models.Index(fields=["crawl_run", "status"], name="crawl_item_run_status_idx"),
            models.Index(fields=["normalized_url"], name="crawl_item_norm_url_idx"),
            models.Index(fields=["content_hash"], name="crawl_item_hash_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.crawl_run_id}:{self.status}:{self.normalized_url}"


class FieldEvidence(TimeStampedModel):
    grant_call = models.ForeignKey(GrantCall, on_delete=models.CASCADE, related_name="field_evidence")
    field_name = models.CharField(max_length=80)
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="field_evidence")
    source_url = models.URLField(max_length=700)
    source_excerpt = models.TextField(max_length=2000)
    selector_or_path = models.CharField(max_length=255, blank=True)
    fetched_at = models.DateTimeField()
    content_hash = models.CharField(max_length=128)
    parser_version = models.CharField(max_length=80)
    confidence = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])

    class Meta:
        ordering = ["grant_call", "field_name", "-fetched_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["grant_call", "field_name", "content_hash", "parser_version"],
                name="uniq_field_evidence_call_field_hash_parser",
            ),
        ]
        indexes = [
            models.Index(fields=["field_name"], name="evidence_field_name_idx"),
            models.Index(fields=["content_hash"], name="evidence_content_hash_idx"),
            models.Index(fields=["fetched_at"], name="evidence_fetched_at_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.grant_call_id}:{self.field_name}"


class ReviewItem(TimeStampedModel):
    class ReasonCode(models.TextChoices):
        LOW_CONFIDENCE = "low_confidence", "Low confidence"
        DEADLINE_CONFLICT = "deadline_conflict", "Deadline conflict"
        MISSING_REQUIRED_FIELD = "missing_required_field", "Missing required field"
        SOURCE_RESTRICTED = "source_restricted", "Source restricted"
        DUPLICATE_CANDIDATE = "duplicate_candidate", "Duplicate candidate"
        PARSER_ERROR = "parser_error", "Parser error"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    grant_call = models.ForeignKey(
        GrantCall, on_delete=models.CASCADE, related_name="review_items", blank=True, null=True
    )
    reason_code = models.CharField(max_length=40, choices=ReasonCode.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    assigned_to = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        related_name="assigned_review_items",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["status", "-created_at"]
        indexes = [
            models.Index(fields=["status", "severity"], name="review_status_severity_idx"),
            models.Index(fields=["reason_code"], name="review_reason_code_idx"),
        ]

    def __str__(self) -> str:
        target = self.grant_call_id or "unlinked"
        return f"{target}:{self.reason_code}"
