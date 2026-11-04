"""Quality report for one course: AI task outcomes, review rates, knowledge density/coverage, vocabulary mix.

Usage: python evaluations/report.py <course-slug> [--benchmark 4,28,52,88,112]
"""
import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import database  # noqa: E402
from engine.config import load_config, path_of  # noqa: E402
from engine.knowledge.mode import _version as knowledge_version  # noqa: E402


def pct(part: int, whole: int) -> str:
    return f"{part}/{whole} ({100 * part / whole:.0f}%)" if whole else "0/0"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("course")
    parser.add_argument("--benchmark", default="4,28,52,88,112", help="lesson positions of the benchmark set")
    args = parser.parse_args()
    cfg = load_config()
    conn = database.connect(path_of(cfg, "database"))
    course = database.course_by_slug(conn, args.course)
    cid = course["id"]
    q = lambda sql, *p: conn.execute(sql, p).fetchall()  # noqa: E731

    print(f"# Báo cáo chất lượng — {course['title']}\n")
    print("## Task AI")
    for mode, pv in q("SELECT DISTINCT mode, prompt_version FROM ai_task WHERE course_id = ? ORDER BY 1, 2", cid):
        counts = dict(q("SELECT status, COUNT(*) FROM ai_task WHERE course_id = ? AND mode = ? AND prompt_version = ? "
                        "GROUP BY status", cid, mode, pv))
        total = sum(counts.values())
        retried = q("SELECT COUNT(*) FROM ai_task WHERE course_id = ? AND mode = ? AND prompt_version = ? "
                    "AND attempts > 0", cid, mode, pv)[0][0]
        print(f"- {mode} ({pv}): {total} task — {', '.join(f'{k}: {v}' for k, v in sorted(counts.items()))}; "
              f"cần chạy lại ≥ 1 lần: {pct(retried, total)}")

    print("\n## Từ vựng")
    entries = q("SELECT e.selected, e.status, e.term_type, e.importance FROM vocab_entry e JOIN vocab_candidate c "
                "ON c.course_id = e.course_id AND c.term_id = e.term_id AND c.filter_status = 'kept' "
                "AND c.context_hash = e.context_hash WHERE e.course_id = ?", cid)
    kept = q("SELECT COUNT(*) FROM vocab_candidate WHERE course_id = ? AND filter_status = 'kept'", cid)[0][0]
    selected = [e for e in entries if e["selected"]]
    print(f"- Ứng viên giữ lại: {kept}; đã đánh giá (khớp ngữ cảnh hiện tại): {pct(len(entries), kept)}")
    print(f"- Được chọn: {pct(len(selected), len(entries))}; needs_review: "
          f"{pct(sum(e['status'] == 'needs_review' for e in selected), len(selected))} (trong số được chọn)")
    print(f"- Loại: {dict(Counter(e['term_type'] for e in selected).most_common())}")
    for floor in (90, 80, 70, 60):
        print(f"- importance ≥ {floor}: {sum(e['importance'] >= floor for e in selected)}")

    print("\n## Kiến thức")
    lessons = q("SELECT l.position, t.id, t.sentence_count FROM transcript t JOIN lesson l ON l.id = t.lesson_id "
                "WHERE l.course_id = ? AND t.language LIKE 'en%' ORDER BY l.position", cid)
    done = {r[0] for r in q("SELECT transcript_id FROM processing_state WHERE stage = 'knowledge' AND status = 'done' "
                            "AND version = ?", knowledge_version(cfg))}  # current prompt version only
    per_lesson, coverage = [], []
    for pos, tid, n_sent in lessons:
        if tid not in done:
            continue
        per_lesson.append(q("SELECT COUNT(*) FROM knowledge_item i JOIN knowledge_node n ON n.id = i.node_id "
                            "WHERE n.transcript_id = ?", tid)[0][0])
        covered = sum(e - s + 1 for s, e in q("SELECT sentence_start, sentence_end FROM knowledge_node "
                                              "WHERE transcript_id = ? AND node_type = 'topic'", tid))
        coverage.append(covered / n_sent if n_sent else 1)
    items = dict(q("SELECT i.status, COUNT(*) FROM knowledge_item i JOIN knowledge_node n ON n.id = i.node_id "
                   "JOIN transcript t ON t.id = n.transcript_id JOIN lesson l ON l.id = t.lesson_id "
                   "WHERE l.course_id = ? GROUP BY i.status", cid))
    print(f"- Bài đã trích (prompt hiện tại): {pct(len(per_lesson), len(lessons))}")
    if per_lesson:
        print(f"- Item/bài: trung vị {statistics.median(per_lesson)}, min {min(per_lesson)}, max {max(per_lesson)}")
        print(f"- Độ phủ câu của topic: trung vị {statistics.median(coverage):.0%}, thấp nhất {min(coverage):.0%}")
    print(f"- Item theo trạng thái: {items}")
    types = q("SELECT i.item_type, COUNT(*) FROM knowledge_item i JOIN knowledge_node n ON n.id = i.node_id "
              "JOIN transcript t ON t.id = n.transcript_id JOIN lesson l ON l.id = t.lesson_id "
              "WHERE l.course_id = ? GROUP BY 1 ORDER BY 2 DESC", cid)
    print(f"- Loại item: {dict(types)}")
    print(f"- Khái niệm dùng chung: {q('SELECT COUNT(*) FROM concept')[0][0]}, "
          f"quan hệ: {q('SELECT COUNT(*) FROM concept_relation')[0][0]}")

    bench = [int(x) for x in args.benchmark.split(",") if x]
    print(f"\n## Bộ benchmark (bài {', '.join(map(str, bench))})")
    for pos in bench:
        row = q("SELECT t.id FROM transcript t JOIN lesson l ON l.id = t.lesson_id WHERE l.course_id = ? "
                "AND l.position = ? AND t.language LIKE 'en%'", cid, pos)
        if not row:
            continue
        tid = row[0][0]
        if tid not in done:
            print(f"- Bài {pos}: chưa trích với prompt hiện tại")
            continue
        topics = q("SELECT title_json FROM knowledge_node WHERE transcript_id = ? AND node_type = 'topic' "
                   "ORDER BY position", tid)
        n_items = q("SELECT COUNT(*) FROM knowledge_item i JOIN knowledge_node n ON n.id = i.node_id "
                    "WHERE n.transcript_id = ?", tid)[0][0]
        titles = "; ".join(json.loads(t[0]).get("vi", "") for t in topics)
        print(f"- Bài {pos}: {len(topics)} topic, {n_items} item — {titles}")
    conn.close()


if __name__ == "__main__":
    main()
