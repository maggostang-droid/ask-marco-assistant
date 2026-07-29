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
