"""Streamlit-Chat für das second-brain — beantwortet Fragen zu Marcos Portfolio-Projekten."""

import sys

import streamlit as st

from second_brain.answering import answer_question
from second_brain.llm import get_llm
from second_brain.snapshot import DEFAULT_SNAPSHOT_PATH, Snapshot, load_snapshot

st.set_page_config(page_title="second brain — Marco Stangs Portfolio", page_icon="🧠")

st.title("🧠 second brain")
st.markdown(
    "**In 30 Sekunden:** Frag mich alles über Marcos Portfolio-Projekte — "
    "z.B. \"welche Projekte zeigen Cloud-Erfahrung?\" oder \"was macht sql-agent?\". "
    "Ich kenne README, Projektkontext und Status jedes fertigen Projekts."
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

question = st.chat_input("Frag etwas über Marcos Projekte...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            llm = get_llm()
            with st.spinner("Antwort wird generiert..."):
                answer = answer_question(llm, question, snapshot)
        except Exception as e:
            # Nutzern keine internen Provider-/Exception-Details zeigen (können
            # z.B. rohe API-Fehlerkörper enthalten) — stattdessen serverseitig loggen.
            print(f"Fehler bei answer_question: {e}", file=sys.stderr)
            answer = "Antwort konnte gerade nicht generiert werden. Bitte später erneut versuchen."
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
