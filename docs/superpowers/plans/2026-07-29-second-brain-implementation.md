# second-brain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein second-brain, das alle fertigen Portfolio-Projekte unter `02_Portfolio/` kennt und Fragen dazu beantwortet — über einen öffentlichen Streamlit-Chat (Recruiter-facing) und einen MCP-Server (für Marco in Claude Code/Desktop), gespeist aus einem gemeinsamen, lokal gebauten Snapshot.

**Architektur:** Python-Package `src/second_brain/` (Snapshot-Schema, Snapshot-Builder, provider-agnostische LLM-Anbindung, Context-Stuffing-Antwortlogik) + zwei dünne Frontends (`app.py` Streamlit-Chat, `mcp_server.py` MCP-Server via `FastMCP`). Gleiches Grundmuster wie `sql-agent`/`ai-act-validation-toolkit`.

**Tech Stack:** Python ≥3.10, Streamlit, LangChain (`init_chat_model`, provider-agnostisch via `LLM_PROVIDER`/`LLM_MODEL`), Pydantic v2, `mcp` (offizielles Python-SDK, `FastMCP`), pytest, python-dotenv.

## Global Constraints

- Alle Doku/Kommentare/UI-Texte auf Deutsch (Deutsch + Lehrstil, siehe Design-Spec Abschnitt "Lernstil").
- `pytest` läuft komplett ohne LLM/Netzwerk-Zugriff (Design-Spec, Abschnitt "Tests").
- Package-Layout `src/second_brain/`, installierbar via `pip install -e ".[dev]"` (Muster aus `sql-agent`/`ai-act-validation-toolkit`).
- Branch heißt `master`, nicht `main`.
- Kein hart kodiertes LLM-Modell im Code — Provider/Modell ausschließlich über `.env` (`LLM_PROVIDER`/`LLM_MODEL`), analog `ai-act-validation-toolkit/src/ai_act_toolkit/llm.py`.
- Snapshot enthält pro Projekt nur `README.md` + `CLAUDE.md` + `HANDOVER.md` (falls vorhanden) — **keine** `docs/superpowers/specs/`/`plans/`-Dateien (Design-Spec, Abschnitt "Snapshot statt Live-Zugriff").
- Kein echtes Vektor-RAG — Context-Stuffing: der komplette Snapshot geht als System-Prompt mit ins LLM-Prompt (Design-Spec, Abschnitt "Antwortmechanismus").
- `app.py` muss iframe-einbettbar sein (keine `X-Frame-Options`, die das blockieren) — Voraussetzung für die spätere marco-os-Integration (Design-Spec, Abschnitt "Integration in marco-os").
- Kein automatischer Snapshot-Rebuild/CI-Trigger — Snapshot wird manuell per Skript gebaut und eingecheckt.

---

### Task 1: Projekt-Grundgerüst

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/second_brain/__init__.py`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Produces: installierbares Package `second_brain` (Import-Pfad für alle folgenden Tasks), Test-Runner-Setup (`pytest tests/`).

- [ ] **Step 1: `pyproject.toml` anlegen**

```toml
[project]
name = "second-brain"
version = "0.1.0"
description = "Second brain, das alle Portfolio-Projekte von Marco Stang kennt und Fragen dazu beantwortet — als Chat und als MCP-Server"
requires-python = ">=3.10"
dependencies = [
    "langchain>=0.3",
    "langchain-anthropic>=0.3",
    "langchain-openai>=0.2",
    "python-dotenv>=1.0",
    "streamlit>=1.38",
    "pydantic>=2.0",
    "mcp>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["src*"]

[tool.setuptools.package-dir]
"" = "src"
```

- [ ] **Step 2: `.gitignore` anlegen**

```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
*.egg-info/
```

- [ ] **Step 3: `.env.example` anlegen**

```
# Welcher LLM-Provider genutzt wird — steuert, welches LangChain-
# Integrationspaket init_chat_model() im Hintergrund verwendet.
LLM_PROVIDER=anthropic
# LLM_PROVIDER=openai

# Modellbezeichner des jeweiligen Anbieters. Bewusst kein Default im Code —
# aktuelle Modell-IDs bitte in der Doku des Anbieters nachschauen.
LLM_MODEL=claude-sonnet-4-5-20250929
# LLM_MODEL=gpt-4o-mini

# Nur den Key des gewählten Providers eintragen.
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

- [ ] **Step 4: `src/second_brain/__init__.py` anlegen (leer)**

- [ ] **Step 5: `tests/test_smoke.py` schreiben**

```python
import second_brain


def test_package_importable():
    assert second_brain is not None
```

- [ ] **Step 6: Package installieren und Test laufen lassen**

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest tests/ -v
```

Erwartet: `test_package_importable` PASSED.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore .env.example src/second_brain/__init__.py tests/test_smoke.py
git commit -m "chore: Projekt-Grundgerüst"
```

---

### Task 2: Snapshot-Schema (`snapshot.py`)

**Files:**
- Create: `src/second_brain/snapshot.py`
- Test: `tests/test_snapshot.py`

**Interfaces:**
- Consumes: nichts.
- Produces: `ProjectDocs`, `Project`, `Snapshot` (Pydantic-Modelle), `DEFAULT_SNAPSHOT_PATH: Path`, `load_snapshot(path: Path = DEFAULT_SNAPSHOT_PATH) -> Snapshot` — genutzt von Task 3 (`snapshot_builder.py`), Task 6 (`answering.py`), Task 7 (`app.py`), Task 8 (`mcp_server.py`).

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_snapshot.py
import json

import pytest
from pydantic import ValidationError

from second_brain.snapshot import load_snapshot


def _valid_snapshot_dict() -> dict:
    return {
        "generated_at": "2026-07-29T00:00:00+00:00",
        "projects": [
            {
                "id": "sql-agent",
                "title": "sql-agent",
                "repo_path": "sql-agent",
                "docs": {"readme": "# sql-agent", "claude_md": None, "handover": None},
            }
        ],
    }


def test_load_snapshot_parses_valid_file(tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps(_valid_snapshot_dict()), encoding="utf-8")

    snapshot = load_snapshot(snapshot_path)

    assert snapshot.projects[0].id == "sql-agent"
    assert snapshot.projects[0].docs.readme == "# sql-agent"
    assert snapshot.projects[0].docs.handover is None


def test_load_snapshot_raises_on_missing_file(tmp_path):
    missing_path = tmp_path / "does-not-exist.json"

    with pytest.raises(FileNotFoundError):
        load_snapshot(missing_path)


def test_load_snapshot_raises_on_invalid_schema(tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps({"generated_at": "x"}), encoding="utf-8")  # "projects" fehlt

    with pytest.raises(ValidationError):
        load_snapshot(snapshot_path)
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag verifizieren**

Run: `.venv/Scripts/python.exe -m pytest tests/test_snapshot.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'second_brain.snapshot'`.

- [ ] **Step 3: `src/second_brain/snapshot.py` implementieren**

```python
"""Pydantic-Schema für den Portfolio-Snapshot + Lade-/Validierungslogik."""

import json
from pathlib import Path

from pydantic import BaseModel

DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parents[2] / "data" / "snapshot.json"


class ProjectDocs(BaseModel):
    readme: str | None = None
    claude_md: str | None = None
    handover: str | None = None


class Project(BaseModel):
    id: str
    title: str
    repo_path: str
    docs: ProjectDocs


class Snapshot(BaseModel):
    generated_at: str
    projects: list[Project]


def load_snapshot(path: Path = DEFAULT_SNAPSHOT_PATH) -> Snapshot:
    if not path.exists():
        raise FileNotFoundError(
            f"Snapshot-Datei nicht gefunden: {path}. "
            "Erst `python scripts/build_snapshot.py` ausführen."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return Snapshot.model_validate(data)
```

- [ ] **Step 4: Tests laufen lassen, Erfolg verifizieren**

Run: `.venv/Scripts/python.exe -m pytest tests/test_snapshot.py -v`
Erwartet: alle 3 Tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/second_brain/snapshot.py tests/test_snapshot.py
git commit -m "feat: Snapshot-Schema + load_snapshot"
```

---

### Task 3: Snapshot-Builder (`snapshot_builder.py` + `scripts/build_snapshot.py`)

**Files:**
- Create: `src/second_brain/snapshot_builder.py`
- Create: `scripts/build_snapshot.py`
- Test: `tests/test_snapshot_builder.py`

**Interfaces:**
- Consumes: `DEFAULT_SNAPSHOT_PATH`, `Project`, `Snapshot` aus Task 2 (`second_brain.snapshot`).
- Produces: `discover_projects(portfolio_root: Path) -> list[Path]`, `extract_project(project_dir: Path) -> dict`, `build_snapshot(portfolio_root: Path) -> Snapshot`, `main() -> None` — `main()` wird von `scripts/build_snapshot.py` aufgerufen (Task 4), sonst kein weiterer Konsument.

Die eigentliche Logik lebt testbar im Package (`src/second_brain/snapshot_builder.py`); `scripts/build_snapshot.py` ist nur ein dünner CLI-Einstiegspunkt, damit `python scripts/build_snapshot.py` wie in der Design-Spec beschrieben funktioniert, ohne Test-Import-Pfadprobleme mit einem nicht-installierten `scripts/`-Verzeichnis.

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_snapshot_builder.py
from second_brain.snapshot_builder import build_snapshot, discover_projects, extract_project


def test_discover_projects_finds_only_dirs_with_claude_md(tmp_path):
    (tmp_path / "project-a").mkdir()
    (tmp_path / "project-a" / "CLAUDE.md").write_text("# A", encoding="utf-8")
    (tmp_path / "not-a-project").mkdir()  # keine CLAUDE.md
    (tmp_path / "second-brain").mkdir()
    (tmp_path / "second-brain" / "CLAUDE.md").write_text("# second-brain", encoding="utf-8")

    result = discover_projects(tmp_path)

    assert [d.name for d in result] == ["project-a"]


def test_extract_project_reads_available_docs(tmp_path):
    project_dir = tmp_path / "project-a"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("# Project A\n\nBeschreibung.", encoding="utf-8")
    (project_dir / "CLAUDE.md").write_text("# Kontext", encoding="utf-8")
    # kein HANDOVER.md

    result = extract_project(project_dir)

    assert result["id"] == "project-a"
    assert result["title"] == "Project A"
    assert result["docs"]["readme"].startswith("# Project A")
    assert result["docs"]["claude_md"] == "# Kontext"
    assert result["docs"]["handover"] is None


def test_extract_project_falls_back_to_dirname_without_readme(tmp_path):
    project_dir = tmp_path / "project-b"
    project_dir.mkdir()
    (project_dir / "CLAUDE.md").write_text("# Kontext", encoding="utf-8")

    result = extract_project(project_dir)

    assert result["title"] == "project-b"


def test_build_snapshot_returns_snapshot_with_all_discovered_projects(tmp_path):
    project_dir = tmp_path / "project-a"
    project_dir.mkdir()
    (project_dir / "CLAUDE.md").write_text("# Kontext", encoding="utf-8")
    (project_dir / "README.md").write_text("# Project A", encoding="utf-8")

    snapshot = build_snapshot(tmp_path)

    assert len(snapshot.projects) == 1
    assert snapshot.projects[0].id == "project-a"
    assert snapshot.generated_at  # nicht leer
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag verifizieren**

Run: `.venv/Scripts/python.exe -m pytest tests/test_snapshot_builder.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'second_brain.snapshot_builder'`.

- [ ] **Step 3: `src/second_brain/snapshot_builder.py` implementieren**

```python
"""Baut den Portfolio-Snapshot aus README/CLAUDE.md/HANDOVER der Sibling-Repos unter 02_Portfolio."""

import re
from datetime import datetime, timezone
from pathlib import Path

from second_brain.snapshot import DEFAULT_SNAPSHOT_PATH, Project, Snapshot

PORTFOLIO_ROOT = DEFAULT_SNAPSHOT_PATH.parents[2]


def discover_projects(portfolio_root: Path) -> list[Path]:
    """Findet alle Sibling-Verzeichnisse mit einer CLAUDE.md, außer second-brain selbst."""
    return sorted(
        d
        for d in portfolio_root.iterdir()
        if d.is_dir() and d.name != "second-brain" and (d / "CLAUDE.md").exists()
    )


def _read_optional(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _extract_title(readme_text: str | None, fallback: str) -> str:
    if readme_text:
        match = re.search(r"^#\s+(.+)$", readme_text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return fallback


def extract_project(project_dir: Path) -> dict:
    readme = _read_optional(project_dir / "README.md")
    claude_md = _read_optional(project_dir / "CLAUDE.md")
    handover = _read_optional(project_dir / "HANDOVER.md")
    return {
        "id": project_dir.name,
        "title": _extract_title(readme, fallback=project_dir.name),
        "repo_path": project_dir.name,
        "docs": {"readme": readme, "claude_md": claude_md, "handover": handover},
    }


def build_snapshot(portfolio_root: Path) -> Snapshot:
    projects = [Project.model_validate(extract_project(d)) for d in discover_projects(portfolio_root)]
    return Snapshot(generated_at=datetime.now(timezone.utc).isoformat(), projects=projects)


def main() -> None:
    snapshot = build_snapshot(PORTFOLIO_ROOT)
    DEFAULT_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_SNAPSHOT_PATH.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    print(f"{len(snapshot.projects)} Projekte in {DEFAULT_SNAPSHOT_PATH} geschrieben.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: `scripts/build_snapshot.py` implementieren**

```python
"""CLI-Einstiegspunkt: `python scripts/build_snapshot.py` baut data/snapshot.json neu."""

from second_brain.snapshot_builder import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Tests laufen lassen, Erfolg verifizieren**

Run: `.venv/Scripts/python.exe -m pytest tests/test_snapshot_builder.py -v`
Erwartet: alle 4 Tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/second_brain/snapshot_builder.py scripts/build_snapshot.py tests/test_snapshot_builder.py
git commit -m "feat: Snapshot-Builder (Scan + Extraktion der Sibling-Repos)"
```

---

### Task 4: Snapshot real bauen und committen

**Files:**
- Create: `data/snapshot.json` (generiert, kein Code-Task)

**Interfaces:**
- Consumes: `main()` aus Task 3.
- Produces: `data/snapshot.json`, gelesen von Task 7 (`app.py`) und Task 8 (`mcp_server.py`).

- [ ] **Step 1: Snapshot-Skript gegen die echten Sibling-Repos laufen lassen**

```bash
.venv/Scripts/python.exe scripts/build_snapshot.py
```

Erwartet: Ausgabe `N Projekte in .../second-brain/data/snapshot.json geschrieben.` mit `N` = Anzahl Verzeichnisse unter `02_Portfolio/` mit `CLAUDE.md` (mind. `ai-act-validation-toolkit`, `cloud-native-pipeline`, `ai-analytics-portal`, `goz-finetune-vs-rag`, `sql-agent`, `stangfolio`, `marco-os`, `stangverse`).

- [ ] **Step 2: Inhalt stichprobenartig prüfen**

```bash
.venv/Scripts/python.exe -c "import json; d = json.load(open('data/snapshot.json', encoding='utf-8')); print([p['id'] for p in d['projects']])"
```

Erwartet: Liste enthält u.a. `"sql-agent"`, `"ai-act-validation-toolkit"`, **nicht** `"second-brain"` selbst.

- [ ] **Step 3: Commit**

```bash
git add data/snapshot.json
git commit -m "data: Snapshot der Portfolio-Projekte generieren"
```

---

### Task 5: LLM-Anbindung (`llm.py`)

**Files:**
- Create: `src/second_brain/llm.py`

**Interfaces:**
- Consumes: nichts.
- Produces: `get_llm() -> BaseChatModel` — genutzt von Task 7 (`app.py`) und Task 8 (`mcp_server.py`).

Provider-agnostisches Muster, identisch zu `ai-act-validation-toolkit/src/ai_act_toolkit/llm.py` übernommen (Global Constraints: kein hart kodiertes Modell im Code).

- [ ] **Step 1: `src/second_brain/llm.py` implementieren**

```python
"""Wählt das LLM aus, ohne einen Anbieter fest zu verdrahten.

init_chat_model() ist LangChains einheitliche Fabrik-Funktion: je nach
model_provider lädt sie im Hintergrund das passende Integrationspaket
(hier langchain-anthropic oder langchain-openai) und liefert in beiden
Fällen dasselbe Chat-Model-Interface zurück.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()


def get_llm() -> BaseChatModel:
    """Baut das Chat-Model aus LLM_PROVIDER/LLM_MODEL in der .env."""
    provider = os.environ.get("LLM_PROVIDER")
    model = os.environ.get("LLM_MODEL")

    if not provider or not model:
        raise RuntimeError(
            "LLM_PROVIDER und LLM_MODEL müssen in der .env gesetzt sein "
            "(siehe .env.example). Aktuell: "
            f"LLM_PROVIDER={provider!r}, LLM_MODEL={model!r}"
        )

    return init_chat_model(model, model_provider=provider)
```

- [ ] **Step 2: Smoke-Test manuell**

```bash
.venv/Scripts/python.exe -c "from second_brain.llm import get_llm; print(get_llm)"
```

Erwartet: kein Fehler beim Import (kein `.env` nötig für den reinen Import — `get_llm()` selbst wird hier nicht aufgerufen).

- [ ] **Step 3: Commit**

```bash
git add src/second_brain/llm.py
git commit -m "feat: provider-agnostische LLM-Anbindung"
```

---

### Task 6: Antwortlogik (`answering.py`)

**Files:**
- Create: `src/second_brain/answering.py`
- Test: `tests/test_answering.py`

**Interfaces:**
- Consumes: `Snapshot`, `Project` aus Task 2.
- Produces: `build_prompt(snapshot: Snapshot) -> str`, `answer_question(llm, question: str, snapshot: Snapshot) -> str` — genutzt von Task 7 (`app.py`) und Task 8 (`mcp_server.py`).

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_answering.py
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
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag verifizieren**

Run: `.venv/Scripts/python.exe -m pytest tests/test_answering.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'second_brain.answering'`.

- [ ] **Step 3: `src/second_brain/answering.py` implementieren**

```python
"""Baut den Prompt aus dem Snapshot (Context-Stuffing) und lässt das LLM antworten."""

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


def answer_question(llm, question: str, snapshot: Snapshot) -> str:
    system_prompt = build_prompt(snapshot)
    response = llm.invoke(
        [
            ("system", system_prompt),
            ("human", question),
        ]
    )
    return response.content
```

- [ ] **Step 4: Tests laufen lassen, Erfolg verifizieren**

Run: `.venv/Scripts/python.exe -m pytest tests/test_answering.py -v`
Erwartet: beide Tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/second_brain/answering.py tests/test_answering.py
git commit -m "feat: Context-Stuffing-Antwortlogik"
```

---

### Task 7: Streamlit-Chat (`app.py`)

**Files:**
- Create: `app.py`

**Interfaces:**
- Consumes: `load_snapshot`, `DEFAULT_SNAPSHOT_PATH` (Task 2), `get_llm` (Task 5), `answer_question` (Task 6).
- Produces: lauffähige Streamlit-App, kein weiterer Konsument im Package.

- [ ] **Step 1: `app.py` implementieren**

```python
"""Streamlit-Chat für das second-brain — beantwortet Fragen zu Marcos Portfolio-Projekten."""

import streamlit as st

from second_brain.answering import answer_question
from second_brain.llm import get_llm
from second_brain.snapshot import DEFAULT_SNAPSHOT_PATH, load_snapshot

st.set_page_config(page_title="second brain — Marco Stangs Portfolio", page_icon="🧠")

st.title("🧠 second brain")
st.markdown(
    "**In 30 Sekunden:** Frag mich alles über Marcos Portfolio-Projekte — "
    "z.B. \"welche Projekte zeigen Cloud-Erfahrung?\" oder \"was macht sql-agent?\". "
    "Ich kenne README, Projektkontext und Status jedes fertigen Projekts."
)

try:
    snapshot = load_snapshot(DEFAULT_SNAPSHOT_PATH)
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
            answer = f"Antwort konnte nicht generiert werden: {e}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
```

- [ ] **Step 2: Manuell verifizieren**

```bash
.venv/Scripts/python.exe -m streamlit run app.py
```

Im Browser prüfen: (1) Titel + 30-Sekunden-Text sichtbar, (2) eine Frage wie "welche Projekte zeigen Cloud-Erfahrung?" liefert eine Antwort mit Projekt-Verweisen, (3) Chat-Verlauf bleibt nach mehreren Fragen sichtbar, (4) `.env` vorübergehend umbenennen und neu laden → Fehlermeldung statt Absturz.

- [ ] **Step 3: iframe-Einbettbarkeit verifizieren**

```bash
.venv/Scripts/python.exe -m streamlit run app.py --server.headless true &
curl -sI "http://localhost:8501/?embed=true" | grep -i x-frame-options
```

Erwartet: kein `X-Frame-Options`-Header (Streamlit setzt standardmäßig keinen) — falls doch einer gefunden wird, `app.py`/Streamlit-Konfiguration anpassen, bis die Seite iframe-fähig ist.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: Streamlit-Chat-UI"
```

---

### Task 8: MCP-Server (`mcp_server.py`)

**Files:**
- Create: `src/second_brain/mcp_server.py`
- Test: `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `load_snapshot` (Task 2), `get_llm` (Task 5), `answer_question` (Task 6).
- Produces: `list_projects() -> list[dict]`, `ask_about_projects(question: str) -> str` (als MCP-Tools registriert über `FastMCP`), kein weiterer Konsument im Package.

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_mcp_server.py
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

    def fake_answer_question(llm, question, snapshot):
        calls["args"] = (llm, question, snapshot)
        return "Antwort"

    monkeypatch.setattr(mcp_server_module, "answer_question", fake_answer_question)

    result = mcp_server_module.ask_about_projects("Was macht sql-agent?")

    assert result == "Antwort"
    assert calls["args"][0] == "fake-llm"
    assert calls["args"][1] == "Was macht sql-agent?"
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag verifizieren**

Run: `.venv/Scripts/python.exe -m pytest tests/test_mcp_server.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'second_brain.mcp_server'`.

- [ ] **Step 3: `src/second_brain/mcp_server.py` implementieren**

```python
"""MCP-Server für das second-brain — exponiert Portfolio-Wissen als MCP-Tools."""

from mcp.server.fastmcp import FastMCP

from second_brain.answering import answer_question
from second_brain.llm import get_llm
from second_brain.snapshot import load_snapshot

mcp = FastMCP("second-brain")


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
    return answer_question(llm, question, snapshot)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Tests laufen lassen, Erfolg verifizieren**

Run: `.venv/Scripts/python.exe -m pytest tests/test_mcp_server.py -v`
Erwartet: beide Tests PASSED.

- [ ] **Step 5: Lokal in Claude Desktop/Code einbinden und manuell verifizieren**

In `claude_desktop_config.json` (bzw. Claude Code `mcp.json`) ergänzen:

```json
{
  "mcpServers": {
    "second-brain": {
      "command": "C:\\Users\\Marco\\OneDrive\\02_Portfolio\\second-brain\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\Marco\\OneDrive\\02_Portfolio\\second-brain\\src\\second_brain\\mcp_server.py"]
    }
  }
}
```

Claude Desktop/Code neu starten, `list_projects` und `ask_about_projects` einmal über den MCP-Client aufrufen, Antwort auf Plausibilität prüfen.

- [ ] **Step 6: Commit**

```bash
git add src/second_brain/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: MCP-Server mit list_projects/ask_about_projects"
```

---

### Task 9: README + CLAUDE.md

**Files:**
- Create: `README.md`
- Create: `CLAUDE.md`

**Interfaces:** keine — reine Dokumentation.

- [ ] **Step 1: `README.md` schreiben**

```markdown
# second-brain

Portfolio-Projekt von Marco Stang für Bewerbungen auf AI/KI-Rollen (ggf.
auch KI-Transformations-Rollen).

🔗 **[Projektseite](https://marco-stang.github.io/second-brain/)**

## In 30 Sekunden

Ein "second brain", das alle fertigen Portfolio-Projekte von Marco kennt —
frag es direkt im Chat, z.B. "welche Projekte zeigen Cloud-Erfahrung?" oder
"was macht sql-agent?", statt jedes README einzeln zu lesen. Dasselbe Wissen
ist zusätzlich als MCP-Server abrufbar, sodass jeder MCP-fähige Client
(Claude Code, Claude Desktop) direkt danach fragen kann.

## Live-Demo

[Link folgt nach Streamlit-Community-Cloud-Deployment]

Hinweis: Streamlit Community Cloud (Free Tier) schläft nach Inaktivität
ein — der erste Ladevorgang kann ein paar Sekunden dauern.

## Was das Tool macht

1. Baut aus README/CLAUDE.md/HANDOVER aller anderen Portfolio-Repos einen
   Snapshot (`data/snapshot.json`).
2. Beantwortet Fragen im Chat, indem der komplette Snapshot als Kontext an
   ein LLM geht (Context-Stuffing statt Vektor-RAG — bei ~10 Projekten
   passt alles in ein Prompt).
3. Exponiert dasselbe Wissen zusätzlich über einen MCP-Server
   (`list_projects`, `ask_about_projects`) für Claude Code/Desktop.

## Architektur

- `src/second_brain/snapshot.py` — Pydantic-Schema + `load_snapshot()`
- `src/second_brain/snapshot_builder.py` — scannt Sibling-Repos, baut den Snapshot
- `src/second_brain/llm.py` — provider-agnostische LLM-Anbindung
- `src/second_brain/answering.py` — Context-Stuffing-Prompt + Antwortlogik
- `app.py` — Streamlit-Chat-UI (öffentlich)
- `src/second_brain/mcp_server.py` — MCP-Server (`list_projects`, `ask_about_projects`)

## Quickstart

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env  # LLM_PROVIDER/LLM_MODEL/API-Key eintragen

.venv/Scripts/python.exe -m pytest tests/ -v          # komplette Test-Suite, kein LLM/Netzwerk nötig
.venv/Scripts/python.exe scripts/build_snapshot.py     # data/snapshot.json neu bauen
.venv/Scripts/python.exe -m streamlit run app.py       # Chat-Demo
```

## Tests

`pytest tests/` läuft komplett ohne LLM-API-Key/Netzwerk (LLM-Aufrufe sind
in allen Tests durch einfache Fakes ersetzt).

## Weiterführende Doku

- Design-Spec: `docs/superpowers/specs/2026-07-29-second-brain-design.md`
- Implementierungsplan: `docs/superpowers/plans/2026-07-29-second-brain-implementation.md`

## Limitierungen

- Snapshot wird manuell gebaut, kein automatisches Aktualisieren bei
  Änderungen in anderen Repos.
- Kein Vektor-RAG — bei stark wachsender Projektzahl würde der Snapshot
  irgendwann nicht mehr komplett ins Prompt passen (aktuell bei ~10
  Projekten kein Problem).
- Nur Projekt-Metadaten/Doku, keine Volltext-Code-Suche.
```

- [ ] **Step 2: `CLAUDE.md` schreiben**

```markdown
# second-brain — Projektkontext

Design-Spec: `docs/superpowers/specs/2026-07-29-second-brain-design.md`
Implementierungsplan: `docs/superpowers/plans/2026-07-29-second-brain-implementation.md`

## Was das hier ist

Portfolio-Projekt von Marco Stang: ein second brain, das alle anderen
Portfolio-Projekte unter `02_Portfolio/` kennt und Fragen dazu beantwortet
— per öffentlichem Streamlit-Chat (Recruiter) und per MCP-Server (Marco in
Claude Code/Desktop). Ersetzt Backlog-Item #3 (`mcp-server-showcase`) in
`../PORTFOLIO_BACKLOG.md`.

## Commands

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env  # LLM_PROVIDER/LLM_MODEL/API-Key eintragen

.venv/Scripts/python.exe -m pytest tests/ -v          # komplette Test-Suite, kein LLM/Netzwerk nötig
.venv/Scripts/python.exe scripts/build_snapshot.py     # data/snapshot.json neu bauen
.venv/Scripts/python.exe -m streamlit run app.py       # Chat-Demo
```

Kein Linter konfiguriert.

## Architektur

- `src/second_brain/snapshot.py` — Pydantic-Schema (`ProjectDocs`,
  `Project`, `Snapshot`) + `load_snapshot()`
- `src/second_brain/snapshot_builder.py` — `discover_projects()` +
  `extract_project()` + `build_snapshot()`, scannt `02_Portfolio/*` nach
  Verzeichnissen mit `CLAUDE.md`
- `src/second_brain/llm.py` — provider-agnostische LLM-Anbindung (Muster
  aus `ai-act-validation-toolkit`)
- `src/second_brain/answering.py` — `build_prompt()` (Context-Stuffing)
  + `answer_question()`
- `app.py` — Streamlit-Chat-UI, muss iframe-einbettbar bleiben (siehe
  Design-Spec, "Integration in marco-os")
- `src/second_brain/mcp_server.py` — MCP-Server (`FastMCP`), Tools
  `list_projects`/`ask_about_projects`
- `scripts/build_snapshot.py` — CLI-Einstiegspunkt für den Snapshot-Builder

## Wie hier gearbeitet wird

Deutsch + Lehrstil wie bei `sql-agent`/`goz-finetune-vs-rag`/
`ai-act-validation-toolkit` — Marco lernt bei RAG-Prompt-Design/MCP aktiv
mit, Konzepte erklären statt vorlösen, alle Doku auf Deutsch.

## Aktueller Stand

*Diesen Abschnitt aktuell halten, sobald ein Task aus dem
Implementierungsplan abgeschlossen ist.*

- ✅ Design-Spec + Implementierungsplan erstellt und freigegeben.
```

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: README und CLAUDE.md"
```

---

### Task 10: GitHub-Pages-Projektseite (`docs/index.html`)

**Files:**
- Create: `docs/index.html`

**Interfaces:** keine — self-contained statische Seite, kein externes CDN/JS/CSS (Konvention aus `PORTFOLIO_AGENT_GUIDE.md`, Abschnitt 5a).

- [ ] **Step 1: `docs/index.html` implementieren**

```html
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>second brain — Marco Stang</title>
<meta name="description" content="Ein second brain, das alle Portfolio-Projekte von Marco Stang kennt — als Chat und als MCP-Server.">
<style>
  :root {
    --bg: #f7f7f5; --bg-alt: #ffffff; --text: #1c1c1a; --text-muted: #58584f;
    --border: #e2e0d8; --accent: #3a5ba0; --accent-soft: #e1e7f3;
    --code-bg: #efede4; --shadow: 0 1px 2px rgba(28,28,26,0.06), 0 8px 24px rgba(28,28,26,0.05);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #17181a; --bg-alt: #1f2123; --text: #ece9e2; --text-muted: #a6a396;
      --border: #33352f; --accent: #8aa6e0; --accent-soft: #23283a;
      --code-bg: #26282a; --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.35);
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.55;
  }
  a { color: var(--accent); }
  .wrap { max-width: 860px; margin: 0 auto; padding: 0 24px; }
  header.hero { padding: 64px 0 48px; border-bottom: 1px solid var(--border); }
  .eyebrow {
    display: inline-block; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.04em;
    text-transform: uppercase; color: var(--accent); background: var(--accent-soft);
    padding: 5px 12px; border-radius: 999px; margin-bottom: 18px;
  }
  h1 { font-size: clamp(1.8rem, 4vw, 2.4rem); margin: 0 0 16px; }
  .lede { font-size: 1.05rem; color: var(--text-muted); max-width: 62ch; margin: 0 0 26px; }
  .cta-row { display: flex; gap: 12px; flex-wrap: wrap; }
  .btn {
    display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px;
    border-radius: 8px; font-weight: 600; font-size: 0.92rem; border: 1px solid transparent;
    text-decoration: none;
  }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-outline { background: transparent; border-color: var(--border); color: var(--text); }
  .btn-disabled { background: transparent; border-color: var(--border); color: var(--text-muted); }
  section { padding: 44px 0; border-bottom: 1px solid var(--border); }
  section:last-of-type { border-bottom: none; }
  h2 { font-size: 1.35rem; margin: 0 0 20px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
  .card { background: var(--bg-alt); border: 1px solid var(--border); border-radius: 10px; padding: 18px; box-shadow: var(--shadow); }
  .card h3 { margin: 0 0 8px; font-size: 1rem; }
  .card p { margin: 0; color: var(--text-muted); font-size: 0.92rem; }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
  th { color: var(--text-muted); font-weight: 600; }
  ul.limits { color: var(--text-muted); font-size: 0.92rem; }
  footer { padding: 32px 0; text-align: center; color: var(--text-muted); font-size: 0.85rem; }
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <span class="eyebrow">Portfolio-Projekt</span>
    <h1>🧠 second brain</h1>
    <p class="lede">
      Ein second brain, das alle Portfolio-Projekte von Marco Stang kennt.
      Frag im Chat statt jedes README einzeln zu lesen — dasselbe Wissen
      ist zusätzlich als MCP-Server für Claude Code/Desktop abrufbar.
    </p>
    <div class="cta-row">
      <a class="btn btn-disabled" aria-disabled="true">💬 Live-Demo folgt</a>
      <a class="btn btn-outline" href="https://github.com/marco-stang/second-brain">Code auf GitHub</a>
    </div>
  </header>

  <section>
    <h2>Was das Tool macht</h2>
    <div class="cards">
      <div class="card">
        <h3>1. Snapshot bauen</h3>
        <p>README/CLAUDE.md/HANDOVER aller Portfolio-Repos werden lokal zu einem Snapshot zusammengefasst.</p>
      </div>
      <div class="card">
        <h3>2. Chat beantworten</h3>
        <p>Der komplette Snapshot geht als Kontext an ein LLM — Context-Stuffing statt Vektor-RAG.</p>
      </div>
      <div class="card">
        <h3>3. MCP exponieren</h3>
        <p>Dasselbe Wissen ist als MCP-Server (list_projects, ask_about_projects) nutzbar.</p>
      </div>
    </div>
  </section>

  <section>
    <h2>Wie es funktioniert</h2>
    <p>
      Bei rund zehn Portfolio-Projekten passt die gesamte Doku in ein
      einziges LLM-Prompt — ein separater Retrieval-Schritt (Embeddings,
      Vektor-Datenbank) wäre unnötige Infrastruktur und würde das RAG-Signal
      duplizieren, das bereits <code>goz-finetune-vs-rag</code> zeigt. Das
      second brain profiliert sich stattdessen über sauberes Wissens-Modell,
      Tool-Exposition per MCP und Cross-Projekt-Synthese.
    </p>
  </section>

  <section>
    <h2>Tech-Stack</h2>
    <table>
      <tr><th>Bereich</th><th>Technologie</th><th>Zweck</th></tr>
      <tr><td>Sprache</td><td>Python ≥3.10</td><td>Snapshot-Builder, Antwortlogik, beide Frontends</td></tr>
      <tr><td>LLM-Anbindung</td><td>LangChain (<code>init_chat_model</code>)</td><td>Provider-agnostisch (Anthropic/OpenAI)</td></tr>
      <tr><td>Datenmodell</td><td>Pydantic v2</td><td>Snapshot-Schema + Validierung</td></tr>
      <tr><td>Chat-UI</td><td>Streamlit</td><td>Öffentliche, Recruiter-facing Demo</td></tr>
      <tr><td>Agentic AI</td><td>MCP (<code>mcp</code>-Python-SDK, <code>FastMCP</code>)</td><td>Tool-Exposition für Claude Code/Desktop</td></tr>
      <tr><td>Tests</td><td>pytest</td><td>Läuft komplett ohne Netzwerk/API-Key</td></tr>
    </table>
  </section>

  <section>
    <h2>Weiterführende Doku</h2>
    <p>
      <a href="https://github.com/marco-stang/second-brain/blob/master/README.md">README</a> ·
      <a href="https://github.com/marco-stang/second-brain/blob/master/docs/superpowers/specs/2026-07-29-second-brain-design.md">Design-Spec</a> ·
      <a href="https://github.com/marco-stang/second-brain/blob/master/docs/superpowers/plans/2026-07-29-second-brain-implementation.md">Implementierungsplan</a>
    </p>
  </section>

  <section>
    <h2>Limitierungen</h2>
    <ul class="limits">
      <li>Snapshot wird manuell gebaut, kein automatisches Aktualisieren.</li>
      <li>Kein Vektor-RAG — bewusste Entscheidung bei aktueller Projektzahl.</li>
      <li>Nur Projekt-Metadaten/Doku, keine Volltext-Code-Suche.</li>
    </ul>
  </section>

  <footer>Marco Stang · <a href="https://github.com/marco-stang">github.com/marco-stang</a></footer>
</div>
</body>
</html>
```

- [ ] **Step 2: Lokal öffnen und Hell/Dunkel-Darstellung prüfen**

Datei im Browser öffnen (direktes `file://` reicht hier, keine ES-Module),
Betriebssystem-Theme zwischen hell/dunkel umschalten, prüfen dass sich die
Seite mitschaltet.

- [ ] **Step 3: Commit**

```bash
git add docs/index.html
git commit -m "docs: GitHub-Pages-Projektseite"
```

---

### Task 11: Neues GitHub-Repo erstellen und pushen

**Files:** keine Code-Dateien — Git-Remote-Operation.

**Interfaces:** keine.

Laut `PORTFOLIO_AGENT_GUIDE.md`, Abschnitt 4: vor dem Anlegen kurz mit
Marco Repo-Name und Sichtbarkeit bestätigen (Standardannahme: public, Name
`second-brain`, wie bei den bestehenden Repos).

- [ ] **Step 1: Mit Marco bestätigen: Repo-Name `second-brain`, public — passt das?**

- [ ] **Step 2: Repo anlegen**

Mit `gh` (falls verfügbar, sonst manuell im Browser als `marco-stang`
→ "New repository" → Name `second-brain`, public, ohne
README/.gitignore-Vorbelegung):

```bash
gh repo create marco-stang/second-brain --public --source=. --remote=origin
```

- [ ] **Step 3: Pushen**

```bash
git push -u origin master
```

- [ ] **Step 4: Verifizieren**

Run: `git remote -v && git log --oneline -1`
Erwartet: `origin` zeigt auf das neue Repo, letzter Commit ist auf GitHub sichtbar.

---

### Task 12: GitHub Pages aktivieren

**Files:** keine — GitHub-Repo-Einstellung.

**Interfaces:** keine.

- [ ] **Step 1: GitHub Pages aktivieren**

```bash
gh api -X POST "repos/marco-stang/second-brain/pages" \
  -f "source[branch]=master" -f "source[path]=/docs"
```

Erwartet: Antwort enthält `html_url` (Format
`https://marco-stang.github.io/second-brain/`).

- [ ] **Step 2: Auf Verfügbarkeit warten**

```bash
until curl -s https://marco-stang.github.io/second-brain/ | grep -q "second brain"; do sleep 3; done
```

- [ ] **Step 3: URL in `README.md` und `docs/index.html` eintragen, falls dort noch Platzhalter stehen, committen und pushen**

```bash
git add README.md docs/index.html
git commit -m "docs: GitHub-Pages-URL bestätigt erreichbar"
git push
```

---

### Task 13: Streamlit Community Cloud Deployment

**Files:** keine — externes Hosting-Setup.

**Interfaces:** keine.

- [ ] **Step 1: Auf share.streamlit.io mit dem GitHub-Account einloggen**

- [ ] **Step 2: Neue App aus `marco-stang/second-brain`, Branch `master`, Datei `app.py` deployen**

- [ ] **Step 3: Secrets setzen (Streamlit-Cloud-UI, "Secrets")**

```toml
LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-sonnet-4-5-20250929"
ANTHROPIC_API_KEY = "..."
```

- [ ] **Step 4: Live-URL in `README.md` und `docs/index.html` eintragen (CTA-Button aktivieren) und committen/pushen**

```bash
git add README.md docs/index.html
git commit -m "docs: Live-Demo-Link ergänzen"
git push
```

- [ ] **Step 5: iframe-Einbettbarkeit an der echten Live-URL verifizieren**

```html
<!-- lokale Testdatei, nicht Teil des Repos -->
<iframe src="https://second-brain.streamlit.app/?embed=true" width="600" height="500"></iframe>
```

In einem Browser öffnen, prüfen dass der Chat innerhalb des iframes lädt
und bedienbar ist (keine `X-Frame-Options`-Blockade).

---

### Task 14: Backlog + stangfolio-Karte aktualisieren

**Files:**
- Modify: `../PORTFOLIO_BACKLOG.md`
- Modify: `../stangfolio/data/projects.js`

**Interfaces:** keine.

- [ ] **Step 1: `PORTFOLIO_BACKLOG.md` aktualisieren**

Neues Item `second-brain` mit Status `fertig` und Links zu Repo/Projektseite/
Live-Demo ergänzen (Muster: siehe Item #0 `ai-act-validation-toolkit`).
Item #3 (`mcp-server-showcase`) als "ersetzt durch second-brain, siehe
neues Item" markieren, Status-Tabelle entsprechend anpassen.

- [ ] **Step 2: Neue Projekt-Karte in `stangfolio/data/projects.js` ergänzen**

Nur die eigene Ergänzung stagen (nicht `-A`, falls dort bereits andere
uncommittete Änderungen liegen — erst `git status` in `stangfolio/`
prüfen). Schema:

```js
{
  id: "second-brain",
  title: "second brain",
  summary: "Second brain, das alle Portfolio-Projekte kennt — als Chat und MCP-Server.",
  description: "Beantwortet Fragen zu allen Portfolio-Projekten per Chat (Context-Stuffing über README/CLAUDE.md/HANDOVER aller Repos) und exponiert dasselbe Wissen als MCP-Server für Claude Code/Desktop.",
  tags: ["Python", "LangChain", "Streamlit", "MCP", "Pydantic"],
  demoUrl: "https://second-brain.streamlit.app/",
  repoUrl: "https://github.com/marco-stang/second-brain",
  status: "live",
  coldStartNote: "Streamlit Community Cloud (Free Tier) schläft nach Inaktivität ein — erster Ladevorgang kann ein paar Sekunden dauern.",
}
```

- [ ] **Step 3: Commit (in beiden Repos separat)**

```bash
cd ../
git -C . add PORTFOLIO_BACKLOG.md  # falls 02_Portfolio selbst kein Repo ist: manuell speichern, siehe PORTFOLIO_AGENT_GUIDE.md
cd stangfolio
git add data/projects.js
git commit -m "feat: second-brain-Projektkarte ergänzen"
git push
```

- [ ] **Step 4: Kurze Rücksprache mit Marco, ob das Ergebnis so passt**

---

## Self-Review

- **Spec-Abdeckung:** Architektur (Task 1-3, 5-8), Snapshot-Scope README+CLAUDE.md+HANDOVER ohne specs/plans (Task 3), Context-Stuffing statt Vektor-RAG (Task 6), zwei Frontends (Task 7-8), iframe-Einbettbarkeit (Task 7 Step 3, Task 13 Step 5), Fehlerbehandlung (Task 2 `load_snapshot`, Task 7 try/except), Tests ohne Netzwerk (Task 2/3/6/8), Definition-of-Done-Punkte README/GitHub-Pages/Backlog/stangfolio-Karte (Task 9-14) sind alle auf Tasks abgebildet.
- **Platzhalter-Scan:** keine TBD/TODO in Code-Blöcken; einzige offenen Werte (Live-Demo-URL, API-Keys, exakte Projektanzahl `N`) sind bewusst erst nach Ausführung/Deployment bekannt und in den jeweiligen Tasks (4, 13, 14) explizit als Schritt dokumentiert, nicht als Platzhalter im Code.
- **Typ-Konsistenz geprüft:** `Snapshot`/`Project`/`ProjectDocs`/`DEFAULT_SNAPSHOT_PATH`/`load_snapshot` (Task 2) werden in Task 3, 6, 7, 8 identisch verwendet; `build_prompt`/`answer_question` (Task 6) identisch in Task 7 und 8; `get_llm` (Task 5) identisch in Task 7 und 8; `list_projects`/`ask_about_projects`-Signaturen (Task 8) stimmen mit der Design-Spec überein.
