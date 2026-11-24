"""Tests for the project-state hook script (.claude/skills/project-state/scripts/state_hook.py)."""
import importlib.util
import io
import json
import os
import subprocess
import time
from datetime import date
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "project-state" / "scripts" / "state_hook.py"
spec = importlib.util.spec_from_file_location("state_hook", SCRIPT)
sh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sh)

TODAY = date(2026, 11, 24)


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("a")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "first")
    return tmp_path


def head(repo):
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True,
                          text=True, check=True).stdout.strip()


def write_state(repo, body="## Goal & scope\nShip the thing.\n", updated="2026-11-23", head_sha=None):
    d = repo / ".claude" / "state"
    d.mkdir(parents=True, exist_ok=True)
    text = f"# Project state\nupdated: {updated}\nhead: {head_sha or head(repo)}\n\n{body}"
    p = d / "STATE.md"
    p.write_text(text, encoding="utf-8")
    return p


def ctx(result):
    return result["hookSpecificOutput"]["additionalContext"]


# --- session-start -------------------------------------------------------------------------

def test_session_start_without_state_points_to_init(repo):
    out = sh.build_session_start({"source": "startup"}, repo, TODAY)
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "project-state init" in ctx(out)


def test_session_start_injects_state_and_decisions_pointer(repo):
    write_state(repo)
    text = ctx(sh.build_session_start({"source": "startup"}, repo, TODAY))
    assert "Ship the thing." in text
    assert ".claude/state/DECISIONS.md" in text


def test_startup_announces_but_compact_does_not(repo):
    write_state(repo)
    assert "Vietnamese" in ctx(sh.build_session_start({"source": "startup"}, repo, TODAY))
    compact = ctx(sh.build_session_start({"source": "compact"}, repo, TODAY))
    assert "do not re-announce" in compact.lower()


def test_old_state_is_flagged_stale(repo):
    write_state(repo, updated="2026-10-01")
    assert "STALE:" in ctx(sh.build_session_start({"source": "startup"}, repo, TODAY))


def test_fresh_state_has_no_warning(repo):
    write_state(repo, updated="2026-11-23")
    assert "STALE:" not in ctx(sh.build_session_start({"source": "startup"}, repo, TODAY))


def test_unknown_head_is_flagged(repo):
    write_state(repo, head_sha="deadbee")
    assert "STALE:" in ctx(sh.build_session_start({"source": "startup"}, repo, TODAY))


def test_head_drift_is_flagged(repo):
    write_state(repo)
    for i in range(3):
        (repo / f"f{i}.txt").write_text("x")
        git(repo, "add", ".")
        git(repo, "commit", "-q", "-m", f"c{i}")
    out = sh.build_session_start({"source": "startup"}, repo, TODAY, drift_threshold=2)
    assert "STALE:" in ctx(out)


def test_oversized_state_is_truncated_with_note(repo):
    write_state(repo, body="line\n" * 5000)
    text = ctx(sh.build_session_start({"source": "startup"}, repo, TODAY))
    assert len(text) < 10_000
    assert "truncated" in text.lower()


# --- secret scan ---------------------------------------------------------------------------

@pytest.mark.parametrize("line", [
    "key: AKIAABCDEFGHIJKLMNOP",
    "token ghp_" + "a" * 36,
    "-----BEGIN RSA PRIVATE KEY-----",
    "access_token: abcdef0123456789abcdef0123456789",
    "password = 'hunter2hunter2hunter2'",
    "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijklmnop",
])
def test_find_secrets_detects_common_shapes(line):
    assert sh.find_secrets("ok line\n" + line + "\n")[0][0] == 2


def test_find_secrets_ignores_plain_prose():
    assert sh.find_secrets("Decided to store the token in config.local.yaml, never in git.\n") == []


# --- stop ----------------------------------------------------------------------------------

def stale_dirty_repo(repo):
    state = write_state(repo)
    old = time.time() - 3600
    os.utime(state, (old, old))
    (repo / "work.py").write_text("print(1)")
    return state


def test_stop_ignores_continuation_turns(repo, tmp_path):
    stale_dirty_repo(repo)
    payload = {"stop_hook_active": True, "session_id": "s1"}
    assert sh.stop_decision(payload, repo, tmp_path / "m") is None


def test_stop_silent_when_no_state_file(repo, tmp_path):
    (repo / "work.py").write_text("x")
    assert sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m") is None


def test_stop_silent_on_clean_tree(repo, tmp_path):
    write_state(repo)
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "state")
    assert sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m") is None


def test_stop_blocks_once_when_state_older_than_work(repo, tmp_path):
    stale_dirty_repo(repo)
    marker = tmp_path / "m"
    first = sh.stop_decision({"session_id": "s1"}, repo, marker)
    assert first["decision"] == "block"
    assert "STATE.md" in first["reason"]
    assert sh.stop_decision({"session_id": "s1"}, repo, marker) is None
    assert sh.stop_decision({"session_id": "s2"}, repo, marker)["decision"] == "block"


def test_stop_silent_when_state_newer_than_work(repo, tmp_path):
    (repo / "work.py").write_text("x")
    old = time.time() - 3600
    os.utime(repo / "work.py", (old, old))
    write_state(repo)
    assert sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m") is None


def test_state_files_themselves_do_not_count_as_work(repo, tmp_path):
    state = write_state(repo)
    decisions = state.parent / "DECISIONS.md"
    decisions.write_text("x")
    old = time.time() - 3600
    os.utime(state, (old, old))
    assert sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m") is None


def test_stop_nudges_when_state_over_line_cap(repo, tmp_path):
    write_state(repo, body="row\n" * 120)
    out = sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m")
    assert out["decision"] == "block"
    assert "archive" in out["reason"]


def test_stop_blocks_on_secret_every_time_without_echoing_it(repo, tmp_path):
    secret = "ghp_" + "b" * 36
    write_state(repo, body=f"note: {secret}\n")
    marker = tmp_path / "m"
    for _ in range(2):
        out = sh.stop_decision({"session_id": "s1"}, repo, marker)
        assert out["decision"] == "block"
        assert secret not in out["reason"]
        assert "STATE.md:5" in out["reason"]


# --- pre-compact and entry point -----------------------------------------------------------

def test_pre_compact_text_protects_state():
    text = sh.pre_compact_text()
    assert "STATE.md" in text and "verbatim" in text


def run_main(argv, payload, repo, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    out = io.StringIO()
    code = sh.main(argv, io.StringIO(payload if isinstance(payload, str) else json.dumps(payload)), out)
    return code, out.getvalue()


def test_main_session_start_prints_json(repo, monkeypatch):
    write_state(repo)
    code, out = run_main(["session-start"], {"source": "startup"}, repo, monkeypatch)
    assert code == 0
    assert "Ship the thing." in json.loads(out)["hookSpecificOutput"]["additionalContext"]


def test_main_never_fails_on_garbage_input(repo, monkeypatch):
    for sub in ("session-start", "stop", "pre-compact"):
        code, _ = run_main([sub], "not json", repo, monkeypatch)
        assert code == 0


def test_main_unknown_subcommand_is_harmless(repo, monkeypatch):
    code, out = run_main(["bogus"], {}, repo, monkeypatch)
    assert code == 0 and out == ""
