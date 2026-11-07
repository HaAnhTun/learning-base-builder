import json

import pytest

from engine import database
from engine.ai import tasks
from engine.importer import import_folder
from engine.knowledge import mode

LESSON_1 = ("The Model Context Protocol connects models to tools. It defines servers and clients.\n\n"
            "To add a server, install it. Then register it. Finally restart the client.\n\n"
            "Never expose secrets in tool descriptions. That is a common exam trap.\n")
LESSON_2 = "Context windows limit how much text a model sees. Long inputs get truncated.\n"


@pytest.fixture
def course(conn, cfg, tmp_path):
    folder = tmp_path / "mcp-mini"
    folder.mkdir()
    (folder / "lesson-01.txt").write_text(LESSON_1, encoding="utf-8")
    (folder / "lesson-02.txt").write_text(LESSON_2, encoding="utf-8")
    import_folder(conn, folder, cfg)
    return database.course_by_slug(conn, "mcp-mini")


def t(en):
    return {"en": en, "vi": en + " (vi)"}


def item(kind, start, end, conf=0.9, **extra):
    base = {"item_type": kind, "title": t(kind), "content": t("content"), "concept_name": None, "relation": None,
            "sentence_start": start, "sentence_end": end, "confidence": conf}
    if kind == "process":
        base["content"] = {"en": ["a", "b"], "vi": ["a", "b"]}
    return {**base, **extra}


def good_result(packet):
    start, end = packet["input"]["part"]["start"], packet["input"]["part"]["end"]
    if end - start >= 5:  # lesson 1: 7 sentences
        return {"topics": [
            {"title": t("MCP basics"), "sentence_start": 0, "sentence_end": 1, "confidence": 0.9, "subtopics": [],
             "items": [item("definition", 0, 0, concept_name="Model Context Protocol"),
                       item("relation", 1, 1, relation={"from": "Model Context Protocol", "to": "MCP server",
                                                        "type": "uses"})]},
            {"title": t("Adding a server"), "sentence_start": 2, "sentence_end": 6, "confidence": 0.95,
             "subtopics": [{"title": t("Steps"), "sentence_start": 2, "sentence_end": 4, "confidence": 0.9,
                            "items": [item("process", 2, 4)]}],
             "items": [item("warning", 5, 6, conf=0.5)]},
        ]}
    return {"topics": [{"title": t("Context window"), "sentence_start": start, "sentence_end": end,
                        "confidence": 0.9, "subtopics": [],
                        "items": [item("concept", start, end, concept_name="model context protocol")]}]}


def write_results(conn, cfg, course, make=good_result):
    for row in tasks.pending_tasks(conn, mode.MODE, course["id"]):
        packet = tasks.load_packet(cfg, row)
        (cfg["root"] / packet["result_path"]).write_text(json.dumps(make(packet)), encoding="utf-8")


def test_parse_lessons():
    assert mode.parse_lessons("1-3,7") == {1, 2, 3, 7}
    assert mode.parse_lessons(None) is None


def test_split_parts_cuts_at_paragraphs():
    doc = {"sentences": [{"text": "w " * 10}] * 6, "paragraphs": [[0, 1], [2, 3], [4, 5]]}
    assert mode.split_parts(doc, 1000) == [(0, 5)]
    assert mode.split_parts(doc, 40) == [(0, 3), (4, 5)]
    assert mode.split_parts(doc, 20) == [(0, 1), (2, 3), (4, 5)]


def test_prepare_ingest_store_and_export(conn, cfg, course):
    r = mode.prepare(conn, "mcp-mini", cfg)
    assert (r["lessons_todo"], r["tasks_created"], r["pending"]) == (2, 2, 2)
    assert mode.prepare(conn, "mcp-mini", cfg)["tasks_created"] == 0
    packet = tasks.load_packet(cfg, tasks.pending_tasks(conn, mode.MODE, course["id"])[0])
    assert packet["input"]["output_languages"] == ["en", "vi"] and packet["input"]["readonly_context"] == []

    write_results(conn, cfg, course)
    s = mode.ingest(conn, "mcp-mini", cfg)
    assert (s["done"], s["lessons"], s["items"]) == (2, 2, 5)
    statuses = dict(conn.execute("SELECT item_type, status FROM knowledge_item").fetchall())
    assert statuses["warning"] == "needs_review" and statuses["definition"] == "auto_approved"
    assert conn.execute("SELECT COUNT(*) FROM knowledge_node WHERE node_type = 'subtopic'").fetchone()[0] == 1
    concepts = {r[0] for r in conn.execute("SELECT normalized_name FROM concept")}
    assert concepts == {"model context protocol", "MCP server"}
    mentions = conn.execute("SELECT COUNT(*) FROM concept_mention").fetchone()[0]
    assert mentions == 2  # the same concept from two lessons is grouped
    assert mode.prepare(conn, "mcp-mini", cfg)["lessons_todo"] == 0

    folder = mode.export(conn, "mcp-mini", cfg)
    model = json.loads((folder / "knowledge.json").read_text(encoding="utf-8"))
    assert model["kind"] == "knowledge" and model["languages"] == ["en", "vi"]
    lesson = model["lessons"][0]
    assert (lesson["n"], lesson["chapter"]) == (1, "mcp-mini")
    assert [tp["title"]["en"] for tp in lesson["topics"]] == ["MCP basics", "Adding a server"]
    proc = next(it for it in lesson["topics"][1]["items"] if it["type"] == "process")
    assert proc["subtopic"]["en"] == "Steps" and proc["content"]["en"] == ["a", "b"] and "time" not in proc
    assert lesson["topics"][0]["items"][0]["concept"] == "Model Context Protocol"
    assert {"name": "Model Context Protocol", "lessons": [1, 2]} in model["concepts"]  # grouped across lessons
    assert model["relations"] == [{"from": "Model Context Protocol", "to": "MCP server", "type": "uses"}]
    md = (folder / "knowledge.md").read_text(encoding="utf-8")
    assert "#### MCP basics / MCP basics (vi)" in md and "1) a; 2) b" in md


@pytest.mark.parametrize("breaker", [
    lambda r: r["topics"][0].update(title="plain string"),                                # topic title not an object
    lambda r: r["topics"][0]["title"].pop("vi"),                                          # topic missing language
    lambda r: r["topics"][0]["items"][1].update(relation=None),                           # relation w/o relation
    lambda r: r.update(topics=[]),                                                        # no topics at all
    lambda r: r["topics"][0].update(sentence_start="0"),                                  # wrong type
])
def test_hard_validation_failures(conn, cfg, course, breaker):
    mode.prepare(conn, "mcp-mini", cfg, lessons="1")

    def broken(packet):
        result = good_result(packet)
        breaker(result)
        return result
    write_results(conn, cfg, course, broken)
    s = mode.ingest(conn, "mcp-mini", cfg)
    assert s["invalid"] == 1 and s["lessons"] == 0
    assert conn.execute("SELECT COUNT(*) FROM knowledge_node").fetchone()[0] == 0


def test_long_lesson_is_split_and_merged(conn, cfg, course):
    cfg["knowledge"]["max_lesson_words"] = 25  # forces lesson 1 into parts
    r = mode.prepare(conn, "mcp-mini", cfg, lessons="1")
    rows = tasks.pending_tasks(conn, mode.MODE, course["id"])
    packets = sorted((tasks.load_packet(cfg, row) for row in rows), key=lambda p: p["input"]["part"]["index"])
    assert r["tasks_created"] == len(packets) > 1
    assert packets[1]["input"]["readonly_context"]  # previous paragraph as context

    def per_part(packet):
        part = packet["input"]["part"]
        return {"topics": [{"title": t("Same topic"), "sentence_start": part["start"], "sentence_end": part["end"],
                            "confidence": 0.9, "subtopics": [], "items": []}]}
    write_results(conn, cfg, course, per_part)
    assert mode.ingest(conn, "mcp-mini", cfg)["lessons"] == 1
    rows = conn.execute("SELECT sentence_start, sentence_end, status FROM knowledge_node").fetchall()
    assert [tuple(r) for r in rows] == [(0, 6, "auto_approved")]  # boundary topics with the same title merged


def test_review_decision_survives_regeneration(conn, cfg, course):
    mode.prepare(conn, "mcp-mini", cfg)
    write_results(conn, cfg, course)
    mode.ingest(conn, "mcp-mini", cfg)
    pending = mode.review_list(conn, "mcp-mini", cfg)
    assert [p["item_type"] for p in pending] == ["warning"] and "exam trap" in pending[0]["source_text"]
    mode.review_decide(conn, "mcp-mini", pending[0]["id"], "approved", {"content": t("edited")})

    cfg["knowledge"]["output_languages"] = ["en", "vi"]
    with conn:  # simulate a content-preserving regeneration (new prompt version)
        conn.execute("UPDATE processing_state SET version = 'old' WHERE stage = 'knowledge'")
    assert mode.prepare(conn, "mcp-mini", cfg)["tasks_created"] == 0  # same input hash → cached task reused
    with conn:
        conn.execute("UPDATE ai_task SET status = 'pending'")
    write_results(conn, cfg, course)
    mode.ingest(conn, "mcp-mini", cfg)
    row = conn.execute("SELECT status, content_json FROM knowledge_item WHERE item_type = 'warning'").fetchone()
    assert row["status"] == "approved" and json.loads(row["content_json"])["en"] == "edited"


def test_stale_lessons_are_not_exported(conn, cfg, course, tmp_path):
    mode.prepare(conn, "mcp-mini", cfg)
    write_results(conn, cfg, course)
    mode.ingest(conn, "mcp-mini", cfg)
    (tmp_path / "mcp-mini" / "lesson-02.txt").write_text("Totally new content here.\n", encoding="utf-8")
    import_folder(conn, tmp_path / "mcp-mini", cfg)  # re-clean invalidates lesson 2
    model = mode.build_export(conn, "mcp-mini", cfg)
    assert [lesson["n"] for lesson in model["lessons"]] == [1]
    assert mode.prepare(conn, "mcp-mini", cfg)["lessons_todo"] == 1


def run_repaired(conn, cfg, course, breaker):
    mode.prepare(conn, "mcp-mini", cfg, lessons="1")

    def broken(packet):
        result = good_result(packet)
        breaker(result)
        return result
    write_results(conn, cfg, course, broken)
    s = mode.ingest(conn, "mcp-mini", cfg)
    assert s["invalid"] == 0 and s["lessons"] == 1
    return conn.execute("SELECT sentence_start, sentence_end, status FROM knowledge_node "
                        "WHERE node_type = 'topic' ORDER BY position").fetchall()


def test_overlapping_topic_is_trimmed_and_flagged(conn, cfg, course):
    topics = run_repaired(conn, cfg, course, lambda r: r["topics"][1].update(sentence_start=1))
    assert [tuple(t) for t in topics] == [(0, 1, "auto_approved"), (2, 6, "needs_review")]


def test_fully_covered_topic_is_merged(conn, cfg, course):
    def breaker(r):
        r["topics"].append({"title": t("Dup"), "sentence_start": 3, "sentence_end": 4, "confidence": 0.9,
                            "subtopics": [], "items": [item("example", 3, 4)]})
    topics = run_repaired(conn, cfg, course, breaker)
    assert [tuple(t)[:2] for t in topics] == [(0, 1), (2, 6)]
    assert conn.execute("SELECT COUNT(*) FROM knowledge_item WHERE item_type = 'example'").fetchone()[0] == 1


def test_item_outside_topic_is_clamped_and_unknown_type_mapped(conn, cfg, course):
    def breaker(r):
        r["topics"][0]["items"][0].update(sentence_start=1, sentence_end=3)
        r["topics"][0]["items"][1].update(item_type="feature", relation=None)
    run_repaired(conn, cfg, course, breaker)
    rows = conn.execute("SELECT item_type, sentence_start, sentence_end, status FROM knowledge_item "
                        "ORDER BY id LIMIT 2").fetchall()
    assert [tuple(r) for r in rows] == [("definition", 1, 1, "needs_review"), ("key_point", 1, 1, "needs_review")]


def test_missing_concept_name_uses_english_title(conn, cfg, course):
    run_repaired(conn, cfg, course, lambda r: r["topics"][0]["items"][0].update(concept_name=None))
    row = conn.execute("SELECT concept_name, status FROM knowledge_item WHERE item_type = 'definition'").fetchone()
    assert tuple(row) == ("definition", "needs_review")


def test_list_content_outside_process_is_joined_and_missing_lists_default(conn, cfg, course):
    def breaker(r):
        r["topics"][0]["items"][0]["content"] = {"en": ["a", "b"], "vi": ["c", "d"]}
        r["topics"][1].pop("items")
    run_repaired(conn, cfg, course, breaker)
    row = conn.execute("SELECT content_json, status FROM knowledge_item WHERE item_type = 'definition'").fetchone()
    assert json.loads(row["content_json"]) == {"en": "a; b", "vi": "c; d"} and row["status"] == "needs_review"


def test_thin_result_for_long_lesson_is_rejected(conn, cfg, course):
    mode.THIN_MIN_SENTENCES = 5  # lesson 1 has 7 sentences

    def thin(packet):
        part = packet["input"]["part"]
        return {"topics": [{"title": t("All"), "sentence_start": part["start"], "sentence_end": part["end"],
                            "confidence": 0.9, "subtopics": [], "items": [item("key_point", 0, 0)]}]}
    try:
        mode.prepare(conn, "mcp-mini", cfg, lessons="1")
        write_results(conn, cfg, course, thin)
        s = mode.ingest(conn, "mcp-mini", cfg)
        assert s["invalid"] == 1 and s["lessons"] == 0
        error = conn.execute("SELECT error FROM ai_task").fetchone()[0]
        assert "too thin" in error
    finally:
        mode.THIN_MIN_SENTENCES = 30


def test_stray_keys_string_process_and_missing_end_are_repaired(conn, cfg, course):
    def breaker(r):
        r["topics"][0]["items"][0]["vi"] = "stray"
        r["topics"][0]["items"][1].pop("sentence_end")
        r["topics"][1]["subtopics"][0]["items"][0]["content"] = {"en": "one", "vi": "một"}
    run_repaired(conn, cfg, course, breaker)
    rows = {r["item_type"]: r for r in conn.execute("SELECT * FROM knowledge_item")}
    assert rows["definition"]["status"] == "needs_review"
    assert (rows["relation"]["sentence_start"], rows["relation"]["sentence_end"]) == (1, 1)
    assert json.loads(rows["process"]["content_json"]) == {"en": ["one"], "vi": ["một"]}


def test_item_missing_a_language_is_dropped_not_the_lesson(conn, cfg, course):
    def breaker(r):
        r["topics"][0]["items"][0]["content"].pop("vi")
        r["topics"][1]["subtopics"][0]["items"][0].pop("item_type")
    topics = run_repaired(conn, cfg, course, breaker)
    types = {r[0] for r in conn.execute("SELECT item_type FROM knowledge_item")}
    assert "definition" not in types and "process" not in types and "warning" in types
    assert [t[2] for t in topics] == ["needs_review", "needs_review"]


def test_enrich_scores_translates_and_filters_export(conn, cfg, course):
    from engine.knowledge import enrich

    mode.prepare(conn, "mcp-mini", cfg)
    write_results(conn, cfg, course)
    mode.ingest(conn, "mcp-mini", cfg)
    r = enrich.prepare(conn, "mcp-mini", cfg)
    assert (r["lessons_todo"], r["items_todo"], r["tasks_created"]) == (2, 5, 1)
    row = tasks.pending_tasks(conn, enrich.MODE, course["id"])[0]
    packet = tasks.load_packet(cfg, row)
    topics, items = [], []
    for lesson in packet["input"]["lessons"]:
        for topic in lesson["topics"]:
            topics.append({"key": topic["key"], "title": {"vi": "Chủ đề " + topic["title_en"]}})
            for it in topic["items"]:
                content = ["bước 1", "bước 2"] if isinstance(it["content_en"], list) else "nội dung của mục"
                items.append({"key": it["key"], "importance": 30 if it["type"] == "concept" else 85,
                              "question": {"en": "Why?", "vi": "Vì sao?"}, "title": {"vi": "tiêu đề"},
                              "content": {"vi": content}})
    items[0]["content"] = {"vi": ""}  # incomplete → skipped, sent again by the next prepare
    items[1]["content"] = {"vi": "Step sender confirm receiver ready before let go"}  # English, not Vietnamese
    topics[0]["title"] = {"vi": "MCP basics"}  # 2 words: may legitimately stay English
    (cfg["root"] / packet["result_path"]).write_text(json.dumps({"topics": topics, "items": items}),
                                                     encoding="utf-8")
    s = enrich.ingest(conn, "mcp-mini", cfg)
    assert (s["done"], s["enriched"], s["skipped"]) == (1, 3, 2)
    again = enrich.prepare(conn, "mcp-mini", cfg)
    assert (again["items_todo"], again["tasks_created"]) == (2, 1)  # same lesson, new round → not blocked by cache
    model = mode.build_export(conn, "mcp-mini", cfg)
    assert [lesson["n"] for lesson in model["lessons"]] == [1]  # lesson 2 only had a 30-point item
    lesson = model["lessons"][0]
    assert lesson["topics"][0]["title"] == {"en": "MCP basics", "vi": "MCP basics"}
    assert enrich._translated("Chủ đề", "Adding a server", "vi") and not enrich._translated("Adding a Server", "Adding a server", "vi")
    assert enrich._names_concept({"concept": "Top P", "title_en": "Nucleus sampling (Top P)"})
    assert not enrich._names_concept({"concept": None, "title_en": "Adding a server"})
    enriched = [it for topic in lesson["topics"] for it in topic["items"] if "importance" in it]
    assert enriched and all(it["question"]["vi"] == "Vì sao?" and it["title"]["en"] != "tiêu đề" for it in enriched)
    process = next(it for topic in lesson["topics"] for it in topic["items"] if it["type"] == "process")
    assert process["content"] == {"en": ["a", "b"], "vi": ["bước 1", "bước 2"]}
    unenriched = next(it for topic in lesson["topics"] for it in topic["items"] if "importance" not in it)
    assert unenriched["title"]["vi"] == "definition (vi)"  # kept until a later batch enriches it
