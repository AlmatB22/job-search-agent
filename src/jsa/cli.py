"""Command line entry point: `jsa analyze file.txt`, `jsa approve 3`, `jsa list`."""

import argparse
from pathlib import Path

from jsa import tracker


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="jsa", description="Job search agent")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Analyze a job posting file and save a draft")
    analyze.add_argument("file", type=Path, help="Path to a posting text file")

    parse = sub.add_parser("parse", help="Only extract the posting's requirements (debugging)")
    parse.add_argument("file", type=Path, help="Path to a posting text file")

    approve = sub.add_parser("approve", help="Approve a draft application")
    approve.add_argument("id", type=int, help="Application id")
    approve.add_argument("--notes", default="", help="Notes to store with the approval")

    list_ = sub.add_parser("list", help="List recent applications")
    list_.add_argument("--status", default="all", choices=("all", *tracker.STATUSES))

    args = parser.parse_args(argv)

    if args.command == "analyze":
        from jsa import pipeline  # deferred: only these commands need the model client

        print(pipeline.analyze(args.file.read_text(encoding="utf-8")).to_text())
    elif args.command == "parse":
        from jsa.parse import parse_posting

        posting = parse_posting(args.file.read_text(encoding="utf-8"), run_id=tracker.new_run_id())
        print(posting.model_dump_json(indent=2))
    elif args.command == "approve":
        print(tracker.approve(args.id, args.notes))
    else:
        print(tracker.list_text(args.status))
