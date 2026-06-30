from __future__ import annotations

from django.contrib import admin

from .models import CrawlItem, CrawlRun, FieldEvidence, ReviewItem


@admin.register(CrawlRun)
class CrawlRunAdmin(admin.ModelAdmin):
    list_display = [
        "source",
        "trigger_type",
        "status",
        "started_at",
        "finished_at",
        "discovered_count",
        "fetched_count",
        "created_count",
        "updated_count",
        "review_count",
        "failed_count",
    ]
    list_filter = ["trigger_type", "status", "source"]
    search_fields = ["source__name", "source__source_key", "error_code", "error_summary", "worker_id"]
    autocomplete_fields = ["source"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(CrawlItem)
class CrawlItemAdmin(admin.ModelAdmin):
    list_display = ["crawl_run", "status", "http_status", "normalized_url", "grant_call", "parser_version"]
    list_filter = ["status", "http_status", "parser_version"]
    search_fields = ["normalized_url", "source_url", "external_id", "content_hash", "error_code"]
    autocomplete_fields = ["crawl_run", "grant_call"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(FieldEvidence)
class FieldEvidenceAdmin(admin.ModelAdmin):
    list_display = ["grant_call", "field_name", "source", "confidence", "fetched_at", "parser_version"]
    list_filter = ["field_name", "source", "parser_version"]
    search_fields = ["grant_call__title", "field_name", "source_url", "source_excerpt", "content_hash"]
    autocomplete_fields = ["grant_call", "source"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ReviewItem)
class ReviewItemAdmin(admin.ModelAdmin):
    list_display = ["grant_call", "reason_code", "severity", "status", "assigned_to", "created_at", "resolved_at"]
    list_filter = ["reason_code", "severity", "status"]
    search_fields = ["grant_call__title", "reason_code", "resolution"]
    autocomplete_fields = ["grant_call", "assigned_to"]
    readonly_fields = ["created_at", "updated_at"]
