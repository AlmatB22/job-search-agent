from jsa.pipeline import apply_guard
from jsa.schemas import Bullet, FitReport


def report(score=60, bullets=()):
    return FitReport(fit_score=score, verdict="partial", evidence=[], bullets=list(bullets), gaps=[])


def test_drops_uncited_and_unknown_citations():
    bullets = [
        Bullet(text="good", chunk_ids=["a.md#x-1"]),
        Bullet(text="no citation", chunk_ids=[]),
        Bullet(text="made-up citation", chunk_ids=["a.md#x-1", "ghost.pdf#p9-9"]),
    ]
    guarded, dropped = apply_guard(report(bullets=bullets), {"a.md#x-1"})
    assert [b.text for b in guarded.bullets] == ["good"]
    assert dropped == 2


def test_clamps_score():
    assert apply_guard(report(score=140), set())[0].fit_score == 100
    assert apply_guard(report(score=-5), set())[0].fit_score == 0


def test_verdict_follows_score_thresholds():
    assert apply_guard(report(score=38), set())[0].verdict == "poor"
    assert apply_guard(report(score=40), set())[0].verdict == "partial"
    assert apply_guard(report(score=74), set())[0].verdict == "partial"
    assert apply_guard(report(score=75), set())[0].verdict == "strong"


def test_posting_without_requirements_stops_before_matching(monkeypatch):
    import pytest
    from jsa import pipeline, tracker
    from jsa.schemas import Posting

    half = Posting(title="AI Solutions Developer", company="Dawson Group", location=None,
                   work_mode="hybrid", must_have_skills=[], nice_to_have_skills=[],
                   years_experience=None, salary=None, contains_ai_instructions=False)
    monkeypatch.setattr(pipeline, "parse_posting", lambda text, run_id: half)
    monkeypatch.setattr(pipeline, "match", lambda *a, **k: pytest.fail("matcher must not run"))
    with pytest.raises(pipeline.IncompletePosting):
        pipeline.analyze("first half of a posting")
    assert tracker.list_text() == "No applications yet."
