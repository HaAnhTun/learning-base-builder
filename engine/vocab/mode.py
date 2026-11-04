"""Vocabulary Mode AI steps (SPEC 2.0 §7.4–7.5, §9): prepare tasks, ingest results, rank, export."""
import json
from pathlib import Path

from engine import database
from engine.ai import tasks
from engine.ai.validate import ValidationError, mentions, soft_status, validate
from engine.cleaner import load_document
from engine.exporter import fmt_time
from engine.database import now
from engine.vocab.candidates import candidates_fresh, context_hash

MODE = "vocab_eval"
PROMPT_VERSION = "vocab_eval-v1"
INSTRUCTIONS = ".claude/skills/learning-base-builder/references/vocab-eval.md"
TERM_TYPES = ["acronym", "abbreviation", "technical_term", "collocation", "phrasal_verb", "academic", "general"]
CEFR = ["A1", "A2", "B1", "B2", "C1", "C2", None]
REVIEWED = ("approved", "rejected")

OUTPUT_SCHEMA = {
    "type": "object", "required": ["results"], "additionalProperties": False,
    "properties": {"results": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["key", "selected", "term_type", "importance", "reason", "vietnamese_meaning",
                     "english_definition", "expansion", "cefr_level", "example_refs", "confidence"],
        "properties": {
            "key": {"type": "string"},
            "selected": {"type": "boolean"},
            "term_type": {"enum": TERM_TYPES},
            "importance": {"type": "integer", "minimum": 0, "maximum": 100},
            "reason": {"type": "string", "minLength": 1},
            "vietnamese_meaning": {"type": ["string", "null"]},
            "english_definition": {"type": ["string", "null"]},
            "expansion": {"type": ["string", "null"]},
            "cefr_level": {"enum": CEFR},
            "example_refs": {"type": "array", "items": {"type": "string"}, "maxItems": 2},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        }}}},
}


def _ref(tid: int, sid: int) -> str:
    return f"{tid}:{sid}"


def _sentences(cfg: dict, conn, refs: list[list[int]], cache: dict) -> dict[str, dict]:
    """Resolve [[transcript_id, sentence_id]] to {ref: {text, start, lesson_position, lesson_title}}."""
    out = {}
    for tid, sid in refs:
        if tid not in cache:
            row = conn.execute("SELECT t.clean_path, l.position, l.title FROM transcript t "
                               "JOIN lesson l ON l.id = t.lesson_id WHERE t.id = ?", (tid,)).fetchone()
            cache[tid] = (load_document(cfg["root"], row["clean_path"]), row["position"], row["title"])
        doc, position, title = cache[tid]
        s = doc["sentences"][sid]
        out[_ref(tid, sid)] = {"text": s["text"], "start": s["start"], "lesson_position": position,
                               "lesson_title": title}
    return out


def _pending_keys(conn, cfg: dict, course_id: int) -> set[str]:
    keys = set()
    for row in tasks.pending_tasks(conn, MODE, course_id):
        keys.update(c["key"] for c in tasks.load_packet(cfg, row)["input"]["candidates"])
    return keys


def _require_fresh(conn, course, cfg: dict) -> None:
    if not candidates_fresh(conn, course["id"], cfg):
        raise LookupError(f"Ứng viên của '{course['slug']}' chưa có hoặc đã cũ — chạy "
                          f"`vocab candidates {course['slug']}` trước.")


def _needs_eval(r, override_reviewed: bool) -> bool:
    if r["e_status"] is None or r["e_hash"] != r["context_hash"]:
        return True  # never evaluated, or its context set changed (a review decision is re-applied on ingest)
    if r["e_status"] in REVIEWED:
        return override_reviewed
    return r["e_pv"] != PROMPT_VERSION


def _settle_invalid_tasks(conn, cfg: dict, course_id: int, todo_keys: set[str]) -> None:
    """Re-arm invalid tasks that still cover work (keeping their retry count); otherwise retire them."""
    for row in conn.execute("SELECT * FROM ai_task WHERE mode = ? AND course_id = ? AND status = 'invalid'",
                            (MODE, course_id)).fetchall():
        keys = {c["key"] for c in tasks.load_packet(cfg, row)["input"]["candidates"]}
        if row["attempts"] > cfg["ai"]["max_retries"]:
            status = "failed"
        elif keys & todo_keys and row["prompt_version"] == PROMPT_VERSION:
            status = "pending"
            (cfg["root"] / row["result_path"]).unlink(missing_ok=True)
        else:
            status = "superseded"  # its candidates were evaluated by later batches
        with conn:
            conn.execute("UPDATE ai_task SET status = ?, updated_at = ? WHERE id = ?", (status, now(), row["id"]))


def prepare(conn, course_slug: str, cfg: dict, limit: int | None = None, override_reviewed: bool = False) -> dict:
    course = database.course_by_slug(conn, course_slug)
    _require_fresh(conn, course, cfg)
    rows = conn.execute(
        """SELECT c.*, t.normalized_term, t.display_term, t.preliminary_type,
                  e.prompt_version AS e_pv, e.context_hash AS e_hash, e.status AS e_status
           FROM vocab_candidate c JOIN vocab_term t ON t.id = c.term_id
           LEFT JOIN vocab_entry e ON e.course_id = c.course_id AND e.term_id = c.term_id
           WHERE c.course_id = ? AND c.filter_status = 'kept'
           ORDER BY c.frequency DESC, t.normalized_term""", (course["id"],)).fetchall()
    needing = [r for r in rows if _needs_eval(r, override_reviewed)]
    _settle_invalid_tasks(conn, cfg, course["id"], {r["normalized_term"] for r in needing})
    in_flight = _pending_keys(conn, cfg, course["id"])
    todo = [r for r in needing if r["normalized_term"] not in in_flight]
    level = cfg["learner"]["cefr_level"]
    size = cfg["vocabulary"]["batch_size"]
    cache: dict = {}
    created = 0
    for i in range(0, len(todo), size):
        if limit is not None and created >= limit:
            break
        batch = []
        for r in todo[i:i + size]:
            refs = json.loads(r["context_sentence_refs"])
            contexts = _sentences(cfg, conn, refs, cache)
            batch.append({"key": r["normalized_term"], "term": r["display_term"], "type": r["preliminary_type"],
                          "frequency": r["frequency"], "lessons": r["lesson_count"],
                          "context_hash": r["context_hash"],
                          "contexts": [{"ref": ref, "text": c["text"]} for ref, c in contexts.items()]})
        task_input = {"course": course["title"], "learner_level": level, "candidates": batch}
        if tasks.ensure_task(conn, cfg, mode=MODE, prompt_version=PROMPT_VERSION, course_id=course["id"],
                             task_input=task_input, hash_extra={"learner_level": level},
                             output_schema=OUTPUT_SCHEMA, instructions=INSTRUCTIONS):
            created += 1
    pending = tasks.pending_tasks(conn, MODE, course["id"])
    return {"candidates_todo": len(todo), "tasks_created": created, "pending": len(pending)}


ITEM_SCHEMA = OUTPUT_SCHEMA["properties"]["results"]["items"]


def _check(packet: dict, result) -> dict[str, dict]:
    """Deterministic fixes, then hard validation (SPEC 9.4); returns {key: result_item}."""
    validate(result, {"type": "object", "required": ["results"], "additionalProperties": False,
                      "properties": {"results": {"type": "array", "items": {"type": "object"}}}})
    expected = {c["key"]: c for c in packet["input"]["candidates"]}
    by_display = {c["term"].lower(): c["key"] for c in packet["input"]["candidates"]}
    got = {}
    for item in result["results"]:
        key = item.get("key")
        if isinstance(key, str) and key not in expected and key.lower() in by_display:  # echoed the display form
            item = {**item, "key": by_display[key.lower()], "_fixed": True}
        refs = item.get("example_refs")
        if isinstance(refs, list) and item.get("key") in expected:
            allowed = {c["ref"] for c in expected[item["key"]]["contexts"]}
            valid_refs = [ref for ref in refs if ref in allowed][:2]
            if valid_refs != refs:  # drop refs outside the given contexts (and extras), flag the item
                item = {**item, "example_refs": valid_refs, "_fixed": True}
        validate({k: v for k, v in item.items() if not k.startswith("_")}, ITEM_SCHEMA, f"$.results[{key!r}]")
        if item["key"] in got or item["key"] not in expected:
            continue  # duplicate or invented key: ignored; a candidate left without result is re-batched
        if item["selected"] and not ((item["vietnamese_meaning"] or "").strip()
                                     and (item["english_definition"] or "").strip()):
            continue  # incomplete item: ignored, its candidate is re-batched by the next prepare
        got[item["key"]] = item
    if not got:
        raise ValidationError("no results")
    # Missing candidates are not an error: they keep no entry, so the next `prepare` re-batches them.
    return got


def ingest(conn, course_slug: str, cfg: dict, override_reviewed: bool = False) -> dict:
    course = database.course_by_slug(conn, course_slug)
    threshold = cfg["ai"]["review_threshold"]
    summary = {"done": 0, "invalid": 0, "failed": 0, "waiting": 0, "entries": 0, "missing": 0, "dropped": 0}
    for row in tasks.pending_tasks(conn, MODE, course["id"]):
        packet = tasks.load_packet(cfg, row)
        try:
            result = tasks.load_result(cfg, row)
            if result is None:
                summary["waiting"] += 1
                continue
            items = _check(packet, result)
        except ValueError as exc:  # includes ValidationError
            with conn:
                summary[tasks.mark_invalid(conn, cfg, row["id"], str(exc))] += 1
            continue
        candidates = {c["key"]: c for c in packet["input"]["candidates"]}
        summary["missing"] += len(candidates) - len(items)
        with conn:
            for key, item in items.items():
                if _store_entry(conn, course["id"], key, item, candidates[key], row["id"], threshold,
                                override_reviewed):
                    summary["entries"] += 1
                else:
                    summary["dropped"] += 1  # candidate no longer kept since the task was prepared
            tasks.mark_done(conn, row["id"])
        summary["done"] += 1
    with conn:
        rerank(conn, course["id"])
    return summary


def _packet_context_hash(candidate_input: dict) -> str:
    """Hash of the contexts the model actually saw (same formula as candidate extraction)."""
    if candidate_input.get("context_hash"):
        return candidate_input["context_hash"]
    return context_hash([[*map(int, c["ref"].split(":")), c["text"]] for c in candidate_input["contexts"]])


def _store_entry(conn, course_id, key, item, candidate_input, task_id, threshold, override_reviewed) -> bool:
    """Store one evaluated term; False when its candidate is gone (removed/filtered since prepare)."""
    term = conn.execute("SELECT id FROM vocab_term WHERE normalized_term = ?", (key,)).fetchone()
    candidate = term and conn.execute("SELECT filter_status FROM vocab_candidate WHERE course_id = ? AND term_id = ?",
                                      (course_id, term["id"])).fetchone()
    if not candidate or candidate["filter_status"] != "kept":
        return False
    term_id, seen_hash = term["id"], _packet_context_hash(candidate_input)
    existing = conn.execute("SELECT status, context_hash FROM vocab_entry WHERE course_id = ? AND term_id = ?",
                            (course_id, term_id)).fetchone()
    if existing and existing["status"] in REVIEWED and not override_reviewed and existing["context_hash"] == seen_hash:
        return True  # human decision on the same contexts stays as is
    contexts = {c["ref"]: c["text"] for c in candidate_input["contexts"]}
    examples_ok = all(mentions(contexts[ref], candidate_input["term"]) for ref in item["example_refs"])
    ok = examples_ok and not item.get("_fixed") and (bool(item["example_refs"]) or not item["selected"])
    status = soft_status(item["confidence"], threshold, ok)
    review = conn.execute("SELECT decision, edited_json FROM review_log WHERE course_id = ? AND mode = 'vocab' "
                          "AND key = ?", (course_id, key)).fetchone()
    fields = {k: item[k] for k in ("selected", "term_type", "importance", "reason", "vietnamese_meaning",
                                   "english_definition", "expansion", "cefr_level")}
    reviewed_at = None
    if review and not override_reviewed:  # re-apply a user's earlier decision after regeneration (SPEC 9.5)
        fields.update(json.loads(review["edited_json"] or "{}"))
        status, reviewed_at = review["decision"], now()
    refs = [[int(x) for x in ref.split(":")] for ref in item["example_refs"]]
    conn.execute(
        """INSERT INTO vocab_entry (course_id, term_id, selected, term_type, importance, reason, vietnamese_meaning,
               english_definition, expansion, cefr_level, example_sentence_refs, context_hash, status, confidence,
               reviewed_at, prompt_version, task_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(course_id, term_id) DO UPDATE SET selected = excluded.selected, term_type = excluded.term_type,
             importance = excluded.importance, reason = excluded.reason,
             vietnamese_meaning = excluded.vietnamese_meaning, english_definition = excluded.english_definition,
             expansion = excluded.expansion, cefr_level = excluded.cefr_level,
             example_sentence_refs = excluded.example_sentence_refs, context_hash = excluded.context_hash,
             status = excluded.status, confidence = excluded.confidence, reviewed_at = excluded.reviewed_at,
             prompt_version = excluded.prompt_version, task_id = excluded.task_id""",
        (course_id, term_id, int(fields["selected"]), fields["term_type"], fields["importance"], fields["reason"],
         fields["vietnamese_meaning"], fields["english_definition"], fields["expansion"], fields["cefr_level"],
         json.dumps(refs), seen_hash, status, item["confidence"], reviewed_at, PROMPT_VERSION, task_id))
    return True


def rerank(conn, course_id: int) -> None:
    """Deterministic course-wide rank (SPEC 7.4): importance ↓, lesson_count ↓, frequency ↓, normalized_term."""
    conn.execute("UPDATE vocab_entry SET rank = NULL WHERE course_id = ?", (course_id,))
    rows = conn.execute(
        """SELECT e.id FROM vocab_entry e JOIN vocab_term t ON t.id = e.term_id
           JOIN vocab_candidate c ON c.course_id = e.course_id AND c.term_id = e.term_id AND c.filter_status = 'kept'
           WHERE e.course_id = ? AND e.selected = 1 AND e.status != 'rejected'
           ORDER BY e.importance DESC, c.lesson_count DESC, c.frequency DESC, t.normalized_term""",
        (course_id,)).fetchall()
    conn.executemany("UPDATE vocab_entry SET rank = ? WHERE id = ?", [(i, r["id"]) for i, r in enumerate(rows, 1)])


def export_rows(conn, course_id: int) -> list:
    """Ranked entries whose evaluation matches the candidate's current contexts (stale ones are skipped)."""
    return conn.execute(
        """SELECT e.*, t.normalized_term, t.display_term, c.id AS candidate_id, c.frequency, c.lesson_count
           FROM vocab_entry e JOIN vocab_term t ON t.id = e.term_id
           JOIN vocab_candidate c ON c.course_id = e.course_id AND c.term_id = e.term_id AND c.filter_status = 'kept'
           WHERE e.course_id = ? AND e.rank IS NOT NULL AND e.context_hash = c.context_hash
           ORDER BY e.rank""", (course_id,)).fetchall()


def build_export(conn, course_slug: str, cfg: dict) -> dict:
    """Export model (SPEC 7.5): only selected, non-rejected entries; examples are original sentences."""
    course = database.course_by_slug(conn, course_slug)
    _require_fresh(conn, course, cfg)  # sentence ids must match the current Clean Dataset
    cache: dict = {}
    terms = []
    for r in export_rows(conn, course["id"]):
        refs = json.loads(r["example_sentence_refs"] or "[]")[:1]  # one original sentence is enough to study
        example = next(iter(_sentences(cfg, conn, refs, cache).values()), None)
        # Lean model for people and the study app; full sources stay in SQLite (vocab_occurrence).
        terms.append({
            "rank": r["rank"], "term": r["display_term"], "type": r["term_type"], "importance": r["importance"],
            "vi": r["vietnamese_meaning"], "en": r["english_definition"], "expansion": r["expansion"],
            "cefr": r["cefr_level"], "frequency": r["frequency"], "lessons": r["lesson_count"],
            "example": {"text": example["text"], "lesson": example["lesson_position"],
                        "time": fmt_time(example["start"])} if example else None,
        })
    return {"kind": "vocabulary", "course": course["title"], "slug": course["slug"],
            "level": cfg["learner"]["cefr_level"], "terms": terms}


def export(conn, course_slug: str, cfg: dict) -> Path:
    from engine.exporter import write_vocabulary

    model = build_export(conn, course_slug, cfg)
    folder = cfg["root"] / cfg["paths"]["export_dir"] / "vocabulary" / course_slug
    write_vocabulary(model, folder, cfg["vocabulary"]["export_max_terms"])
    return folder


# --- review (SPEC 9.4): list / decide needs_review items ---

def review_list(conn, course_slug: str, cfg: dict, status: str = "needs_review") -> list[dict]:
    """Items to review, selected terms first; entries evaluated on outdated contexts are skipped."""
    course = database.course_by_slug(conn, course_slug)
    _require_fresh(conn, course, cfg)
    rows = conn.execute(
        """SELECT e.*, t.normalized_term, t.display_term FROM vocab_entry e JOIN vocab_term t ON t.id = e.term_id
           JOIN vocab_candidate c ON c.course_id = e.course_id AND c.term_id = e.term_id AND c.filter_status = 'kept'
           WHERE e.course_id = ? AND e.status = ? AND e.context_hash = c.context_hash
           ORDER BY e.selected DESC, e.importance DESC, t.normalized_term""", (course["id"], status)).fetchall()
    cache: dict = {}
    out = []
    for r in rows:
        examples = _sentences(cfg, conn, json.loads(r["example_sentence_refs"] or "[]"), cache)
        out.append({"id": r["id"], "term": r["display_term"], "key": r["normalized_term"],
                    "selected": bool(r["selected"]), "term_type": r["term_type"], "importance": r["importance"],
                    "vietnamese_meaning": r["vietnamese_meaning"], "english_definition": r["english_definition"],
                    "confidence": r["confidence"], "examples": [e["text"] for e in examples.values()]})
    return out


EDITABLE = {"term_type", "importance", "reason", "vietnamese_meaning", "english_definition", "expansion",
            "cefr_level", "selected"}


def review_decide(conn, course_slug: str, entry_id: int, decision: str, edits: dict | None = None) -> None:
    course = database.course_by_slug(conn, course_slug)
    row = conn.execute("SELECT e.*, t.normalized_term FROM vocab_entry e JOIN vocab_term t ON t.id = e.term_id "
                       "WHERE e.id = ? AND e.course_id = ?", (entry_id, course["id"])).fetchone()
    if row is None:
        raise LookupError(f"Không có mục từ vựng id={entry_id} trong khóa '{course_slug}'.")
    edits = edits or {}
    unknown = set(edits) - EDITABLE
    if unknown:
        raise ValueError(f"Không sửa được các trường: {sorted(unknown)}")
    try:
        validate(edits, {"type": "object", "properties": {k: ITEM_SCHEMA["properties"][k] for k in EDITABLE}})
    except ValidationError as exc:
        raise ValueError(f"Giá trị sửa không hợp lệ: {exc}") from None
    with conn:
        sets = ", ".join(f"{k} = ?" for k in edits)
        values = [int(v) if k == "selected" else v for k, v in edits.items()]
        conn.execute(f"UPDATE vocab_entry SET status = ?, reviewed_at = ?{', ' + sets if sets else ''} WHERE id = ?",
                     [decision, now(), *values, entry_id])
        conn.execute(
            """INSERT INTO review_log (course_id, mode, key, decision, edited_json, reviewed_at)
               VALUES (?, 'vocab', ?, ?, ?, ?)
               ON CONFLICT(course_id, mode, key) DO UPDATE SET decision = excluded.decision,
                 edited_json = excluded.edited_json, reviewed_at = excluded.reviewed_at""",
            (course["id"], row["normalized_term"], decision, json.dumps(edits, ensure_ascii=False) if edits else None,
             now()))
        rerank(conn, course["id"])
