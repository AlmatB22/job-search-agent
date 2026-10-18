"""Job search agent: match job postings against your own documents."""

from dotenv import load_dotenv

# Read .env once, for every entry point (CLI, MCP server, evals). Variables that are
# already set win, so `JSA_DOCS_DIR=data/sample_docs uv run jsa ...` and Docker's
# env_file both override the file.
load_dotenv()
