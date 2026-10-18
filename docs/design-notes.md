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
