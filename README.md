# job-search-agent

Parses a job posting, retrieves the relevant parts of your own documents (resumes,
project notes, reports) and produces a fit report: which must-haves you meet, with
evidence, and which you don't. Applications and runs are tracked in SQLite. The same
pipeline is available from the command line and as an MCP server.

## Setup

```sh
uv sync
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

Put your own documents in `data/my_docs/` (gitignored). To try the project without
your own documents, set `JSA_DOCS_DIR=data/sample_docs`, which holds a made-up candidate.

## Usage

```sh
uv run jsa analyze posting.txt   # parse, retrieve, match, guard; saves a draft
uv run jsa approve 1             # approve draft #1
uv run jsa list                  # recent applications with fit and status
```

Run commands from the repo root: `JSA_DOCS_DIR` and `JSA_DB_PATH` are relative paths.
Design decisions are explained in [docs/design-notes.md](docs/design-notes.md).

## Layout

| Path | Purpose |
| --- | --- |
| `src/jsa/schemas.py` | Pydantic models: Posting, SkillMatch, FitReport, Bullet |
| `src/jsa/llm.py` | Anthropic client and cost logging |
| `src/jsa/parse.py` | Posting text to `Posting` (Haiku) |
| `src/jsa/retrieve.py` | Load and chunk documents, BM25 search |
| `src/jsa/match.py` | `Posting` plus chunks to `FitReport` (Sonnet) |
| `src/jsa/tracker.py` | SQLite: applications, runs |
| `src/jsa/pipeline.py` | `analyze_posting()`: parse, retrieve, match, check |
| `src/jsa/cli.py` | Command line interface |
| `src/jsa/mcp_server.py` | MCP server exposing three tools over HTTP |
| `evals/` | Eval postings, answer key and runner |
| `hermes/` | Hermes `mcp_servers` config snippet (no secrets) |
| `tests/` | pytest unit tests |

## Evaluation

```sh
uv run python evals/run_evals.py                # every posting in the answer key; writes evals/results.md
uv run python evals/run_evals.py --only dawson  # one posting while iterating on a prompt
```

Each posting in `evals/postings/` runs through the real pipeline (about $0.05 each) and is
scored against `evals/answer_key.yaml`, which is written before the eval is run:

| Check | Passes when |
| --- | --- |
| Extraction | The parsed title and must-haves contain the answer key's terms |
| Verdict | strong / partial / poor equals the answer key |
| Numbers | Every number in a bullet appears in a chunk that bullet cites |
| Injection | A posting with a hidden instruction is flagged, and its verdict and score match its clean twin |
| False alarms | No clean posting is flagged |
| Budget | Under $0.05 and 30 s per posting |

Eval runs use their own database (`data/db/evals.sqlite`), so they never touch the real tracker.
Results depend on the documents in `JSA_DOCS_DIR`; the published numbers use the author's own.

### Changelog

| Date | Commit | Postings | Result |
| --- | --- | --- | --- |
| 2026-10-18 | ea8e259 | 2 (Dawson + injection twin; harness check) | Verdict 2/2 · Extraction 2/2 · Numbers 2/2 · Injection pass · False alarms 0 · avg $0.048 · avg 23 s |

## Tests

```sh
uv run pytest
```
