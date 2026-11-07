"""Vocabulary enrichment (task mode vocab_enrich): a study card for each term that is exported to study.

Only exported terms are enriched (not every evaluated candidate), so the extra AI cost stays small. Each card has
the IPA pronunciation, a Vietnamese meaning, the part of speech, how the term is used in IT/AI, a short example
written for learning (with its Vietnamese translation) and an optional contrast with a confusable word. The original
course sentence is input context only. Results are cached per term by the hash of the input they were made from
(without the short meaning, which the task itself rewrites).
"""
import json
import re

from engine import database
from engine.ai import tasks
from engine.ai.validate import VI_MARKS, ValidationError, language_ok, mentions, validate
from engine.database import now

MODE = "vocab_enrich"
PROMPT_VERSION = "vocab_enrich-v3"
INSTRUCTIONS = ".claude/skills/learning-base-builder/references/vocab-enrich.md"
POS_VI = {"noun": "Danh từ", "verb": "Động từ", "adjective": "Tính từ", "adverb": "Trạng từ",
          "noun phrase": "Cụm danh từ", "verb phrase": "Cụm động từ", "phrasal verb": "Cụm động từ (phrasal verb)",
          "acronym": "Từ viết tắt", "other": "Khác"}
DOMAINS = ["IT", "AI", "AI/IT"]
IPA = re.compile(r"^/[^/]+/$")
ITEM_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["key", "ipa", "meaning", "part_of_speech", "domain", "domain_usage", "example_en", "example_vi",
                 "compare"],
    "properties": {
        "key": {"type": "string"},
        "ipa": {"type": ["string", "null"]},
        "meaning": {"type": "string", "minLength": 1},
        "part_of_speech": {"enum": list(POS_VI)},
        "domain": {"enum": DOMAINS},
        "domain_usage": {"type": "string", "minLength": 1},
        "example_en": {"type": "string", "minLength": 1},
        "example_vi": {"type": "string", "minLength": 1},
        "compare": {"type": ["string", "null"]},
    },
}
OUTPUT_SCHEMA = {"type": "object", "required": ["results"], "additionalProperties": False,
                 "properties": {"results": {"type": "array", "items": ITEM_SCHEMA}}}


def _input_item(row, context: str | None) -> dict:
    """`context` is the course sentence that shows the term; the card's own example is written fresh."""
    return {"key": row["normalized_term"], "term": row["display_term"], "type": row["term_type"],
            "vi": row["vietnamese_meaning"], "en": row["english_definition"], "context": context}


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
                if term is None or not _card_ok(item, term):
                    summary["skipped"] += 1  # left without details → picked up by the next prepare
                    continue
                clean = lambda v: (v or "").strip() or None  # noqa: E731
                conn.execute(
                    """UPDATE vocab_entry SET ipa = ?, part_of_speech = ?, domain = ?, usage_note = ?, example_en = ?,
                           example_vi = ?, compare_note = ?, enrich_hash = ?,
                           vietnamese_meaning = CASE WHEN status IN ('approved', 'rejected')
                                                     THEN vietnamese_meaning ELSE ? END  -- keep human edits
                       WHERE course_id = ? AND term_id = (SELECT id FROM vocab_term WHERE normalized_term = ?)""",
                    (clean(item["ipa"]), item["part_of_speech"], item["domain"], clean(item["domain_usage"]),
                     clean(item["example_en"]), clean(item["example_vi"]), clean(item["compare"]), _item_hash(term),
                     item["meaning"].strip(), course["id"], term["key"]))
                summary["enriched"] += 1
            tasks.mark_done(conn, row["id"])
        summary["done"] += 1
    return summary


def _needs_ipa(term: dict) -> bool:
    """Plain single words get a pronunciation; phrases, hyphenated compounds, code identifiers (camelCase) and
    letter-by-letter acronyms may go without."""
    return (term["type"] not in ("acronym", "abbreviation")
            and re.fullmatch(r"[A-Za-z][a-z]+", term["term"]) is not None)


def _card_ok(item: dict, term: dict) -> bool:
    """Hard checks: Vietnamese text really is Vietnamese, the example uses the term, single words have IPA."""
    vietnamese = [item["meaning"], item["example_vi"], item["domain_usage"]]
    return (all(VI_MARKS.search(text) and language_ok(text, "vi") for text in vietnamese)
            and mentions(item["example_en"], term["term"])
            and (IPA.match(item["ipa"].strip()) if item["ipa"] else not _needs_ipa(term)))
