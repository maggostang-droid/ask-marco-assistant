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
