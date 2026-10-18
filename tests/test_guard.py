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
