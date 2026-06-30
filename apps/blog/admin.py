from __future__ import annotations

from django.contrib import admin

from .models import BlogAuthor, BlogPost


@admin.register(BlogAuthor)
class BlogAuthorAdmin(admin.ModelAdmin):
    list_display = ["name", "title", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "title", "bio"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            "İçerik",
            {
                "fields": [
                    "title",
                    "slug",
                    "excerpt",
                    "category",
                    "author",
                    "body_html",
                    "related_calls",
                ]
            },
        ),
        (
            "Görsel",
            {
                "fields": [
                    "cover_image",
                    "cover_alt_text",
                    "cover_caption",
                    "cover_source_url",
                ]
            },
        ),
        (
            "Yayın",
            {
                "fields": [
                    "status",
                    "publish_at",
                    "reading_time_minutes",
                ]
            },
        ),
        (
            "SEO",
            {
                "fields": [
                    "seo_title",
                    "seo_description",
                    "canonical_url",
                ]
            },
        ),
    ]
    list_display = ["title", "author", "category", "status", "publish_at", "updated_at"]
    list_filter = ["status", "category", "author"]
    search_fields = ["title", "excerpt", "body_html", "author__name"]
    autocomplete_fields = ["author", "related_calls"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at"]
