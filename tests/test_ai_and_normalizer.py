import json

import pytest

from engine.ai import tasks
from engine.ai.validate import ValidationError, mentions, soft_status, validate
from engine.normalizer import is_abbreviation, is_acronym, normalize_name, normalize_tokens


def test_acronym_and_abbreviation_detection():
    assert all(is_acronym(t) for t in ["S3", "EC2", "IAM", "API", "IPv4", "OAuth", "JSON"])
    assert not any(is_acronym(t) for t in ["Claude", "I", "A", "api"])
    assert is_abbreviation("k8s") and not is_abbreviation("kates")


def test_normalization_keeps_acronyms_and_merges_plurals():
    assert normalize_tokens([("EC2", "ec2"), ("instances", "instance")]) == "EC2 instance"
    assert normalize_tokens([("APIs", None)]) == "API"
    assert normalize_name("Dead – Letter  Queue") == "dead-letter queue"
    assert normalize_name("Model Context Protocol (MCP)") == "model context protocol MCP"


SCHEMA = {"type": "object", "required": ["a"], "additionalProperties": False, "properties": {
    "a": {"type": "array", "maxItems": 2, "items": {"type": "integer", "minimum": 0, "maximum": 10}},
    "b": {"type": ["string", "null"], "minLength": 1}, "c": {"enum": ["x", "y"]}}}


def test_validate_accepts_and_rejects():
    validate({"a": [1, 2], "b": None, "c": "x"}, SCHEMA)
    for bad in ({}, {"a": [1, 2, 3]}, {"a": [11]}, {"a": [True]}, {"a": [], "b": " "}, {"a": [], "c": "z"},
                {"a": [], "extra": 1}):
        with pytest.raises(ValidationError):
            validate(bad, SCHEMA)


def test_soft_helpers():
    assert mentions("We spin up EC2 instances quickly.", "spin up")
    assert mentions("Retries use exponential backoff.", "exponential backoffs")
    assert not mentions("Nothing relevant here.", "context window")
    assert soft_status(0.9, 0.7, True) == "auto_approved"
    assert soft_status(0.5, 0.7, True) == "needs_review"
    assert soft_status(0.9, 0.7, False) == "needs_review"


def test_task_lifecycle_cache_and_retries(conn, cfg):
    with conn:
        conn.execute("INSERT INTO course (id, title, source, slug, created_at) VALUES (1, 'C', 'local', 'c', 'now')")
    kwargs = dict(mode="vocab_eval", prompt_version="v1", course_id=1, task_input={"x": 1}, hash_extra={},
                  output_schema={}, instructions="i.md")
    tid = tasks.ensure_task(conn, cfg, **kwargs)
    assert tid.startswith("vocab_eval-") and len(tid) == len("vocab_eval-") + 12
    assert tasks.ensure_task(conn, cfg, **kwargs) == tid  # still pending → same task, no duplicate
    row = tasks.pending_tasks(conn, "vocab_eval", 1)[0]
    packet = tasks.load_packet(cfg, row)
    assert packet["result_path"] == f"data/work/tasks/vocab_eval/{tid}.result.json"
    assert tasks.load_result(cfg, row) is None

    (cfg["root"] / row["result_path"]).write_text("{bad json", encoding="utf-8")
    with pytest.raises(ValueError):
        tasks.load_result(cfg, row)
    with conn:
        assert tasks.mark_invalid(conn, cfg, tid, "bad") == "invalid"
    assert tasks.ensure_task(conn, cfg, **kwargs) == tid  # re-armed for retry, old result removed
    assert not (cfg["root"] / row["result_path"]).exists()
    with conn:
        tasks.mark_invalid(conn, cfg, tid, "bad")
        assert tasks.mark_invalid(conn, cfg, tid, "bad") == "failed"  # max_retries = 2 → third failure
    assert tasks.ensure_task(conn, cfg, **kwargs) is None

    other = tasks.ensure_task(conn, cfg, **{**kwargs, "task_input": {"x": 2}})
    with conn:
        tasks.mark_done(conn, other)
    assert tasks.ensure_task(conn, cfg, **{**kwargs, "task_input": {"x": 2}}) is None  # cached
    assert tasks.ensure_task(conn, cfg, **{**kwargs, "task_input": {"x": 2}, "hash_extra": {"level": "C1"}})


def test_batches():
    rows = [{"task_path": f"t{i}.json"} for i in range(7)]
    assert tasks.batches(rows, 3) == [["t0.json", "t1.json", "t2.json"], ["t3.json", "t4.json", "t5.json"],
                                      ["t6.json"]]


def test_compute_hash_is_order_independent():
    assert tasks.compute_hash({"a": 1, "b": [1, 2]}) == tasks.compute_hash(json.loads('{"b": [1, 2], "a": 1}'))


@pytest.mark.parametrize("broken, expected", [
    # '}' where a ']' was needed (subtopics array not closed before the topic)
    ('{"topics": [{"subtopics": [{"items": [{"a": 1}]}}, {"subtopics": []}]}',
     {"topics": [{"subtopics": [{"items": [{"a": 1}]}]}, {"subtopics": []}]}),
    # a key written while an array is still open
    ('{"topics": [{"subtopics": [{"items": []}, "items": [1]}]}',
     {"topics": [{"subtopics": [{"items": []}], "items": [1]}]}),
    # brackets inside strings are left alone
    ('{"t": ["a ] } [ b"}', {"t": ["a ] } [ b"]}),
])
def test_rebalance_brackets(broken, expected):
    with pytest.raises(json.JSONDecodeError):
        json.loads(broken)
    assert json.loads(tasks.rebalance_brackets(broken)) == expected
