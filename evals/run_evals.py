"""Run the pipeline over evals/postings/ and score it against answer_key.yaml.

    uv run python evals/run_evals.py               # all postings; writes evals/results.md
    uv run python evals/run_evals.py --only dawson # one posting while iterating; no file

Spends real API money, about $0.05 per posting. Run it from the repo root. Exits
non-zero when any check fails.
"""

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

# Eval runs save drafts like any run; keep them out of the real tracker. Set before
# importing jsa, whose .env loading never overrides a variable that is already set.
os.environ["JSA_DB_PATH"] = "data/db/evals.sqlite"

import yaml  # noqa: E402

from jsa import llm, retrieve, tracker  # noqa: E402
from jsa.eval_checks import (  # noqa: E402
    PostingScore, failure_details, missing_terms, results_table, score_twins,
    summary_line, unsupported_numbers,
)
from jsa.pipeline import analyze  # noqa: E402

EVALS = Path(__file__).parent
POSTINGS = EVALS / "postings"


def load_key() -> dict[str, dict]:
    key = yaml.safe_load((EVALS / "answer_key.yaml").read_text(encoding="utf-8")) or {}
    for name, spec in key.items():
        if not (POSTINGS / name).exists():
            sys.exit(f"answer_key.yaml lists {name}, but evals/postings/{name} does not exist")
        twin = spec.get("twin")
        if twin:
            if twin not in key:
                sys.exit(f"{name}: twin {twin} has no answer key entry")
            # An injected posting should get exactly its clean twin's verdict.
            spec.setdefault("expected_verdict", key[twin]["expected_verdict"])
    unkeyed = sorted(p.name for p in POSTINGS.glob("*.txt") if p.name not in key)
    if unkeyed:
        print(f"Skipping postings with no answer key entry: {', '.join(unkeyed)}\n")
    return key


def run_one(name: str, spec: dict) -> PostingScore:
    score = PostingScore(
        name=name,
        expected_verdict=spec["expected_verdict"],
        expect_flag=bool(spec.get("expect_ai_instructions_flag", False)),
        twin=spec.get("twin"),
    )
    run_id = tracker.new_run_id()
    try:
        result = analyze((POSTINGS / name).read_text(encoding="utf-8"), run_id=run_id)
    except Exception as e:  # one bad posting must not stop the run
        score.error = f"{type(e).__name__}: {e}"
        score.cost_usd = tracker.run_cost(run_id)
        return score
    score.verdict = result.report.verdict
    score.fit_score = result.report.fit_score
    score.flagged = result.posting.contains_ai_instructions
    score.missing = missing_terms(result.posting, spec)
    score.unsupported = unsupported_numbers(result.report, result.chunks)
    score.dropped = result.dropped_bullets
    score.cost_usd = result.cost_usd
    score.seconds = result.seconds
    return score


def git_version() -> str:
    def git(*args):
        return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()

    dirty = git("status", "--porcelain", "src", "evals")
    return git("rev-parse", "--short", "HEAD") + (" (uncommitted changes)" if dirty else "")


def write_results(scores: list[PostingScore], summary: str, details: list[str]) -> None:
    lines = [
        "# Eval results",
        "",
        f"Run {date.today().isoformat()} at commit {git_version()} · parse {llm.parse_model()}"
        f" · match {llm.match_model()} · documents `{retrieve.docs_dir()}`",
        "",
        f"**{summary}**",
        "",
        results_table(scores),
    ]
    if details:
        lines += ["", "## Failures", ""] + [f"- {d}" for d in details]
    (EVALS / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", action="append", default=[],
                        help="Run only postings whose file name contains this text (repeatable)")
    args = parser.parse_args()

    key = load_key()
    names = [n for n in sorted(key) if not args.only or any(o in n for o in args.only)]
    if not names:
        sys.exit("No postings to run.")

    scores = []
    for name in names:
        print(f"Running {name} ...", flush=True)
        scores.append(run_one(name, key[name]))
    score_twins(scores)

    summary = summary_line(scores)
    details = failure_details(scores)
    print("\n" + results_table(scores) + "\n")
    print("\n".join(details + [""]) if details else "", end="")
    print(summary)
    if args.only:
        print("(partial run: evals/results.md not updated)")
    else:
        write_results(scores, summary, details)
        print("Wrote evals/results.md")
    sys.exit(0 if all(s.passed for s in scores) else 1)


if __name__ == "__main__":
    main()
