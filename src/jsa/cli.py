"""Command line entry point: `jsa analyze file.txt`, `jsa list`."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="jsa", description="Job search agent")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Analyze a job posting file")
    analyze.add_argument("file", help="Path to a posting .txt file")
    sub.add_parser("list", help="List tracked applications")
    args = parser.parse_args()
    raise SystemExit(f"`jsa {args.command}` is not implemented yet")
