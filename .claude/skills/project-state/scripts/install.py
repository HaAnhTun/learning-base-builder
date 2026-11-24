#!/usr/bin/env python3
"""Install the project-state files and hooks into a project (stdlib only).

Usage: python install.py [project_dir]

Creates .claude/state/{STATE.md,DECISIONS.md} when missing, merges the three hooks into
.claude/settings.json without touching other keys, and writes the working-agreement block into CLAUDE.md.
Safe to run again: it replaces its own entries and never overwrites existing state.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
BLOCK_RE = re.compile(r"<!-- project-state:begin -->.*?<!-- project-state:end -->", re.S)
HOOK_SCRIPT = "${CLAUDE_PROJECT_DIR}/.claude/skills/project-state/scripts/state_hook.py"
HOOKS = {
    "SessionStart": ("startup|resume|clear|compact", "session-start"),
    "Stop": (None, "stop"),
    "PreCompact": (None, "pre-compact"),
}


def _head(project_dir):
    try:
        proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=project_dir, capture_output=True,
                              text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else "unknown"


def _is_ours(entry):
    return any("state_hook.py" in " ".join(h.get("args", [])) for h in entry.get("hooks", []))


def _merge_settings(path):
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ValueError(f"{path} is not valid JSON ({exc}); fix it first") from exc
        if not isinstance(data, dict):
            raise ValueError(f"{path} must hold a JSON object")
    else:
        data = {}
    hooks = data.setdefault("hooks", {})
    for event, (matcher, sub) in HOOKS.items():
        entries = [e for e in hooks.get(event, []) if not _is_ours(e)]
        entry = {"hooks": [{"type": "command", "command": "python", "args": [HOOK_SCRIPT, sub], "timeout": 15}]}
        if matcher:
            entry = {"matcher": matcher, **entry}
        hooks[event] = entries + [entry]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_claude_md(path, block):
    block = block.strip()
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if BLOCK_RE.search(text):
            text = BLOCK_RE.sub(lambda _m: block, text)
        else:
            text = text.rstrip("\n") + "\n\n" + block + "\n"
    else:
        text = block + "\n"
    path.write_text(text, encoding="utf-8")


def install(project_dir, skill_dir=SKILL_DIR):
    project_dir, skill_dir = Path(project_dir), Path(skill_dir)
    settings_path = project_dir / ".claude" / "settings.json"
    _merge_settings(settings_path)  # validates settings first; nothing else is written if it raises

    state_dir = project_dir / ".claude" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    assets = skill_dir / "assets"
    state = state_dir / "STATE.md"
    if not state.exists():
        text = (assets / "STATE.template.md").read_text(encoding="utf-8")
        state.write_text(text.replace("<today>", date.today().isoformat()).replace("<head>", _head(project_dir)),
                         encoding="utf-8")
    decisions = state_dir / "DECISIONS.md"
    if not decisions.exists():
        decisions.write_text((assets / "DECISIONS.template.md").read_text(encoding="utf-8"), encoding="utf-8")
    _write_claude_md(project_dir / "CLAUDE.md", (assets / "CLAUDE-block.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    try:
        install(target)
    except ValueError as exc:
        sys.exit(str(exc))
    print(f"project-state installed in {Path(target).resolve()}")
