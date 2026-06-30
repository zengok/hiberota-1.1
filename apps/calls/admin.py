from __future__ import annotations

from django.contrib import admin

from .models import GrantCall


@admin.register(GrantCall)
class GrantCallAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "institution",
        "workflow_status",
        "availability_status",
        "deadline_at",
        "confidence_score",
        "published_at",
    ]
    list_filter = ["workflow_status", "availability_status", "is_featured", "institution", "source"]
    search_fields = ["title", "summary", "official_url", "canonical_source_url", "institution__name"]
    autocomplete_fields = [
        "source",
        "institution",
        "countries",
        "audiences",
        "sectors",
        "themes",
        "program_types",
        "organization_sizes",
        "regions",
    ]
    prepopulated_fields = {"slug": ("title",)}
