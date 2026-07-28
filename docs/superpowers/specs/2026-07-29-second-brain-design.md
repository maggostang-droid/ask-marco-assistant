# second-brain — Design-Spec

Erstellt: 2026-07-29

## Was das hier ist

Portfolio-Projekt von Marco Stang: ein "second brain", das alle anderen
Portfolio-Projekte unter `02_Portfolio/` kennt und Fragen dazu beantworten
kann — sowohl für Marco selbst (Überblick behalten) als auch für Recruiter
(interaktiv statt nur READMEs lesen).

Ersetzt Backlog-Item #3 (`mcp-server-showcase`) in
`../PORTFOLIO_BACKLOG.md` — das MCP-Signal wird hier mit abgedeckt, ein
separates SQL-Guardrails-MCP-Projekt ist damit nicht mehr geplant.

**Zielgruppe:** beide — Recruiter über eine öffentliche Chat-Seite, Marco
selbst zusätzlich über einen MCP-Server in Claude Code/Desktop.

**Lernstil:** Deutsch + Lehrstil (wie `sql-agent`/`goz-finetune-vs-rag`/
`ai-act-validation-toolkit`) — Marco lernt bei RAG-Prompt-Design/MCP aktiv
mit, Konzepte erklären statt nur vorlösen.

## Architektur

Ein gemeinsames Python-Backend, zwei Frontends:

```
second-brain/
├── data/snapshot.json          # generiert, aber eingecheckt (App läuft auch ohne Neubau)
├── scripts/build_snapshot.py   # liest alle Sibling-Repos, schreibt snapshot.json
├── src/second_brain/
│   ├── snapshot.py             # Pydantic-Schema + Lade-/Validierungslogik für snapshot.json
│   ├── llm.py                  # provider-agnostisch, Muster aus sql-agent/ai-act-validation-toolkit
│   └── answering.py            # answer_question(question, snapshot) -> Antwort mit Projekt-Verweisen
├── app.py                      # Streamlit-Chat (öffentlich, Recruiter-facing)
├── mcp_server.py                # MCP-Server (stdio), nutzt answering.py — für Marco in Claude Code/Desktop
└── tests/
```

### Snapshot statt Live-Zugriff

`scripts/build_snapshot.py` läuft lokal und manuell (kein automatischer
Trigger — `02_Portfolio` ist selbst kein Git-Repo, die Quell-Repos sind
nicht miteinander verknüpft, es gibt keine CI). Es scannt
`02_Portfolio/*` nach Verzeichnissen mit `CLAUDE.md` (= Portfolio-Projekt)
und zieht pro Projekt:

- `README.md`
- `CLAUDE.md`
- `HANDOVER.md` (falls vorhanden)

Bewusst **ausgeschlossen**: `docs/superpowers/specs/`/`plans/`-Dateien —
Implementierungsdetail (Task-Listen, Zwischenentscheidungen), nicht das,
was ein Recruiter fragt. README+CLAUDE.md sind bereits auf
Recruiter-Verständlichkeit getrimmt (siehe `../PORTFOLIO_AGENT_GUIDE.md`,
Abschnitt 5a) und liefern Ziel/Stack/Status zuverlässig. Hält den Snapshot
klein genug fürs Context-Stuffing.

Ergebnis: `data/snapshot.json`, wird committet (App/MCP-Server laufen
auch ohne Neubau; Aktualität hängt vom letzten manuellen Rebuild ab —
siehe "Bewusst weggelassen").

### Antwortmechanismus: Context-Stuffing statt Vektor-RAG

Bei ~9-10 Projekten mit überschaubarer Doku passt der komplette Snapshot
in ein einziges LLM-Prompt — kein Retrieval-Schritt (Embeddings,
Vektor-DB) nötig. `answer_question(question, snapshot)` baut einen Prompt
(System: alle Projekt-Zusammenfassungen aus dem Snapshot; User: die
Frage) und lässt Claude direkt antworten, mit Verweis auf die jeweiligen
Projekt-IDs/Links.

Bewusst kein echtes Vektor-RAG: würde ein Skill-Signal duplizieren, das
`goz-finetune-vs-rag` bereits abdeckt, und wäre für diese Corpus-Größe
unnötige Infrastruktur. Das Profil dieses Projekts liegt stattdessen auf
sauberem Wissens-Modell + Tool-Exposition über MCP + Cross-Projekt-
Synthese ("welche Projekte zeigen Cloud-Erfahrung?" über mehrere Projekte
hinweg).

### Zwei Frontends, ein Backend

- **`app.py`** — Streamlit-Chat-UI (öffentlich, Recruiter-facing,
  Deployment analog `ai-act-validation-toolkit`/`cloud-native-pipeline`
  via Streamlit Community Cloud). Lädt `snapshot.json` beim Start, nutzt
  `answer_question()`. **Muss iframe-einbettbar sein** (siehe
  "Integration in marco-os" unten) — Streamlit setzt standardmäßig keine
  `X-Frame-Options`, die das verhindern, das wird trotzdem explizit
  verifiziert statt angenommen.
- **`mcp_server.py`** — MCP-Server (Python-SDK, stdio-Transport), läuft
  lokal bei Marco (Claude Code/Desktop `mcp.json`). Exponiert:
  - `list_projects()` — kompakte Liste aller Projekte (id/title/summary/
    status/links)
  - `ask_about_projects(question)` — ruft dieselbe `answer_question()`

### Integration in marco-os (iframe)

`marco-os` (separates Repo, eigene Spec unter
`../marco-os/docs/superpowers/specs/`) ist bewusst backend-frei (plain
HTML/CSS/Vanilla-JS, kein Build-Tool, GitHub Pages). Ein echter LLM-Chat
kann dort nicht direkt laufen (API-Key dürfte nicht im Browser-JS
landen). Statt marco-os' Architektur aufzubrechen, bekommt es später
einen neuen Fenstertyp, der die second-brain-Streamlit-App per `<iframe
src="https://second-brain.streamlit.app/?embed=true">` einbettet
(Streamlits eingebauter `?embed=true`-Parameter blendet Sidebar/Menü/
Footer aus, für ein aufgeräumteres Einbetten). second-brain bleibt
alleiniger Besitzer der Chat-Logik/des Hostings; marco-os bleibt
backend-frei. Diese Integration ist **nicht Teil des second-brain-
Implementierungsplans** (marco-os-seitiger Code gehört ins marco-os-Repo
und braucht die second-brain-Live-URL als Voraussetzung), wird aber hier
als Anforderung an `app.py` (iframe-Tauglichkeit) vorgemerkt.

## Datenfluss

1. Lokal, manuell: `python scripts/build_snapshot.py` → `data/snapshot.json`,
   committet.
2. Streamlit-App lädt `snapshot.json` beim Start in den Speicher.
3. Nutzerfrage im Chat → `answer_question()` → LLM-Call (Claude, über
   `llm.py`) → Antwort im Chat mit Projekt-Verweisen.
4. MCP-Server lädt denselben Snapshot, exponiert die zwei Tools über
   stdio.

## Fehlerbehandlung

- Snapshot fehlt/leer/kaputt: verständliche Fehlermeldung statt Absturz
  (Pydantic-Validierung beim Laden).
- LLM-Fehler (kein Key, Rate-Limit, Netzwerk): Fehlermeldung im Chat statt
  Stacktrace — Muster aus `ai-act-validation-toolkit/llm.py` übernehmen.
- Snapshot-Staleness: bewusst kein Auto-Rebuild/CI-Trigger. `CLAUDE.md`
  dokumentiert, dass der Snapshot manuell neu gebaut werden muss, wenn
  sich andere Repos ändern.

## Tests (laufen ohne Netzwerk/API-Key)

- `build_snapshot.py` gegen Fixture-Verzeichnisse (Extraktion korrekt,
  fehlende Dateien werden übersprungen statt zu crashen)
- `snapshot.py`-Schema-Validierung (gültige/ungültige `snapshot.json`)
- `answer_question()` mit gemocktem LLM-Client (Prompt enthält alle
  Projekte, Antwort wird durchgereicht)
- MCP-Server: Tools sind korrekt registriert und rufen `answer_question()`
  mit den richtigen Parametern auf

## Bewusst weggelassen

- Automatischer Snapshot-Rebuild/CI-Trigger — `02_Portfolio` ist kein
  gemeinsames Repo, kein CI vorhanden.
- Vektor-RAG/Embeddings — Corpus zu klein, würde `goz-finetune-vs-rag`
  duplizieren.
- Volltext-Code-Indexierung — nur Projekt-Metadaten/Doku, keine
  Implementierungsdetails.
- User-Accounts/Rate-Limiting auf der Chat-Seite — öffentliche
  Demo-App wie die anderen Streamlit-Deployments im Portfolio.
- Separates SQL-Guardrails-MCP-Projekt (Backlog-Item #3) — durch dieses
  Projekt ersetzt.

## Definition of Done

- Snapshot-Builder läuft gegen die realen Sibling-Repos, `data/snapshot.json`
  enthält alle fertigen Projekte.
- Streamlit-Chat live deployed, beantwortet Fragen zu mind. 3 verschiedenen
  Projekten korrekt (inkl. Cross-Projekt-Frage wie "welche Projekte zeigen
  Cloud-Erfahrung?").
- iframe-Einbettbarkeit verifiziert (`app.py` lädt mit `?embed=true` in
  einem `<iframe>`, keine `X-Frame-Options`, die das blockieren) —
  Voraussetzung für die spätere marco-os-Integration.
- MCP-Server lokal lauffähig, in Claude Desktop/Code eingebunden, mind.
  eine Anfrage End-to-End demonstriert.
- README + GitHub-Pages-Projektseite nach dem etablierten Muster
  (`../PORTFOLIO_AGENT_GUIDE.md`, Abschnitt 5a).
- `PORTFOLIO_BACKLOG.md`: neues Item für `second-brain` ergänzt (Status
  `in Arbeit`→`fertig`), Item #3 als "ersetzt durch second-brain"
  markiert.
- Neue Projekt-Karte in `stangfolio/data/projects.js` ergänzt (Konvention
  aus `../PORTFOLIO_AGENT_GUIDE.md`, Schritt 9).
