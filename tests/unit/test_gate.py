from code_review_skill_evolution.contracts import Score
from code_review_skill_evolution.gate import aggregate_scores, strict_gate


def test_gate_requires_strict_improvement() -> None:
    incumbent = Score(0.5, 0.4)
    assert not strict_gate(incumbent, Score(0.5, 0.4)).accepted
    assert not strict_gate(incumbent, Score(0.4, 1.0)).accepted
    assert strict_gate(incumbent, Score(0.5, 0.5)).accepted
    assert strict_gate(incumbent, Score(0.6, 0.0)).accepted


def test_aggregate_scores_records_task_count() -> None:
    score = aggregate_scores([Score(0.0, 0.5), Score(1.0, 1.0)])
    assert score.primary == 0.5
    assert score.secondary == 0.75
    assert score.details["task_count"] == 2
