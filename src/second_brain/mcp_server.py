"""MCP-Server für das second-brain — exponiert Portfolio-Wissen als MCP-Tools."""

from mcp.server.mcpserver import MCPServer

from second_brain.answering import answer_question
from second_brain.llm import get_llm
from second_brain.snapshot import load_snapshot

mcp = MCPServer("second-brain")


@mcp.tool()
def list_projects() -> list[dict]:
    """Listet alle bekannten Portfolio-Projekte mit id, Titel und Repo-Pfad."""
    snapshot = load_snapshot()
    return [{"id": p.id, "title": p.title, "repo_path": p.repo_path} for p in snapshot.projects]


@mcp.tool()
def ask_about_projects(question: str) -> str:
    """Beantwortet eine Frage zu Marcos Portfolio-Projekten."""
    snapshot = load_snapshot()
    llm = get_llm()
    # include_handover bleibt beim Default True: der MCP-Server läuft nur
    # lokal bei Marco, anders als der öffentliche Streamlit-Chat (app.py).
    return answer_question(llm, question, snapshot, include_handover=True)


if __name__ == "__main__":
    mcp.run()
