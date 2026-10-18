"""analyze(): parse -> retrieve -> match -> check -> save as draft.

The check step is plain Python and doesn't trust the model: bullets that cite
nothing, or cite a chunk that wasn't retrieved, are dropped and counted, the fit
score is clamped to 0-100, and the verdict is derived from the score.
"""

import time
from dataclasses import dataclass

from jsa import retrieve, tracker
from jsa.match import match
from jsa.parse import parse_posting
from jsa.retrieve import Chunk
from jsa.schemas import FitReport, Posting

# The matcher's rubric: 75 and up is strong, below 40 is poor.
STRONG_FROM, POOR_BELOW = 75, 40

INJECTION_WARNING = (
    "This posting contains text that tries to instruct an AI screener. "
    "It was ignored, but read the posting yourself before applying."
)


@dataclass
class AnalysisResult:
    application_id: int
    run_id: str
    posting: Posting
    report: FitReport
    chunks: list[Chunk]  # what was retrieved, so the eval can check bullets against it
    dropped_bullets: int
    warnings: list[str]
    cost_usd: float
    seconds: float

    def to_text(self) -> str:
        p, r = self.posting, self.report
        lines = [
            f"Draft #{self.application_id}: {p.company} - {p.title}",
            f"Fit {r.fit_score}/100 ({r.verdict})",
            "",
            "Evidence:",
        ]
        for e in r.evidence:
            cites = f"  [{', '.join(e.chunk_ids)}]" if e.chunk_ids else ""
            lines.append(f"  {e.status:<8} {e.skill}: {e.note}{cites}")
        lines += ["", "Bullets:"]
        lines += [f"  - {b.text}  [{', '.join(b.chunk_ids)}]" for b in r.bullets] or ["  (none)"]
        if r.gaps:
            lines += ["", "Gaps:"] + [f"  - {g}" for g in r.gaps]
        if self.warnings:
            lines += ["", "Warnings:"] + [f"  ! {w}" for w in self.warnings]
        lines += [
            "",
            f"Dropped {self.dropped_bullets} uncited bullet(s).",
            f"Cost ${self.cost_usd:.4f} · {self.seconds:.1f} s · run {self.run_id[:8]}",
            f"Saved as a draft. Nothing is final until you approve #{self.application_id}.",
        ]
        return "\n".join(lines)


def verdict_for(score: int) -> str:
    return "strong" if score >= STRONG_FROM else "poor" if score < POOR_BELOW else "partial"


def apply_guard(report: FitReport, retrieved_ids: set[str]) -> tuple[FitReport, int]:
    """Drop bullets without a valid citation, clamp the score and derive the verdict.

    The model sometimes labels a score of 38 "partial"; taking the verdict from the
    score means the two can never disagree. Returns (report, bullets dropped).
    """
    kept = [b for b in report.bullets if b.chunk_ids and set(b.chunk_ids) <= retrieved_ids]
    score = max(0, min(100, report.fit_score))
    update = {"bullets": kept, "fit_score": score, "verdict": verdict_for(score)}
    return report.model_copy(update=update), len(report.bullets) - len(kept)


def analyze(posting_text: str, run_id: str | None = None) -> AnalysisResult:
    """Run the whole pipeline. Pass `run_id` to look up the run's cost even if it fails."""
    t0 = time.monotonic()
    run_id = run_id or tracker.new_run_id()

    posting = parse_posting(posting_text, run_id=run_id)
    chunks = retrieve.get_retriever(retrieve.docs_dir()).search(posting.must_have_skills)
    report = match(posting, chunks, run_id=run_id)
    report, dropped = apply_guard(report, {c.id for c in chunks})

    warnings = []
    if posting.contains_ai_instructions:
        warnings.append(INJECTION_WARNING)
    if not chunks:
        warnings.append("No document chunks matched the must-have skills.")

    app_id = tracker.save_draft(run_id, posting, report, warnings, dropped)
    return AnalysisResult(
        application_id=app_id,
        run_id=run_id,
        posting=posting,
        report=report,
        chunks=chunks,
        dropped_bullets=dropped,
        warnings=warnings,
        cost_usd=tracker.run_cost(run_id),
        seconds=time.monotonic() - t0,
    )
