from __future__ import annotations

from django.contrib import admin

from .models import AudienceType, KeywordRule, OrganizationSize, ProgramType, Region, Sector, Theme


class TaxonomyAdmin(admin.ModelAdmin):
    list_display = ["key", "name_tr", "name_en", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["key", "name_tr", "name_en"]
    prepopulated_fields = {"key": ("name_tr",)}


@admin.register(AudienceType)
class AudienceTypeAdmin(TaxonomyAdmin):
    pass


@admin.register(Sector)
class SectorAdmin(TaxonomyAdmin):
    pass


@admin.register(Theme)
class ThemeAdmin(TaxonomyAdmin):
    pass


@admin.register(ProgramType)
class ProgramTypeAdmin(TaxonomyAdmin):
    pass


@admin.register(OrganizationSize)
class OrganizationSizeAdmin(TaxonomyAdmin):
    pass


@admin.register(Region)
class RegionAdmin(TaxonomyAdmin):
    pass


@admin.register(KeywordRule)
class KeywordRuleAdmin(admin.ModelAdmin):
    list_display = ["key", "match_field", "weight", "audience", "sector", "theme", "is_active"]
    list_filter = ["match_field", "is_active", "audience", "sector", "theme"]
    search_fields = ["key", "pattern"]
    autocomplete_fields = ["audience", "sector", "theme"]
