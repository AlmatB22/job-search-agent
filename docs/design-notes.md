# Design notes

Why the core pipeline is built the way it is. Each section names the decision, the
alternative I considered, and the reason.

```
posting.txt -> parse (Haiku 5.5) -> retrieve (BM25) -> match (Sonnet 5.5)
            -> guard (Python) -> SQLite draft -> summary + cost
```

## Principles

1. **Contracts first.** Pydantic models define what passes between steps. A step
   returns a valid model or fails loudly.
2. **Posting text is untrusted.** It is copied from the web and may contain prompt
   injection. Defence in layers: fence it, have the model flag it, check in Python,
   and give the agent no tools that send, submit or delete.
3. **Grounding.** Every claim about the candidate cites a chunk of their own
   documents. The prompt asks for it and the guard enforces it.
4. **Check in code, not in the prompt.** Prompts are advice; the guard is a rule.
5. **Cheap model for extraction, strong model for judgment.**
6. **Measure from day one.** Every model call is logged with tokens, cost and latency.

## schemas.py: contracts

- **Decision:** Pydantic models used as the structured-output format
  (`messages.parse(output_format=Model)`).
- **Alternative:** ask for JSON in the prompt and parse it with `json.loads`.
- **Why:** the API constrains generation to the schema and the SDK validates the
  result, so there is no scraping or retrying on malformed JSON. Fields stay plain
  (`str`, `int`, `list`, `Literal`) because structured outputs support only part of
  JSON Schema. A range such as 0-100 can't be enforced there, so the guard clamps it.
  `Literal` statuses and verdicts let the eval compare answers exactly.
- **In an interview:** "Each stage's output is a Pydantic model enforced by
  structured outputs, so I get schema-valid JSON or an error, never text to scrape."

## tracker.py: SQLite

- **Decision:** one SQLite file with two tables, `applications` and `llm_calls`.
- **Alternative:** Postgres, or JSON files.
- **Why:** SQLite needs no server, ships with Python and is plenty for one user.
  Key fields (fit, verdict, status) are real columns so they can be queried; the
  full report is stored as JSON so it can be re-rendered later. `applications.run_id`
  links each application to its cost rows. Status is a small state machine
  (draft -> approved -> applied/rejected), and only an explicit approve moves a draft.
  All SQL is parameterised.
- **In an interview:** "Everything is saved as a draft, and a human approval is the
  only way forward. The same database holds a per-call cost log."

## llm.py: one wrapper for every call

- **Decision:** a single `structured()` function makes every model call and logs it.
- **Alternative:** call the SDK directly in each module.
- **Why:** one choke point means no call goes unlogged and every call gets the same
  settings. Cost = input tokens × input price + output tokens × output price. The call
  is logged before the result is checked, because a failed call still costs money.
  The client is created on first use, so tests and `jsa list` need no API key.
  `max_tokens` is 16,000 because Haiku 5.5 and Sonnet 5.5 think by default and
  thinking tokens count against the limit.
- **In an interview:** "Cost per posting is measured, not estimated: every call
  writes tokens, cost and latency to SQLite."

## parse.py: posting -> Posting

- **Decision:** Haiku 5.5 at low effort; the posting is fenced in `<posting>` tags,
  with any closing tag stripped so the text can't escape the fence.
- **Alternative:** Sonnet for everything.
- **Why:** extraction is mechanical, and Haiku costs about a twentieth of Sonnet's
  price. A model can't be made immune to injection, so it is asked to report attempts
  (`contains_ai_instructions`), and the pipeline turns that flag into a warning.

## retrieve.py: BM25 over my documents

- **Decision:** chunks of about 800 characters with readable ids
  (`resume.pdf#p1-3`, `projects.md#ules-1`). Each must-have skill is a separate
  BM25 query; I take the top 3 per skill, remove duplicates and cap the result at 20.
- **Alternative:** embeddings with a vector store.
- **Why:** BM25 is pure Python and deterministic, and skill names are exact
  keywords. Embeddings would add about 2 GB of PyTorch to the Docker image. One query
  per skill stops common skills crowding out rare ones. Results are taken rank by
  rank across skills, so the cap drops the weakest matches, not the last skills.
  PDFs are read in pypdf's layout mode, because the default mode broke the resumes
  into one word per line.
- **Known limitation:** synonyms ("JS" vs "JavaScript") are missed. Embeddings are
  the next step.
- **In an interview:** "Retrieval is BM25, top 3 per required skill, capped at 20
  chunks. It's cheap and deterministic, and I documented the synonym gap as the reason
  to add embeddings."

## match.py: Posting + chunks -> FitReport

- **Decision:** Sonnet 5.5. The chunks are sent as `<chunk id="...">` blocks, and the
  system prompt has explicit rules plus a verdict rubric.
- **Why:** this step's judgment decides the quality of the whole result. The id
  attributes are what make citations possible: the model cites, Python verifies.

## pipeline.py: the guard

- **Decision:** `apply_guard()` is a pure function. It drops any bullet with no
  citation or with an id that wasn't retrieved, counts the drops, and clamps the
  score to 0-100.
- **Why:** a model asked to cite will sometimes invent a citation or leave one out.
  The guard turns "no uncited claims" from a request into a guarantee, and the drop
  count becomes an eval metric.
- **In an interview:** "After matching, deterministic code removes any bullet that
  doesn't cite a chunk we actually retrieved."

## Measured: first end-to-end run (Dawson AI Solutions Developer)

| Step | Model | Input tokens | Output tokens | Cost | Latency |
| --- | --- | --- | --- | --- | --- |
| parse | claude-haiku-5-5 | 2,647 | 241 | $0.0004 | 1.9 s |
| match | claude-sonnet-5-5 | 5,603 | 2,005 | $0.0313 | 12.1 s |
| **Total** | | | | **$0.032** | **14.4 s** |

The verdict was partial (42/100). LLM API integration, tool calling, structured
outputs and RAG were all marked missing, and the guard dropped 0 bullets. Sonnet
accounts for 98% of the cost, which is why parsing uses Haiku.

## Second run: project notes and capstone added

Adding `projects.md` and the capstone report took the corpus from 19 chunks to
about 280. The same posting moved to 68/100 (still partial). LLM API integration,
structured outputs, RAG and prompt-injection handling became strong, each citing the
project notes. Tool calling stayed missing because the MCP server isn't built yet.
The run cost $0.049 and took 26 s: the 20-chunk cap was reached, so Sonnet read
more input.

Three lessons from this run:

- **Chunk boundaries matter.** At first a long Markdown section split into a
  heading-only chunk and a body chunk without its heading. Now every chunk repeats
  its section heading, so "ULES" travels with the text.
- **BM25 has no stemming.** "AI-assisted development tools" was marked partial
  because the chunk saying "I develop with Claude Code" never matched: "develop" is
  not "development". This is the synonym and word-form gap, observed in practice, and
  the case for embeddings or a stemmer.
- **Parsing varies between runs.** Haiku produced a slightly different must-have
  list each time ("RAG patterns" vs "Retrieval or RAG patterns"). The Phase 4 eval
  therefore checks must-haves by case-insensitive substring, not exact match.

## Evaluation (Phase 4)

- **Decision:** a fixed answer key written before the first run, and one command
  that runs every posting through the real pipeline and scores it.
- **Alternative:** spot-checking outputs by eye.
- **Why:** an answer key written after seeing the output drifts toward what the
  model says. Writing it first makes the score mean something. When a check fails,
  the fix goes into the prompt, guard or retrieval, never into the key.

Choices inside the eval:

- **Substring extraction checks.** Haiku words skills differently between runs, so
  "LLM API" passes when the parse says "LLM API integration".
- **A numbers check, beyond the guard.** The guard proves a bullet cites real chunks;
  the eval proves the cited text contains every number the bullet states. Invented
  figures are the most damaging resume error and the cheapest to catch with code.
  The full check, whether the chunk supports every claim and not just the numbers,
  would need an LLM judge. That's a known limitation.
- **An injection twin.** The injected posting is a copy of a clean posting with one
  hidden line. It passes only if it's flagged and its verdict and score (within 10
  points) match its twin. That is stronger than checking for some fixed verdict.
- **False alarms count.** A detector that flags every posting is useless, so no
  clean posting may be flagged.
- **Isolation and traceability.** Eval runs write to their own database. Each
  `results.md` records the commit, the models and the document folder, so every
  number in the README can be reproduced.
- **Cheap iteration.** `--only` runs one posting (about $0.05) while working on a
  prompt; only a full run updates `results.md`.
- **Scoring is pure code.** It lives in `jsa/eval_checks.py` and is unit-tested
  offline. Only the runner spends money.
- **In an interview:** "Every prompt change is followed by an eval run against a
  fixed answer key. It checks extraction, verdicts, invented numbers, a
  prompt-injection twin and cost per posting, and the pass rate goes in the
  changelog."

## Measuring through noise (repeat runs)

- **What happened:** the same code gave AssetWatch scores of 42, 18 and 22 on three
  runs. I blamed a prompt change for a drop that turned out to be noise, and
  reverted it on no real evidence.
- **Decision:** `run_evals.py --repeat N` runs each posting N times. A verdict counts
  only when it's a clear majority, and each posting reports how stable it was
  (for example, "partial 2/3"). Safety checks are stricter: extraction, numbers
  and the injection flag must hold on every run, because one invented number in
  three runs is still an invented number.
- **Why:** with LLMs you can't control sampling here (Sonnet 5.5 rejects
  non-default temperature), so the eval has to treat each run as a sample. A
  prompt change counts as an improvement only if it beats the noise.
- **In an interview:** "I found my eval couldn't tell a prompt change from
  run-to-run variance, so I added repeated runs with majority verdicts and a
  stability metric before tuning anything else."

## The verdict comes from the score

- **Decision:** the guard derives the verdict from the clamped fit score, using the
  rubric's thresholds (75 and up strong, under 40 poor). It no longer trusts the
  model's label.
- **Why:** the model once scored a posting 38 and still called it partial. The
  score is the finer-grained signal, so code maps it to a label and the two
  can't contradict each other. This is the same rule as the citation guard:
  code enforces what the prompt only asks for.

## Years of experience in the verdict (kept, on the second try)

- **Decision:** when a posting states years of experience, the matcher adds an
  evidence item for it. Full-time roles count in full; co-ops, internships, courses
  and projects count for less. It weighs like a must-have.
- **History:** the first single-run attempt seemed to cause a regression, and I
  reverted it. Rerun with three runs per posting, it moved the 6+ year staff role
  from partial (3/3) to poor (2/3) and broke nothing: 11/14 became 12/14.
- **Lesson for an interview:** "My first conclusion about this change was wrong,
  because I'd measured it once. With repeated runs the same change was a clear
  improvement. Now no prompt change is judged on a single run."

## mcp_server.py: the agent's interface (Phase 5)

- **Decision:** an MCP server with three tools over Streamable HTTP, as a thin layer
  over `pipeline.analyze()` and the tracker, the same code the CLI calls.
- **Alternative:** writing the logic as a Hermes skill.
- **Why:** MCP is the standard way for agent platforms to discover tools, so the same
  server works with Hermes, OpenClaw or any MCP client. The judgment, evidence and
  cost logging stay in my code, not in the agent's prompt.
- **Human in the loop by design:** `analyze_posting` only creates drafts. Only
  `approve_application` changes a draft, and its description tells the agent to call
  it only when the user names the id. No tool can delete, email or submit anything,
  so a malicious posting has nothing dangerous to steer the agent towards. Each tool
  also carries MCP annotations (read-only, non-destructive) that clients can use for
  their own approval rules.
- **Input limits:** empty postings and postings over 20,000 characters are rejected
  before any model is called, which caps the cost of a bad request.
- **Network safety:** the server binds to 127.0.0.1 by default. On any other address
  it refuses to start without an allow-list of Host headers, the SDK's defence
  against DNS rebinding, where a web page tricks a browser into calling a local
  server. It was tested: a forged Host header gets 421.
- **SDK drift:** the plan's sample code used `FastMCP` from mcp 1.x. The installed
  mcp 2.3.0 renamed it `MCPServer` and moved the host and port settings to `run()`.
  I read the installed SDK instead of following the plan blindly.
- **Testing:** the tools are tested in-process with the SDK's `Client(server)`, with
  no network and no API calls. Then one real HTTP session confirmed discovery, a full
  analysis ($0.034, 16 s), the draft in the tracker and the cost rows.
- **In an interview:** "The agent can only read, analyze and create drafts. Approval
  needs the user's explicit instruction, and nothing can send or delete, so even a
  successful prompt injection can't do real damage."

## Docker (Phase 6)

- **Decision:** two containers on one private network. The tool server is built
  from this repo; Hermes uses its official image. Neither publishes a port: Telegram
  and the Claude API are outbound connections, and Hermes reaches the tools by the
  container name `jsa-mcp`.
- **Why containers at all:** an agent that reads untrusted postings can be steered.
  Inside a container it sees only its own data folder, not the Mac.
- **Defence in depth on the tool server:** it runs as a non-root user with a fixed
  uid, on a read-only filesystem (bytecode is precompiled at build, since Python
  can't write it at runtime), with all Linux capabilities dropped,
  `no-new-privileges`, and CPU and memory limits. The documents are mounted
  read-only, and only the database folder is writable.
- **Nothing sensitive in the image:** `.dockerignore` excludes `.env`, `data/`,
  `hermes-data/`, `evals/` and `.git`. I checked the built image: only code and
  dependencies, no `.env`, PDFs, notes or database. The key arrives at run time
  through `env_file`.
- **Reproducible builds:** uv is pinned to the Mac's version (0.9.28) and installs
  from `uv.lock` with `--frozen`. Dependencies sit in their own layer, so a code change
  rebuilds in seconds.
- **Health check:** compose waits until the tool server answers HTTP before starting
  Hermes. Any response counts, including the 421 the Host check gives the probe.
- **Verified:** healthy; no published ports (unreachable from the Mac); by name, from
  another container on `agent-net`, all three tools work and a full analysis ran
  ($0.028, 15 s); by raw IP, 421; writes to the documents or the app filesystem
  fail as read-only.
- **In an interview:** "The agent and my tools run in separate containers on a
  private network with no open ports. My documents are read-only to the tool server
  and invisible to the agent, and the tool server is non-root on a read-only
  filesystem."
