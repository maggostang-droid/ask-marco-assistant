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


def _format_project(project: Project) -> str:
    parts = [f"## {project.title} (id: {project.id})"]
    if project.docs.readme:
        parts.append(f"### README\n{project.docs.readme}")
    if project.docs.claude_md:
        parts.append(f"### CLAUDE.md\n{project.docs.claude_md}")
    if project.docs.handover:
        parts.append(f"### HANDOVER.md\n{project.docs.handover}")
    return "\n\n".join(parts)


def build_prompt(snapshot: Snapshot) -> str:
    projects_block = "\n\n---\n\n".join(_format_project(p) for p in snapshot.projects)
    return SYSTEM_PROMPT_TEMPLATE.format(projects_block=projects_block)


def answer_question(llm: BaseChatModel, question: str, snapshot: Snapshot) -> str:
    system_prompt = build_prompt(snapshot)
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
