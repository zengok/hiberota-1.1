from __future__ import annotations

from django.contrib import admin

from .models import Country, Institution


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["code", "name_tr", "name_en", "region_code", "is_active"]
    list_filter = ["is_active", "is_eu_member", "is_europe", "region_code"]
    search_fields = ["code", "name_tr", "name_en"]


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name", "institution_type", "country", "is_verified", "is_active"]
    list_filter = ["institution_type", "is_verified", "is_active", "country"]
    search_fields = ["name", "short_name", "website_url"]
    prepopulated_fields = {"slug": ("name",)}
