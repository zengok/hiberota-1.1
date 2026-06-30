from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.calls.audit import build_call_data_quality_report
from apps.calls.models import GrantCall
from apps.sources.models import Source


class Command(BaseCommand):
    help = "Report semantic duplicate candidates and stale availability statuses."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source-key", action="append", default=[], help="Limit verification to one source key.")
        parser.add_argument("--fail-on-issues", action="store_true", help="Exit with an error when issues are found.")
        parser.add_argument("--require-checked", action="store_true", help="Fail when no calls were checked.")
        parser.add_argument(
            "--probe",
            action="store_true",
            help="Run a rollback-only duplicate/status probe against the configured database.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        queryset = GrantCall.objects.all()
        source_keys = [str(key).strip() for key in options["source_key"] if str(key).strip()]
        if source_keys:
            queryset = queryset.filter(source__source_key__in=source_keys)

        report = build_call_data_quality_report(queryset=queryset)

        self.stdout.write(f"Checked calls: {report.checked_calls}")
        self.stdout.write(f"Duplicate candidates: {len(report.duplicate_candidates)}")
        for candidate in report.duplicate_candidates:
            self.stdout.write(
                f"duplicate key={candidate.key} call_ids={','.join(str(call_id) for call_id in candidate.call_ids)}"
            )

        self.stdout.write(f"Availability mismatches: {len(report.availability_mismatches)}")
        for mismatch in report.availability_mismatches:
            self.stdout.write(
                "availability "
                f"call_id={mismatch.call_id} "
                f"current={mismatch.current_status} "
                f"expected={mismatch.expected_status} "
                f"title={mismatch.title}"
            )

        if report.checked_calls == 0 and options["require_checked"]:
            raise CommandError("Call data quality verification did not check any calls.")

        if report.has_issues and options["fail_on_issues"]:
            raise CommandError("Call data quality verification found issues.")

        if not report.has_issues:
            self.stdout.write(self.style.SUCCESS("Call data quality verification passed."))

        if options["probe"]:
            _run_probe()
            self.stdout.write(self.style.SUCCESS("Call data quality probe passed."))


def _run_probe() -> None:
    source = Source.objects.select_related("institution").order_by("id").first()
    if source is None:
        raise CommandError("Call data quality probe requires at least one imported source.")

    now = timezone.now()
    prefix = f"quality-probe-{int(now.timestamp() * 1000)}"
    deadline = now + timedelta(days=20)
    expired_deadline = now - timedelta(days=1)
    base_url = source.base_url.rstrip("/")

    with transaction.atomic():
        GrantCall.objects.create(
            title="KOBI Hibe Programi",
            slug=f"{prefix}-duplicate-a",
            source=source,
            institution=source.institution,
            official_url=f"{base_url}/{prefix}/duplicate-a",
            canonical_source_url=f"{base_url}/{prefix}/duplicate-a",
            fingerprint=f"{prefix}-duplicate-a",
            deadline_at=deadline,
            first_seen_at=now,
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )
        GrantCall.objects.create(
            title="KOBİ Hibe Programı",
            slug=f"{prefix}-duplicate-b",
            source=source,
            institution=source.institution,
            official_url=f"{base_url}/{prefix}/duplicate-b",
            canonical_source_url=f"{base_url}/{prefix}/duplicate-b",
            fingerprint=f"{prefix}-duplicate-b",
            deadline_at=deadline,
            first_seen_at=now,
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )
        GrantCall.objects.create(
            title="Suresi Dolmus Hibe Programi",
            slug=f"{prefix}-closed-mismatch",
            source=source,
            institution=source.institution,
            official_url=f"{base_url}/{prefix}/closed-mismatch",
            canonical_source_url=f"{base_url}/{prefix}/closed-mismatch",
            fingerprint=f"{prefix}-closed-mismatch",
            deadline_at=expired_deadline,
            first_seen_at=now,
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )

        report = build_call_data_quality_report(
            queryset=GrantCall.objects.filter(fingerprint__startswith=prefix),
            now=now,
        )
        transaction.set_rollback(True)

    if report.checked_calls != 3:
        raise CommandError(f"Call data quality probe checked {report.checked_calls} calls, expected 3.")
    if len(report.duplicate_candidates) != 1:
        raise CommandError("Call data quality probe did not detect the semantic duplicate candidate.")
    if len(report.availability_mismatches) != 1:
        raise CommandError("Call data quality probe did not detect the stale availability status.")
    if report.availability_mismatches[0].expected_status != GrantCall.AvailabilityStatus.CLOSED:
        raise CommandError("Call data quality probe did not expect the expired call to be closed.")
