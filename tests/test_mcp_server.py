import second_brain.mcp_server as mcp_server_module
from second_brain.snapshot import Project, ProjectDocs, Snapshot


def _sample_snapshot() -> Snapshot:
    return Snapshot(
        generated_at="2026-07-29T00:00:00+00:00",
        projects=[
            Project(
                id="sql-agent",
                title="sql-agent",
                repo_path="sql-agent",
                docs=ProjectDocs(readme="# sql-agent", claude_md=None, handover=None),
            )
        ],
    )


def test_list_projects_returns_compact_project_list(monkeypatch):
    monkeypatch.setattr(mcp_server_module, "load_snapshot", lambda: _sample_snapshot())

    result = mcp_server_module.list_projects()

    assert result == [{"id": "sql-agent", "title": "sql-agent", "repo_path": "sql-agent"}]


def test_ask_about_projects_delegates_to_answer_question(monkeypatch):
    monkeypatch.setattr(mcp_server_module, "load_snapshot", lambda: _sample_snapshot())
    monkeypatch.setattr(mcp_server_module, "get_llm", lambda: "fake-llm")
    calls = {}

    def fake_answer_question(llm, question, snapshot, include_handover=True):
        calls["args"] = (llm, question, snapshot)
        calls["include_handover"] = include_handover
        return "Antwort"

    monkeypatch.setattr(mcp_server_module, "answer_question", fake_answer_question)

    result = mcp_server_module.ask_about_projects("Was macht sql-agent?")

    assert result == "Antwort"
    assert calls["args"][0] == "fake-llm"
    assert calls["args"][1] == "Was macht sql-agent?"
    # MCP-Server läuft nur lokal bei Marco — anders als der öffentliche
    # Streamlit-Chat darf er HANDOVER.md-Inhalte weiterhin sehen.
    assert calls["include_handover"] is True
