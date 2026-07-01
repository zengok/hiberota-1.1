from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO

from apps.calls.models import GrantCall
from apps.ingestion.models import FieldEvidence, ReviewItem
from apps.institutions.models import Country, Institution
from apps.sources.models import Source
from apps.taxonomy.models import AudienceType, ProgramType, Sector, Theme
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from automation.adapters.contracts import ParsedCall, ParsedEvidence
from automation.pipeline.persistence import persist_parsed_call


class ParsedCallPersistenceTests(TestCase):
    def setUp(self) -> None:
        self.country = Country.objects.create(code="TR", name_tr="Turkiye", name_en="Turkey")
        self.audience = AudienceType.objects.create(key="sme", name_tr="KOBI", name_en="SME")
        self.academic = AudienceType.objects.create(key="academic", name_tr="Akademisyen", name_en="Academic")
        self.researcher = AudienceType.objects.create(key="researcher", name_tr="Araştırmacı", name_en="Researcher")
        self.sector = Sector.objects.create(key="energy", name_tr="Enerji", name_en="Energy")
        self.theme = Theme.objects.create(key="innovation", name_tr="Inovasyon", name_en="Innovation")
        self.program_type = ProgramType.objects.create(key="grant", name_tr="Hibe", name_en="Grant")
        self.institution = Institution.objects.create(
            country=self.country,
            name="Kalkinma Kurumu",
            slug="kalkinma-kurumu",
        )
        self.source = Source.objects.create(
            institution=self.institution,
            source_key="source-a",
            name="Kaynak A",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="source_a_html_v1",
            robots_status=Source.RobotsStatus.ALLOWED,
            terms_status=Source.TermsStatus.REVIEWED,
        )
        self.fetched_at = timezone.now()

    def test_persists_high_confidence_call_with_taxonomy_and_evidence(self) -> None:
        parsed = self._parsed_call()

        result = persist_parsed_call(
            source=self.source,
            parsed_call=parsed,
            fetched_at=self.fetched_at,
            content_hash="hash-1",
            parser_version="parser-1",
        )

        call = result.grant_call
        self.assertTrue(result.created)
        self.assertFalse(result.review_created)
        self.assertEqual(result.evidence_count, 1)
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)
        self.assertEqual(call.availability_status, GrantCall.AvailabilityStatus.OPEN)
        self.assertEqual(call.confidence_score, 100)
        self.assertEqual(call.institution, self.institution)
        self.assertEqual(list(call.countries.all()), [self.country])
        self.assertEqual(list(call.audiences.all()), [self.audience])
        self.assertEqual(list(call.sectors.all()), [self.sector])
        self.assertEqual(list(call.themes.all()), [self.theme])
        self.assertEqual(list(call.program_types.all()), [self.program_type])
        self.assertEqual(FieldEvidence.objects.filter(grant_call=call).count(), 1)
        self.assertEqual(ReviewItem.objects.count(), 0)

    def test_resolves_catalog_audience_key_aliases(self) -> None:
        self.audience.delete()
        ngo = AudienceType.objects.create(key="stk", name_tr="STK", name_en="NGO")

        result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(audience_keys=("ngo",)),
            fetched_at=self.fetched_at,
            content_hash="hash-1",
            parser_version="parser-1",
        )

        self.assertEqual(list(result.grant_call.audiences.all()), [ngo])

    def test_infers_missing_audience_from_call_text_before_persisting(self) -> None:
        result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(
                title="TÜBİTAK Kutup Araştırma Projeleri Çağrısı",
                summary="Bilimsel araştırma projeleri desteklenecektir.",
                eligibility_text="Araştırmacılar başvurabilir.",
                audience_keys=(),
            ),
            fetched_at=self.fetched_at,
            content_hash="hash-polar",
            parser_version="parser-1",
        )

        self.assertEqual(
            set(result.grant_call.audiences.values_list("key", flat=True)),
            {"researcher"},
        )
        self.assertFalse(result.review_created)

    def test_infers_missing_audience_from_source_catalog_hints(self) -> None:
        self.source.config_json = {"audience_hints": ["academic", "researcher"]}
        self.source.save(update_fields=["config_json", "updated_at"])

        result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(
                title="Genel araştırma desteği",
                summary="Başvuru çağrısı.",
                eligibility_text="Akademik proje ekipleri başvurabilir.",
                audience_keys=(),
            ),
            fetched_at=self.fetched_at,
            content_hash="hash-source-hints",
            parser_version="parser-1",
        )

        self.assertEqual(
            set(result.grant_call.audiences.values_list("key", flat=True)),
            {"academic", "researcher"},
        )

    def test_backfill_command_updates_existing_open_calls_without_audiences(self) -> None:
        call = GrantCall.objects.create(
            title="TÜBİTAK Kutup Araştırma Projeleri Çağrısı",
            slug="tubitak-kutup-arastirma-projeleri-cagrisi",
            source=self.source,
            institution=self.institution,
            official_url="https://example.org/polar",
            canonical_source_url="https://example.org/polar",
            fingerprint="polar-call",
            summary="Bilimsel araştırma projeleri desteklenecektir.",
            eligibility_text="Araştırmacılar başvurabilir.",
            deadline_at=self.fetched_at + timedelta(days=30),
            first_seen_at=self.fetched_at,
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )
        closed_call = GrantCall.objects.create(
            title="Kapalı Araştırma Çağrısı",
            slug="kapali-arastirma-cagrisi",
            source=self.source,
            institution=self.institution,
            official_url="https://example.org/closed-polar",
            canonical_source_url="https://example.org/closed-polar",
            fingerprint="closed-polar-call",
            summary="Bilimsel araştırma projeleri desteklenecektir.",
            eligibility_text="Araştırmacılar başvurabilir.",
            deadline_at=self.fetched_at - timedelta(days=1),
            first_seen_at=self.fetched_at,
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.CLOSED,
        )

        out = StringIO()
        call_command(
            "backfill_call_audiences",
            "--commit",
            "--workflow-status",
            "published",
            "--availability-status",
            "open",
            stdout=out,
        )

        self.assertIn("updated=1", out.getvalue())
        self.assertEqual(set(call.audiences.values_list("key", flat=True)), {"researcher"})
        self.assertFalse(closed_call.audiences.exists())

    def test_audience_gap_report_explains_unresolved_open_calls(self) -> None:
        GrantCall.objects.create(
            title="Genel destek duyurusu",
            slug="genel-destek-duyurusu",
            source=self.source,
            institution=self.institution,
            official_url="https://example.org/general",
            canonical_source_url="https://example.org/general",
            fingerprint="general-call",
            summary="Başvuru detayları resmi kaynakta paylaşılmıştır.",
            deadline_at=self.fetched_at + timedelta(days=30),
            first_seen_at=self.fetched_at,
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )

        out = StringIO()
        call_command(
            "report_call_audience_gaps",
            "--workflow-status",
            "published",
            "--availability-status",
            "open",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("Audience gap summary", output)
        self.assertIn("missing_eligibility_text: 1", output)
        self.assertIn("Genel destek duyurusu", output)

    def test_preserves_published_call_when_recrawl_only_loses_deadline(self) -> None:
        first_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(),
            fetched_at=self.fetched_at,
            content_hash="hash-1",
            parser_version="parser-1",
        )
        published_at = first_result.grant_call.published_at

        second_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(include_deadline=False),
            fetched_at=self.fetched_at + timedelta(minutes=5),
            content_hash="hash-2",
            parser_version="parser-1",
        )

        second_result.grant_call.refresh_from_db()
        self.assertFalse(second_result.created)
        self.assertFalse(second_result.review_created)
        self.assertEqual(second_result.grant_call.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)
        self.assertEqual(second_result.grant_call.published_at, published_at)
        self.assertIsNone(second_result.grant_call.deadline_at)
        self.assertEqual(ReviewItem.objects.count(), 0)

    def test_preserves_manually_published_low_confidence_call_without_validation_issues(self) -> None:
        first_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(summary="", include_deadline=False),
            fetched_at=self.fetched_at,
            content_hash="hash-1",
            parser_version="parser-1",
        )
        call = first_result.grant_call
        call.workflow_status = GrantCall.WorkflowStatus.PUBLISHED
        call.published_at = self.fetched_at
        call.save(update_fields=["workflow_status", "published_at", "updated_at"])
        ReviewItem.objects.filter(grant_call=call).update(status=ReviewItem.Status.RESOLVED)

        second_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(summary="", include_deadline=False),
            fetched_at=self.fetched_at + timedelta(minutes=5),
            content_hash="hash-2",
            parser_version="parser-1",
        )

        second_result.grant_call.refresh_from_db()
        self.assertFalse(second_result.review_created)
        self.assertEqual(second_result.grant_call.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)
        self.assertEqual(second_result.grant_call.published_at, self.fetched_at)
        self.assertFalse(
            ReviewItem.objects.filter(grant_call=second_result.grant_call, status=ReviewItem.Status.OPEN).exists()
        )

    def test_preserves_rejected_call_on_recrawl(self) -> None:
        first_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(include_deadline=False),
            fetched_at=self.fetched_at,
            content_hash="hash-1",
            parser_version="parser-1",
        )
        call = first_result.grant_call
        call.workflow_status = GrantCall.WorkflowStatus.REJECTED
        call.save(update_fields=["workflow_status", "updated_at"])
        ReviewItem.objects.filter(grant_call=call).update(status=ReviewItem.Status.RESOLVED)

        second_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(summary="Updated rejected summary", include_deadline=False),
            fetched_at=self.fetched_at + timedelta(minutes=5),
            content_hash="hash-2",
            parser_version="parser-1",
        )

        second_result.grant_call.refresh_from_db()
        self.assertFalse(second_result.created)
        self.assertFalse(second_result.review_created)
        self.assertEqual(second_result.grant_call.workflow_status, GrantCall.WorkflowStatus.REJECTED)
        self.assertEqual(second_result.grant_call.summary, "Updated rejected summary")
        self.assertFalse(
            ReviewItem.objects.filter(grant_call=second_result.grant_call, status=ReviewItem.Status.OPEN).exists()
        )

    def test_updates_existing_call_by_canonical_url_without_changing_first_seen(self) -> None:
        parsed = self._parsed_call(summary="Ilk ozet")
        first_result = persist_parsed_call(
            source=self.source,
            parsed_call=parsed,
            fetched_at=self.fetched_at,
            content_hash="hash-1",
            parser_version="parser-1",
        )
        first_seen_at = first_result.grant_call.first_seen_at

        second_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(summary="Guncel ozet"),
            fetched_at=self.fetched_at + timedelta(minutes=5),
            content_hash="hash-2",
            parser_version="parser-1",
        )

        self.assertFalse(second_result.created)
        self.assertEqual(GrantCall.objects.count(), 1)
        second_result.grant_call.refresh_from_db()
        self.assertEqual(second_result.grant_call.summary, "Guncel ozet")
        self.assertEqual(second_result.grant_call.first_seen_at, first_seen_at)
        self.assertEqual(FieldEvidence.objects.filter(grant_call=second_result.grant_call).count(), 2)

    def test_updates_existing_call_by_source_external_id_before_canonical_url(self) -> None:
        first_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(),
            fetched_at=self.fetched_at,
            content_hash="hash-1",
            parser_version="parser-1",
        )

        second_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(canonical_source_url="https://example.org/call/new-url"),
            fetched_at=self.fetched_at + timedelta(minutes=5),
            content_hash="hash-2",
            parser_version="parser-1",
        )

        self.assertFalse(second_result.created)
        self.assertEqual(second_result.grant_call.id, first_result.grant_call.id)
        self.assertEqual(GrantCall.objects.count(), 1)
        second_result.grant_call.refresh_from_db()
        self.assertEqual(second_result.grant_call.canonical_source_url, "https://example.org/call/new-url")

    def test_updates_existing_call_by_semantic_fingerprint(self) -> None:
        first_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(external_id=""),
            fetched_at=self.fetched_at,
            content_hash="hash-1",
            parser_version="parser-1",
        )

        second_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(
                external_id="",
                title="KOBİ Enerji Hibe Programı",
                canonical_source_url="https://example.org/call/semantic-duplicate",
            ),
            fetched_at=self.fetched_at + timedelta(minutes=5),
            content_hash="hash-2",
            parser_version="parser-1",
        )

        self.assertFalse(second_result.created)
        self.assertEqual(second_result.grant_call.id, first_result.grant_call.id)
        self.assertEqual(GrantCall.objects.count(), 1)

    def test_low_confidence_call_goes_to_review(self) -> None:
        parsed = ParsedCall(
            title="Eksik Program",
            official_url="https://example.org/missing",
            canonical_source_url="https://example.org/missing",
        )

        result = persist_parsed_call(
            source=self.source,
            parsed_call=parsed,
            fetched_at=self.fetched_at,
            content_hash="hash-low",
            parser_version="parser-1",
        )

        self.assertTrue(result.created)
        self.assertTrue(result.review_created)
        self.assertEqual(result.grant_call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertGreater(ReviewItem.objects.filter(grant_call=result.grant_call).count(), 0)

    def test_missing_dates_create_low_confidence_review_not_deadline_conflict(self) -> None:
        result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(include_deadline=False),
            fetched_at=self.fetched_at,
            content_hash="hash-missing-dates",
            parser_version="parser-1",
        )

        self.assertTrue(result.review_created)
        self.assertTrue(
            ReviewItem.objects.filter(
                grant_call=result.grant_call,
                reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE,
            ).exists()
        )
        self.assertFalse(
            ReviewItem.objects.filter(
                grant_call=result.grant_call,
                reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT,
            ).exists()
        )

    def test_open_source_status_keeps_missing_deadline_call_visible_as_open(self) -> None:
        result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(include_deadline=False, raw_metadata={"source_status": "open"}),
            fetched_at=self.fetched_at,
            content_hash="hash-open-source-status",
            parser_version="parser-1",
        )

        self.assertEqual(result.grant_call.availability_status, GrantCall.AvailabilityStatus.OPEN)
        self.assertTrue(result.review_created)

    def test_missing_official_url_blocks_auto_publish_even_when_score_is_high(self) -> None:
        result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(official_url=""),
            fetched_at=self.fetched_at,
            content_hash="hash-missing-official",
            parser_version="parser-1",
        )

        self.assertTrue(result.review_created)
        self.assertEqual(result.grant_call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        review = ReviewItem.objects.get(
            grant_call=result.grant_call,
            reason_code=ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
        )
        self.assertEqual(review.severity, ReviewItem.Severity.HIGH)

    def test_deadline_conflict_blocks_auto_publish(self) -> None:
        result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(
                application_open_at=self.fetched_at + timedelta(days=20),
                deadline_at=self.fetched_at + timedelta(days=5),
            ),
            fetched_at=self.fetched_at,
            content_hash="hash-deadline-conflict",
            parser_version="parser-1",
        )

        self.assertTrue(result.review_created)
        self.assertEqual(result.grant_call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertTrue(
            ReviewItem.objects.filter(
                grant_call=result.grant_call,
                reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT,
            ).exists()
        )

    def test_resolves_stale_review_items_after_parser_improves(self) -> None:
        first_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(title="", summary="Eksik title"),
            fetched_at=self.fetched_at,
            content_hash="hash-missing-title",
            parser_version="parser-1",
        )
        review = ReviewItem.objects.get(
            grant_call=first_result.grant_call,
            reason_code=ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
        )
        self.assertEqual(review.status, ReviewItem.Status.OPEN)

        second_result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(),
            fetched_at=self.fetched_at + timedelta(minutes=5),
            content_hash="hash-fixed-title",
            parser_version="parser-2",
        )

        self.assertFalse(second_result.created)
        review.refresh_from_db()
        self.assertEqual(review.status, ReviewItem.Status.RESOLVED)
        second_result.grant_call.refresh_from_db()
        self.assertEqual(second_result.grant_call.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)

    def test_portal_source_category_blocks_auto_publish(self) -> None:
        result = persist_parsed_call(
            source=self.source,
            parsed_call=self._parsed_call(raw_metadata={"source_category": "programme_portal"}),
            fetched_at=self.fetched_at,
            content_hash="hash-portal",
            parser_version="parser-1",
        )

        self.assertTrue(result.review_created)
        self.assertEqual(result.grant_call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertTrue(
            ReviewItem.objects.filter(
                grant_call=result.grant_call,
                reason_code=ReviewItem.ReasonCode.SOURCE_RESTRICTED,
            ).exists()
        )

    def _parsed_call(
        self,
        *,
        summary: str = "Enerji yatırımı desteği",
        eligibility_text: str = "KOBI'ler başvurabilir.",
        external_id: str = "external-1",
        title: str = "KOBI Enerji Hibe Programi",
        official_url: str = "https://example.org/call/1/apply",
        canonical_source_url: str = "https://example.org/call/1",
        application_open_at: datetime | None = None,
        deadline_at: datetime | None = None,
        include_deadline: bool = True,
        audience_keys: tuple[str, ...] = ("sme",),
        raw_metadata: dict[str, str] | None = None,
    ) -> ParsedCall:
        deadline: datetime | None = deadline_at if deadline_at is not None else self.fetched_at + timedelta(days=30)
        if not include_deadline:
            deadline = None
        return ParsedCall(
            title=title,
            official_url=official_url,
            canonical_source_url=canonical_source_url,
            institution_name=self.institution.name,
            external_id=external_id,
            summary=summary,
            purpose="Enerji verimliliğini artırmak.",
            eligibility_text=eligibility_text,
            funding_text="100000 TRY destek.",
            application_open_at=application_open_at,
            deadline_at=deadline,
            funding_min=Decimal("10000.00"),
            funding_max=Decimal("100000.00"),
            currency="TRY",
            country_codes=("TR",),
            audience_keys=audience_keys,
            sector_keys=("energy",),
            theme_keys=("innovation",),
            program_type_keys=("grant",),
            evidence=(
                ParsedEvidence(
                    field_name="title",
                    source_url="https://example.org/call/1",
                    source_excerpt="KOBI Enerji Hibe Programi",
                    selector_or_path="h1",
                    confidence=95,
                ),
            ),
            raw_metadata=raw_metadata or {},
        )
