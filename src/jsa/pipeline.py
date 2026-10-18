"""analyze(): parse -> retrieve -> match -> check -> save as draft.

The check step is plain Python and doesn't trust the model: bullets that cite
nothing, or cite a chunk that wasn't retrieved, are dropped and counted, and the
fit score is clamped to 0-100.
"""

import time
from dataclasses import dataclass

from jsa import retrieve, tracker
from jsa.match import match
from jsa.parse import parse_posting
from jsa.schemas import FitReport, Posting

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


def apply_guard(report: FitReport, retrieved_ids: set[str]) -> tuple[FitReport, int]:
    """Drop bullets without a valid citation and clamp the score; return (report, dropped)."""
    kept = [b for b in report.bullets if b.chunk_ids and set(b.chunk_ids) <= retrieved_ids]
    score = max(0, min(100, report.fit_score))
    return report.model_copy(update={"bullets": kept, "fit_score": score}), len(report.bullets) - len(kept)


def analyze(posting_text: str) -> AnalysisResult:
    t0 = time.monotonic()
    run_id = tracker.new_run_id()

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
        dropped_bullets=dropped,
        warnings=warnings,
        cost_usd=tracker.run_cost(run_id),
        seconds=time.monotonic() - t0,
    )
