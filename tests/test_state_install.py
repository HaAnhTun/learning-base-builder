"""Tests for the project-state installer (.claude/skills/project-state/scripts/install.py)."""
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "project-state"
spec = importlib.util.spec_from_file_location("state_install", SKILL / "scripts" / "install.py")
inst = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inst)


@pytest.fixture
def project(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def settings(project):
    return json.loads((project / ".claude" / "settings.json").read_text(encoding="utf-8"))


def ours(entries):
    return [e for e in entries if any("state_hook.py" in " ".join(h.get("args", [])) for h in e["hooks"])]


def test_creates_state_files_from_templates(project):
    inst.install(project, skill_dir=SKILL)
    state = (project / ".claude/state/STATE.md").read_text(encoding="utf-8")
    assert "## Goal & scope" in state and "## Next" in state
    assert "updated: " in state and "<today>" not in state
    assert (project / ".claude/state/DECISIONS.md").exists()


def test_existing_state_is_never_overwritten(project):
    (project / ".claude/state").mkdir(parents=True)
    (project / ".claude/state/STATE.md").write_text("mine", encoding="utf-8")
    inst.install(project, skill_dir=SKILL)
    assert (project / ".claude/state/STATE.md").read_text(encoding="utf-8") == "mine"


def test_registers_three_hook_events_in_exec_form(project):
    inst.install(project, skill_dir=SKILL)
    hooks = settings(project)["hooks"]
    assert set(hooks) >= {"SessionStart", "Stop", "PreCompact"}
    start = ours(hooks["SessionStart"])[0]
    assert start["matcher"] == "startup|resume|clear|compact"
    cmd = start["hooks"][0]
    assert cmd["type"] == "command" and cmd["command"] == "python"
    assert cmd["args"][0].startswith("${CLAUDE_PROJECT_DIR}/.claude/skills/project-state/scripts/")
    assert cmd["args"][1] == "session-start"


def test_install_is_idempotent(project):
    inst.install(project, skill_dir=SKILL)
    inst.install(project, skill_dir=SKILL)
    hooks = settings(project)["hooks"]
    assert all(len(ours(hooks[event])) == 1 for event in ("SessionStart", "Stop", "PreCompact"))
    claude_md = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude_md.count("project-state:begin") == 1


def test_merge_keeps_foreign_settings_and_hooks(project):
    (project / ".claude").mkdir()
    existing = {"permissions": {"allow": ["Bash(ls)"]},
                "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo", "args": ["hi"]}]}]}}
    (project / ".claude/settings.json").write_text(json.dumps(existing), encoding="utf-8")
    inst.install(project, skill_dir=SKILL)
    merged = settings(project)
    assert merged["permissions"] == existing["permissions"]
    assert any(h["command"] == "echo" for e in merged["hooks"]["Stop"] for h in e["hooks"])
    assert len(ours(merged["hooks"]["Stop"])) == 1


def test_claude_md_block_is_appended_without_touching_existing_text(project):
    (project / "CLAUDE.md").write_text("# Mine\n\nKeep me.\n", encoding="utf-8")
    inst.install(project, skill_dir=SKILL)
    text = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith("# Mine\n\nKeep me.\n")
    assert ".claude/state/STATE.md" in text
    for name in ("context-discipline", "prompt-craft", "agent-orchestration"):
        assert name not in text  # user-invoked reference skills are not advertised in CLAUDE.md


def test_claude_md_block_is_replaced_in_place_on_reinstall(project):
    (project / "CLAUDE.md").write_text("# Mine\n", encoding="utf-8")
    inst.install(project, skill_dir=SKILL)
    path = project / "CLAUDE.md"
    path.write_text(path.read_text(encoding="utf-8").replace("Rewrite the blocks", "OLD WORDING")
                    + "\n## After\nkeep\n", encoding="utf-8")
    inst.install(project, skill_dir=SKILL)
    text = path.read_text(encoding="utf-8")
    assert "OLD WORDING" not in text and text.count("project-state:begin") == 1
    assert text.rstrip().endswith("keep")


def test_malformed_settings_json_aborts_without_writing(project):
    (project / ".claude").mkdir()
    (project / ".claude/settings.json").write_text("{ not json", encoding="utf-8")
    with pytest.raises(ValueError):
        inst.install(project, skill_dir=SKILL)
    assert (project / ".claude/settings.json").read_text(encoding="utf-8") == "{ not json"
