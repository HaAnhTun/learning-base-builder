"""Knowledge Mode (SPEC 2.0 §8–9): one AI task per lesson (pre-split when too long), validate, store, export."""
import json
from pathlib import Path

from engine import database
from engine.ai import tasks
from engine.ai.validate import ValidationError, validate
from engine.cleaner import load_document
from engine.database import now
from engine.normalizer import normalize_name

MODE = "knowledge_extract"
PROMPT_VERSION = "knowledge_extract-v2"
INSTRUCTIONS = ".claude/skills/learning-base-builder/references/knowledge-extract.md"
ITEM_TYPES = ["concept", "definition", "key_point", "process", "example", "advantage", "disadvantage", "relation",
              "warning"]
RELATION_TYPES = ["is_a", "part_of", "uses", "compared_with", "alternative_to", "related_to"]
NEEDS_CONCEPT = {"concept", "definition"}
REVIEWED = ("approved", "rejected")
MAX_UNCOVERED = 0.2  # topics may leave at most 20% of a lesson's sentences uncovered (soft check)
THIN_MIN_SENTENCES, THIN_MIN_TOPICS, THIN_MIN_ITEMS = 30, 2, 4  # hard floor for parts with >= 30 sentences


def output_schema(langs: list[str]) -> dict:
    text = {"type": "object", "required": langs, "additionalProperties": False,
            "properties": {lang: {"type": "string", "minLength": 1} for lang in langs}}
    content = {"type": "object", "required": langs, "additionalProperties": False,
               "properties": {lang: {"type": ["string", "array"], "minLength": 1,
                                     "items": {"type": "string", "minLength": 1}} for lang in langs}}
    rng = {"sentence_start": {"type": "integer", "minimum": 0}, "sentence_end": {"type": "integer", "minimum": 0},
           "confidence": {"type": "number", "minimum": 0, "maximum": 1}}
    item = {"type": "object", "additionalProperties": False,
            "required": ["item_type", "title", "content", "concept_name", "relation", "sentence_start",
                         "sentence_end", "confidence"],
            "properties": {"item_type": {"enum": ITEM_TYPES}, "title": text, "content": content,
                           "concept_name": {"type": ["string", "null"]},
                           "relation": {"type": ["object", "null"], "additionalProperties": False,
                                        "required": ["from", "to", "type"],
                                        "properties": {"from": {"type": "string", "minLength": 1},
                                                       "to": {"type": "string", "minLength": 1},
                                                       "type": {"enum": RELATION_TYPES}}},
                           **rng}}
    subtopic = {"type": "object", "additionalProperties": False,
                "required": ["title", "sentence_start", "sentence_end", "confidence", "items"],
                "properties": {"title": text, "items": {"type": "array", "items": item}, **rng}}
    topic = {"type": "object", "additionalProperties": False,
             "required": ["title", "sentence_start", "sentence_end", "confidence", "subtopics", "items"],
             "properties": {"title": text, "subtopics": {"type": "array", "items": subtopic},
                            "items": {"type": "array", "items": item}, **rng}}
    return {"type": "object", "required": ["topics"], "additionalProperties": False,
            "properties": {"topics": {"type": "array", "minItems": 1, "items": topic}}}


def _languages(cfg: dict) -> list[str]:
    return list(cfg["knowledge"]["output_languages"])


def _version(cfg: dict) -> str:
    return f"{PROMPT_VERSION}|{','.join(_languages(cfg))}|max_words={cfg['knowledge']['max_lesson_words']}"


def parse_lessons(spec: str | None) -> set[int] | None:
    """'1-10,15' -> {1..10, 15}."""
    if not spec:
        return None
    out = set()
    for part in spec.split(","):
        a, _, b = part.strip().partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def split_parts(doc: dict, max_words: int) -> list[tuple[int, int]]:
    """Inclusive sentence ranges, cut at paragraph boundaries so each part is <= max_words when possible."""
    words = [len(s["text"].split()) for s in doc["sentences"]]
    if sum(words) <= max_words or not doc["paragraphs"]:
        return [(0, len(words) - 1)] if words else []
    parts, start, count = [], doc["paragraphs"][0][0], 0
    for p_start, p_end in doc["paragraphs"]:
        size = sum(words[p_start:p_end + 1])
        if count and count + size > max_words:
            parts.append((start, p_start - 1))
            start, count = p_start, 0
        count += size
    parts.append((start, doc["paragraphs"][-1][1]))
    return parts


def _context_before(doc: dict, start: int) -> list[dict]:
    """The paragraph right before `start`, sent as read-only context."""
    for p_start, p_end in doc["paragraphs"]:
        if p_end == start - 1:
            return [{"id": s["id"], "text": s["text"]} for s in doc["sentences"][p_start:p_end + 1]]
    return []


def _transcripts(conn, course_id: int, lessons: set[int] | None) -> list:
    rows = database.course_transcripts(conn, course_id, "en")
    rows = [r for r in database.pick_one_per_lesson(rows, "en") if r["clean_path"]]
    return [r for r in rows if lessons is None or r["position"] in lessons]


def _pending_by_transcript(conn, cfg: dict, course_id: int) -> dict[int, list]:
    out: dict[int, list] = {}
    for row in tasks.pending_tasks(conn, MODE, course_id):
        out.setdefault(tasks.load_packet(cfg, row)["input"]["transcript_id"], []).append(row)
    return out


def prepare(conn, course_slug: str, cfg: dict, limit: int | None = None, lessons: str | None = None) -> dict:
    course = database.course_by_slug(conn, course_slug)
    langs, version = _languages(cfg), _version(cfg)
    in_flight = _pending_by_transcript(conn, cfg, course["id"])
    todo, created = 0, 0
    for row in _transcripts(conn, course["id"], parse_lessons(lessons)):
        state = database.get_state(conn, row["id"], "knowledge")
        if state and state["status"] == "done" and state["input_hash"] == row["content_hash"] \
                and state["version"] == version:
            continue
        todo += 1
        if row["id"] in in_flight:
            continue
        if limit is not None and created >= limit:
            continue
        doc = load_document(cfg["root"], row["clean_path"])
        parts = split_parts(doc, cfg["knowledge"]["max_lesson_words"])
        for index, (start, end) in enumerate(parts, 1):
            task_input = {
                "transcript_id": row["id"], "course": course["title"], "chapter": row["chapter"],
                "lesson": {"position": row["position"], "title": row["lesson_title"]},
                "output_languages": langs, "part": {"index": index, "of": len(parts), "start": start, "end": end},
                "readonly_context": _context_before(doc, start) if index > 1 else [],
                "paragraph_starts": [p[0] for p in doc["paragraphs"] if start <= p[0] <= end],
                "sentences": [{"id": s["id"], "text": s["text"]} for s in doc["sentences"][start:end + 1]],
            }
            if tasks.ensure_task(conn, cfg, mode=MODE, prompt_version=PROMPT_VERSION, course_id=course["id"],
                                 task_input=task_input, hash_extra={"version": version},
                                 output_schema=output_schema(langs), instructions=INSTRUCTIONS):
                created += 1
    return {"lessons_todo": todo, "tasks_created": created,
            "pending": len(tasks.pending_tasks(conn, MODE, course["id"]))}


def _check_range(start: int, end: int, lo: int, hi: int, what: str) -> None:
    if not (lo <= start <= end <= hi):
        raise ValidationError(f"{what}: range [{start}, {end}] outside [{lo}, {hi}]")


def _check_items(items: list[dict], lo: int, hi: int, where: str) -> None:
    for i, it in enumerate(items):
        _check_range(it["sentence_start"], it["sentence_end"], lo, hi, f"{where}.items[{i}]")
        for lang, value in it["content"].items():
            if it["item_type"] == "process" and not isinstance(value, list):
                raise ValidationError(f"{where}.items[{i}]: process content[{lang}] must be a list of steps")
            if it["item_type"] != "process" and not isinstance(value, str):
                raise ValidationError(f"{where}.items[{i}]: content[{lang}] must be a string")
        if it["item_type"] in NEEDS_CONCEPT and not (it["concept_name"] or "").strip():
            raise ValidationError(f"{where}.items[{i}]: {it['item_type']} needs concept_name")
        if it["item_type"] == "relation" and not it["relation"]:
            raise ValidationError(f"{where}.items[{i}]: relation item needs relation")


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _clamp(node: dict, lo: int, hi: int) -> None:
    """Clamp a node/item range into [lo, hi]; with no overlap at all it takes the whole parent range."""
    s, e = node.get("sentence_start"), node.get("sentence_end")
    if not (_is_int(s) and _is_int(e)):
        return
    ns, ne = max(s, lo), min(e, hi)
    if ns > ne:
        ns, ne = lo, hi
    if (ns, ne) != (s, e):
        node["sentence_start"], node["sentence_end"], node["_repaired"] = ns, ne, True


ITEM_KEYS = {"item_type", "title", "content", "concept_name", "relation", "sentence_start", "sentence_end",
             "confidence"}


def _fix_range_keys(node: dict) -> None:
    """A single missing range end is taken from the other end."""
    s, e = node.get("sentence_start"), node.get("sentence_end")
    if _is_int(s) and e is None:
        node["sentence_end"], node["_repaired"] = s, True
    elif _is_int(e) and s is None:
        node["sentence_start"], node["_repaired"] = e, True


def _fix_items(items, lo: int, hi: int) -> None:
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        extra = [k for k in it if k not in ITEM_KEYS and not k.startswith("_")]
        for k in extra:  # e.g. a stray "vi" key next to title/content
            del it[k]
        if extra:
            it["_repaired"] = True
        it.setdefault("concept_name", None)
        it.setdefault("relation", None)
        _fix_range_keys(it)
        if it.get("item_type") == "process" and isinstance(it.get("content"), dict):
            for lang, value in it["content"].items():
                if isinstance(value, str):  # a process written as one text → one step
                    it["content"][lang], it["_repaired"] = [value], True
        if isinstance(it.get("item_type"), str) and it["item_type"] not in ITEM_TYPES:
            it["item_type"], it["_repaired"] = "key_point", True
        content = it.get("content")
        if it.get("item_type") != "process" and isinstance(content, dict):
            for lang, value in content.items():  # a list outside `process` is joined into one text
                if isinstance(value, list) and all(isinstance(v, str) for v in value):
                    content[lang], it["_repaired"] = "; ".join(value), True
        title = it.get("title") if isinstance(it.get("title"), dict) else {}
        if it.get("item_type") in NEEDS_CONCEPT and not (it.get("concept_name") or "").strip() \
                and isinstance(title.get("en"), str) and title["en"].strip():
            it["concept_name"], it["_repaired"] = title["en"].strip(), True
        _clamp(it, lo, hi)


def repair_result(packet: dict, result) -> dict:
    """Deterministically repair small boundary slips (SPEC 9.4).

    Overlapping topics are trimmed (a topic left empty is folded into the previous one), child ranges are clamped
    into their parent, unknown item types become key_point. Repaired nodes/items are flagged and stored as
    needs_review. Anything structurally wrong is left for hard validation.
    """
    if not isinstance(result, dict) or not isinstance(result.get("topics"), list):
        return result
    lo, hi = packet["input"]["part"]["start"], packet["input"]["part"]["end"]
    topics = [t for t in result["topics"] if isinstance(t, dict)]
    for topic in topics:
        _fix_range_keys(topic)
        for sub in topic.get("subtopics") or []:
            if isinstance(sub, dict):
                _fix_range_keys(sub)
    if not all(_is_int(t.get("sentence_start")) and _is_int(t.get("sentence_end")) for t in topics):
        return result
    for node in topics + [s for t in topics for s in t.get("subtopics") or [] if isinstance(s, dict)]:
        node.setdefault("items", [])  # an omitted list means "none"
    for topic in topics:
        topic.setdefault("subtopics", [])
    topics.sort(key=lambda t: (t["sentence_start"], t["sentence_end"]))
    merged: list[dict] = []
    for topic in topics:
        _clamp(topic, lo, hi)
        if merged and topic["sentence_start"] <= merged[-1]["sentence_end"]:
            topic["sentence_start"], topic["_repaired"] = merged[-1]["sentence_end"] + 1, True
            if topic["sentence_start"] > topic["sentence_end"]:  # fully covered → fold into the previous topic
                prev = merged[-1]
                prev["items"] = list(prev.get("items") or []) + list(topic.get("items") or [])
                prev["subtopics"] = list(prev.get("subtopics") or []) + list(topic.get("subtopics") or [])
                prev["_repaired"] = True
                continue
        merged.append(topic)
    langs = packet["input"]["output_languages"]
    for topic in merged:
        t_lo, t_hi = topic["sentence_start"], topic["sentence_end"]
        _fix_items(topic.get("items"), t_lo, t_hi)
        _drop_incomplete(topic, langs)
        for sub in topic.get("subtopics") or []:
            if isinstance(sub, dict):
                _clamp(sub, t_lo, t_hi)
                _fix_items(sub.get("items"), sub.get("sentence_start", t_lo), sub.get("sentence_end", t_hi))
                if _drop_incomplete(sub, langs):
                    topic["_repaired"] = True
    return {**result, "topics": merged}


def _complete(item, langs: list[str]) -> bool:
    """An item needs a known type and a non-empty title and content in every output language."""
    if not isinstance(item, dict) or item.get("item_type") not in ITEM_TYPES:
        return False
    title, content = item.get("title"), item.get("content")
    return (isinstance(title, dict) and isinstance(content, dict)
            and all(isinstance(title.get(lang), str) and title[lang].strip() for lang in langs)
            and all(content.get(lang) for lang in langs))


def _drop_incomplete(node: dict, langs: list[str]) -> bool:
    """Drop items missing a language or a type (the rest of the lesson is kept); flag the node."""
    items = node.get("items")
    if not isinstance(items, list):
        return False
    kept = [it for it in items if _complete(it, langs)]
    if len(kept) != len(items):
        node["items"], node["_repaired"] = kept, True
        return True
    return False


def _public(obj):
    """Copy without private '_' markers, for schema validation."""
    if isinstance(obj, dict):
        return {k: _public(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_public(v) for v in obj]
    return obj


def check_result(packet: dict, result: dict) -> None:
    """Hard validation (SPEC 9.4) of one part's (already repaired) result."""
    validate(_public(result), packet["output_schema"])
    lo, hi = packet["input"]["part"]["start"], packet["input"]["part"]["end"]
    n_items = sum(len(t["items"]) + sum(len(s["items"]) for s in t["subtopics"]) for t in result["topics"])
    if hi - lo + 1 >= THIN_MIN_SENTENCES and (len(result["topics"]) < THIN_MIN_TOPICS or n_items < THIN_MIN_ITEMS):
        # Benchmark: Haiku degrades late in long runs to 1 topic / 1 item per lesson — reject and retry.
        raise ValidationError(f"result too thin for {hi - lo + 1} sentences: {len(result['topics'])} topics, "
                              f"{n_items} items")
    prev_end = lo - 1
    for t_i, topic in enumerate(result["topics"]):
        where = f"topics[{t_i}]"
        _check_range(topic["sentence_start"], topic["sentence_end"], lo, hi, where)
        if topic["sentence_start"] <= prev_end:
            raise ValidationError(f"{where}: overlaps or is out of order with the previous topic")
        prev_end = topic["sentence_end"]
        _check_items(topic["items"], topic["sentence_start"], topic["sentence_end"], where)
        for s_i, sub in enumerate(topic["subtopics"]):
            _check_range(sub["sentence_start"], sub["sentence_end"], topic["sentence_start"], topic["sentence_end"],
                         f"{where}.subtopics[{s_i}]")
            _check_items(sub["items"], sub["sentence_start"], sub["sentence_end"], f"{where}.subtopics[{s_i}]")


def _merge_parts(parts: list[tuple[dict, dict]]) -> list[dict]:
    """Concatenate topics of consecutive parts; merge boundary topics with the same normalized title (SPEC 8.1)."""
    topics: list[dict] = []
    for i, (_, result) in enumerate(parts):
        incoming = [dict(t) for t in result["topics"]]
        if i > 0 and topics and incoming:
            last, first = topics[-1], incoming[0]
            if normalize_name(next(iter(last["title"].values()))) == normalize_name(next(iter(first["title"].values()))):
                last["sentence_end"] = first["sentence_end"]
                last["subtopics"] = last["subtopics"] + first["subtopics"]
                last["items"] = last["items"] + first["items"]
                last["confidence"] = min(last["confidence"], first["confidence"])
                incoming.pop(0)
            else:
                last["_boundary"] = first["_boundary"] = True
        topics.extend(incoming)
    return topics


def _status(conf: float, threshold: float, ok: bool = True) -> str:
    return "auto_approved" if ok and conf >= threshold else "needs_review"


def _apply_review(conn, course_id: int, key: str):
    return conn.execute("SELECT decision, edited_json FROM review_log WHERE course_id = ? AND mode = 'knowledge' "
                        "AND key = ?", (course_id, key)).fetchone()


def item_key(lesson_external_id: str, item_type: str, title: dict) -> str:
    return f"{lesson_external_id}|{item_type}|{normalize_name(title.get('en') or next(iter(title.values())))}"


def _store_transcript(conn, cfg: dict, course_id: int, transcript_id: int, topics: list[dict], n_sentences: int,
                      task_id: str) -> int:
    threshold = cfg["ai"]["review_threshold"]
    lesson_ext = conn.execute("SELECT l.external_id FROM transcript t JOIN lesson l ON l.id = t.lesson_id "
                              "WHERE t.id = ?", (transcript_id,)).fetchone()[0]
    covered = sum(t["sentence_end"] - t["sentence_start"] + 1 for t in topics)
    coverage_ok = n_sentences == 0 or (n_sentences - covered) / n_sentences <= MAX_UNCOVERED
    conn.execute("DELETE FROM knowledge_node WHERE transcript_id = ?", (transcript_id,))
    count = 0

    def insert_items(node_id: int, items: list[dict]) -> None:
        nonlocal count
        for pos, it in enumerate(items):
            status, reviewed_at = _status(it["confidence"], threshold, not it.get("_repaired")), None
            title, content = it["title"], it["content"]
            review = _apply_review(conn, course_id, item_key(lesson_ext, it["item_type"], title))
            if review:  # re-apply an earlier human decision after regeneration (SPEC 9.5)
                edits = json.loads(review["edited_json"] or "{}")
                title, content = edits.get("title", title), edits.get("content", content)
                status, reviewed_at = review["decision"], now()
            cur = conn.execute(
                """INSERT INTO knowledge_item (node_id, position, item_type, concept_name, title_json, content_json,
                       relation_json, sentence_start, sentence_end, status, confidence, reviewed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (node_id, pos, it["item_type"], it["concept_name"], json.dumps(title, ensure_ascii=False),
                 json.dumps(content, ensure_ascii=False),
                 json.dumps(it["relation"], ensure_ascii=False) if it["relation"] else None,
                 it["sentence_start"], it["sentence_end"], status, it["confidence"], reviewed_at))
            _link_concepts(conn, cur.lastrowid, it)
            count += 1

    for pos, topic in enumerate(topics):
        ok = coverage_ok and not topic.get("_boundary") and not topic.get("_repaired")
        cur = conn.execute(
            """INSERT INTO knowledge_node (transcript_id, parent_id, node_type, title_json, position, sentence_start,
                   sentence_end, status, confidence, prompt_version, task_id)
               VALUES (?, NULL, 'topic', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (transcript_id, json.dumps(topic["title"], ensure_ascii=False), pos, topic["sentence_start"],
             topic["sentence_end"], _status(topic["confidence"], threshold, ok), topic["confidence"], PROMPT_VERSION,
             task_id))
        topic_id = cur.lastrowid
        insert_items(topic_id, topic["items"])
        for s_pos, sub in enumerate(topic["subtopics"]):
            cur = conn.execute(
                """INSERT INTO knowledge_node (transcript_id, parent_id, node_type, title_json, position,
                       sentence_start, sentence_end, status, confidence, prompt_version, task_id)
                   VALUES (?, ?, 'subtopic', ?, ?, ?, ?, ?, ?, ?, ?)""",
                (transcript_id, topic_id, json.dumps(sub["title"], ensure_ascii=False), s_pos, sub["sentence_start"],
                 sub["sentence_end"], _status(sub["confidence"], threshold, not sub.get("_repaired")),
                 sub["confidence"], PROMPT_VERSION,
                 task_id))
            insert_items(cur.lastrowid, sub["items"])
    return count


def _concept_id(conn, name: str) -> int:
    normalized = normalize_name(name)
    conn.execute("INSERT INTO concept (normalized_name, name) VALUES (?, ?) ON CONFLICT(normalized_name) DO NOTHING",
                 (normalized, name.strip()))
    return conn.execute("SELECT id FROM concept WHERE normalized_name = ?", (normalized,)).fetchone()[0]


def _link_concepts(conn, item_id: int, item: dict) -> None:
    if item["concept_name"]:
        conn.execute("INSERT OR IGNORE INTO concept_mention (concept_id, knowledge_item_id) VALUES (?, ?)",
                     (_concept_id(conn, item["concept_name"]), item_id))
    if item["item_type"] == "relation" and item["relation"]:
        rel = item["relation"]
        a, b = _concept_id(conn, rel["from"]), _concept_id(conn, rel["to"])
        if a != b:
            conn.execute("INSERT OR IGNORE INTO concept_relation (concept_id, related_concept_id, relation_type, "
                         "knowledge_item_id) VALUES (?, ?, ?, ?)", (a, b, rel["type"], item_id))


def ingest(conn, course_slug: str, cfg: dict) -> dict:
    course = database.course_by_slug(conn, course_slug)
    summary = {"done": 0, "invalid": 0, "failed": 0, "waiting": 0, "lessons": 0, "items": 0}
    version = _version(cfg)
    for transcript_id, rows in _pending_by_transcript(conn, cfg, course["id"]).items():
        loaded, ready = [], True
        for row in rows:
            packet = tasks.load_packet(cfg, row)
            try:
                result = tasks.load_result(cfg, row)
                if result is None:
                    summary["waiting"] += 1
                    ready = False
                    continue
                result = repair_result(packet, result)
                check_result(packet, result)
                loaded.append((packet, result))
            except ValueError as exc:  # includes ValidationError
                with conn:
                    summary[tasks.mark_invalid(conn, cfg, row["id"], str(exc))] += 1
                ready = False
        expected = loaded[0][0]["input"]["part"]["of"] if loaded else 0
        if not ready or len(loaded) != expected:
            continue  # wait until every part of this lesson has a valid result
        loaded.sort(key=lambda pr: pr[0]["input"]["part"]["index"])
        transcript = conn.execute("SELECT content_hash, sentence_count FROM transcript WHERE id = ?",
                                  (transcript_id,)).fetchone()
        with conn:
            summary["items"] += _store_transcript(conn, cfg, course["id"], transcript_id, _merge_parts(loaded),
                                                  transcript["sentence_count"], rows[0]["id"])
            for row in rows:
                tasks.mark_done(conn, row["id"])
            database.set_state(conn, transcript_id, "knowledge", "done", transcript["content_hash"], version)
        summary["done"] += len(rows)
        summary["lessons"] += 1
    with conn:  # drop concepts no longer mentioned anywhere
        conn.execute("DELETE FROM concept WHERE id NOT IN (SELECT concept_id FROM concept_mention) "
                     "AND id NOT IN (SELECT concept_id FROM concept_relation) "
                     "AND id NOT IN (SELECT related_concept_id FROM concept_relation)")
    return summary


# --- export (SPEC 8.3–8.4): lean model for people and the study app; full sources stay in SQLite ---

def _item_model(r, subtopic: dict | None) -> dict:
    item = {"type": r["item_type"], "title": json.loads(r["title_json"]), "content": json.loads(r["content_json"])}
    if r["importance"] is not None:  # learning details from knowledge_enrich
        item["importance"] = r["importance"]
        item["question"] = json.loads(r["question_json"])
    if subtopic:
        item["subtopic"] = subtopic
    if r["concept_name"]:
        item["concept"] = r["concept_name"]
    if r["relation_json"]:
        item["relation"] = json.loads(r["relation_json"])
    return item


def build_export(conn, course_slug: str, cfg: dict) -> dict:
    course = database.course_by_slug(conn, course_slug)
    version = _version(cfg)
    min_importance = cfg["knowledge"]["export_min_importance"]
    lessons = []
    for row in _transcripts(conn, course["id"], None):
        state = database.get_state(conn, row["id"], "knowledge")
        if state is None or state["status"] != "done" or state["version"] != version:
            continue  # not extracted yet, or stale (SPEC 9.5)
        nodes = conn.execute("SELECT * FROM knowledge_node WHERE transcript_id = ? ORDER BY parent_id IS NOT NULL, "
                             "position", (row["id"],)).fetchall()
        topics, by_id = [], {}
        for n in nodes:
            title = json.loads(n["title_json"])
            parent = by_id.get(n["parent_id"])
            items = [_item_model(i, title if parent else None) for i in conn.execute(
                "SELECT * FROM knowledge_item WHERE node_id = ? AND status != 'rejected' "
                "AND (importance IS NULL OR importance >= ?) ORDER BY position", (n["id"], min_importance))]
            if n["parent_id"] is None:
                topic = {"title": title, "items": items}
                topics.append(topic)
                by_id[n["id"]] = topic
            elif parent is not None:
                parent["items"].extend(items)  # subtopic items follow the topic's own items, labelled by subtopic
        topics = [t for t in topics if t["items"]]
        if not topics:
            continue  # nothing worth studying (e.g. a course check-in)
        chapter = (f"Chapter {row['chapter_index']}: {row['chapter']}" if row["chapter"] else course["title"])
        lessons.append({"n": row["position"], "title": row["lesson_title"], "chapter": chapter, "topics": topics})
    concepts = []
    for c in conn.execute("SELECT * FROM concept WHERE id IN (SELECT concept_id FROM concept_mention) ORDER BY name"):
        positions = sorted({m[0] for m in conn.execute(
            """SELECT l.position FROM concept_mention m JOIN knowledge_item i ON i.id = m.knowledge_item_id
               JOIN knowledge_node n ON n.id = i.node_id JOIN transcript t ON t.id = n.transcript_id
               JOIN lesson l ON l.id = t.lesson_id
               WHERE m.concept_id = ? AND l.course_id = ? AND i.status != 'rejected'""", (c["id"], course["id"]))})
        if positions:
            concepts.append({"name": c["name"], "lessons": positions})
    relations = [dict(r) for r in conn.execute(
        """SELECT DISTINCT a.name AS "from", b.name AS "to", r.relation_type AS type FROM concept_relation r
           JOIN concept a ON a.id = r.concept_id JOIN concept b ON b.id = r.related_concept_id
           JOIN knowledge_item i ON i.id = r.knowledge_item_id JOIN knowledge_node n ON n.id = i.node_id
           JOIN transcript t ON t.id = n.transcript_id JOIN lesson l ON l.id = t.lesson_id
           WHERE l.course_id = ? AND i.status != 'rejected' ORDER BY 1, 2, 3""", (course["id"],))]
    return {"kind": "knowledge", "course": course["title"], "slug": course["slug"], "languages": _languages(cfg),
            "min_importance": min_importance, "concepts": concepts, "relations": relations, "lessons": lessons}


def export(conn, course_slug: str, cfg: dict) -> Path:
    from engine.exporter import write_knowledge

    folder = cfg["root"] / cfg["paths"]["export_dir"] / "knowledge" / course_slug
    write_knowledge(build_export(conn, course_slug, cfg), folder, _languages(cfg))
    return folder


# --- review (SPEC 9.4): knowledge items ---

def review_list(conn, course_slug: str, cfg: dict, status: str = "needs_review") -> list[dict]:
    course = database.course_by_slug(conn, course_slug)
    out, docs = [], {}
    for r in conn.execute(
            """SELECT i.*, n.transcript_id, l.position AS lesson FROM knowledge_item i
               JOIN knowledge_node n ON n.id = i.node_id JOIN transcript t ON t.id = n.transcript_id
               JOIN lesson l ON l.id = t.lesson_id WHERE l.course_id = ? AND i.status = ?
               ORDER BY l.position, n.position, i.position""", (course["id"], status)):
        if r["transcript_id"] not in docs:
            path = conn.execute("SELECT clean_path FROM transcript WHERE id = ?", (r["transcript_id"],)).fetchone()[0]
            docs[r["transcript_id"]] = load_document(cfg["root"], path)
        sentences = docs[r["transcript_id"]]["sentences"][r["sentence_start"]:r["sentence_end"] + 1]
        out.append({"id": r["id"], "lesson": r["lesson"], "item_type": r["item_type"],
                    "title": json.loads(r["title_json"]), "content": json.loads(r["content_json"]),
                    "confidence": r["confidence"], "source_text": " ".join(s["text"] for s in sentences)})
    return out


def review_decide(conn, course_slug: str, item_id: int, decision: str, edits: dict | None = None) -> None:
    course = database.course_by_slug(conn, course_slug)
    row = conn.execute(
        """SELECT i.*, l.external_id AS lesson_ext FROM knowledge_item i JOIN knowledge_node n ON n.id = i.node_id
           JOIN transcript t ON t.id = n.transcript_id JOIN lesson l ON l.id = t.lesson_id
           WHERE i.id = ? AND l.course_id = ?""", (item_id, course["id"])).fetchone()
    if row is None:
        raise LookupError(f"Không có mục kiến thức id={item_id} trong khóa '{course_slug}'.")
    edits = edits or {}
    unknown = set(edits) - {"title", "content"}
    if unknown:
        raise ValueError(f"Không sửa được các trường: {sorted(unknown)}")
    title = edits.get("title", json.loads(row["title_json"]))
    content = edits.get("content", json.loads(row["content_json"]))
    with conn:
        conn.execute("UPDATE knowledge_item SET status = ?, reviewed_at = ?, title_json = ?, content_json = ? "
                     "WHERE id = ?", (decision, now(), json.dumps(title, ensure_ascii=False),
                                      json.dumps(content, ensure_ascii=False), item_id))
        conn.execute(
            """INSERT INTO review_log (course_id, mode, key, decision, edited_json, reviewed_at)
               VALUES (?, 'knowledge', ?, ?, ?, ?)
               ON CONFLICT(course_id, mode, key) DO UPDATE SET decision = excluded.decision,
                 edited_json = excluded.edited_json, reviewed_at = excluded.reviewed_at""",
            (course["id"], item_key(row["lesson_ext"], row["item_type"], json.loads(row["title_json"])), decision,
             json.dumps(edits, ensure_ascii=False) if edits else None, now()))
