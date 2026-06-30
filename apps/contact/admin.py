from __future__ import annotations

from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "email", "status", "created_at"]
    list_filter = ["status", "privacy_accepted", "created_at"]
    search_fields = ["name", "email", "subject", "message"]
    readonly_fields = ["name", "email", "subject", "message", "privacy_accepted", "ip_hash", "user_agent", "created_at"]
    fields = [
        "status",
        "name",
        "email",
        "subject",
        "message",
        "privacy_accepted",
        "ip_hash",
        "user_agent",
        "created_at",
    ]
