import csv
import json

import pytest

from engine import database
from engine.ai import tasks
from engine.importer import import_folder
from engine.vocab import mode
from engine.vocab.candidates import extract_course_candidates, filter_reason, pick_contexts

LESSONS = {
    "lesson-01.txt": "We spin up EC2 instances in each region. The EC2 instance runs in a region.\n"
                     "Dead letter queues catch failed messages. A dead letter queue is idempotent storage.\n",
    "lesson-02.txt": "You spin up more EC2 instances when load grows. Every region has EC2 capacity.\n"
                     "The dead letter queue keeps messages. Um, the API returns JSON.\n",
    "lesson-03.txt": "Spin up a new EC2 instance in another region. APIs return JSON documents.\n",
}


@pytest.fixture
def course(conn, cfg, tmp_path):
    folder = tmp_path / "aws-mini"
    folder.mkdir()
    for name, text in LESSONS.items():
        (folder / name).write_text(text, encoding="utf-8")
    import_folder(conn, folder, cfg)
    cfg["vocabulary"]["batch_size"] = 4
    return database.course_by_slug(conn, "aws-mini")


def kept(conn):
    return {r["normalized_term"]: r for r in conn.execute(
        "SELECT t.normalized_term, t.preliminary_type, c.* FROM vocab_candidate c JOIN vocab_term t ON t.id = c.term_id "
        "WHERE c.filter_status = 'kept'")}


def test_filter_rules_never_use_length():
    args = dict(total_words=10_000, stop_words={"the"}, zipf_threshold=4.0, keyness_min=4.0, phrase_min_frequency=3)
    assert filter_reason("S3", "acronym", 1, zipf=None, **args)[0] is None
    assert filter_reason("the", "general", 50, zipf=7.7, **args)[0] == "stopword"
    assert filter_reason("um", "general", 5, zipf=4.0, **args)[0] == "noise"
    assert filter_reason("42", "general", 5, zipf=None, **args)[0] == "noise"
    assert filter_reason("use", "general", 5, zipf=5.8, **args)[0] == "common_word"
    assert filter_reason("region", "general", 300, zipf=5.0, **args)[0] is None  # common but salient in the course
    assert filter_reason("idempotent", "general", 1, zipf=2.0, **args)[0] is None
    assert filter_reason("api bill", "collocation", 1, zipf=None, **args)[0] == "low_frequency"
    assert filter_reason("spin up", "phrasal_verb", 3, zipf=None, **args)[0] is None


def test_pick_contexts_prefers_distinct_lessons():
    occ = [(1, 10, 0), (1, 10, 5), (2, 20, 3), (3, 30, 1), (3, 30, 2)]
    assert pick_contexts(occ, 3) == [[10, 0], [20, 3], [30, 1]]
    assert pick_contexts(occ[:2], 3) == [[10, 0], [10, 5]]


def test_extract_candidates(conn, cfg, course):
    cfg["vocabulary"]["phrase_min_frequency"] = 2
    r = extract_course_candidates(conn, course["id"], cfg)
    assert r["transcripts"] == 3 and r["kept"] > 0
    k = kept(conn)
    assert k["EC2"]["preliminary_type"] == "acronym" and k["EC2"]["lesson_count"] == 3
    assert "API" in k and "JSON" in k  # APIs merged into API
    assert k["spin up"]["preliminary_type"] == "phrasal_verb" and k["spin up"]["frequency"] == 3
    assert "dead letter queue" in k
    assert "um" not in k and "the" not in k
    contexts = json.loads(k["EC2"]["context_sentence_refs"])
    assert len(contexts) == 3 and len({tid for tid, _ in contexts}) == 3
    occurrences = conn.execute("SELECT COUNT(*) FROM vocab_occurrence o JOIN vocab_candidate c ON c.id = o.candidate_id "
                               "JOIN vocab_term t ON t.id = c.term_id WHERE t.normalized_term = 'EC2'").fetchone()[0]
    assert occurrences == 5  # one row per sentence containing it

    before = {key: row["context_hash"] for key, row in kept(conn).items()}
    extract_course_candidates(conn, course["id"], cfg)  # idempotent
    assert {key: row["context_hash"] for key, row in kept(conn).items()} == before


def fake_results(packet, *, confidence=0.9, select=lambda key: True):
    out = []
    for c in packet["input"]["candidates"]:
        sel = select(c["key"])
        out.append({"key": c["key"], "selected": sel, "term_type": "technical_term", "importance": 80 if sel else 10,
                    "reason": "test", "vietnamese_meaning": "nghĩa" if sel else None,
                    "english_definition": "meaning" if sel else None, "expansion": None, "cefr_level": None,
                    "example_refs": [c["contexts"][0]["ref"]] if sel else [], "confidence": confidence})
    return {"results": out}


def run_all_tasks(conn, cfg, course, **kw):
    for row in tasks.pending_tasks(conn, mode.MODE, course["id"]):
        packet = tasks.load_packet(cfg, row)
        (cfg["root"] / packet["result_path"]).write_text(json.dumps(fake_results(packet, **kw)), encoding="utf-8")


def test_prepare_requires_fresh_candidates(conn, cfg, course):
    with pytest.raises(LookupError):
        mode.prepare(conn, "aws-mini", cfg)


def test_prepare_ingest_rank_export_and_incremental(conn, cfg, course):
    extract_course_candidates(conn, course["id"], cfg)
    n = len(kept(conn))
    r = mode.prepare(conn, "aws-mini", cfg)
    assert r["candidates_todo"] == n and r["pending"] == -(-n // 4)
    assert mode.prepare(conn, "aws-mini", cfg)["tasks_created"] == 0  # in-flight candidates are not re-batched

    run_all_tasks(conn, cfg, course, select=lambda key: key != "region")
    s = mode.ingest(conn, "aws-mini", cfg)
    assert s["done"] == r["pending"] and s["entries"] == n
    ranks = [row["rank"] for row in conn.execute("SELECT rank FROM vocab_entry WHERE selected = 1 ORDER BY rank")]
    assert ranks == list(range(1, n))  # 'region' not selected → no rank
    assert mode.prepare(conn, "aws-mini", cfg)["candidates_todo"] == 0  # everything evaluated → nothing to do

    folder = mode.export(conn, "aws-mini", cfg)
    model = json.loads((folder / "vocabulary.json").read_text(encoding="utf-8"))
    ec2 = next(t for t in model["terms"] if t["term"] == "EC2")
    assert ec2["examples"][0]["text"].startswith("We spin up EC2") and len(ec2["sources"]) == 5
    rows = list(csv.DictReader((folder / "vocabulary.csv").open(encoding="utf-8-sig")))
    assert len(rows) == n - 1 and "region" not in {r["term"] for r in rows}
    assert "## 1." in (folder / "vocabulary.md").read_text(encoding="utf-8")


def test_invalid_result_is_not_stored_and_retried(conn, cfg, course):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    row = tasks.pending_tasks(conn, mode.MODE, course["id"])[0]
    packet = tasks.load_packet(cfg, row)
    (cfg["root"] / packet["result_path"]).write_text('{"results": [', encoding="utf-8")  # truncated JSON
    s = mode.ingest(conn, "aws-mini", cfg)
    assert s["invalid"] == 1
    assert conn.execute("SELECT COUNT(*) FROM vocab_entry").fetchone()[0] == 0
    mode.prepare(conn, "aws-mini", cfg)  # re-arms the invalid task
    assert conn.execute("SELECT status FROM ai_task WHERE id = ?", (row["id"],)).fetchone()[0] == "pending"


def test_partial_result_is_stored_and_missing_candidates_rebatched(conn, cfg, course):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    row = tasks.pending_tasks(conn, mode.MODE, course["id"])[0]
    packet = tasks.load_packet(cfg, row)
    partial = fake_results(packet)
    dropped = partial["results"].pop()["key"]
    (cfg["root"] / packet["result_path"]).write_text(json.dumps(partial), encoding="utf-8")
    s = mode.ingest(conn, "aws-mini", cfg)
    assert (s["done"], s["missing"]) == (1, 1)
    run_all_tasks(conn, cfg, course)  # finish the other batches
    mode.ingest(conn, "aws-mini", cfg)
    r = mode.prepare(conn, "aws-mini", cfg)
    assert (r["candidates_todo"], r["tasks_created"]) == (1, 1)
    new = tasks.load_packet(cfg, tasks.pending_tasks(conn, mode.MODE, course["id"])[0])
    assert [c["key"] for c in new["input"]["candidates"]] == [dropped]


def test_example_refs_outside_contexts_are_dropped_and_flagged(conn, cfg, course):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    row = tasks.pending_tasks(conn, mode.MODE, course["id"])[0]
    packet = tasks.load_packet(cfg, row)
    bad = fake_results(packet)
    first = bad["results"][0]
    first["example_refs"] = [first["example_refs"][0], "999:999"]
    (cfg["root"] / packet["result_path"]).write_text(json.dumps(bad), encoding="utf-8")
    assert mode.ingest(conn, "aws-mini", cfg)["done"] == 1
    entry = conn.execute("SELECT e.status, e.example_sentence_refs FROM vocab_entry e JOIN vocab_term t "
                         "ON t.id = e.term_id WHERE t.normalized_term = ?", (first["key"],)).fetchone()
    assert entry["status"] == "needs_review" and "999" not in entry["example_sentence_refs"]


def test_low_confidence_needs_review_and_review_survives_regeneration(conn, cfg, course):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    run_all_tasks(conn, cfg, course, confidence=0.4)
    mode.ingest(conn, "aws-mini", cfg)
    items = mode.review_list(conn, "aws-mini", cfg)
    assert items and all(i["confidence"] == 0.4 for i in items)
    ec2 = next(i for i in items if i["key"] == "EC2")
    mode.review_decide(conn, "aws-mini", ec2["id"], "approved", {"vietnamese_meaning": "máy ảo EC2"})
    entry = conn.execute("SELECT status, vietnamese_meaning FROM vocab_entry WHERE id = ?", (ec2["id"],)).fetchone()
    assert tuple(entry) == ("approved", "máy ảo EC2")

    # Regenerate everything with a new prompt version: the human decision is kept / re-applied.
    with conn:
        conn.execute("UPDATE vocab_entry SET prompt_version = 'old'")
    mode.prepare(conn, "aws-mini", cfg)
    run_all_tasks(conn, cfg, course, confidence=0.95)
    mode.ingest(conn, "aws-mini", cfg)
    entry = conn.execute("SELECT status, vietnamese_meaning FROM vocab_entry WHERE id = ?", (ec2["id"],)).fetchone()
    assert tuple(entry) == ("approved", "máy ảo EC2")
    with pytest.raises(ValueError):
        mode.review_decide(conn, "aws-mini", ec2["id"], "approved", {"rank": 1})


def keys_of(text):
    from engine.vocab.candidates import nlp, sentence_candidates

    return {c[0] for c in sentence_candidates(nlp()(text))}


def test_hyphen_compounds_possessives_and_content_stopwords():
    keys = keys_of("The sub-agents use few-shot prompts. The model's output follows least privilege on the front end.")
    assert {"sub-agent", "few-shot", "few-shot prompt", "least privilege", "front end", "output"} <= keys
    assert not {"sub", "shot prompt", "privilege end"} & keys


def test_proper_noun_plurals_are_lemmatized():
    assert {"token", "schema"} <= keys_of("Tokens matter. Schemas define rules.")


def test_case_variants_merge_into_acronym():
    from collections import Counter

    from engine.vocab.candidates import Aggregate, merge_case_variants

    aggs = {"JSON": Aggregate(Counter({"JSON": 3}), Counter({"acronym": 3}), [(1, 1, 0)] * 3),
            "json": Aggregate(Counter({"json": 1}), Counter({"general": 1}), [(2, 2, 0)]),
            "US": Aggregate(Counter({"US": 1}), Counter({"acronym": 1}), [(1, 1, 1)]),
            "us": Aggregate(Counter({"us": 5}), Counter({"general": 5}), [(1, 1, 2)] * 5)}
    merge_case_variants(aggs, stop_words={"us"})
    assert set(aggs) == {"JSON", "US", "us"} and len(aggs["JSON"].occurrences) == 4


def test_export_and_review_refuse_stale_candidates(conn, cfg, course, tmp_path):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    run_all_tasks(conn, cfg, course)
    mode.ingest(conn, "aws-mini", cfg)
    (tmp_path / "aws-mini" / "lesson-03.txt").write_text("Totally different now.\n", encoding="utf-8")
    import_folder(conn, tmp_path / "aws-mini", cfg)
    with pytest.raises(LookupError):
        mode.export(conn, "aws-mini", cfg)
    with pytest.raises(LookupError):
        mode.review_list(conn, "aws-mini", cfg)


def test_changed_contexts_trigger_reevaluation_even_when_reviewed(conn, cfg, course, tmp_path):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    run_all_tasks(conn, cfg, course)
    mode.ingest(conn, "aws-mini", cfg)
    ec2 = conn.execute("SELECT e.id FROM vocab_entry e JOIN vocab_term t ON t.id = e.term_id "
                       "WHERE t.normalized_term = 'EC2'").fetchone()["id"]
    mode.review_decide(conn, "aws-mini", ec2, "approved", {"vietnamese_meaning": "máy ảo EC2"})
    (tmp_path / "aws-mini" / "lesson-03.txt").write_text("An EC2 fleet scales. Spin up EC2 now.\n", encoding="utf-8")
    import_folder(conn, tmp_path / "aws-mini", cfg)
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    keys = {c["key"] for row in tasks.pending_tasks(conn, mode.MODE, course["id"])
            for c in tasks.load_packet(cfg, row)["input"]["candidates"]}
    assert "EC2" in keys  # contexts changed → re-evaluated
    run_all_tasks(conn, cfg, course, confidence=0.95)
    mode.ingest(conn, "aws-mini", cfg)
    row = conn.execute("SELECT status, vietnamese_meaning FROM vocab_entry WHERE id = ?", (ec2,)).fetchone()
    assert tuple(row) == ("approved", "máy ảo EC2")  # the human decision is re-applied
    mode.export(conn, "aws-mini", cfg)  # no IndexError on stale refs


def test_removed_candidate_is_dropped_on_ingest(conn, cfg, course, tmp_path):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    (tmp_path / "aws-mini" / "lesson-01.txt").write_text("Nothing about storage here.\n", encoding="utf-8")
    import_folder(conn, tmp_path / "aws-mini", cfg)
    extract_course_candidates(conn, course["id"], cfg)
    run_all_tasks(conn, cfg, course)
    s = mode.ingest(conn, "aws-mini", cfg)
    assert s["dropped"] > 0 and s["invalid"] == 0


def test_override_reviewed_reevaluates_and_ignores_review_log(conn, cfg, course):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    run_all_tasks(conn, cfg, course)
    mode.ingest(conn, "aws-mini", cfg)
    ec2 = conn.execute("SELECT e.id FROM vocab_entry e JOIN vocab_term t ON t.id = e.term_id "
                       "WHERE t.normalized_term = 'EC2'").fetchone()["id"]
    mode.review_decide(conn, "aws-mini", ec2, "rejected")
    assert mode.prepare(conn, "aws-mini", cfg)["candidates_todo"] == 0
    assert mode.prepare(conn, "aws-mini", cfg, override_reviewed=True)["candidates_todo"] == 1
    run_all_tasks(conn, cfg, course)
    mode.ingest(conn, "aws-mini", cfg, override_reviewed=True)
    assert conn.execute("SELECT status FROM vocab_entry WHERE id = ?", (ec2,)).fetchone()[0] == "auto_approved"


def test_review_edits_are_validated(conn, cfg, course):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    run_all_tasks(conn, cfg, course)
    mode.ingest(conn, "aws-mini", cfg)
    entry = conn.execute("SELECT id FROM vocab_entry LIMIT 1").fetchone()["id"]
    for bad in ({"importance": "high"}, {"term_type": "banana"}, {"selected": None}):
        with pytest.raises(ValueError):
            mode.review_decide(conn, "aws-mini", entry, "approved", bad)


def test_display_form_key_is_remapped_and_flagged(conn, cfg, course):
    extract_course_candidates(conn, course["id"], cfg)
    mode.prepare(conn, "aws-mini", cfg)
    row = tasks.pending_tasks(conn, mode.MODE, course["id"])[0]
    packet = tasks.load_packet(cfg, row)
    result = fake_results(packet)
    cand = next(c for c in packet["input"]["candidates"] if c["term"].lower() != c["key"].lower())
    item = next(i for i in result["results"] if i["key"] == cand["key"])
    item["key"] = cand["term"]
    (cfg["root"] / packet["result_path"]).write_text(json.dumps(result), encoding="utf-8")
    assert mode.ingest(conn, "aws-mini", cfg)["done"] == 1
    status = conn.execute("SELECT e.status FROM vocab_entry e JOIN vocab_term t ON t.id = e.term_id "
                          "WHERE t.normalized_term = ?", (cand["key"],)).fetchone()[0]
    assert status == "needs_review"
