"""Vocabulary enrichment (task mode vocab_enrich): learning details for the terms that are exported to study.

Only exported terms are enriched (not every evaluated candidate), so the extra AI cost stays small. Each term gets a
part of speech, a corrected short Vietnamese meaning, a Vietnamese translation of its English definition, a Vietnamese translation of its example sentence
and an optional short usage note. Results are cached per term by the hash of the input they were made from
(without the short meaning, which the task itself may rewrite).
"""
import json

from engine import database
from engine.ai import tasks
from engine.ai.validate import ValidationError, language_ok, validate
from engine.database import now

MODE = "vocab_enrich"
PROMPT_VERSION = "vocab_enrich-v2"
INSTRUCTIONS = ".claude/skills/learning-base-builder/references/vocab-enrich.md"
POS = ["noun", "verb", "adjective", "adverb", "noun phrase", "verb phrase", "phrasal verb", "acronym", "other"]
ITEM_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["key", "vi", "part_of_speech", "definition_vi", "example_vi", "usage_note"],
    "properties": {
        "key": {"type": "string"},
        "vi": {"type": "string", "minLength": 1},
        "part_of_speech": {"enum": POS},
        "definition_vi": {"type": "string", "minLength": 1},
        "example_vi": {"type": ["string", "null"]},
        "usage_note": {"type": ["string", "null"]},
    },
}
OUTPUT_SCHEMA = {"type": "object", "required": ["results"], "additionalProperties": False,
                 "properties": {"results": {"type": "array", "items": ITEM_SCHEMA}}}


def _input_item(row, example_text: str | None) -> dict:
    return {"key": row["normalized_term"], "term": row["display_term"], "type": row["term_type"],
            "vi": row["vietnamese_meaning"], "en": row["english_definition"], "example": example_text}


def _item_hash(item: dict) -> str:
    return tasks.compute_hash({"item": {k: v for k, v in item.items() if k != "vi"}, "prompt_version": PROMPT_VERSION})


def _targets(conn, course, cfg: dict) -> list[tuple[dict, str, object]]:
    """(input item, input hash, entry row) for every exported term."""
    from engine.vocab.mode import _sentences, export_entries

    cache: dict = {}
    out = []
    for row in export_entries(conn, course["id"], cfg):
        refs = json.loads(row["example_sentence_refs"] or "[]")[:1]
        example = next(iter(_sentences(cfg, conn, refs, cache).values()), None)
        item = _input_item(row, example["text"] if example else None)
        out.append((item, _item_hash(item), row))
    return out


def prepare(conn, course_slug: str, cfg: dict, limit: int | None = None) -> dict:
    from engine.vocab.mode import _require_fresh

    course = database.course_by_slug(conn, course_slug)
    _require_fresh(conn, course, cfg)
    targets = _targets(conn, course, cfg)
    needing = [(item, h) for item, h, row in targets if row["enrich_hash"] != h]
    needed_keys = {item["key"] for item, _ in needing}
    tasks.retire_stale(conn, MODE, course["id"], PROMPT_VERSION)
    tasks.settle_invalid(conn, cfg, MODE, course["id"], PROMPT_VERSION,
                         lambda packet: any(i["key"] in needed_keys for i in packet["input"]["terms"]))
    in_flight = {i["key"] for row in tasks.pending_tasks(conn, MODE, course["id"])
                 for i in tasks.load_packet(cfg, row)["input"]["terms"]}
    todo = [item for item, _ in needing if item["key"] not in in_flight]
    size = cfg["vocabulary"]["enrich_batch_size"]
    # A done task whose result skipped some terms has the same input as its retry; the round count keeps them apart.
    rounds = conn.execute("SELECT COUNT(*) FROM ai_task WHERE mode = ? AND course_id = ? AND status = 'done'",
                          (MODE, course["id"])).fetchone()[0]
    created = 0
    for i in range(0, len(todo), size):
        if limit is not None and created >= limit:
            break
        task_input = {"course": course["title"], "learner_level": cfg["learner"]["cefr_level"],
                      "terms": todo[i:i + size]}
        if tasks.ensure_task(conn, cfg, mode=MODE, prompt_version=PROMPT_VERSION, course_id=course["id"],
                             task_input=task_input, hash_extra={"round": rounds}, output_schema=OUTPUT_SCHEMA,
                             instructions=INSTRUCTIONS):
            created += 1
    return {"exported_terms": len(targets), "terms_todo": len(todo), "tasks_created": created,
            "pending": len(tasks.pending_tasks(conn, MODE, course["id"]))}


def ingest(conn, course_slug: str, cfg: dict) -> dict:
    course = database.course_by_slug(conn, course_slug)
    summary = {"done": 0, "invalid": 0, "failed": 0, "waiting": 0, "enriched": 0, "skipped": 0}
    for row in tasks.pending_tasks(conn, MODE, course["id"]):
        packet = tasks.load_packet(cfg, row)
        try:
            result = tasks.load_result(cfg, row)
            if result is None:
                summary["waiting"] += 1
                continue
            validate(result, {"type": "object", "required": ["results"],
                              "properties": {"results": {"type": "array", "items": {"type": "object"}}}})
        except ValueError as exc:  # includes ValidationError
            with conn:
                summary[tasks.mark_invalid(conn, cfg, row["id"], str(exc))] += 1
            continue
        expected = {i["key"]: i for i in packet["input"]["terms"]}
        with conn:
            for item in result["results"]:
                term = expected.get(item.get("key"))
                try:
                    validate(item, ITEM_SCHEMA)
                except ValidationError:
                    term = None
                if term is None or (term["example"] and not (item["example_vi"] or "").strip()) or not (
                        language_ok(item["definition_vi"], "vi") and language_ok(item["example_vi"] or "", "vi")):
                    summary["skipped"] += 1  # left without details → picked up by the next prepare
                    continue
                conn.execute(
                    """UPDATE vocab_entry SET part_of_speech = ?, definition_vi = ?, example_vi = ?, usage_note = ?,
                           enrich_hash = ?,
                           vietnamese_meaning = CASE WHEN status IN ('approved', 'rejected')
                                                     THEN vietnamese_meaning ELSE ? END  -- keep human edits
                       WHERE course_id = ? AND term_id = (SELECT id FROM vocab_term WHERE normalized_term = ?)""",
                    (item["part_of_speech"], item["definition_vi"].strip(),
                     (item["example_vi"] or "").strip() or None, (item["usage_note"] or "").strip() or None,
                     _item_hash(term), item["vi"].strip(),
                     course["id"], term["key"]))
                summary["enriched"] += 1
            tasks.mark_done(conn, row["id"])
        summary["done"] += 1
    return summary
