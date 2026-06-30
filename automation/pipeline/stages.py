from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PipelineStage(StrEnum):
    SCHEDULE = "schedule"
    SOURCE_LOCK = "source_lock"
    DISCOVER = "discover"
    NORMALIZE_DISCOVERED_URL = "normalize_discovered_url"
    EARLY_DUPLICATE = "early_duplicate"
    FETCH = "fetch"
    PARSE = "parse"
    NORMALIZE_FIELDS = "normalize_fields"
    VALIDATE = "validate"
    TAXONOMY_RULES = "taxonomy_rules"
    DUPLICATE_MATCH = "duplicate_match"
    CONFIDENCE = "confidence"
    REVIEW_OR_PUBLISH = "review_or_publish"
    EVIDENCE = "evidence"
    METRICS = "metrics"


PIPELINE_STAGE_ORDER: tuple[PipelineStage, ...] = (
    PipelineStage.SCHEDULE,
    PipelineStage.SOURCE_LOCK,
    PipelineStage.DISCOVER,
    PipelineStage.NORMALIZE_DISCOVERED_URL,
    PipelineStage.EARLY_DUPLICATE,
    PipelineStage.FETCH,
    PipelineStage.PARSE,
    PipelineStage.NORMALIZE_FIELDS,
    PipelineStage.VALIDATE,
    PipelineStage.TAXONOMY_RULES,
    PipelineStage.DUPLICATE_MATCH,
    PipelineStage.CONFIDENCE,
    PipelineStage.REVIEW_OR_PUBLISH,
    PipelineStage.EVIDENCE,
    PipelineStage.METRICS,
)


class StageStatus(StrEnum):
    PENDING = "pending"
    SKIPPED = "skipped"
    SUCCESS = "success"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True, slots=True)
class StageResult:
    stage: PipelineStage
    status: StageStatus
    error_code: str = ""
    error_summary: str = ""
    metrics: dict[str, int | float] = field(default_factory=dict)

    @property
    def is_successful(self) -> bool:
        return self.status in {StageStatus.SUCCESS, StageStatus.SKIPPED}


@dataclass(frozen=True, slots=True)
class PipelineOutcome:
    results: tuple[StageResult, ...]
    payload: Any | None = None

    @property
    def is_successful(self) -> bool:
        return all(result.is_successful for result in self.results)

    @property
    def failed_stage(self) -> PipelineStage | None:
        for result in self.results:
            if result.status == StageStatus.FAILED:
                return result.stage
        return None


def pending_results() -> tuple[StageResult, ...]:
    return tuple(StageResult(stage=stage, status=StageStatus.PENDING) for stage in PIPELINE_STAGE_ORDER)
