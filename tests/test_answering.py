from types import SimpleNamespace

from second_brain.answering import answer_question, build_prompt
from second_brain.snapshot import Project, ProjectDocs, Snapshot


class _FakeLLM:
    def __init__(self, reply: str):
        self.reply = reply
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        return SimpleNamespace(content=self.reply)


def _sample_snapshot() -> Snapshot:
    return Snapshot(
        generated_at="2026-07-29T00:00:00+00:00",
        projects=[
            Project(
                id="cloud-native-pipeline",
                title="cloud-native-pipeline",
                repo_path="cloud-native-pipeline",
                docs=ProjectDocs(
                    readme="# cloud-native-pipeline\n\nAWS-Pipeline.",
                    claude_md=None,
                    handover=None,
                ),
            )
        ],
    )


def test_build_prompt_includes_all_project_titles_and_docs():
    snapshot = _sample_snapshot()

    prompt = build_prompt(snapshot)

    assert "cloud-native-pipeline" in prompt
    assert "AWS-Pipeline" in prompt


def test_answer_question_passes_question_and_returns_llm_reply():
    snapshot = _sample_snapshot()
    fake_llm = _FakeLLM(reply="cloud-native-pipeline zeigt AWS-Erfahrung.")

    result = answer_question(fake_llm, "Welches Projekt zeigt AWS-Erfahrung?", snapshot)

    assert result == "cloud-native-pipeline zeigt AWS-Erfahrung."
    system_message, human_message = fake_llm.last_messages
    assert system_message[0] == "system"
    assert "cloud-native-pipeline" in system_message[1]
    assert human_message == ("human", "Welches Projekt zeigt AWS-Erfahrung?")
