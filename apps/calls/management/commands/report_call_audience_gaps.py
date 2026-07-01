from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.calls.audience_gaps import AudienceGapReason, build_audience_gap_report
from apps.calls.models import GrantCall


class Command(BaseCommand):
    help = "Report published calls that still have no audience tags and why they could not be inferred."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print per reason.")
        parser.add_argument("--reason", choices=tuple(reason.value for reason in AudienceGapReason))
        parser.add_argument(
            "--workflow-status",
            action="append",
            default=[],
            help="Limit to a workflow status. Can be passed multiple times.",
        )
        parser.add_argument(
            "--availability-status",
            action="append",
            default=[],
            help="Limit to an availability status. Can be passed multiple times.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        limit = int(options["limit"])
        if limit < 1:
            raise CommandError("limit must be greater than zero.")

        queryset = GrantCall.objects.all()
        workflow_statuses = [str(status).strip() for status in options["workflow_status"] if str(status).strip()]
        if workflow_statuses:
            queryset = queryset.filter(workflow_status__in=workflow_statuses)
        availability_statuses = [
            str(status).strip() for status in options["availability_status"] if str(status).strip()
        ]
        if availability_statuses:
            queryset = queryset.filter(availability_status__in=availability_statuses)

        selected_reason = _reason_from_option(options.get("reason"))
        report = build_audience_gap_report(queryset=queryset)
        counts = report.counts_by_reason()

        self.stdout.write("Audience gap summary")
        for reason in AudienceGapReason:
            self.stdout.write(f"- {reason.value}: {counts[reason]}")

        reasons = (selected_reason,) if selected_reason else tuple(AudienceGapReason)
        for reason in reasons:
            entries = report.entries_for(reason)[:limit]
            self.stdout.write("")
            self.stdout.write(f"{reason.value} ({counts[reason]})")
            if not entries:
                self.stdout.write("  No matching calls.")
                continue
            for entry in entries:
                call = entry.call
                deadline = call.deadline_at.date().isoformat() if call.deadline_at else "missing"
                inferred = ",".join(entry.inferred_keys) if entry.inferred_keys else "none"
                source_hints = ",".join(entry.source_hint_keys) if entry.source_hint_keys else "none"
                self.stdout.write(
                    "  "
                    f"{call.id}. {call.source.source_key} | status={call.availability_status} | "
                    f"deadline={deadline} | inferred={inferred} | source_hints={source_hints} | "
                    f"{call.title[:110]} | {entry.note}"
                )


def _reason_from_option(value: str | None) -> AudienceGapReason | None:
    if not value:
        return None
    try:
        return AudienceGapReason(value)
    except ValueError as exc:
        raise CommandError(str(exc)) from exc
