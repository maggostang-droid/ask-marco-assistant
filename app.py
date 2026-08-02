"""Streamlit-Chat des Ask-Marco Assistant (Portfolio-Demo, MARCO.OS-Stil)."""

import sys

import streamlit as st

from pathlib import Path

# Das Verzeichnis dieser Datei auf den Importpfad legen, damit portfolio_ui
# sowohl beim normalen Start (Streamlit legt es selbst dorthin) als auch im
# Test-Harness (AppTest.from_file laeuft vom Repo-Wurzelverzeichnis) gefunden wird.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from portfolio_ui import (
    example_picker,
    page_header,
    page_setup,
    portfolio_footer,
    under_the_hood,
)

from second_brain.answering import answer_question
from second_brain.llm import get_llm
from second_brain.snapshot import DEFAULT_SNAPSHOT_PATH, Snapshot, load_snapshot

page_setup("Ask-Marco Assistant")

page_header(
    title="Ask-Marco Assistant",
    claim=(
        "Ein Chat, der alle Portfolio-Projekte kennt: er baut seinen Kontext aus der Doku "
        "der Nachbar-Repos, statt jedes README einzeln lesen zu müssen."
    ),
    project_id="second-brain",
    cluster="agentic-ai",
)


@st.cache_resource
def _load_snapshot_cached() -> Snapshot:
    # Streamlit führt das Skript bei jeder Interaktion komplett neu aus.
    # cache_resource verhindert, dass die ~150KB snapshot.json bei jeder
    # Chat-Nachricht erneut gelesen und validiert wird.
    return load_snapshot(DEFAULT_SNAPSHOT_PATH)


try:
    snapshot = _load_snapshot_cached()
except Exception as e:
    st.error(f"Snapshot konnte nicht geladen werden: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

SUGGESTIONS = {
    "Cloud-Erfahrung?": "sucht quer über alle Projekte",
    "Was macht der SQL Copilot?": "Detailfrage zu einem Projekt",
    "Wo sind die Schwächen?": "die unangenehme Frage",
}
SUGGESTION_PROMPTS = {
    "Cloud-Erfahrung?": "Welche Projekte zeigen Cloud-Erfahrung, und woran genau?",
    "Was macht der SQL Copilot?": "Was macht der SQL Copilot, und was ist daran technisch besonders?",
    "Wo sind die Schwächen?": "Welche Schwächen und Limitierungen haben die Projekte laut Doku?",
}

picked = None
if not st.session_state.messages:
    picked = example_picker(
        "Frage anklicken, ganz ohne Tippen:", SUGGESTIONS, key="frage"
    )

question = st.chat_input("Frag etwas über Marcos Projekte...")
if picked and not question:
    question = SUGGESTION_PROMPTS[picked]

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            llm = get_llm()
            with st.spinner("Antwort wird generiert..."):
                # include_handover=False: öffentlicher Chat bekommt keine
                # HANDOVER.md-Inhalte (können Betriebsdetails wie AWS-Account-IDs
                # enthalten), nur der lokale MCP-Server sieht sie (Default True).
                answer = answer_question(llm, question, snapshot, include_handover=False)
        except Exception as e:
            # Nutzern keine internen Provider-/Exception-Details zeigen (können
            # z.B. rohe API-Fehlerkörper enthalten), stattdessen serverseitig loggen.
            print(f"Fehler bei answer_question: {e}", file=sys.stderr)
            answer = "Antwort konnte gerade nicht generiert werden. Bitte später erneut versuchen."
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})


with under_the_hood():
    st.markdown(
        "Es gibt **kein Vektor-RAG**. Die komplette Doku aller Projekte wird als "
        "ein einziger Kontext an das Modell übergeben (Context-Stuffing), weil sie "
        "bei dieser Projektzahl in ein Prompt passt. Das spart Datenbank, "
        "Chunking-Strategie und die typischen Retrieval-Fehlgriffe."
    )
    st.code(
        "\n".join(
            f"{p.id:<28} {len(p.docs.readme or ''):>7} Zeichen README" for p in snapshot.projects
        ),
        language="text",
    )
    st.caption(
        f"{len(snapshot.projects)} Projekte im Snapshot. Der öffentliche Chat bekommt "
        "bewusst keine HANDOVER-Inhalte in den Kontext, nur der lokale MCP-Server."
    )

portfolio_footer(
    repo="ask-marco-assistant",
    project_id="second-brain",
    caveats=[
        "der Snapshot wird manuell gebaut, er aktualisiert sich nicht selbst",
        "kein Vektor-RAG, bei viel mehr Projekten würde der Kontext nicht mehr passen",
        "nur Projekt-Doku, keine Volltext-Code-Suche",
        "Free-Tier-Hosting, der erste Aufruf kann einen Kaltstart haben",
    ],
)
