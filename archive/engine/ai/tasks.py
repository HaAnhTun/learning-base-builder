"""Task packets and the ai_task table: prepare → (runner writes result) → ingest (SPEC 2.0 §9.1–9.3)."""
import hashlib
import json
from pathlib import Path

from engine.database import now

MODES = ("vocab_eval", "vocab_enrich", "knowledge_extract", "knowledge_enrich")


def compute_hash(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def task_dir(cfg: dict, mode: str) -> Path:
    return cfg["root"] / cfg["paths"]["work_dir"] / "tasks" / mode


def _rel(cfg: dict, path: Path) -> str:
    return path.relative_to(cfg["root"]).as_posix()


def ensure_task(conn, cfg: dict, *, mode: str, prompt_version: str, course_id: int, task_input: dict,
                hash_extra: dict, output_schema: dict, instructions: str) -> str | None:
    """Create (or re-arm) a task for this input. Returns the task id if it needs running, else None.

    The cache key is (mode, prompt_version, input_hash); input_hash covers the input plus every config value
    that affects the output (hash_extra).
    """
    input_hash = compute_hash({"input": task_input, "extra": hash_extra, "prompt_version": prompt_version})
    task_id = f"{mode}-{input_hash[:12]}"
    folder = task_dir(cfg, mode)
    task_path, result_path = folder / f"{task_id}.json", folder / f"{task_id}.result.json"
    row = conn.execute("SELECT * FROM ai_task WHERE mode = ? AND prompt_version = ? AND input_hash = ?",
                       (mode, prompt_version, input_hash)).fetchone()
    if row is not None and row["status"] in ("done", "failed"):
        return None
    if row is not None and row["status"] == "invalid":
        if row["attempts"] >= cfg["ai"]["max_retries"] + 1:
            with conn:
                conn.execute("UPDATE ai_task SET status = 'failed', updated_at = ? WHERE id = ?", (now(), row["id"]))
            return None
        result_path.unlink(missing_ok=True)
    packet = {
        "task_id": task_id, "mode": mode, "prompt_version": prompt_version, "instructions": instructions,
        "input_hash": input_hash, "input": task_input, "output_schema": output_schema,
        "result_path": _rel(cfg, result_path),
    }
    folder.mkdir(parents=True, exist_ok=True)
    task_path.write_text(json.dumps(packet, ensure_ascii=False, indent=1), encoding="utf-8")
    with conn:
        conn.execute(
            """INSERT INTO ai_task (id, mode, prompt_version, input_hash, course_id, task_path, result_path, status,
                                    attempts, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)
               ON CONFLICT(id) DO UPDATE SET status = 'pending', updated_at = excluded.updated_at""",
            (task_id, mode, prompt_version, input_hash, course_id, _rel(cfg, task_path), _rel(cfg, result_path),
             now(), now()))
    return task_id


def pending_tasks(conn, mode: str, course_id: int) -> list:
    return conn.execute("SELECT * FROM ai_task WHERE mode = ? AND course_id = ? AND status = 'pending' ORDER BY id",
                        (mode, course_id)).fetchall()


def load_packet(cfg: dict, row) -> dict:
    return json.loads((cfg["root"] / row["task_path"]).read_text(encoding="utf-8"))


def rebalance_brackets(text: str) -> str:
    """Fix mis-nested closers in hand-written JSON (seen with Haiku on deeply nested results).

    Outside strings: a '}' that meets an open '[' first closes that array; a ']' that meets an open '{' first
    closes that object; an object key ("...":) met while an array is open closes the array. String contents are
    never touched.
    """
    out, stack, i, n = [], [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            k = j + 1
            while k < n and text[k] in " \t\r\n":
                k += 1
            if k < n and text[k] == ":" and stack and stack[-1] == "[":  # a key cannot live in an array
                while out and out[-1] in " \t\r\n":
                    out.pop()
                comma = bool(out) and out[-1] == ","
                if comma:
                    out.pop()  # close the array before the separator: `..., "key"` -> `...], "key"`
                while stack and stack[-1] == "[":
                    out.append("]")
                    stack.pop()
                if comma:
                    out.append(", ")
            out.append(text[i:j + 1])
            i = j + 1
            continue
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            want, other = ("{", "]") if ch == "}" else ("[", "}")
            while stack and stack[-1] != want:
                out.append(other)
                stack.pop()
            if stack:
                stack.pop()
        out.append(ch)
        i += 1
    out.extend("}" if s == "{" else "]" for s in reversed(stack))
    return "".join(out)


def load_result(cfg: dict, row):
    """Return the parsed result, None when the runner has not written it yet; raise ValueError on bad JSON."""
    path = cfg["root"] / row["result_path"]
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        try:
            return json.loads(rebalance_brackets(text))  # still goes through hard validation afterwards
        except json.JSONDecodeError:
            raise ValueError(f"result is not valid JSON: {exc}") from None


def mark_done(conn, task_id: str) -> None:
    conn.execute("UPDATE ai_task SET status = 'done', error = NULL, updated_at = ? WHERE id = ?", (now(), task_id))


def mark_invalid(conn, cfg: dict, task_id: str, error: str) -> str:
    """Record a hard validation failure; becomes 'failed' once retries are exhausted. Returns the new status."""
    row = conn.execute("SELECT attempts FROM ai_task WHERE id = ?", (task_id,)).fetchone()
    attempts = row["attempts"] + 1
    status = "failed" if attempts > cfg["ai"]["max_retries"] else "invalid"
    conn.execute("UPDATE ai_task SET status = ?, attempts = ?, error = ?, updated_at = ? WHERE id = ?",
                 (status, attempts, error[:2000], now(), task_id))
    return status


def settle_invalid(conn, cfg: dict, mode: str, course_id: int, prompt_version: str, still_needed) -> None:
    """Re-arm invalid tasks that still cover needed work (keeping their retry count), retire the others.

    still_needed(packet) -> bool tells whether any of the task's input still needs processing.
    """
    for row in conn.execute("SELECT * FROM ai_task WHERE mode = ? AND course_id = ? AND status = 'invalid'",
                            (mode, course_id)).fetchall():
        if row["attempts"] > cfg["ai"]["max_retries"]:
            status = "failed"
        elif row["prompt_version"] == prompt_version and still_needed(load_packet(cfg, row)):
            status = "pending"
            (cfg["root"] / row["result_path"]).unlink(missing_ok=True)
        else:
            status = "superseded"  # its work was done by later tasks
        with conn:
            conn.execute("UPDATE ai_task SET status = ?, updated_at = ? WHERE id = ?", (status, now(), row["id"]))


def retire_stale(conn, mode: str, course_id: int, prompt_version: str) -> None:
    """Supersede pending tasks made with an older prompt version, so their work is planned again."""
    with conn:
        conn.execute("UPDATE ai_task SET status = 'superseded', updated_at = ? WHERE mode = ? AND course_id = ? "
                     "AND status = 'pending' AND prompt_version != ?", (now(), mode, course_id, prompt_version))


def batches(rows, size: int) -> list[list[str]]:
    """Group pending task files for subagents (ai.tasks_per_subagent)."""
    paths = [row["task_path"] for row in rows]
    return [paths[i:i + size] for i in range(0, len(paths), size)]
