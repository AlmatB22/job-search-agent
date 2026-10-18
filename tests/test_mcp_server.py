import anyio
import pytest
from mcp import Client

from jsa import mcp_server, tracker
from jsa.schemas import FitReport, Posting

POSTING = Posting(
    title="Data Analyst", company="Acme", location=None, work_mode="remote",
    must_have_skills=["SQL"], nice_to_have_skills=[], years_experience=None,
    salary=None, contains_ai_instructions=False,
)
REPORT = FitReport(fit_score=70, verdict="partial", evidence=[], bullets=[], gaps=[])


def call(tool: str, args: dict | None = None):
    """Call a tool on the server in-process, the way an MCP client would."""
    async def go():
        async with Client(mcp_server.mcp) as client:
            return await client.call_tool(tool, args or {})
    result = anyio.run(go)
    return result, "".join(c.text for c in result.content if c.type == "text")


def test_exposes_exactly_three_tools_with_safety_hints():
    async def go():
        async with Client(mcp_server.mcp) as client:
            return (await client.list_tools()).tools
    tools = {t.name: t for t in anyio.run(go)}
    assert set(tools) == {"analyze_posting", "approve_application", "list_applications"}
    assert tools["list_applications"].annotations.read_only_hint is True
    # destructive_hint only applies to tools that write; none of ours may destroy anything.
    writers = [t for t in tools.values() if not t.annotations.read_only_hint]
    assert {t.name for t in writers} == {"analyze_posting", "approve_application"}
    assert all(t.annotations.destructive_hint is False for t in writers)


def test_list_and_approve_round_trip():
    app_id = tracker.save_draft("run1", POSTING, REPORT, [], 0)
    assert "draft" in call("list_applications")[1]
    assert call("approve_application", {"application_id": app_id})[1].startswith("Approved")
    assert "Acme" in call("list_applications", {"status": "approved"})[1]


def test_analyze_rejects_empty_and_oversized_postings_without_calling_the_model(monkeypatch):
    def boom(_):
        raise AssertionError("pipeline should not run")
    monkeypatch.setattr(mcp_server.pipeline, "analyze", boom)
    assert "empty" in call("analyze_posting", {"posting_text": "   "})[1]
    assert "too long" in call("analyze_posting", {"posting_text": "x" * 20_001})[1]


def test_refuses_public_bind_without_allowed_hosts():
    assert mcp_server.transport_security("127.0.0.1", "") is None
    settings = mcp_server.transport_security("0.0.0.0", "jsa-mcp:8000")
    assert settings.allowed_hosts == ["jsa-mcp:8000"]
    with pytest.raises(SystemExit):
        mcp_server.transport_security("0.0.0.0", "")
