from __future__ import annotations

from typing import Any

from automation.pipeline.persistence import resolve_audience_keys
from automation.pipeline.taxonomy_rules import infer_audience_keys_for_call
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from apps.calls.models import GrantCall
from apps.taxonomy.models import AudienceType


class Command(BaseCommand):
    help = "Backfill missing call audiences using conservative source and text taxonomy rules."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--commit", action="store_true", help="Write inferred audiences. Defaults to dry run.")
        parser.add_argument("--limit", type=int, default=0, help="Limit checked calls for a smaller run.")
        parser.add_argument(
            "--workflow-status",
            action="append",
            default=[],
            help="Limit to a workflow status. Can be passed multiple times.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        commit = bool(options["commit"])
        queryset = (
            GrantCall.objects.filter(audiences__isnull=True)
            .select_related("source", "source__institution")
            .order_by("id")
            .distinct()
        )
        workflow_statuses = [str(status).strip() for status in options["workflow_status"] if str(status).strip()]
        if workflow_statuses:
            queryset = queryset.filter(workflow_status__in=workflow_statuses)
        limit = int(options["limit"] or 0)
        if limit > 0:
            queryset = queryset[:limit]

        checked = 0
        updated = 0
        unresolved = 0
        with transaction.atomic():
            for call in queryset:
                checked += 1
                inferred_keys = resolve_audience_keys(infer_audience_keys_for_call(call))
                if not inferred_keys:
                    unresolved += 1
                    continue
                audiences = AudienceType.objects.filter(key__in=inferred_keys)
                if commit:
                    call.audiences.set(audiences)
                updated += 1
                self.stdout.write(f"call_id={call.id} audiences={','.join(inferred_keys)} title={call.title[:90]}")

            if not commit:
                transaction.set_rollback(True)

        mode = "committed" if commit else "dry-run"
        self.stdout.write(
            self.style.SUCCESS(
                f"Audience backfill {mode}: checked={checked}, updated={updated}, unresolved={unresolved}"
            )
        )
