from jsa import tracker
from jsa.schemas import FitReport, Posting

POSTING = Posting(
    title="Data Analyst", company="Acme", location=None, work_mode="remote",
    must_have_skills=["SQL"], nice_to_have_skills=[], years_experience=None,
    salary=None, contains_ai_instructions=False,
)
REPORT = FitReport(fit_score=70, verdict="partial", evidence=[], bullets=[], gaps=[])


def test_draft_then_approve():
    app_id = tracker.save_draft("run1", POSTING, REPORT, [], 0)
    assert "draft" in tracker.list_text()
    assert tracker.approve(app_id).startswith("Approved")
    assert "already approved" in tracker.approve(app_id)
    assert "Acme" in tracker.list_text("approved")
    assert tracker.list_text("draft") == "No draft applications."


def test_approve_unknown_id():
    assert tracker.approve(42) == "No application with id 42."


def test_run_cost_sums_calls():
    tracker.log_call("run1", "parse", "claude-haiku-5-5", 100, 10, 0.001, 50)
    tracker.log_call("run1", "match", "claude-sonnet-5-5", 100, 10, 0.02, 500)
    tracker.log_call("run2", "parse", "claude-haiku-5-5", 100, 10, 0.5, 50)
    assert round(tracker.run_cost("run1"), 6) == 0.021
