from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedModel


class TaxonomyBase(TimeStampedModel):
    key = models.SlugField(max_length=80, unique=True)
    name_tr = models.CharField(max_length=160)
    name_en = models.CharField(max_length=160, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["name_tr"]

    def __str__(self) -> str:
        return self.name_tr


class AudienceType(TaxonomyBase):
    class Meta(TaxonomyBase.Meta):
        verbose_name = "audience type"
        verbose_name_plural = "audience types"


class Sector(TaxonomyBase):
    class Meta(TaxonomyBase.Meta):
        verbose_name = "sector"
        verbose_name_plural = "sectors"


class Theme(TaxonomyBase):
    class Meta(TaxonomyBase.Meta):
        verbose_name = "theme"
        verbose_name_plural = "themes"


class ProgramType(TaxonomyBase):
    class Meta(TaxonomyBase.Meta):
        verbose_name = "program type"
        verbose_name_plural = "program types"


class OrganizationSize(TaxonomyBase):
    class Meta(TaxonomyBase.Meta):
        verbose_name = "organization size"
        verbose_name_plural = "organization sizes"


class Region(TaxonomyBase):
    class Meta(TaxonomyBase.Meta):
        verbose_name = "region"
        verbose_name_plural = "regions"


class KeywordRule(TimeStampedModel):
    class MatchField(models.TextChoices):
        TITLE = "title", "Title"
        SUMMARY = "summary", "Summary"
        ELIGIBILITY = "eligibility", "Eligibility"
        FUNDING = "funding", "Funding"
        ANY = "any", "Any"

    key = models.SlugField(max_length=100, unique=True)
    pattern = models.CharField(max_length=255)
    match_field = models.CharField(max_length=20, choices=MatchField.choices, default=MatchField.ANY)
    audience = models.ForeignKey(AudienceType, on_delete=models.SET_NULL, blank=True, null=True)
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, blank=True, null=True)
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, blank=True, null=True)
    weight = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key
