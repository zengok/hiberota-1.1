from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.calls.audit import build_call_data_quality_report
from apps.calls.models import GrantCall
from apps.ingestion.models import ReviewItem


class Command(BaseCommand):
    help = "Move false-open historical/listing calls out of the public list and into review."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source-key", action="append", default=[], help="Limit to one source key.")
        parser.add_argument("--limit", type=int, default=0, help="Limit matched candidates.")
        parser.add_argument("--commit", action="store_true", help="Apply changes. Omit for dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        queryset = GrantCall.objects.all()
        source_keys = [str(key).strip() for key in options["source_key"] if str(key).strip()]
        if source_keys:
            queryset = queryset.filter(source__source_key__in=source_keys)

        report = build_call_data_quality_report(queryset=queryset)
        candidates = list(report.false_open_candidates)
        limit = int(options["limit"] or 0)
        if limit > 0:
            candidates = candidates[:limit]

        self.stdout.write(f"Matched false-open candidates: {len(candidates)}")
        for candidate in candidates:
            self.stdout.write(f"{candidate.call_id}. {candidate.source_key} | {candidate.title} | {candidate.reason}")

        if not options["commit"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete. Run again with --commit to quarantine calls."))
            return

        now = timezone.now()
        candidate_ids = tuple(candidate.call_id for candidate in candidates)
        with transaction.atomic():
            updated_calls = GrantCall.objects.filter(id__in=candidate_ids).update(
                workflow_status=GrantCall.WorkflowStatus.REVIEW,
                availability_status=GrantCall.AvailabilityStatus.UNKNOWN,
                updated_at=now,
            )
            created_reviews = 0
            for call_id in candidate_ids:
                if ReviewItem.objects.filter(
                    grant_call_id=call_id,
                    reason_code=ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
                    status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
                ).exists():
                    continue
                ReviewItem.objects.create(
                    grant_call_id=call_id,
                    reason_code=ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
                    severity=ReviewItem.Severity.HIGH,
                    status=ReviewItem.Status.OPEN,
                    resolution="False-open candidate: missing deadline, eligibility, and audience.",
                )
                created_reviews += 1

        self.stdout.write(self.style.SUCCESS(f"Quarantined calls: {updated_calls}"))
        self.stdout.write(self.style.SUCCESS(f"Created review items: {created_reviews}"))
