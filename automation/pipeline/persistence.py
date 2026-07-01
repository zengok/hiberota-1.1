from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apps.calls.fingerprints import build_duplicate_fingerprint
from apps.calls.models import GrantCall
from apps.calls.services import calculate_availability_status
from apps.ingestion.models import FieldEvidence, ReviewItem
from apps.institutions.models import Country
from apps.sources.models import Source
from apps.taxonomy.models import AudienceType, ProgramType, Sector, Theme
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from automation.adapters.contracts import ParsedCall
from automation.pipeline.confidence import calculate_confidence
from automation.pipeline.validation import ValidationIssue, validate_parsed_call

AUDIENCE_KEY_ALIASES = {
    "student": ("student", "ogrenci"),
    "graduate_student": ("graduate_student", "lisansustu_ogrenci"),
    "academic": ("academic", "akademisyen"),
    "researcher": ("researcher", "arastirmaci"),
    "entrepreneur": ("entrepreneur", "girisimci"),
    "sme": ("sme", "kobi"),
    "company": ("company", "sirket", "firma"),
    "ngo": ("ngo", "stk"),
    "municipality": ("municipality", "belediye"),
    "public_institution": ("public_institution", "kamu_kurumu", "kamu"),
}


@dataclass(frozen=True, slots=True)
class PersistedCall:
    grant_call: GrantCall
    created: bool
    review_created: bool
    evidence_count: int


def persist_parsed_call(
    *,
    source: Source,
    parsed_call: ParsedCall,
    fetched_at: datetime | None,
    content_hash: str,
    parser_version: str,
) -> PersistedCall:
    """Persist one parsed call without bypassing duplicate, status, confidence, or evidence rules."""
    now = timezone.now()
    observed_at = fetched_at or now
    confidence = calculate_confidence(parsed_call)
    validation = validate_parsed_call(parsed_call)
    requires_review = confidence.requires_review or validation.requires_review

    with transaction.atomic():
        grant_call, created, effective_requires_review = _upsert_grant_call(
            source=source,
            parsed_call=parsed_call,
            confidence_score=confidence.score,
            requires_review=requires_review,
            confidence_reason_codes=confidence.reason_codes,
            validation_issues=validation.issues,
            now=now,
        )
        _sync_taxonomy(grant_call, parsed_call)
        evidence_count = _persist_evidence(
            source=source,
            grant_call=grant_call,
            parsed_call=parsed_call,
            fetched_at=observed_at,
            content_hash=content_hash,
            parser_version=parser_version,
        )
        review_created = _sync_review_items(
            grant_call=grant_call,
            confidence_reason_codes=confidence.reason_codes if effective_requires_review else (),
            validation_issues=validation.issues if effective_requires_review else (),
        )

    return PersistedCall(
        grant_call=grant_call,
        created=created,
        review_created=review_created,
        evidence_count=evidence_count,
    )


def _upsert_grant_call(
    *,
    source: Source,
    parsed_call: ParsedCall,
    confidence_score: int,
    requires_review: bool,
    confidence_reason_codes: tuple[str, ...],
    validation_issues: tuple[ValidationIssue, ...],
    now: datetime,
) -> tuple[GrantCall, bool, bool]:
    availability_status = calculate_availability_status(
        application_open_at=parsed_call.application_open_at,
        deadline_at=parsed_call.deadline_at,
        now=now,
    )
    fingerprint = build_duplicate_fingerprint(
        institution_id=source.institution_id,
        title=parsed_call.title,
        deadline_at=parsed_call.deadline_at,
        canonical_source_url=parsed_call.canonical_source_url,
    )
    workflow_status = GrantCall.WorkflowStatus.REVIEW
    if confidence_score >= 85 and not requires_review:
        workflow_status = GrantCall.WorkflowStatus.PUBLISHED
    published_at = now if workflow_status == GrantCall.WorkflowStatus.PUBLISHED else None
    values = {
        "title": parsed_call.title,
        "slug": _slug_for(parsed_call.title),
        "source": source,
        "institution": source.institution,
        "external_id": parsed_call.external_id,
        "official_url": parsed_call.official_url,
        "fingerprint": fingerprint,
        "summary": parsed_call.summary,
        "purpose": parsed_call.purpose,
        "eligibility_text": parsed_call.eligibility_text,
        "conditions_text": parsed_call.conditions_text,
        "duration_text": parsed_call.duration_text,
        "funding_text": parsed_call.funding_text,
        "application_process_text": parsed_call.application_process_text,
        "contact_text": parsed_call.contact_text,
        "source_published_at": parsed_call.source_published_at,
        "application_open_at": parsed_call.application_open_at,
        "deadline_at": parsed_call.deadline_at,
        "deadline_timezone": parsed_call.deadline_timezone,
        "last_seen_at": now,
        "last_verified_at": now,
        "duration_min_months": parsed_call.duration_min_months,
        "duration_max_months": parsed_call.duration_max_months,
        "funding_min": parsed_call.funding_min,
        "funding_max": parsed_call.funding_max,
        "currency": parsed_call.currency,
        "funding_rate_percent": parsed_call.funding_rate_percent,
        "workflow_status": workflow_status,
        "availability_status": availability_status,
        "confidence_score": confidence_score,
        "published_at": published_at,
    }
    grant_call = _find_existing_call(
        source=source,
        parsed_call=parsed_call,
        fingerprint=fingerprint,
    )
    if grant_call is None:
        return (
            GrantCall.objects.create(
                canonical_source_url=parsed_call.canonical_source_url,
                first_seen_at=now,
                **values,
            ),
            True,
            requires_review,
        )

    effective_requires_review = requires_review
    if grant_call.workflow_status == GrantCall.WorkflowStatus.REJECTED:
        effective_requires_review = False
        values["workflow_status"] = GrantCall.WorkflowStatus.REJECTED
        values["published_at"] = grant_call.published_at
    elif requires_review and _should_preserve_published_review_approval(
        grant_call=grant_call,
        confidence_reason_codes=confidence_reason_codes,
        validation_issues=validation_issues,
    ):
        effective_requires_review = False
        values["workflow_status"] = GrantCall.WorkflowStatus.PUBLISHED
        values["published_at"] = grant_call.published_at or now

    for field_name, value in values.items():
        setattr(grant_call, field_name, value)
    grant_call.canonical_source_url = parsed_call.canonical_source_url
    grant_call.save(update_fields=[*values.keys(), "canonical_source_url", "updated_at"])
    return grant_call, False, effective_requires_review


def _should_preserve_published_review_approval(
    *,
    grant_call: GrantCall,
    confidence_reason_codes: tuple[str, ...],
    validation_issues: tuple[ValidationIssue, ...],
) -> bool:
    if grant_call.workflow_status != GrantCall.WorkflowStatus.PUBLISHED:
        return False
    if validation_issues:
        return False
    return True


def _find_existing_call(*, source: Source, parsed_call: ParsedCall, fingerprint: str) -> GrantCall | None:
    if parsed_call.external_id:
        source_match = GrantCall.objects.filter(source=source, external_id=parsed_call.external_id).first()
        if source_match is not None:
            return source_match

    canonical_match = GrantCall.objects.filter(canonical_source_url=parsed_call.canonical_source_url).first()
    if canonical_match is not None:
        return canonical_match

    return GrantCall.objects.filter(fingerprint=fingerprint).first()


def _sync_taxonomy(grant_call: GrantCall, parsed_call: ParsedCall) -> None:
    grant_call.countries.set(Country.objects.filter(code__in=parsed_call.country_codes))
    grant_call.audiences.set(AudienceType.objects.filter(key__in=_resolve_audience_keys(parsed_call.audience_keys)))
    grant_call.sectors.set(Sector.objects.filter(key__in=parsed_call.sector_keys))
    grant_call.themes.set(Theme.objects.filter(key__in=parsed_call.theme_keys))
    grant_call.program_types.set(ProgramType.objects.filter(key__in=parsed_call.program_type_keys))


def _resolve_audience_keys(audience_keys: tuple[str, ...]) -> tuple[str, ...]:
    candidate_keys = tuple(
        dict.fromkeys(alias for key in audience_keys for alias in AUDIENCE_KEY_ALIASES.get(key, (key,)))
    )
    existing_keys = set(AudienceType.objects.filter(key__in=candidate_keys).values_list("key", flat=True))
    return tuple(key for key in candidate_keys if key in existing_keys)


def _persist_evidence(
    *,
    source: Source,
    grant_call: GrantCall,
    parsed_call: ParsedCall,
    fetched_at: datetime,
    content_hash: str,
    parser_version: str,
) -> int:
    count = 0
    for evidence in parsed_call.evidence:
        FieldEvidence.objects.update_or_create(
            grant_call=grant_call,
            field_name=evidence.field_name,
            content_hash=content_hash,
            parser_version=parser_version,
            defaults={
                "source": source,
                "source_url": evidence.source_url,
                "source_excerpt": evidence.source_excerpt[:2000],
                "selector_or_path": evidence.selector_or_path,
                "fetched_at": fetched_at,
                "confidence": evidence.confidence,
            },
        )
        count += 1
    return count


def _sync_review_items(
    *,
    grant_call: GrantCall,
    confidence_reason_codes: tuple[str, ...],
    validation_issues: tuple[ValidationIssue, ...],
) -> bool:
    created_any = False
    active_reason_codes = {issue.reason_code for issue in validation_issues}
    for issue in validation_issues:
        review, created = ReviewItem.objects.get_or_create(
            grant_call=grant_call,
            reason_code=issue.reason_code,
            defaults={"severity": issue.severity.value, "resolution": issue.message},
        )
        if review.status == ReviewItem.Status.RESOLVED:
            review.status = ReviewItem.Status.OPEN
            review.resolution = issue.message
            review.save(update_fields=["status", "resolution", "updated_at"])
        created_any = created_any or created
    for reason in confidence_reason_codes:
        active_reason_codes.add(_review_reason_for(reason))
        review, created = ReviewItem.objects.get_or_create(
            grant_call=grant_call,
            reason_code=_review_reason_for(reason),
            defaults={"severity": ReviewItem.Severity.MEDIUM},
        )
        if review.status == ReviewItem.Status.RESOLVED:
            review.status = ReviewItem.Status.OPEN
            review.save(update_fields=["status", "updated_at"])
        created_any = created_any or created
    stale_reviews = ReviewItem.objects.filter(
        grant_call=grant_call,
        status=ReviewItem.Status.OPEN,
        reason_code__in=_managed_review_reason_codes(),
    ).exclude(reason_code__in=active_reason_codes)
    for review in stale_reviews:
        review.status = ReviewItem.Status.RESOLVED
        review.resolution = "Resolved by latest parser validation."
        review.resolved_at = timezone.now()
        review.save(update_fields=["status", "resolution", "resolved_at", "updated_at"])
    return created_any


def _review_reason_for(reason: str) -> str:
    if reason in {"missing_title", "missing_official_url"}:
        return ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD
    return ReviewItem.ReasonCode.LOW_CONFIDENCE


def _managed_review_reason_codes() -> tuple[str, ...]:
    return (
        ReviewItem.ReasonCode.DEADLINE_CONFLICT,
        ReviewItem.ReasonCode.LOW_CONFIDENCE,
        ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
        ReviewItem.ReasonCode.SOURCE_RESTRICTED,
    )


def _slug_for(title: str) -> str:
    return slugify(title, allow_unicode=False)[:300] or "cagri"
