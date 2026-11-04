"""Export Manager (SPEC 2.0 §10.2): serializes each mode's export model to JSON / CSV / Markdown."""
import csv
import json
from pathlib import Path


def _fmt_time(seconds) -> str:
    if seconds is None:
        return ""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _write_json(path: Path, model: dict) -> None:
    path.write_text(json.dumps(model, ensure_ascii=False, indent=1), encoding="utf-8")


CSV_FIELDS = ["rank", "term", "term_type", "importance", "vietnamese_meaning", "english_definition", "expansion",
              "cefr_level", "frequency", "lesson_count", "example", "example_lesson", "status", "reason"]


def write_vocabulary(model: dict, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    _write_json(folder / "vocabulary.json", model)

    with (folder / "vocabulary.csv").open("w", encoding="utf-8-sig", newline="") as f:  # BOM so Excel reads UTF-8
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for t in model["terms"]:
            example = t["examples"][0] if t["examples"] else None
            writer.writerow({**{k: t.get(k) for k in CSV_FIELDS if k in t},
                             "example": example["text"] if example else "",
                             "example_lesson": f"{example['lesson']} @ {_fmt_time(example['start'])}" if example else ""})

    out = [f"# Từ vựng — {model['course']['title']}", "",
           f"> Trình độ người học: {model['learner_level']} · {len(model['terms'])} mục · xếp theo mức quan trọng", ""]
    for t in model["terms"]:
        head = f"## {t['rank']}. {t['term']}"
        if t.get("expansion"):
            head += f" ({t['expansion']})"
        out += [head, "",
                f"*{t['term_type']}* · quan trọng {t['importance']}/100 · {t['frequency']} lần trong {t['lesson_count']} bài"
                + (f" · CEFR {t['cefr_level']}" if t.get("cefr_level") else ""), "",
                f"- **Nghĩa:** {t['vietnamese_meaning']}",
                f"- **Definition:** {t['english_definition']}"]
        for e in t["examples"]:
            out.append(f"- *\"{e['text']}\"* — bài {e['lesson']} [{_fmt_time(e['start'])}]")
        out.append("")
    (folder / "vocabulary.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def write_knowledge(model: dict, folder: Path, languages: list[str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    _write_json(folder / "knowledge.json", model)
    lang = languages[0]
    label = {"definition": "Định nghĩa", "concept": "Khái niệm", "key_point": "Ý chính", "process": "Quy trình",
             "example": "Ví dụ", "advantage": "Ưu điểm", "disadvantage": "Nhược điểm", "relation": "Quan hệ",
             "warning": "Lưu ý"}

    def text(value: dict) -> str:
        return " / ".join(str(value[x]) for x in languages if value.get(x)) if isinstance(value, dict) else str(value)

    def items_md(items: list[dict], indent: str) -> list[str]:
        lines = []
        for it in items:
            src = it["source"]
            when = f" [{_fmt_time(src['start'])}]" if src.get("start") is not None else ""
            content = it["content"]
            if it["item_type"] == "process":
                steps = content.get(lang) or next(iter(content.values()))
                body = "; ".join(f"{i}) {s}" for i, s in enumerate(steps, 1))
            else:
                body = text(content)
            lines.append(f"{indent}- **{label.get(it['item_type'], it['item_type'])} — {text(it['title'])}**{when}: {body}")
        return lines

    out = [f"# Kiến thức — {model['course']['title']}", ""]
    for ch in model["chapters"]:
        out += [f"## Chapter {ch['index']}: {ch['title']}", ""]
        for lesson in ch["lessons"]:
            out += [f"### {lesson['position']}. {lesson['title']}", ""]
            for topic in lesson["topics"]:
                src = topic["source"]
                when = f" [{_fmt_time(src['start'])}]" if src.get("start") is not None else ""
                out.append(f"#### {text(topic['title'])}{when}")
                out.append("")
                out += items_md(topic["items"], "")
                for sub in topic["subtopics"]:
                    out.append(f"- *{text(sub['title'])}*")
                    out += items_md(sub["items"], "  ")
                out.append("")
    if model.get("concepts"):
        out += ["## Khái niệm dùng chung", ""]
        for c in model["concepts"]:
            out.append(f"- **{c['name']}** — {len(c['mentions'])} lần nhắc: "
                       + ", ".join(f"bài {m['lesson']}" for m in c["mentions"][:10]))
        out.append("")
    (folder / "knowledge.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
