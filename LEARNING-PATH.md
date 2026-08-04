# LEARNING-PATH.md — second-brain

Lernpfad zur Interview-Vorbereitung. Alles hier ist am tatsächlichen Repo-Stand
verifiziert (Code gelesen, `pytest` lokal ausgeführt, `git log` geprüft) —
nicht nur aus README/CLAUDE.md abgeschrieben.

**Wichtigster Fund vorab:** Die Portfolio-Karte in `marco-os/data/projects.js`
(`status: "planned"`, `demoUrl: null`, Text "noch in Arbeit ... die Umsetzung
läuft noch") ist **veraltet**. Der tatsächliche Stand in diesem Repo ist
weiter fortgeschritten: alle 14 Tasks des Implementierungsplans sind laut
`CLAUDE.md` ("Aktueller Stand") abgeschlossen, es gibt eine echte Live-Demo,
ein öffentliches GitHub-Repo und einen laufenden MCP-Server. Das ist eine
Diskrepanz, auf die du im Interview vorbereitet sein solltest, falls jemand
die marco-os-Seite mit dem echten Repo vergleicht.

---

## 1. Elevator-Pitch (auswendig lernen)

> "second-brain ist ein Chat-Assistent, der alle meine fertigen
> Portfolio-Projekte kennt — er liest README, CLAUDE.md und HANDOVER aus
> jedem Repo, baut daraus einen Snapshot und gibt den kompletten Snapshot als
> Kontext an ein LLM, statt ein Vektor-RAG mit Embeddings aufzusetzen — bei
> aktuell acht Projekten passt die gesamte Doku locker in ein Prompt-Fenster,
> ein Retrieval-Schritt wäre unnötige Infrastruktur. Zielgruppen sind
> Recruiter über einen öffentlichen Streamlit-Chat und ich selbst über einen
> MCP-Server, den ich in Claude Code/Desktop einbinde. Der öffentliche Chat
> bekommt bewusst kein HANDOVER.md zu sehen, weil das bei einem Projekt
> Betriebsdetails wie eine echte AWS-Account-ID enthält — nur der lokale
> MCP-Server sieht die volle Doku."

Ehrlicher Zusatz, falls nachgefragt wird: Die ursprüngliche Idee (Design-Spec)
und die Umsetzung stimmen inhaltlich fast exakt überein — der einzige echte
Rework war eine nachträgliche Sicherheits-Korrektur (HANDOVER.md aus dem
öffentlichen Chat ausschließen) nach einem selbst durchgeführten
Whole-Branch-Review, nicht während der ursprünglichen Implementierung.

---

## 2. Aktueller Stand vs. geplant

### Was JETZT funktioniert (verifiziert)

- **Snapshot-Pipeline ist real und lief gegen die echten Sibling-Repos:**
  `data/snapshot.json` enthält aktuell 8 Projekte (`ai-act-validation-toolkit`,
  `ai-analytics-portal`, `cloud-native-pipeline`, `goz-finetune-vs-rag`,
  `marco-os`, `sql-agent`, `stangfolio`, `stangverse`), zuletzt generiert am
  2026-07-29. Kein Platzhalter — echte README/CLAUDE.md-Inhalte der anderen
  Repos stehen im JSON (`data/snapshot.json`, ca. 153 KB).
- **Kompletter Code-Pfad implementiert:** `src/second_brain/snapshot.py`,
  `snapshot_builder.py`, `llm.py`, `answering.py`, `mcp_server.py`, `app.py`,
  `scripts/build_snapshot.py` — alle existieren, sind keine Stubs.
- **Testsuite läuft grün:** `pytest tests/ -v` → **15/15 PASSED**, keine
  Netzwerk-/API-Key-Abhängigkeit (selbst nachvollzogen).
- **Live deployed, nicht nur lokal:**
  - GitHub-Repo public: `github.com/marco-stang/ask-marco-assistant`
  - GitHub-Pages-Projektseite: `marco-stang.github.io/ask-marco-assistant/`
  - Streamlit-Community-Cloud-Chat:
    `second-brain-projects.streamlit.app` — laut `CLAUDE.md` als erreichbar
    und iframe-einbettbar (kein `X-Frame-Options`-Header) verifiziert.
- **MCP-Server ist real, nicht nur geplant:** `src/second_brain/mcp_server.py`
  registriert `list_projects()` und `ask_about_projects(question)` als Tools
  über `MCPServer` aus `mcp.server.mcpserver` und wird über
  `tests/test_mcp_server.py` getestet.
- **`PORTFOLIO_BACKLOG.md`** (Item 5) ist bereits auf Status **"fertig"**
  aktualisiert.

### Was NICHT stimmt / noch fehlt

- **`marco-os/data/projects.js` ist stale** (siehe oben) — sagt "planned"/
  "noch in Arbeit", `demoUrl: null`, `repoUrl: null`. Das widerspricht dem
  tatsächlichen Repo-Zustand. Task 14 des Implementierungsplans sah genau
  diese Aktualisierung vor; laut `CLAUDE.md`-Abschnitt "Aktueller Stand" ist
  sie zwar als "Task 14 abgeschlossen" vermerkt, aber der reale Karten-Text
  in `marco-os` zeigt trotzdem noch den alten Stand — vor einem Interview
  lohnt sich ein kurzer Check/Fix, damit die eigene Portfolio-Seite nicht
  gegen das eigene Repo aussagt.
- **Offen laut CLAUDE.md, Abschnitt "Aktueller Stand", Punkt 2:**
  `list_projects()`/`Project`-Schema tragen aktuell **keine**
  `demo_url`/`repo_url`/`status`-Felder — die Design-Spec wollte das, der
  Implementierungsplan hat es beim Schreiben stillschweigend weggelassen.
  Konkrete Konsequenz: Der Bot kann in einer Antwort zwar über ein Projekt
  sprechen, aber keinen zuverlässigen klickbaren Demo-Link mitliefern, weil
  diese Info schlicht nicht im Snapshot-Schema steckt
  (`src/second_brain/snapshot.py`, Klasse `Project`).
- **Kein automatischer Snapshot-Rebuild:** `data/snapshot.json` ist ein
  eingecheckter Schnappschuss, kein Live-Zugriff. Ändert sich ein anderes
  Repo, weiß der Chat erst nach manuellem `python scripts/build_snapshot.py`
  + Commit davon (bewusste Design-Entscheidung, siehe Abschnitt 5).
- **Implementierungs-Detail weicht vom Plan-Pseudocode ab (kleiner, aber
  interview-relevanter Punkt):** Der Implementierungsplan
  (`docs/superpowers/plans/2026-07-29-second-brain-implementation.md`, Task 8)
  schlug `from mcp.server.fastmcp import FastMCP` vor. Die tatsächliche
  Installation (`mcp>=2,<3`) hat diese Klasse nicht — Commit `ae9edfa`
  ("fix: Task 8 - Use MCPServer instead of low-level Server") dokumentiert,
  dass stattdessen `mcp.server.mcpserver.MCPServer` verwendet wurde, weil sie
  dieselbe Decorator-Semantik bietet. Guter Beleg dafür, dass real gegen eine
  echte Library-Version gebaut wurde, nicht nur Pseudocode kopiert.

---

## 3. Architektur-Überblick (echte Dateipfade)

```
second-brain/
├── data/snapshot.json                     # generiert, eingecheckt, 8 Projekte
├── scripts/build_snapshot.py              # CLI-Einstieg, ruft snapshot_builder.main()
├── src/second_brain/
│   ├── snapshot.py                        # Pydantic: ProjectDocs, Project, Snapshot
│   │                                       # + load_snapshot()
│   ├── snapshot_builder.py                # discover_projects(), extract_project(),
│   │                                       # build_snapshot(), _write_snapshot()
│   ├── llm.py                             # get_llm() — provider-agnostisch via
│   │                                       # LangChains init_chat_model()
│   ├── answering.py                       # build_prompt() (Context-Stuffing),
│   │                                       # answer_question()
│   └── mcp_server.py                      # MCPServer, Tools list_projects/
│                                           # ask_about_projects
├── app.py                                 # Streamlit-Chat-UI (öffentlich)
├── tests/                                 # 15 Tests, alle ohne Netzwerk/LLM
├── docs/index.html                        # GitHub-Pages-Projektseite
└── docs/superpowers/{specs,plans}/        # Design-Spec + Implementierungsplan
```

Ein gemeinsames Backend (`src/second_brain/`), zwei dünne Frontends
(`app.py` für Recruiter, `mcp_server.py` für Marco selbst) — beide rufen
dieselbe `answer_question()`-Funktion auf, nur mit unterschiedlichem
`include_handover`-Flag.

---

## 4. Stationen

### Station 1 — Snapshot-Aufbau: `src/second_brain/snapshot_builder.py`

`discover_projects(portfolio_root)` (Zeile 21) scannt `02_Portfolio/*` nach
Verzeichnissen mit einer `CLAUDE.md` — das ist das Kriterium "das ist ein
Portfolio-Projekt". `extract_project(project_dir)` (Zeile 42) liest dann
`README.md`, `CLAUDE.md`, `HANDOVER.md` (jeweils optional, fehlt eine Datei
→ `None` statt Absturz, siehe `_read_optional`, Zeile 30) und leitet den Titel
per Regex aus der ersten `# Überschrift` des READMEs ab
(`_extract_title`, Zeile 34), mit Fallback auf den Verzeichnisnamen.
`_write_snapshot()` (Zeile 59) bricht bewusst mit `sys.exit(1)` ab, wenn
weniger als `MIN_EXPECTED_PROJECTS = 3` Projekte gefunden werden — das ist ein
Schutz gegen ein falsch konfiguriertes `portfolio_root` (z.B. wenn das Skript
versehentlich aus einem Git-Worktree unter `.worktrees/` heraus läuft und dort
fast nichts findet).

**Selbstkontrollfrage:** Was passiert, wenn ein Sibling-Repo eine `CLAUDE.md`,
aber kein `README.md` hat? (Antwort: `readme` wird `None`, der Titel fällt auf
den Verzeichnisnamen zurück, `CLAUDE.md`-Inhalt geht trotzdem in den Snapshot.)

### Station 2 — Context-Stuffing statt Vektor-RAG: `src/second_brain/answering.py`

`build_prompt(snapshot, include_handover)` (Zeile 28) baut **einen einzigen**
System-Prompt: für jedes Projekt im Snapshot werden README/CLAUDE.md (und
optional HANDOVER.md) als Markdown-Abschnitte aneinandergehängt
(`_format_project`, Zeile 17), getrennt durch `---`. Kein Embedding, keine
Ähnlichkeitssuche, kein Chunking — die komplette Doku aller 8 Projekte geht
bei jeder einzelnen Chat-Frage komplett mit ins Prompt. `answer_question()`
(Zeile 41) schickt das als `("system", ...)`-Nachricht plus die Nutzerfrage
als `("human", ...)` ans LLM.

**Warum das eine bewusste Entscheidung ist, nicht Faulheit:** Design-Spec
(`docs/superpowers/specs/2026-07-29-second-brain-design.md`, Abschnitt
"Antwortmechanismus") begründet es so: Bei ~8-10 Projekten mit überschaubarer
Doku passt alles in ein Prompt-Fenster, ein Retrieval-Schritt (Vektor-DB,
Embeddings) wäre unnötige Infrastruktur — und würde ein Signal duplizieren,
das das Schwesterprojekt `goz-finetune-vs-rag` ohnehin schon zeigt. Der
Kosten/Nutzen-Vergleich: Vektor-RAG lohnt sich, wenn der Corpus nicht mehr ins
Kontextfenster passt oder Latenz/Kosten durch weniger Input-Tokens gesenkt
werden sollen — bei acht kurzen READMEs ist beides kein Problem, Context-
Stuffing ist hier schlicht die einfachere und robustere Lösung.

**Selbstkontrollfrage:** Ab welchem Corpus-/Projektumfang würdest du auf
Vektor-RAG umsteigen, und was wäre der erste Umbau-Schritt? (Siehe Abschnitt 5
"Ehrliche Grenzen".)

### Station 3 — Der `include_handover`-Sicherheitsschalter: `answering.py` + `app.py` + `mcp_server.py`

Ursprünglich (laut Implementierungsplan, Task 6) gab es kein
`include_handover`-Flag — `build_prompt()` hat immer alle drei Dokumente
eingebaut. Ein **Whole-Branch-Review nach der Implementierung** deckte auf,
dass `HANDOVER.md` bei `cloud-native-pipeline` eine echte AWS-Account-ID und
IAM-Ressourcennamen enthält (Design-Spec, "Addendum" oben, sowie
`tests/test_answering.py::test_build_prompt_includes_handover_by_default`,
das genau diesen Fall mit der Beispiel-ID `840385630706` testet). Diese Info
ist im jeweiligen Repo bereits öffentlich, aber ein interaktiver Chat macht
sie deutlich leichter auffindbar. Lösung: `include_handover: bool = True` als
Parameter in `build_prompt()`/`answer_question()`, `app.py` (öffentlicher
Chat) setzt ihn explizit auf `False` (Zeile 55 in `app.py`), `mcp_server.py`
(nur lokal bei Marco) lässt den Default `True` stehen.

**Selbstkontrollfrage:** Warum reicht "die Datei ist im Repo ja eh schon
öffentlich" als Rechtfertigung nicht aus, um HANDOVER.md unverändert in den
öffentlichen Chat zu stuffen? (Antwort: Auffindbarkeit ist nicht dasselbe wie
Öffentlichkeit — ein interaktiver Chat, der auf Nachfrage Account-IDs
zitiert, senkt die Hürde drastisch gegenüber "man müsste das Repo klonen und
die Datei gezielt öffnen".)

### Station 4 — Provider-agnostische LLM-Anbindung: `src/second_brain/llm.py`

`get_llm()` (Zeile 18) liest `LLM_PROVIDER`/`LLM_MODEL` aus der `.env` und
ruft `init_chat_model(model, model_provider=provider)` — LangChains
einheitliche Fabrik-Funktion, die je nach Provider-String automatisch das
passende Integrationspaket (`langchain-anthropic` oder `langchain-openai`)
lädt und in beiden Fällen dasselbe `BaseChatModel`-Interface liefert. Kein
Modellname ist hart im Code verdrahtet — bewusst, weil sich Modell-IDs häufig
ändern (Kommentar in `.env.example`: "aktuelle Modell-IDs bitte in der Doku
des Anbieters nachschauen"). Fehlt `LLM_PROVIDER`/`LLM_MODEL`, wirft die
Funktion einen `RuntimeError` mit klarer Fehlermeldung statt eines kryptischen
Stacktraces weiter unten im Call-Stack.

**Selbstkontrollfrage:** Was müsstest du ändern, um einen dritten Provider
(z.B. Mistral) zu unterstützen? (Antwort: im Prinzip nichts im Code — nur
`langchain-mistralai` installieren und `LLM_PROVIDER=mistralai` in der `.env`
setzen, sofern LangChain den Provider-String kennt.)

### Station 5 — MCP-Server: `src/second_brain/mcp_server.py`

`mcp = MCPServer("second-brain")` registriert zwei Tools per Decorator:
`list_projects()` (Zeile 12, gibt eine kompakte Liste `{id, title,
repo_path}` zurück) und `ask_about_projects(question)` (Zeile 19, lädt den
Snapshot, holt sich ein LLM über `get_llm()` und delegiert an
`answer_question()` mit `include_handover=True`, weil der Server nur lokal
bei Marco läuft). `mcp.run()` startet den Server über stdio-Transport — das
ist das Protokoll, über das Claude Code/Desktop lokale MCP-Server anspricht.
Getestet wird das **ohne** echten MCP-Client: `tests/test_mcp_server.py`
importiert das Modul direkt und ruft die Python-Funktionen unter dem
Decorator auf (`monkeypatch` ersetzt `load_snapshot`/`get_llm`/
`answer_question`) — ein Beleg dafür, dass die `MCPServer.tool()`-Decorators
bewusst so gewählt wurden, dass sie die Originalfunktion unverändert
zurückgeben (siehe Commit `ae9edfa`).

**Selbstkontrollfrage:** Warum kann `tests/test_mcp_server.py` die Tools
direkt als normale Python-Funktionen aufrufen, obwohl sie mit `@mcp.tool()`
dekoriert sind? (Antwort: Der Decorator registriert die Funktion beim
MCP-Server, gibt sie aber unverändert zurück — anders als ein Decorator, der
das Funktionsobjekt ersetzt oder wrappt.)

---

## 5. Ehrliche Grenzen

- **Skalierung von Context-Stuffing:** README + `.env.example` + Design-Spec
  nennen das Problem explizit ("Kein Vektor-RAG — bei stark wachsender
  Projektzahl würde der Snapshot irgendwann nicht mehr komplett ins Prompt
  passen (aktuell bei 8 Projekten kein Problem)."). Es gibt aber **keinen
  dokumentierten konkreten Schwellenwert oder Migrationsplan** — kein
  "ab X Projekten/Y Tokens steigen wir auf Retrieval um". Das ist eine ehrliche
  Lücke: Wenn im Interview gefragt wird "was würdest du bei 50 Projekten
  machen?", ist die ehrliche Antwort "noch nicht im Detail durchdacht, aber
  der nächste Schritt wäre vermutlich Chunking + Embeddings pro Projekt-Doku
  plus ein Retrieval-Schritt vor dem Prompt-Aufbau — genau das Muster, das
  `goz-finetune-vs-rag` bereits zeigt", nicht ein vorgetäuschtes fertiges
  Konzept.
- **Snapshot-Staleness ist bewusst in Kauf genommen, nicht gelöst:** Kein
  Auto-Rebuild, keine CI (weil `02_Portfolio` selbst kein gemeinsames Git-Repo
  ist). Ändert sich ein README in einem anderen Projekt, weiß der Chat davon
  erst nach manuellem Rebuild + Commit von `data/snapshot.json`.
- **Fehlende `demo_url`/`repo_url`/`status`-Felder** (siehe Abschnitt 2) sind
  ein konkreter, kleiner offener Task — nicht kritisch für die Kernidee, aber
  eine sichtbare Lücke, wenn ein Recruiter im Chat nach einem klickbaren Link
  fragt.
- **Keine Volltext-Code-Suche:** Der Bot kennt nur Projekt-Metadaten/Doku
  (README/CLAUDE.md/HANDOVER), keine Implementierungsdetails aus dem
  jeweiligen Quellcode.
- **Die Portfolio-Karte in `marco-os` ist nicht synchron mit dem echten
  Repo-Stand** (siehe "Wichtigster Fund" oben) — ein Punkt, den Marco vor
  einem Interview selbst beheben sollte, sonst widerspricht die eigene
  Portfolio-Seite dem, was im Interview gezeigt wird.

---

## 6. Recruiter-Simulation

**F1: "Zeig mir das mal live."**
A: Live-Demo unter second-brain-projects.streamlit.app zeigen (Hinweis:
Streamlit Community Cloud Free Tier schläft nach Inaktivität ein, erster
Ladevorgang kann ein paar Sekunden dauern). Alternativ: MCP-Server lokal in
Claude Code zeigen, `list_projects`/`ask_about_projects` live aufrufen.

**F2: "Warum kein Vektor-RAG, ist das nicht der Standard für sowas?"**
A: Bewusste Entscheidung, kein Wissensdefizit — bei acht Projekten mit
überschaubarer Doku passt alles ins Prompt-Fenster, ein Retrieval-Schritt wäre
unnötige Infrastruktur und würde ein Signal duplizieren, das `goz-finetune-
vs-rag` bereits zeigt. Kosten/Nutzen: Vektor-RAG lohnt sich erst, wenn der
Corpus nicht mehr reinpasst oder Latenz/Kosten durch weniger Tokens gesenkt
werden müssen.

**F3: "Was passiert, wenn du 100 Projekte hättest?"**
A: Ehrlich zugeben, dass es dafür noch kein ausgearbeitetes Konzept gibt
(siehe Abschnitt 5), aber den naheliegenden nächsten Schritt benennen:
Chunking + Embeddings pro Projekt, Retrieval vor dem Prompt-Aufbau — nicht so
tun, als sei das schon gelöst.

**F4: "Wie stellst du sicher, dass der Chat keine sensiblen Daten
preisgibt?"**
A: Konkretes Beispiel erzählen: HANDOVER.md von `cloud-native-pipeline` enthält
eine echte AWS-Account-ID, das wurde in einem selbst durchgeführten
Whole-Branch-Review entdeckt und über ein `include_handover`-Flag behoben
(öffentlicher Chat sieht kein HANDOVER.md mehr, nur der lokale MCP-Server).
Zeigt sowohl technisches Verständnis als auch Selbstkritik/Review-Disziplin.

**F5: "Ist das Projekt fertig?"**
A: Ehrlich differenzieren: Kernfunktionalität (Snapshot, Chat, MCP-Server) ist
fertig, getestet (15/15 Tests grün) und live deployed. Es gibt aber noch einen
offenen kleinen Punkt (Demo-/Repo-Links fehlen im Snapshot-Schema) und die
eigene Portfolio-Seite (marco-os) zeigt noch den alten "in Arbeit"-Stand — das
ist ein Beleg dafür, dass ich meinen eigenen Fortschritt realistisch
einschätze, statt pauschal "fertig" oder "noch nicht angefangen" zu sagen.

**F6: "Wie hast du entschieden, welche Doku in den Snapshot kommt?"**
A: Nur README.md, CLAUDE.md, HANDOVER.md pro Repo — bewusst **ohne**
`docs/superpowers/specs/`/`plans/`-Dateien, weil das Implementierungsdetails
sind (Task-Listen, Zwischenentscheidungen), die kein Recruiter fragt. README +
CLAUDE.md sind ohnehin schon auf Verständlichkeit für Außenstehende getrimmt.

**F7: "Warum zwei Frontends (Chat + MCP) statt nur einem?"**
A: Zwei unterschiedliche Zielgruppen mit unterschiedlichen
Sicherheits-/Zugriffsanforderungen: Recruiter brauchen einen öffentlichen,
niedrigschwelligen Chat ohne Betriebsdetails; ich selbst will dasselbe Wissen
direkt in meinem Editor/Claude Code abrufbar haben, inklusive interner Doku
wie HANDOVER.md. Beide teilen sich dieselbe `answer_question()`-Logik, nur
mit unterschiedlichem `include_handover`-Flag — kein doppelt gepflegter Code.

**F8: "Was war die größte technische Überraschung beim Bauen?"**
A: Der Implementierungsplan sah `FastMCP` aus `mcp.server.fastmcp` vor — die
tatsächlich installierte `mcp`-Paketversion hatte diese Klasse nicht mehr.
Musste auf `MCPServer` aus `mcp.server.mcpserver` umsteigen, die dieselbe
Decorator-Semantik bietet. Kleines, aber reales Beispiel dafür, dass Pläne
gegen echte Library-Versionen verifiziert werden müssen, nicht nur gegen
Pseudocode.

---

## 7. Checkliste — Bist du bereit?

- [ ] Ich kann den Elevator-Pitch (Abschnitt 1) frei sprechen, ohne
      abzulesen.
- [ ] Ich kann erklären, warum Context-Stuffing hier bewusst statt Vektor-RAG
      gewählt wurde — inklusive Kosten/Nutzen-Abwägung (Station 2).
- [ ] Ich kann den `include_handover`-Sicherheitsfall (AWS-Account-ID in
      HANDOVER.md) im Detail erzählen, inklusive warum das trotz "Datei ist
      eh schon öffentlich im Repo" ein echtes Risiko war (Station 3).
- [ ] Ich kann zeigen, wie der Snapshot gebaut wird und was passiert, wenn
      ein Repo kein README hat (Station 1).
- [ ] Ich kann den MCP-Server live vorführen oder zumindest genau erklären,
      was `list_projects`/`ask_about_projects` tun (Station 5).
- [ ] Ich weiß, was NICHT fertig ist (fehlende demo_url/repo_url im Schema,
      kein Auto-Rebuild, kein Skalierungskonzept jenseits ~8-10 Projekten)
      und kann das ohne Beschönigung zugeben (Abschnitt 5).
- [ ] Ich habe geprüft/erinnere mich daran, dass `marco-os/data/projects.js`
      noch den alten "planned"-Stand zeigt, und weiß, dass das vor einem
      Interview idealerweise aktualisiert werden sollte.
- [ ] Ich kann mindestens 3 der Recruiter-Fragen aus Abschnitt 6 aus dem
      Stegreif beantworten, ohne diese Datei nochmal zu öffnen.
