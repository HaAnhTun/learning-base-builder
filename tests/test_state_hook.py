"""Tests for the project-state hook script (.claude/skills/project-state/scripts/state_hook.py)."""
import importlib.util
import io
import json
import os
import re
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


VALID_SECTIONS = {
    "Goal & scope": "Ship the thing.\n",
    "Current state": "Skeleton in place.\n",
    "In progress": "- (none)\n",
    "Next": "1. Write the first test.\n",
    "Done": "- 2026-11-23 Set up the repo (git log shows the first commit).\n",
    "Open questions": "- (none)\n",
    "Constraints & gotchas": "None yet.\n",
    "Last session": "Set up the repo; nothing half-done; start with the first test.\n",
}


def build_body(overrides=None):
    """A STATE.md body with every template section; `overrides` maps a section name to its new content."""
    sections = {**VALID_SECTIONS, **(overrides or {})}
    return "\n".join(f"## {name}\n{content}" for name, content in sections.items())


VALID_BODY = build_body()


def state_text(body=VALID_BODY, updated="2026-11-23", head_sha="abc1234"):
    return f"# Project state\nupdated: {updated}\nhead: {head_sha}\n\n{body}"


def write_state(repo, body=VALID_BODY, updated="2026-11-23", head_sha=None):
    d = repo / ".claude" / "state"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "STATE.md"
    p.write_text(state_text(body, updated, head_sha or head(repo)), encoding="utf-8")
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
    startup = ctx(sh.build_session_start({"source": "startup"}, repo, TODAY))
    assert "2-3 lines in the user's language" in startup
    assert "Vietnamese" not in startup
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
    write_state(repo, body=VALID_BODY + "line\n" * 5000)
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


# --- structure lint ------------------------------------------------------------------------

def dated_items(n):
    return "".join(f"- 2026-11-{i:02d} finished item {i}\n" for i in range(1, n + 1))


def test_valid_state_has_no_structure_problems():
    assert sh.structure_problems(state_text()) == []


@pytest.mark.parametrize("name", list(VALID_SECTIONS))
def test_each_missing_section_is_reported(name):
    problems = sh.structure_problems(state_text(VALID_BODY.replace(f"## {name}\n", "")))
    assert len(problems) == 1
    assert f"## {name}" in problems[0]


@pytest.mark.parametrize("header", [
    "updated: <today>", "updated: 2026-13-45", "updated: yesterday", "",
])
def test_missing_or_invalid_updated_line_is_reported(header):
    text = state_text().replace("updated: 2026-11-23\n", header + "\n" if header else "")
    problems = sh.structure_problems(text)
    assert len(problems) == 1
    assert "updated:" in problems[0]


@pytest.mark.parametrize("header", ["head: <head>", "head: not-a-sha", ""])
def test_missing_or_invalid_head_line_is_reported(header):
    text = state_text().replace("head: abc1234\n", header + "\n" if header else "")
    problems = sh.structure_problems(text)
    assert len(problems) == 1
    assert "head:" in problems[0]


def test_head_unknown_from_a_non_git_install_is_valid():
    assert sh.structure_problems(state_text(head_sha="unknown")) == []


def test_done_cap_is_ten_items():
    assert sh.structure_problems(state_text(build_body({"Done": dated_items(10)}))) == []
    problems = sh.structure_problems(state_text(build_body({"Done": dated_items(11)})))
    assert len(problems) == 1
    assert "Done" in problems[0] and "11" in problems[0]


def test_done_none_marker_and_other_sections_do_not_count():
    body = build_body({"Done": "- (none)\n", "In progress": dated_items(12)})
    assert sh.structure_problems(state_text(body)) == []


def test_next_cap_is_seven_items():
    def steps(n):
        return "".join(f"{i}. step {i}\n" for i in range(1, n + 1))
    assert sh.structure_problems(state_text(build_body({"Next": steps(7)}))) == []
    problems = sh.structure_problems(state_text(build_body({"Next": steps(8)})))
    assert len(problems) == 1
    assert "Next" in problems[0] and "8" in problems[0]


def test_numbered_lines_outside_next_do_not_count():
    notes = "".join(f"{i}. gotcha {i}\n" for i in range(1, 10))
    assert sh.structure_problems(state_text(build_body({"Constraints & gotchas": notes}))) == []


def test_empty_text_reports_every_section_and_both_headers():
    problems = sh.structure_problems("")
    assert len(problems) == len(VALID_SECTIONS) + 2
    assert any("updated:" in p for p in problems) and any("head:" in p for p in problems)


def messy(text, how):
    if how == "crlf":
        return text.replace("\n", "\r\n")
    if how == "trailing spaces":
        return re.sub(r"(?m)^(.*)$", r"\1  ", text)
    if how == "extra blank lines":
        return text.replace("\n", "\n\n")
    return messy(messy(text, "trailing spaces"), "crlf").replace("\r\n", "\r\n\r\n")


@pytest.mark.parametrize("how", ["crlf", "trailing spaces", "extra blank lines", "all three"])
def test_valid_state_stays_valid_under_messy_whitespace(how):
    assert sh.structure_problems(messy(state_text(), how)) == []


@pytest.mark.parametrize("how", ["crlf", "trailing spaces", "extra blank lines", "all three"])
def test_caps_and_missing_sections_are_still_found_under_messy_whitespace(how):
    body = build_body({"Done": dated_items(11), "Next": "".join(f"{i}. s\n" for i in range(1, 9))})
    body = body.replace("## Open questions\n", "")
    problems = sh.structure_problems(messy(state_text(body), how))
    assert len(problems) == 3
    assert any("## Open questions" in p for p in problems)
    assert any("Done" in p for p in problems) and any("Next" in p for p in problems)


def test_state_template_passes_the_lint_once_placeholders_are_filled():
    template = SCRIPT.parent.parent / "assets" / "STATE.template.md"
    text = template.read_text(encoding="utf-8").replace("<today>", TODAY.isoformat()).replace("<head>", "abc1234")
    assert sh.structure_problems(text) == []
    assert sh.structure_problems(template.read_text(encoding="utf-8")) != []  # unfilled headers are caught


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


def test_agent_worktrees_do_not_count_as_work(repo, tmp_path):
    state = write_state(repo)
    old = time.time() - 3600
    os.utime(state, (old, old))
    wt = repo / ".claude" / "worktrees" / "wf_1-1"
    wt.mkdir(parents=True)
    (wt / "f.txt").write_text("x")
    assert sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m") is None


def test_stop_nudges_when_state_over_line_cap(repo, tmp_path):
    write_state(repo, body=VALID_BODY + "row\n" * 120)
    out = sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m")
    assert out["decision"] == "block"
    assert "archive" in out["reason"]


def test_stop_blocks_on_secret_every_time_without_echoing_it(repo, tmp_path):
    secret = "ghp_" + "b" * 36
    write_state(repo, body=f"note: {secret}\n" + VALID_BODY)
    marker = tmp_path / "m"
    for _ in range(2):
        out = sh.stop_decision({"session_id": "s1"}, repo, marker)
        assert out["decision"] == "block"
        assert secret not in out["reason"]
        assert "STATE.md:5" in out["reason"]


def test_stop_secret_is_not_re_blocked_within_one_stop_chain(repo, tmp_path):
    # stop_hook_active is true while Claude Code continues because of a stop hook: the loop guard lets that stop
    # through even with the secret still present; the next turn blocks again.
    write_state(repo, body=f"note: {'ghp_' + 'e' * 36}\n" + VALID_BODY)
    marker = tmp_path / "m"
    assert sh.stop_decision({"stop_hook_active": True, "session_id": "s1"}, repo, marker) is None
    assert sh.stop_decision({"session_id": "s1"}, repo, marker)["decision"] == "block"


def test_stop_nudges_once_on_structure_problem(repo, tmp_path):
    write_state(repo, body=VALID_BODY.replace("## Open questions\n", ""))
    marker = tmp_path / "m"
    first = sh.stop_decision({"session_id": "s1"}, repo, marker)
    assert first["decision"] == "block"
    assert "## Open questions" in first["reason"]
    assert sh.stop_decision({"session_id": "s1"}, repo, marker) is None


def test_stop_ignores_structure_problem_on_continuation_turn(repo, tmp_path):
    write_state(repo, body=VALID_BODY.replace("## Open questions\n", ""))
    assert sh.stop_decision({"stop_hook_active": True, "session_id": "s1"}, repo, tmp_path / "m") is None


def test_stop_problems_share_one_nudge_per_session(repo, tmp_path):
    state = write_state(repo, body=VALID_BODY.replace("## Open questions\n", "") + "row\n" * 120)
    old = time.time() - 3600
    os.utime(state, (old, old))
    (repo / "work.py").write_text("print(1)")
    marker = tmp_path / "m"
    first = sh.stop_decision({"session_id": "s1"}, repo, marker)
    assert first["decision"] == "block"
    assert "lines (cap" in first["reason"]  # over the line cap
    assert "## Open questions" in first["reason"]  # structure
    assert "Files changed after STATE.md" in first["reason"]  # stale
    assert sh.stop_decision({"session_id": "s1"}, repo, marker) is None


def test_stop_secret_still_blocks_every_time_when_structure_is_also_broken(repo, tmp_path):
    secret = "ghp_" + "c" * 36
    write_state(repo, body=f"note: {secret}\n" + VALID_BODY.replace("## Done\n", ""))
    marker = tmp_path / "m"
    for _ in range(2):
        out = sh.stop_decision({"session_id": "s1"}, repo, marker)
        assert out["decision"] == "block"
        assert "STATE.md:5" in out["reason"] and secret not in out["reason"]


# --- check ---------------------------------------------------------------------------------

def test_check_report_for_a_healthy_state(repo):
    state = write_state(repo)
    report = sh.check_report(repo, TODAY)
    assert f"STATE.md: {len(state.read_text(encoding='utf-8').splitlines())} lines (cap 80)" in report
    assert "OVER" not in report
    assert "Structure: ok" in report and "Freshness: ok" in report and "Secrets: none" in report


def test_check_report_lists_every_kind_of_finding_without_the_secret(repo):
    secret = "ghp_" + "d" * 36
    write_state(repo, body=f"note: {secret}\n" + VALID_BODY.replace("## Done\n", "") + "row\n" * 120,
                updated="2026-10-01")
    report = sh.check_report(repo, TODAY)
    assert "OVER" in report  # line cap
    assert "## Done" in report  # structure
    assert "STALE:" in report  # freshness
    assert "STATE.md:5" in report  # secret location
    assert secret not in report


def test_check_report_never_echoes_a_secret_pasted_on_the_head_line(repo):
    secret = "ghp_" + "Z" * 36
    write_state(repo, head_sha=secret)
    report = sh.check_report(repo, TODAY)
    assert secret not in report
    assert "STALE: recorded head is not a valid sha." in report
    assert "STATE.md:3" in report  # the secret is still located


def test_session_start_never_echoes_a_malformed_head_in_its_warning(repo):
    write_state(repo, head_sha="--upload-pack=evil")
    warning = ctx(sh.build_session_start({"source": "startup"}, repo, TODAY)).split("Verify against")[0]
    assert "evil" not in warning and "not a valid sha" in warning


def write_state_bytes(repo, name, data):
    d = repo / ".claude" / "state"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_bytes(data)


def test_undecodable_state_files_still_get_a_report_and_a_secret_block(repo, tmp_path, monkeypatch):
    key = "AKIAABCDEFGHIJKLMNOP"
    write_state_bytes(repo, "STATE.md", state_text().encode("utf-8") + b"caf\xe9\n")  # stray cp1252 byte
    write_state_bytes(repo, "DECISIONS.md", f"# Decisions\nkey {key} caf\xe9\n".encode("latin-1"))
    code, out = run_main(["check"], {}, repo, monkeypatch)
    assert code == 0
    assert "STATE.md:" in out and "Secret: DECISIONS.md:2" in out and key not in out
    blocked = sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m")
    assert blocked["decision"] == "block"
    assert "DECISIONS.md:2" in blocked["reason"] and key not in blocked["reason"]


def test_utf16_state_file_is_decoded_and_scanned_for_secrets(repo, tmp_path):
    secret = "ghp_" + "f" * 36
    write_state_bytes(repo, "STATE.md", state_text(f"note: {secret}\n" + VALID_BODY).encode("utf-16"))
    out = sh.stop_decision({"session_id": "s1"}, repo, tmp_path / "m")
    assert out["decision"] == "block"
    assert "STATE.md:5" in out["reason"] and secret not in out["reason"]
    assert "Structure: ok" in sh.check_report(repo, TODAY)


def test_session_start_injects_an_undecodable_state_file(repo):
    write_state_bytes(repo, "STATE.md", state_text().encode("utf-8") + b"caf\xe9\n")
    assert "Ship the thing." in ctx(sh.build_session_start({"source": "startup"}, repo, TODAY))


def test_check_report_without_state_file(repo):
    assert "STATE.md" in sh.check_report(repo, TODAY)


def test_main_check_prints_report_and_never_reads_stdin(repo, monkeypatch):
    write_state(repo, updated=date.today().isoformat())

    class NoStdin:
        def read(self):
            raise AssertionError("check must not wait for a hook payload")

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    out = io.StringIO()
    assert sh.main(["check"], NoStdin(), out) == 0
    assert "cap 80" in out.getvalue()
    assert "Structure: ok" in out.getvalue()


def test_main_check_never_raises(repo, monkeypatch):
    write_state(repo)

    def boom(_text):
        raise RuntimeError("boom")

    monkeypatch.setattr(sh, "structure_problems", boom)
    code, _ = run_main(["check"], {}, repo, monkeypatch)
    assert code == 0


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
    for sub in ("session-start", "stop", "pre-compact", "check"):
        code, _ = run_main([sub], "not json", repo, monkeypatch)
        assert code == 0


def test_main_unknown_subcommand_is_harmless(repo, monkeypatch):
    code, out = run_main(["bogus"], {}, repo, monkeypatch)
    assert code == 0 and out == ""
