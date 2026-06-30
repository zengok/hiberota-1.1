from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedModel


class NewsletterSubscriber(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Onay bekliyor"
        CONFIRMED = "confirmed", "Onaylandı"
        UNSUBSCRIBED = "unsubscribed", "Abonelikten çıktı"

    class Frequency(models.TextChoices):
        DAILY = "DAILY", "Günlük"
        WEEKLY = "WEEKLY", "Haftalık"
        MONTHLY = "MONTHLY", "Aylık"

    email = models.EmailField(max_length=254, unique=True)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.WEEKLY)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    consent_accepted = models.BooleanField(default=False)
    confirmation_token_hash = models.CharField(max_length=64, blank=True)
    unsubscribe_token_hash = models.CharField(max_length=64, blank=True)
    token_created_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "frequency"], name="newsletter_status_freq_idx"),
            models.Index(fields=["confirmation_token_hash"], name="newsletter_confirm_hash_idx"),
            models.Index(fields=["unsubscribe_token_hash"], name="newsletter_unsub_hash_idx"),
        ]

    def __str__(self) -> str:
        return self.email


class NewsletterDigestRun(TimeStampedModel):
    class Status(models.TextChoices):
        RUNNING = "running", "Çalışıyor"
        COMPLETED = "completed", "Tamamlandı"
        FAILED = "failed", "Başarısız"

    frequency = models.CharField(max_length=20, choices=NewsletterSubscriber.Frequency.choices)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    subscriber_count = models.PositiveIntegerField(default=0)
    call_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    error_message = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-period_end", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["frequency", "period_start", "period_end"],
                name="uniq_newsletter_digest_period",
            )
        ]
        indexes = [
            models.Index(fields=["frequency", "status"], name="newsletter_run_freq_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.frequency} {self.period_start:%Y-%m-%d}"


class NewsletterSuppression(TimeStampedModel):
    class Reason(models.TextChoices):
        UNSUBSCRIBE = "unsubscribe", "Abonelikten çıkış"
        BOUNCE = "bounce", "Bounce"
        COMPLAINT = "complaint", "Şikayet"
        MANUAL = "manual", "Manuel"

    email_hash = models.CharField(max_length=64, unique=True)
    reason = models.CharField(max_length=20, choices=Reason.choices)
    note = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reason", "created_at"], name="newsletter_suppress_reason_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.reason}:{self.email_hash[:10]}"
