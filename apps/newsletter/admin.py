from __future__ import annotations

from django.contrib import admin

from .models import NewsletterDigestRun, NewsletterSubscriber, NewsletterSuppression


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "status", "frequency", "confirmed_at", "unsubscribed_at", "updated_at"]
    list_filter = ["status", "frequency", "consent_accepted", "created_at"]
    search_fields = ["email"]
    readonly_fields = [
        "email",
        "confirmation_token_hash",
        "unsubscribe_token_hash",
        "token_created_at",
        "confirmed_at",
        "unsubscribed_at",
        "ip_hash",
        "created_at",
        "updated_at",
    ]


@admin.register(NewsletterDigestRun)
class NewsletterDigestRunAdmin(admin.ModelAdmin):
    list_display = ["frequency", "period_start", "period_end", "status", "subscriber_count", "call_count", "sent_count"]
    list_filter = ["frequency", "status", "created_at"]
    readonly_fields = [
        "frequency",
        "period_start",
        "period_end",
        "status",
        "subscriber_count",
        "call_count",
        "sent_count",
        "error_message",
        "created_at",
        "updated_at",
    ]


@admin.register(NewsletterSuppression)
class NewsletterSuppressionAdmin(admin.ModelAdmin):
    list_display = ["email_hash", "reason", "created_at"]
    list_filter = ["reason", "created_at"]
    search_fields = ["email_hash", "note"]
    readonly_fields = ["email_hash", "reason", "note", "created_at", "updated_at"]
