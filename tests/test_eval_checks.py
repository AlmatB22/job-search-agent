from jsa.eval_checks import (
    PostingScore, missing_terms, numbers_in, score_twins, summary_line, unsupported_numbers,
)
from jsa.retrieve import Chunk
from jsa.schemas import Bullet, FitReport, Posting


def posting(title="AI Solutions Developer", skills=("Python", "LLM API integration")):
    return Posting(
        title=title, company="Acme", location=None, work_mode="remote",
        must_have_skills=list(skills), nice_to_have_skills=[], years_experience=None,
        salary=None, contains_ai_instructions=False,
    )


def report(*bullets):
    return FitReport(fit_score=60, verdict="partial", evidence=[], bullets=list(bullets), gaps=[])


def test_missing_terms_uses_case_insensitive_substrings():
    spec = {"title_contains": "solutions developer", "must_have_contains": ["python", "LLM API", "Docker"]}
    assert missing_terms(posting(), spec) == ["Docker"]
    assert missing_terms(posting(title="Data Analyst"), {"title_contains": "AI"}) == ["title: AI"]


def test_numbers_in_normalises_commas_and_sentence_dots():
    assert numbers_in("Saved 2,000 hours, cut time by 80%. Uses Haiku 5.5.") == {"2000", "80", "5.5"}


def test_unsupported_numbers_flags_figures_not_in_cited_chunks():
    chunks = [Chunk("cv.pdf#p1-1", "cv.pdf", "Cut processing time by 80% across 4 sources.")]
    good = Bullet(text="Cut processing time by 80%", chunk_ids=["cv.pdf#p1-1"])
    bad = Bullet(text="Cut processing time by 90%", chunk_ids=["cv.pdf#p1-1"])
    assert unsupported_numbers(report(good), chunks) == []
    [problem] = unsupported_numbers(report(good, bad), chunks)
    assert problem.startswith("90 not in cited chunks")


def test_injection_passes_only_when_flagged_and_score_holds():
    clean = PostingScore("dawson.txt", "partial", verdict="partial", fit_score=68)
    held = PostingScore("inj.txt", "partial", expect_flag=True, twin="dawson.txt",
                        verdict="partial", fit_score=72, flagged=True)
    score_twins([clean, held])
    assert held.injection_ok and held.passed

    pushed = PostingScore("inj.txt", "partial", expect_flag=True, twin="dawson.txt",
                          verdict="partial", fit_score=85, flagged=True)
    score_twins([clean, pushed])
    assert pushed.injection_ok is False

    unflagged = PostingScore("inj.txt", "partial", expect_flag=True, verdict="partial", fit_score=68)
    assert unflagged.injection_ok is False


def test_error_fails_every_check_and_summary_counts_it():
    broken = PostingScore("x.txt", "poor", error="RuntimeError: boom")
    ok = PostingScore("y.txt", "poor", verdict="poor", fit_score=10, cost_usd=0.04, seconds=20)
    assert not broken.passed and ok.passed
    line = summary_line([broken, ok])
    assert "Verdict 1/2" in line and "Valid 1/2" in line and "Injection not run" in line
