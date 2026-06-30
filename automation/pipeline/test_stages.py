from __future__ import annotations

from django.test import SimpleTestCase

from automation.pipeline.stages import PIPELINE_STAGE_ORDER, PipelineOutcome, PipelineStage, StageResult, StageStatus


class PipelineStageTests(SimpleTestCase):
    def test_stage_order_matches_documented_flow(self) -> None:
        self.assertEqual(PIPELINE_STAGE_ORDER[0], PipelineStage.SCHEDULE)
        self.assertEqual(PIPELINE_STAGE_ORDER[-1], PipelineStage.METRICS)
        self.assertLess(
            PIPELINE_STAGE_ORDER.index(PipelineStage.FETCH), PIPELINE_STAGE_ORDER.index(PipelineStage.PARSE)
        )
        self.assertLess(
            PIPELINE_STAGE_ORDER.index(PipelineStage.DUPLICATE_MATCH),
            PIPELINE_STAGE_ORDER.index(PipelineStage.CONFIDENCE),
        )

    def test_failed_outcome_reports_failed_stage(self) -> None:
        outcome = PipelineOutcome(
            results=(
                StageResult(stage=PipelineStage.DISCOVER, status=StageStatus.SUCCESS),
                StageResult(stage=PipelineStage.FETCH, status=StageStatus.FAILED, error_code="timeout"),
            )
        )

        self.assertFalse(outcome.is_successful)
        self.assertEqual(outcome.failed_stage, PipelineStage.FETCH)
