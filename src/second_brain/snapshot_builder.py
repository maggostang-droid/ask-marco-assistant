"""Baut den Portfolio-Snapshot aus README/CLAUDE.md/HANDOVER der Sibling-Repos unter 02_Portfolio."""

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from second_brain.snapshot import DEFAULT_SNAPSHOT_PATH, Project, Snapshot

# Nur korrekt, wenn second-brain direkt unter 02_Portfolio/ liegt (nicht in einem
# Git-Worktree wie second-brain/.worktrees/<name>/). Für abweichende Layouts
# SECOND_BRAIN_PORTFOLIO_ROOT setzen (siehe main()).
PORTFOLIO_ROOT = DEFAULT_SNAPSHOT_PATH.parents[2]

PORTFOLIO_ROOT_ENV_VAR = "SECOND_BRAIN_PORTFOLIO_ROOT"

MIN_EXPECTED_PROJECTS = 3

#: Verzeichnisnamen dieses Repos selbst - es gehört nicht in seinen eigenen
#: Snapshot. Zwei Einträge, weil der lokale Ordner im August 2026 von
#: "second-brain" auf den GitHub-Namen "ask-marco-assistant" umbenannt wurde;
#: der alte Name bleibt drin, damit ältere Arbeitskopien weiter korrekt bauen.
#: Der Ausschluss geht über den Namen und nicht über eine Marker-Datei, weil
#: der Builder auch über gespiegelte Bäume läuft, die nur die .md-Dateien
#: enthalten (siehe SECOND_BRAIN_PORTFOLIO_ROOT).
SELF_DIR_NAMES = {"second-brain", "ask-marco-assistant"}

#: Nicht mehr verfolgte Konzepte. Beide liegen ggf. noch als Ordner unter
#: 02_Portfolio und haben eine CLAUDE.md, wären also weiter eingesammelt worden
#: — der Chat hätte sie Recruitern als aktuelle Portfolio-Projekte präsentiert.
#: Am 03.08.2026 eingestellt: marco-os ist das Portfolio.
RETIRED_DIR_NAMES = {"stangfolio", "stangverse"}

EXCLUDED_DIR_NAMES = SELF_DIR_NAMES | RETIRED_DIR_NAMES


def discover_projects(portfolio_root: Path) -> list[Path]:
    """Findet alle Sibling-Verzeichnisse mit einer CLAUDE.md.

    Ausgenommen sind dieses Repo selbst und eingestellte Konzepte
    (siehe EXCLUDED_DIR_NAMES).
    """
    return sorted(
        d
        for d in portfolio_root.iterdir()
        if d.is_dir() and d.name not in EXCLUDED_DIR_NAMES and (d / "CLAUDE.md").exists()
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


def _write_snapshot(portfolio_root: Path) -> None:
    """Baut den Snapshot und schreibt ihn nach DEFAULT_SNAPSHOT_PATH.

    Bricht mit sys.exit(1) ab, statt eine verdächtig kleine Projektzahl
    (z.B. weil portfolio_root falsch ist — etwa in einem Git-Worktree) einfach
    über data/snapshot.json zu schreiben.
    """
    snapshot = build_snapshot(portfolio_root)

    if len(snapshot.projects) < MIN_EXPECTED_PROJECTS:
        print(
            f"Fehler: Nur {len(snapshot.projects)} Projekt(e) unter {portfolio_root} "
            f"gefunden (erwartet: mindestens {MIN_EXPECTED_PROJECTS}). Das sieht falsch "
            "aus — data/snapshot.json wird NICHT überschrieben.\n"
            "Möglicher Grund: Dieses Repo liegt nicht direkt unter 02_Portfolio/ (z.B. "
            "weil es sich um einen Git-Worktree wie second-brain/.worktrees/<name>/ "
            f"handelt). In dem Fall {PORTFOLIO_ROOT_ENV_VAR} auf den echten "
            "02_Portfolio-Pfad setzen und erneut ausführen.",
            file=sys.stderr,
        )
        sys.exit(1)

    DEFAULT_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_SNAPSHOT_PATH.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    print(f"{len(snapshot.projects)} Projekte in {DEFAULT_SNAPSHOT_PATH} geschrieben.")


def main() -> None:
    override = os.environ.get(PORTFOLIO_ROOT_ENV_VAR)
    portfolio_root = Path(override) if override else PORTFOLIO_ROOT
    _write_snapshot(portfolio_root)


if __name__ == "__main__":
    main()
