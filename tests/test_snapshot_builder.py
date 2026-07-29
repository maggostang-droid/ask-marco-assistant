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
