from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedModel


class ContactMessage(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "Yeni"
        IN_REVIEW = "in_review", "İncelemede"
        RESOLVED = "resolved", "Yanıtlandı"
        SPAM = "spam", "Spam"

    name = models.CharField(max_length=160)
    email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=160)
    message = models.TextField(max_length=4000)
    privacy_accepted = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="contact_status_created_idx"),
            models.Index(fields=["email"], name="contact_email_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.subject} - {self.email}"
