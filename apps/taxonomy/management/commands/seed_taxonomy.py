from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from apps.taxonomy.models import AudienceType, OrganizationSize, ProgramType, Region, Sector, Theme

TaxonomyRows = tuple[tuple[str, str, str], ...]


AUDIENCE_TYPES: TaxonomyRows = (
    ("student", "Öğrenci", "Student"),
    ("graduate_student", "Lisansüstü Öğrenci", "Graduate Student"),
    ("academic", "Akademisyen", "Academic"),
    ("researcher", "Araştırmacı", "Researcher"),
    ("entrepreneur", "Girişimci", "Entrepreneur"),
    ("startup", "Girişim", "Startup"),
    ("sme", "KOBİ", "SME"),
    ("company", "Şirket", "Company"),
    ("ngo", "STK", "NGO"),
    ("municipality", "Belediye", "Municipality"),
    ("public_institution", "Kamu Kurumu", "Public Institution"),
    ("consortium", "Konsorsiyum", "Consortium"),
)

SECTORS: TaxonomyRows = (
    ("agriculture", "Tarım", "Agriculture"),
    ("civil_society", "Sivil Toplum", "Civil Society"),
    ("culture", "Kültür", "Culture"),
    ("development", "Kalkınma", "Development"),
    ("digital", "Dijital", "Digital"),
    ("education", "Eğitim", "Education"),
    ("energy", "Enerji", "Energy"),
    ("environment", "Çevre", "Environment"),
    ("health", "Sağlık", "Health"),
    ("research", "Araştırma", "Research"),
    ("social_impact", "Sosyal Etki", "Social Impact"),
    ("technology", "Teknoloji", "Technology"),
)

THEMES: TaxonomyRows = (
    ("capacity_building", "Kapasite Geliştirme", "Capacity Building"),
    ("climate", "İklim", "Climate"),
    ("democracy", "Demokrasi", "Democracy"),
    ("entrepreneurship", "Girişimcilik", "Entrepreneurship"),
    ("human_rights", "İnsan Hakları", "Human Rights"),
    ("innovation", "İnovasyon", "Innovation"),
    ("rd", "Ar-Ge", "R&D"),
    ("sustainability", "Sürdürülebilirlik", "Sustainability"),
    ("youth", "Gençlik", "Youth"),
)

PROGRAM_TYPES: TaxonomyRows = (
    ("grant", "Hibe", "Grant"),
    ("fund", "Fon", "Fund"),
    ("loan", "Kredi", "Loan"),
    ("award", "Ödül", "Award"),
    ("scholarship", "Burs", "Scholarship"),
    ("accelerator", "Hızlandırıcı", "Accelerator"),
)

ORGANIZATION_SIZES: TaxonomyRows = (
    ("micro", "Mikro", "Micro"),
    ("small", "Küçük", "Small"),
    ("medium", "Orta", "Medium"),
    ("large", "Büyük", "Large"),
)

REGIONS: TaxonomyRows = (
    ("turkiye", "Türkiye", "Turkey"),
    ("europe", "Avrupa", "Europe"),
    ("middle_east_north_africa", "Orta Doğu ve Kuzey Afrika", "Middle East and North Africa"),
    ("africa", "Afrika", "Africa"),
    ("asia", "Asya", "Asia"),
    ("oceania", "Okyanusya", "Oceania"),
    ("global", "Küresel", "Global"),
)


class Command(BaseCommand):
    help = "Seed the baseline taxonomy rows used by catalog import and public filters."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Write changes. Without this flag the command performs a dry run.",
        )

    def handle(self, *args: object, **options: object) -> None:
        commit = bool(options["commit"])
        datasets = (
            (AudienceType, AUDIENCE_TYPES),
            (Sector, SECTORS),
            (Theme, THEMES),
            (ProgramType, PROGRAM_TYPES),
            (OrganizationSize, ORGANIZATION_SIZES),
            (Region, REGIONS),
        )
        total_created = 0
        total_updated = 0

        with transaction.atomic():
            for model, rows in datasets:
                created, updated = _seed_model(model, rows)
                total_created += created
                total_updated += updated
                self.stdout.write(f"{model.__name__}: created={created}, updated={updated}")
            if not commit:
                transaction.set_rollback(True)
                self.stdout.write("Dry run complete; no taxonomy rows were written.")
                return

        self.stdout.write(self.style.SUCCESS(f"Seeded taxonomy rows: created={total_created}, updated={total_updated}"))


def _seed_model(model: Any, rows: Iterable[tuple[str, str, str]]) -> tuple[int, int]:
    created_count = 0
    updated_count = 0
    for key, name_tr, name_en in rows:
        _obj, created = model.objects.update_or_create(
            key=key,
            defaults={
                "name_tr": name_tr,
                "name_en": name_en,
                "is_active": True,
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1
    return created_count, updated_count
