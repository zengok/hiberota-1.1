from __future__ import annotations

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.taxonomy.models import AudienceType, ProgramType, Sector


class SeedTaxonomyCommandTests(TestCase):
    def test_dry_run_does_not_write_rows(self) -> None:
        output = StringIO()

        call_command("seed_taxonomy", stdout=output)

        self.assertIn("Dry run complete", output.getvalue())
        self.assertEqual(AudienceType.objects.count(), 0)

    def test_commit_seeds_canonical_catalog_taxonomy(self) -> None:
        output = StringIO()

        call_command("seed_taxonomy", "--commit", stdout=output)

        self.assertTrue(AudienceType.objects.filter(key="ngo", name_tr="STK").exists())
        self.assertTrue(AudienceType.objects.filter(key="sme", name_tr="KOBİ").exists())
        self.assertTrue(AudienceType.objects.filter(key="researcher", name_tr="Araştırmacı").exists())
        self.assertTrue(Sector.objects.filter(key="development", name_tr="Kalkınma").exists())
        self.assertTrue(ProgramType.objects.filter(key="grant", name_tr="Hibe").exists())

    def test_commit_is_idempotent_and_updates_existing_rows(self) -> None:
        AudienceType.objects.create(key="ngo", name_tr="Old", name_en="Old", is_active=False)

        call_command("seed_taxonomy", "--commit", stdout=StringIO())
        call_command("seed_taxonomy", "--commit", stdout=StringIO())

        ngo = AudienceType.objects.get(key="ngo")
        self.assertEqual(ngo.name_tr, "STK")
        self.assertEqual(ngo.name_en, "NGO")
        self.assertTrue(ngo.is_active)
