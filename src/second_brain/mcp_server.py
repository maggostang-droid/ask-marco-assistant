"""MCP-Server für das second-brain — exponiert Portfolio-Wissen als MCP-Tools."""

from mcp.server import Server, ServerRequestContext
from mcp import types
from mcp.server.stdio import stdio_server

from second_brain.answering import answer_question
from second_brain.llm import get_llm
from second_brain.snapshot import load_snapshot


def list_projects() -> list[dict]:
    """Listet alle bekannten Portfolio-Projekte mit id, Titel und Repo-Pfad."""
    snapshot = load_snapshot()
    return [{"id": p.id, "title": p.title, "repo_path": p.repo_path} for p in snapshot.projects]


def ask_about_projects(question: str) -> str:
    """Beantwortet eine Frage zu Marcos Portfolio-Projekten."""
    snapshot = load_snapshot()
    llm = get_llm()
    return answer_question(llm, question, snapshot)


# Create the MCP server
mcp = Server("second-brain")


async def handle_list_tools(
    context: ServerRequestContext, params: types.PaginatedRequestParams | None
) -> types.ListToolsResult:
    """List available tools."""
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="list_projects",
                description="Listet alle bekannten Portfolio-Projekte mit id, Titel und Repo-Pfad.",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="ask_about_projects",
                description="Beantwortet eine Frage zu Marcos Portfolio-Projekten.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "Die Frage zu Marcos Projekten"}
                    },
                    "required": ["question"],
                },
            ),
        ]
    )


async def handle_call_tool(
    context: ServerRequestContext, params: types.CallToolRequestParams
) -> types.CallToolResult:
    """Handle tool calls."""
    if params.name == "list_projects":
        result = list_projects()
        return types.CallToolResult(content=[types.TextContent(type="text", text=str(result))])
    elif params.name == "ask_about_projects":
        question = params.arguments.get("question", "")
        result = ask_about_projects(question)
        return types.CallToolResult(content=[types.TextContent(type="text", text=result)])
    else:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Unknown tool: {params.name}")],
            isError=True,
        )


# Register handlers
mcp.add_request_handler("tools/list", types.PaginatedRequestParams, handle_list_tools)
mcp.add_request_handler("tools/call", types.CallToolRequestParams, handle_call_tool)


if __name__ == "__main__":
    stdio_server(mcp)
