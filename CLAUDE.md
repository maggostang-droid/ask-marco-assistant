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
- `src/second_brain/mcp_server.py` — MCP-Server (Klasse `MCPServer` aus
  `mcp.server.mcpserver`), Tools `list_projects`/`ask_about_projects`
- `scripts/build_snapshot.py` — CLI-Einstiegspunkt für den Snapshot-Builder

## Wie hier gearbeitet wird

Deutsch + Lehrstil wie bei `sql-agent`/`goz-finetune-vs-rag`/
`ai-act-validation-toolkit` — Marco lernt bei RAG-Prompt-Design/MCP aktiv
mit, Konzepte erklären statt vorlösen, alle Doku auf Deutsch.

## Aktueller Stand

*Diesen Abschnitt aktuell halten, sobald ein Task aus dem
Implementierungsplan abgeschlossen ist.*

- ✅ Design-Spec + Implementierungsplan erstellt und freigegeben.
- ✅ Tasks 1–10 abgeschlossen: Skeleton, Snapshot-Schema, Snapshot-Builder +
  echte Daten, LLM-Anbindung, Antwortlogik, Streamlit-App, MCP-Server,
  README/CLAUDE.md, GitHub-Pages-Seite.
- ⏳ Tasks 11–14 offen (Repo-Erstellung, Pages-Aktivierung,
  Streamlit-Cloud-Deployment, Aktualisierung von Portfolio-Backlog/-Index) —
  brauchen Marcos Zugangsdaten bzw. explizites Go, daher pausiert bis er
  mitmacht.
