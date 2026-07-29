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
