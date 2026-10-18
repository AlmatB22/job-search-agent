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

## Tests

```sh
uv run pytest
```
