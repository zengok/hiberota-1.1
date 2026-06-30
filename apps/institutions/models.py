from __future__ import annotations

from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import TimeStampedModel

country_code_validator = RegexValidator(
    regex=r"^[A-Z]{2}$",
    message="Country code must be ISO 3166-1 alpha-2.",
)


class Country(TimeStampedModel):
    code = models.CharField(max_length=2, unique=True, validators=[country_code_validator])
    name_tr = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    region_code = models.CharField(max_length=40, blank=True)
    is_eu_member = models.BooleanField(default=False)
    is_europe = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name_tr"]
        verbose_name_plural = "countries"

    def __str__(self) -> str:
        return f"{self.name_tr} ({self.code})"


class Institution(TimeStampedModel):
    class InstitutionType(models.TextChoices):
        PUBLIC = "public", "Public"
        MUNICIPALITY = "municipality", "Municipality"
        DEVELOPMENT_AGENCY = "development_agency", "Development agency"
        UNIVERSITY = "university", "University"
        NGO = "ngo", "NGO"
        FOUNDATION = "foundation", "Foundation"
        MULTILATERAL = "multilateral", "Multilateral"
        COMPANY = "company", "Company"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    short_name = models.CharField(max_length=120, blank=True)
    institution_type = models.CharField(max_length=40, choices=InstitutionType.choices, default=InstitutionType.OTHER)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="institutions")
    website_url = models.URLField(max_length=500, blank=True)
    logo = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["country", "name"], name="uniq_institution_country_name"),
        ]

    def __str__(self) -> str:
        return self.short_name or self.name
