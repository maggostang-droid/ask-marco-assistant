"""Baut den Prompt aus dem Snapshot (Context-Stuffing) und lässt das LLM antworten."""

from langchain_core.language_models.chat_models import BaseChatModel

from second_brain.snapshot import Project, Snapshot

SYSTEM_PROMPT_TEMPLATE = """Du bist das "second brain" von Marco Stangs Portfolio-Website. \
Du kennst die folgenden Portfolio-Projekte und beantwortest Fragen dazu ausschließlich \
anhand der untenstehenden Informationen. Wenn eine Frage nicht anhand der Projekte \
beantwortbar ist, sag das ehrlich, statt zu spekulieren. Nenne bei jeder Antwort, auf \
welche Projekt-ID(s) sie sich bezieht.

{projects_block}
"""


def _format_project(project: Project, include_handover: bool) -> str:
    parts = [f"## {project.title} (id: {project.id})"]
    if project.docs.readme:
        parts.append(f"### README\n{project.docs.readme}")
    if project.docs.claude_md:
        parts.append(f"### CLAUDE.md\n{project.docs.claude_md}")
    if include_handover and project.docs.handover:
        parts.append(f"### HANDOVER.md\n{project.docs.handover}")
    return "\n\n".join(parts)


def build_prompt(snapshot: Snapshot, include_handover: bool = True) -> str:
    # include_handover=False für den öffentlichen Streamlit-Chat: HANDOVER.md
    # enthält bei manchen Projekten Betriebsdetails (z.B. echte AWS-Account-IDs,
    # IAM-Ressourcennamen bei cloud-native-pipeline), die zwar im jeweiligen
    # Repo selbst schon öffentlich sind, aber über einen interaktiven Chat
    # deutlich leichter auffindbar wären. Der lokale MCP-Server (nur Marco)
    # nutzt weiterhin den Default True.
    projects_block = "\n\n---\n\n".join(
        _format_project(p, include_handover) for p in snapshot.projects
    )
    return SYSTEM_PROMPT_TEMPLATE.format(projects_block=projects_block)


def answer_question(
    llm: BaseChatModel, question: str, snapshot: Snapshot, include_handover: bool = True
) -> str:
    system_prompt = build_prompt(snapshot, include_handover=include_handover)
    response = llm.invoke(
        [
            ("system", system_prompt),
            ("human", question),
        ]
    )
    # .text ist in der installierten langchain-core-Version (1.5.x) ein
    # TextAccessor (str-Subklasse), der zuverlässig den reinen Antworttext
    # liefert — auch wenn .content (z.B. bei manchen Anthropic-Antwortformen)
    # eine Liste von Content-Blöcken statt eines plain str sein kann.
    return response.text
