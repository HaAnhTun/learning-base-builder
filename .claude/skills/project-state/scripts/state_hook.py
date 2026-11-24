#!/usr/bin/env python3
"""Hook entry point for the project-state skill (stdlib only).

Subcommands, each reads the hook payload as JSON on stdin (except check):
  session-start  inject .claude/state/STATE.md into the model context
  stop           block the stop once when STATE.md is outdated, over its line cap, off the template
                 structure, or holds a secret
  pre-compact    print instructions that make the compaction summary keep the state
  check          run by hand: print the line cap, structure, freshness and secret findings; always exits 0

A hook must never break the session, so every failure path exits 0 silently.
"""
import codecs
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

STATE_REL = Path(".claude") / "state"
STATE_FILE = "STATE.md"
# Paths that never count as project work: the state files and the scratch worktrees agents create.
IGNORED_PREFIXES = (STATE_REL.as_posix() + "/", ".claude/worktrees/")
STATE_LINE_CAP = 80
REQUIRED_SECTIONS = ("Goal & scope", "Current state", "In progress", "Next", "Done", "Open questions",
                     "Constraints & gotchas", "Last session")  # the "## " headings of assets/STATE.template.md
DONE_CAP = 10
NEXT_CAP = 7
HEAD_PATTERN = re.compile(r"[0-9a-fA-F]{4,40}|unknown")  # install.py writes "unknown" outside git
STALE_DAYS = 14
DRIFT_COMMITS = 30
MAX_INJECT_CHARS = 8000  # additionalContext is capped at 10,000 chars; leave room for the header and warnings

SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("API key (sk-)", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("credential assignment", re.compile(
        r"(?i)(token|secret|passw(?:or)?d|api[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9/+_.\-]{16,}")),
]

ANNOUNCE_RULE = (
    "On your first reply, say in 2-3 lines in the user's language what is in progress and what comes next, then do what "
    "the user asks. Ask before proceeding only when the request contradicts this state or a STALE warning applies."
)
NO_ANNOUNCE_RULE = (
    "Context was just compacted: this state is reloaded for you; do not re-announce it, keep working."
)


def _git(project_dir, *args):
    """Run git in project_dir; return stdout text, or None on any failure."""
    try:
        proc = subprocess.run(["git", *args], cwd=project_dir, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _read_text(path):
    """Text of a state file, or None when unreadable. Undecodable bytes become U+FFFD, so a stray cp1252 byte or a
    UTF-16 file (PowerShell redirection) never hides the check report or a secret."""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8", errors="replace")


def load_state(project_dir):
    return _read_text(Path(project_dir) / STATE_REL / STATE_FILE)


def parse_meta(text):
    """Read `updated:` and `head:` from the top of STATE.md."""
    meta = {}
    for line in text.splitlines()[:12]:
        m = re.match(r"\s*(updated|head)\s*:\s*(\S+)", line)
        if m:
            meta[m.group(1)] = m.group(2)
    return meta


def structure_problems(text):
    """Short messages for where STATE.md departs from the template; [] when it follows it."""
    sections, current = {}, None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            current = sections.setdefault(line[3:].strip(), [])
        elif current is not None:
            current.append(line)
    problems = [f"missing section `## {name}`" for name in REQUIRED_SECTIONS if name not in sections]
    meta = parse_meta(text)
    try:
        datetime.strptime(meta["updated"], "%Y-%m-%d")
    except (KeyError, ValueError):
        problems.append("`updated:` line missing or not YYYY-MM-DD")
    if not HEAD_PATTERN.fullmatch(meta.get("head", "")):
        problems.append("`head:` line missing or not a short git sha")
    done = sum(1 for line in sections.get("Done", []) if line.startswith("- ") and line != "- (none)")
    if done > DONE_CAP:
        problems.append(f"Done has {done} items (max {DONE_CAP}); archive the oldest in .claude/state/archive/YYYY-MM.md")
    steps = sum(1 for line in sections.get("Next", []) if re.match(r"\d+\.(\s|$)", line))
    if steps > NEXT_CAP:
        problems.append(f"Next has {steps} items (max {NEXT_CAP}); cut or merge the lowest priority")
    return problems


def staleness_warnings(meta, project_dir, today, drift_threshold=DRIFT_COMMITS):
    warnings = []
    try:
        age = (today - datetime.strptime(meta["updated"], "%Y-%m-%d").date()).days
        if age > STALE_DAYS:
            warnings.append(f"STALE: state last updated {age} days ago (limit {STALE_DAYS}).")
    except (KeyError, ValueError):
        warnings.append("STALE: STATE.md has no valid `updated: YYYY-MM-DD` line.")
    sha = meta.get("head")
    if sha and not HEAD_PATTERN.fullmatch(sha):  # never echo or pass to git an unvalidated value: it may be a secret
        warnings.append("STALE: recorded head is not a valid sha.")
    elif sha and _git(project_dir, "rev-parse", "--git-dir") is not None:
        if _git(project_dir, "cat-file", "-e", f"{sha}^{{commit}}") is None:
            warnings.append(f"STALE: recorded head {sha} is not in this repo's history.")
        else:
            count = _git(project_dir, "rev-list", "--count", f"{sha}..HEAD")
            if count and count.strip().isdigit() and int(count) > drift_threshold:
                warnings.append(f"STALE: {int(count)} commits since the state was written (limit {drift_threshold}).")
    return warnings


def build_session_start(payload, project_dir, today, drift_threshold=DRIFT_COMMITS):
    text = load_state(project_dir)
    if text is None:
        body = ("No .claude/state/STATE.md found. Ask the user whether to run `/project-state init` "
                "to create the project state files.")
    else:
        parts = []
        warnings = staleness_warnings(parse_meta(text), project_dir, today, drift_threshold)
        if warnings:
            parts.append("\n".join(warnings) + " Verify against git log and the working tree before relying on it.")
        if len(text) > MAX_INJECT_CHARS:
            text = text[:MAX_INJECT_CHARS] + "\n[truncated: STATE.md is over the size limit; prune it]"
        parts.append(text)
        parts.append("Cold details (decisions, rejected options): .claude/state/DECISIONS.md, read it when needed.")
        parts.append(NO_ANNOUNCE_RULE if payload.get("source") == "compact" else ANNOUNCE_RULE)
        body = "\n\n".join(parts)
    return {"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "PROJECT STATE (auto-loaded by the project-state hook)\n\n" + body,
    }}


def find_secrets(text):
    """Return [(line_number, pattern_name)] without echoing the matched value."""
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                hits.append((number, name))
                break
    return hits


def _secret_hits(project_dir):
    """[(file name, line number, pattern name)] across the state files; never the matched value."""
    hits = []
    for name in (STATE_FILE, "DECISIONS.md"):
        text = _read_text(Path(project_dir) / STATE_REL / name)
        if text is None:
            continue
        hits +=[(name, n, kind) for n, kind in find_secrets(text)]
    return hits


def _worktree_changes(project_dir):
    """Paths git reports as changed or untracked, excluding IGNORED_PREFIXES."""
    out = _git(project_dir, "status", "--porcelain", "-z", "-uall")
    if not out:
        return []
    entries, paths, skip = out.split("\0"), [], False
    for entry in entries:
        if skip:
            skip = False
            continue
        if len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        if "R" in status or "C" in status:
            skip = True
        if path.replace("\\", "/").startswith(IGNORED_PREFIXES):
            continue
        paths.append(path)
    return paths


def _work_newer_than(project_dir, state_mtime):
    for rel in _worktree_changes(project_dir):
        try:
            if (Path(project_dir) / rel).stat().st_mtime > state_mtime:
                return True
        except OSError:
            continue
    return False


def stop_decision(payload, project_dir, marker_dir):
    if payload.get("stop_hook_active"):
        return None
    state_path = Path(project_dir) / STATE_REL / STATE_FILE
    state_text = load_state(project_dir)
    if state_text is None:
        return None

    leaks = [f"{name}:{n} ({kind})" for name, n, kind in _secret_hits(project_dir)]
    if leaks:
        return {"decision": "block", "reason": (
            "Possible secret in the committed state files: " + ", ".join(leaks) +
            ". Remove the value (refer to where it lives instead), then finish.")}

    session = re.sub(r"[^A-Za-z0-9_.-]", "_", str(payload.get("session_id", "unknown")))
    marker = Path(marker_dir) / session
    if marker.exists():
        return None

    problems = []
    line_count = len(state_text.splitlines())
    if line_count > STATE_LINE_CAP:
        problems.append(f"STATE.md has {line_count} lines (cap {STATE_LINE_CAP}): move the oldest Done items "
                        "to .claude/state/archive/YYYY-MM.md.")
    structure = structure_problems(state_text)
    if structure:
        problems.append("STATE.md structure: " + "; ".join(structure) + ".")
    if _work_newer_than(project_dir, state_path.stat().st_mtime):
        problems.append("Files changed after STATE.md was last written: update .claude/state/STATE.md "
                        "(in progress, next, done, open questions, last session, `updated:` and `head:` lines) "
                        "and log any decision in DECISIONS.md.")
    if not problems:
        return None
    try:
        Path(marker_dir).mkdir(parents=True, exist_ok=True)
        marker.write_text("1")
    except OSError:
        pass
    return {"decision": "block", "reason": " ".join(problems)}


def check_report(project_dir, today):
    """The `check` subcommand's report: line cap, structure, freshness, secret locations."""
    text = load_state(project_dir)
    if text is None:
        return "No .claude/state/STATE.md found. Run `/project-state init` to create it.\n"
    count = len(text.splitlines())
    lines = [f"STATE.md: {count} lines (cap {STATE_LINE_CAP})" + (" - OVER" if count > STATE_LINE_CAP else "")]
    lines += [f"Structure: {p}" for p in structure_problems(text)] or ["Structure: ok"]
    lines += staleness_warnings(parse_meta(text), project_dir, today) or ["Freshness: ok"]
    lines += [f"Secret: {name}:{n}" for name, n, _kind in _secret_hits(project_dir)] or ["Secrets: none"]
    return "\n".join(lines) + "\n"


def pre_compact_text():
    return ("When summarizing, keep verbatim: the current goal, the task in progress, the next steps, and any "
            "decision made this session. .claude/state/STATE.md is the source of truth and is reloaded after "
            "compaction; record anything the summary would lose there first.")


def main(argv, stdin, stdout):
    try:
        sub = argv[0] if argv else ""
        if sub == "check":  # run by hand: no hook payload, so never wait on stdin
            stdout.write(check_report(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd(), date.today()))
            return 0
        try:
            payload = json.loads(stdin.read() or "{}")
            if not isinstance(payload, dict):
                payload = {}
        except ValueError:
            payload = {}
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
        if sub == "session-start":
            result = build_session_start(payload, project_dir, date.today())
        elif sub == "stop":
            result = stop_decision(payload, project_dir, Path(tempfile.gettempdir()) / "project-state-nudged")
        elif sub == "pre-compact":
            stdout.write(pre_compact_text())
            return 0
        else:
            return 0
        if result:
            stdout.write(json.dumps(result))
    except Exception:  # a hook must never break the session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout))
