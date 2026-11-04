"""Knowledge enrichment (task mode knowledge_enrich): learning details for extracted knowledge items.

Works on the stored items, not the transcript, so it is much cheaper than extracting again. Every item gets an
importance score (export threshold `knowledge.export_min_importance`), an active-recall question, and its non-English
title/content rewritten from the English as natural text (references/translation-vi.md). Topic titles are rewritten
too. Items are cached by the hash of their English input; a lesson is sent again while any of its items is missing.
"""
import json

from engine import database
from engine.ai import tasks
from engine.ai.validate import ValidationError, language_ok, validate
from engine.knowledge.mode import REVIEWED, _languages, _transcripts, _version

MODE = "knowledge_enrich"
PROMPT_VERSION = "knowledge_enrich-v1"
INSTRUCTIONS = ".claude/skills/learning-base-builder/references/knowledge-enrich.md"


def _targets(cfg: dict) -> list[str]:
    langs = _languages(cfg)
    if "en" not in langs:
        raise ValueError("knowledge_enrich dịch từ tiếng Anh: knowledge.output_languages phải có 'en'.")
    return [lang for lang in langs if lang != "en"]


def output_schema(cfg: dict) -> dict:
    langs, targets = _languages(cfg), _targets(cfg)

    def texts(keys):
        return {"type": "object", "additionalProperties": False, "required": keys,
                "properties": {k: {"type": "string", "minLength": 1} for k in keys}}

    item = {"type": "object", "additionalProperties": False,
            "required": ["key", "importance", "question", "title", "content"],
            "properties": {"key": {"type": "string"}, "importance": {"type": "integer", "minimum": 0, "maximum": 100},
                           "question": texts(langs), "title": texts(targets),
                           "content": {"type": "object", "required": targets}}}
    topic = {"type": "object", "additionalProperties": False, "required": ["key", "title"],
             "properties": {"key": {"type": "string"}, "title": texts(targets)}}
    return {"type": "object", "additionalProperties": False, "required": ["topics", "items"],
            "properties": {"topics": {"type": "array", "items": topic}, "items": {"type": "array", "items": item}}}


def _item_input(r) -> dict:
    item = {"key": f"i{r['id']}", "type": r["item_type"], "title_en": json.loads(r["title_json"]).get("en"),
            "content_en": json.loads(r["content_json"]).get("en")}
    if r["concept_name"]:
        item["concept"] = r["concept_name"]
    return item


def _item_hash(item: dict, targets: list[str]) -> str:
    return tasks.compute_hash({"item": {k: v for k, v in item.items() if k != "key"}, "languages": targets,
                               "prompt_version": PROMPT_VERSION})


def _lessons(conn, course, cfg: dict) -> list[tuple[dict, list[str]]]:
    """(lesson input, keys of its items still needing enrichment) for every extracted lesson.

    The input holds only those items (and the topics containing them), so a retry resends just the missing work.
    """
    version, targets = _version(cfg), _targets(cfg)
    out = []
    for row in _transcripts(conn, course["id"], None):
        state = database.get_state(conn, row["id"], "knowledge")
        if state is None or state["status"] != "done" or state["version"] != version:
            continue
        topics, todo = [], []
        for n in conn.execute("SELECT * FROM knowledge_node WHERE transcript_id = ? ORDER BY parent_id IS NOT NULL, "
                              "position", (row["id"],)):
            items = []
            for r in conn.execute("SELECT * FROM knowledge_item WHERE node_id = ? ORDER BY position", (n["id"],)):
                item = _item_input(r)
                if r["enrich_hash"] != _item_hash(item, targets):
                    items.append(item)
                    todo.append(item["key"])
            if items:
                topics.append({"key": f"t{n['id']}", "title_en": json.loads(n["title_json"]).get("en"),
                               "items": items})
        out.append(({"lesson": row["position"], "title": row["lesson_title"], "topics": topics}, todo))
    return out


def prepare(conn, course_slug: str, cfg: dict, limit: int | None = None) -> dict:
    course = database.course_by_slug(conn, course_slug)
    lessons = _lessons(conn, course, cfg)
    needed = {key for _, todo in lessons for key in todo}
    tasks.retire_stale(conn, MODE, course["id"], PROMPT_VERSION)
    tasks.settle_invalid(conn, cfg, MODE, course["id"], PROMPT_VERSION,
                         lambda packet: any(i["key"] in needed for les in packet["input"]["lessons"]
                                            for t in les["topics"] for i in t["items"]))
    in_flight = {les["lesson"] for row in tasks.pending_tasks(conn, MODE, course["id"])
                 for les in tasks.load_packet(cfg, row)["input"]["lessons"]}
    todo = [les for les, keys in lessons if keys and les["lesson"] not in in_flight]
    size, schema = cfg["knowledge"]["enrich_batch_size"], output_schema(cfg)
    groups, current, count = [], [], 0
    for les in todo:  # whole lessons, about enrich_batch_size items per task
        n = sum(len(t["items"]) for t in les["topics"])
        if current and count + n > size:
            groups.append(current)
            current, count = [], 0
        current.append(les)
        count += n
    if current:
        groups.append(current)
    # A done task whose result skipped some items has the same input as its retry; the round count keeps them apart.
    rounds = conn.execute("SELECT COUNT(*) FROM ai_task WHERE mode = ? AND course_id = ? AND status = 'done'",
                          (MODE, course["id"])).fetchone()[0]
    created = 0
    for group in groups:
        if limit is not None and created >= limit:
            break
        task_input = {"course": course["title"], "learner_level": cfg["learner"]["cefr_level"],
                      "languages": _languages(cfg), "lessons": group}
        if tasks.ensure_task(conn, cfg, mode=MODE, prompt_version=PROMPT_VERSION, course_id=course["id"],
                             task_input=task_input, hash_extra={"round": rounds}, output_schema=schema, instructions=INSTRUCTIONS):
            created += 1
    return {"lessons": len(lessons), "lessons_todo": len(todo), "items_todo": len(needed), "tasks_created": created,
            "pending": len(tasks.pending_tasks(conn, MODE, course["id"]))}


def _content_ok(value, english, lang: str) -> bool:
    if isinstance(english, list):
        ok = isinstance(value, list) and bool(value) and all(isinstance(s, str) and s.strip() for s in value)
        text = " ".join(value) if ok else ""
    else:
        ok, text = isinstance(value, str) and bool(value.strip()), value if isinstance(value, str) else ""
    return ok and language_ok(text, lang)


def _translated(text: str, english: str | None, lang: str) -> bool:
    """A title of 3+ words copied unchanged from English was not translated (Haiku does this ~8% of the time)."""
    english = english or ""
    return lang == "en" or len(english.split()) < 3 or text.strip().lower() != english.strip().lower()


def _names_concept(item: dict) -> bool:
    """A concept/definition title that is the concept's name ("Model Context Protocol") may stay in English."""
    concept, title = (item.get("concept") or "").lower(), (item.get("title_en") or "").lower()
    return bool(concept) and concept in title


def ingest(conn, course_slug: str, cfg: dict) -> dict:
    course = database.course_by_slug(conn, course_slug)
    targets, schema = _targets(cfg), output_schema(cfg)
    summary = {"done": 0, "invalid": 0, "failed": 0, "waiting": 0, "enriched": 0, "skipped": 0}
    for row in tasks.pending_tasks(conn, MODE, course["id"]):
        packet = tasks.load_packet(cfg, row)
        try:
            result = tasks.load_result(cfg, row)
            if result is None:
                summary["waiting"] += 1
                continue
            validate(result, {"type": "object", "required": ["topics", "items"],
                              "properties": {"topics": {"type": "array"}, "items": {"type": "array"}}})
        except ValueError as exc:  # includes ValidationError
            with conn:
                summary[tasks.mark_invalid(conn, cfg, row["id"], str(exc))] += 1
            continue
        sent = {i["key"]: i for les in packet["input"]["lessons"] for t in les["topics"] for i in t["items"]}
        sent_topics = {t["key"]: t["title_en"] for les in packet["input"]["lessons"] for t in les["topics"]}
        with conn:
            for topic in result["topics"]:
                try:
                    validate(topic, schema["properties"]["topics"]["items"])
                except ValidationError:
                    continue
                if topic["key"] not in sent_topics or not all(
                        _translated(topic["title"][lang], sent_topics[topic["key"]], lang) for lang in targets):
                    continue
                node = conn.execute("SELECT title_json FROM knowledge_node WHERE id = ?",
                                    (int(topic["key"][1:]),)).fetchone()
                if node is not None and json.loads(node["title_json"]).get("en") == sent_topics[topic["key"]]:
                    _merge_texts(conn, "knowledge_node", int(topic["key"][1:]), {"title_json": topic["title"]})
            for item in result["items"]:
                original = sent.get(item.get("key")) if isinstance(item, dict) else None
                try:
                    validate(item, schema["properties"]["items"]["items"])
                except ValidationError:
                    original = None
                if original is None or not all(_content_ok(item["content"].get(lang), original["content_en"], lang)
                                               and language_ok(item["question"][lang], lang)
                                               and (_translated(item["title"][lang], original["title_en"], lang)
                                                    or _names_concept(original))
                                               for lang in targets):
                    summary["skipped"] += 1  # its lesson is sent again by the next prepare
                    continue
                item_id = int(item["key"][1:])
                current = conn.execute("SELECT * FROM knowledge_item WHERE id = ?", (item_id,)).fetchone()
                if current is None or _item_input(current) != original:
                    summary["skipped"] += 1  # re-extracted meanwhile
                    continue
                if current["status"] not in REVIEWED:  # keep human edits of title/content
                    _merge_texts(conn, "knowledge_item", item_id, {
                        "title_json": item["title"],
                        "content_json": {lang: item["content"][lang] for lang in targets}})
                conn.execute("UPDATE knowledge_item SET importance = ?, question_json = ?, enrich_hash = ? "
                             "WHERE id = ?", (item["importance"], json.dumps(item["question"], ensure_ascii=False),
                                              _item_hash(original, targets), item_id))
                summary["enriched"] += 1
            tasks.mark_done(conn, row["id"])
        summary["done"] += 1
    return summary


def _merge_texts(conn, table: str, row_id: int, updates: dict[str, dict]) -> None:
    """Replace the given languages inside the row's JSON text columns, keeping the other languages."""
    row = conn.execute(f"SELECT {', '.join(updates)} FROM {table} WHERE id = ?", (row_id,)).fetchone()
    if row is None:
        return
    values = []
    for column, texts in updates.items():
        merged = json.loads(row[column])
        merged.update({k: v.strip() if isinstance(v, str) else [s.strip() for s in v] for k, v in texts.items()})
        values.append(json.dumps(merged, ensure_ascii=False))
    conn.execute(f"UPDATE {table} SET {', '.join(c + ' = ?' for c in updates)} WHERE id = ?", (*values, row_id))
