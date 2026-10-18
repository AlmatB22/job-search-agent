"""One Anthropic client plus a cost-logging wrapper.

Every model call in the project goes through structured(), so every call is
schema-validated and every call lands in the llm_calls table with its tokens,
cost and latency.
"""

import os
import time
from functools import cache

import anthropic

from jsa import tracker

# USD per 1M tokens (input, output), from Anthropic's pricing page, Oct 2026
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),  # prompts up to 100k tokens
    "claude-sonnet-5-5": (2.00, 10.00),
}

# Haiku 5.5 and Sonnet 5.5 think by default, and thinking tokens count against
# max_tokens, so leave generous room rather than truncating the JSON.
MAX_TOKENS = 16_000


def parse_model() -> str:
    return os.environ.get("JSA_PARSE_MODEL", "claude-haiku-5-5")


def match_model() -> str:
    return os.environ.get("JSA_MATCH_MODEL", "claude-sonnet-5-5")


@cache
def _client() -> anthropic.Anthropic:
    # Created on first use, not at import, so tests and `jsa list` need no key.
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY


def structured(model, system, user, schema, *, run_id, step, effort=None):
    """Call `model` and return its reply validated as an instance of `schema`."""
    if model not in PRICES:
        raise ValueError(f"No price for model {model!r}; add it to PRICES in llm.py")
    extra = {"output_config": {"effort": effort}} if effort else {}

    t0 = time.monotonic()
    resp = _client().messages.parse(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
        **extra,
    )
    latency_ms = int((time.monotonic() - t0) * 1000)

    # Log before checking the result: a failed call still cost money.
    u = resp.usage
    p_in, p_out = PRICES[model]
    cost = (u.input_tokens * p_in + u.output_tokens * p_out) / 1_000_000
    tracker.log_call(run_id, step, model, u.input_tokens, u.output_tokens, round(cost, 6), latency_ms)

    if resp.parsed_output is None:
        raise RuntimeError(f"{step}: model returned no valid output (stop_reason={resp.stop_reason})")
    return resp.parsed_output
