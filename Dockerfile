# Image for the jsa MCP server (src/jsa/mcp_server.py).
# No secrets and no documents are baked in: the key arrives via env_file at run
# time, and the documents are mounted read-only (see docker-compose.yml).
FROM python:3.12-slim

# Same uv version as the Mac (`uv --version`), so the lockfile resolves identically.
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /usr/local/bin/uv

# Use the image's Python rather than downloading one; copy files instead of
# hard-linking; precompile bytecode, because the container filesystem is read-only.
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Dependencies first, in their own layer, so code changes don't reinstall them.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

# Run as an unprivileged user with a fixed uid.
RUN useradd --create-home --uid 10001 app
USER app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["python", "-m", "jsa.mcp_server"]
