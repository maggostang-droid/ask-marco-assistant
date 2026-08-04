# HANDOVER — second-brain

Stand: 2026-07-29. Dieses Dokument ist so geschrieben, dass eine komplett
neue Session (Marco selbst oder ein neuer Agent) ohne Kenntnis des
bisherigen Chatverlaufs sofort weiß, was fertig und live ist, was bewusste
Scope-Grenzen sind, und was als Nächstes ansteht.

## Status: Live deployed, alle 14 Tasks abgeschlossen ✅

- **Live-Demo:** https://second-brain-projects.streamlit.app/
- **Repo:** https://github.com/marco-stang/ask-marco-assistant
- **Projektseite:** https://marco-stang.github.io/ask-marco-assistant/
- **MCP-Server:** implementiert und getestet, aber **nicht** von einer
  Agenten-Session in Marcos lokales Claude Desktop/Code eingebunden
  (persönliche App-Konfiguration) — Anleitung in
  `docs/superpowers/plans/2026-07-29-second-brain-implementation.md`,
  Task 8, Step 5, falls Marco das selbst nachziehen will.

## Was ist fertig und getestet

- Snapshot-Builder (`src/second_brain/snapshot_builder.py`) scannt alle
  Sibling-Repos unter `02_Portfolio/` nach README/CLAUDE.md/HANDOVER,
  baut `data/snapshot.json`. Worktree-sicher (env-var-Override +
  Mindest-Projektzahl-Guard, siehe `SECOND_BRAIN_PORTFOLIO_ROOT`).
- Context-Stuffing-Antwortlogik (`src/second_brain/answering.py`):
  kompletter Snapshot geht als System-Prompt ans LLM, kein Vektor-RAG.
  **Antworten sind jetzt bewusst kurz** (2-4 Sätze Default, ausführlicher
  nur auf explizite Nachfrage) — Marco fand die ersten Antworten zu lang.
- `app.py` (öffentlicher Streamlit-Chat) und `src/second_brain/mcp_server.py`
  (MCP-Server, `MCPServer` aus `mcp.server.mcpserver` — **nicht** `FastMCP`,
  das existiert in der installierten `mcp`-Version 2.0.0 nicht mehr) teilen
  sich dieselbe Backend-Logik.
- **HANDOVER.md-Scoping-Entscheidung (mit Marco getroffen):** der
  öffentliche Chat bekommt kein `HANDOVER.md`-Material in den Prompt
  (`include_handover=False` in `app.py`) — manche Projekt-HANDOVERs
  enthalten Betriebsdetails (z.B. eine echte AWS-Account-ID bei
  `cloud-native-pipeline`), die ein interaktiver Chat leichter auffindbar
  macht als ein vergrabenes Dokument. Der lokale MCP-Server sieht weiterhin
  alles (Default `include_handover=True`).
- Tests: `pytest tests/ -v` → **15/15 grün**, kein Netzwerk/API-Key nötig
  (LLM-Aufrufe überall durch Fakes ersetzt).
- **marco-os-Integration:** Klick auf den zentralen "Marco Stang"-Knoten in
  `marco-os` öffnet diesen Chat als eingebettetes `<iframe
  src=".../?embed=true">`-Fenster. Details/Bugs dazu (Sentinel-ID-Kollision
  mit einer echten `data/projects.js`-Karte, Fokus-Restaurations-Bug) stehen
  in `marco-os`s eigenem `HANDOVER.md`, nicht hier.

## Deployment, wie es tatsächlich lief

Marco hat den Streamlit-Community-Cloud-Login und die Secrets selbst
gesetzt (kann/darf eine Agenten-Session nicht — kein API-Key-Handling
durch den Agenten):

```toml
LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-sonnet-4-5-20250929"
ANTHROPIC_API_KEY = "..."
```

**Wichtige Deploy-Stolperfalle, bereits im Vorfeld gefixt:** `app.py`
importiert aus `src/` (src-Layout), aber Streamlit Community Cloud
installiert per `requirements.txt`, nicht per `pip install -e .` des
gesamten Repos. Ohne die im Repo liegende `requirements.txt` (Inhalt: `-e
.`) hätte der Deploy mit `ModuleNotFoundError: No module named
'second_brain'` fehlschlagen können — wurde vor dem ersten echten
Deploy-Versuch bereits im Whole-Branch-Review gefunden und behoben.

## Bekannte offene Punkte (bewusst geparkt, kein Nacharbeiten nötig ohne Rücksprache)

- **`list_projects()`/`Project`-Schema tragen keine `demo_url`/`repo_url`/
  `status`.** Die Design-Spec wollte das (Zeile "Antwort mit Verweis auf
  die jeweiligen Projekt-IDs/Links"), der Implementierungsplan hat es
  stillschweigend weggelassen. Der Bot kann Projekte aktuell nicht
  zuverlässig mit einem klickbaren Demo-Link beantworten — nur wenn ein
  Link zufällig im README-Fließtext auftaucht. Möglicher Folge-Task:
  Felder ergänzen + durch `answering.py`/`mcp_server.py` durchreichen.
- **Kein automatischer Snapshot-Rebuild.** `data/snapshot.json` ist
  eingecheckt, aber wird nur manuell per `scripts/build_snapshot.py` neu
  gebaut. Ändert sich ein anderes Portfolio-Repo (neues README, neuer
  Status), merkt second-brain das nicht von selbst.
- **iframe-Sandboxing** (`sandbox`/`referrerpolicy` auf dem `<iframe>` in
  `marco-os`) wurde im dortigen Final-Review als sinnvolle Härtung
  vorgeschlagen, aber bewusst nicht umgesetzt — ein fehlendes
  Sandbox-Token kann Streamlits Websocket-/Storage-Nutzung stillschweigend
  brechen, das braucht eine eigene Verifikationsrunde gegen die Live-App,
  kein Drive-by-Fix.

## Schnellreferenz: wichtigste Befehle

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env  # LLM_PROVIDER/LLM_MODEL/API-Key eintragen

.venv/Scripts/python.exe -m pytest tests/ -v          # 15/15, kein Netzwerk nötig
.venv/Scripts/python.exe scripts/build_snapshot.py     # data/snapshot.json neu bauen
.venv/Scripts/python.exe -m streamlit run app.py       # Chat lokal starten
```

## Links

- Live-Demo: https://second-brain-projects.streamlit.app/
- Repo: https://github.com/marco-stang/ask-marco-assistant
- Projektseite (GitHub Pages): https://marco-stang.github.io/ask-marco-assistant/
- Design-Spec: [`docs/superpowers/specs/2026-07-29-second-brain-design.md`](docs/superpowers/specs/2026-07-29-second-brain-design.md)
- Implementierungsplan: [`docs/superpowers/plans/2026-07-29-second-brain-implementation.md`](docs/superpowers/plans/2026-07-29-second-brain-implementation.md)
- Portfolio-Backlog-Eintrag: [`../PORTFOLIO_BACKLOG.md`](../PORTFOLIO_BACKLOG.md), Item #5
- Ablauf-Anleitung für Agenten-Sessions: [`../PORTFOLIO_AGENT_GUIDE.md`](../PORTFOLIO_AGENT_GUIDE.md)
- marco-os-Integration (eigenes Handover dort): [`../marco-os/HANDOVER.md`](../marco-os/HANDOVER.md)
