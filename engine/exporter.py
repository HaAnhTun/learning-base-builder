"""Export Manager (SPEC 2.0 §10.2): serializes each mode's (lean) export model to JSON / CSV / Markdown."""
import csv
import json
from pathlib import Path


def fmt_time(seconds) -> str | None:
    if seconds is None:
        return None
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def write_compact_json(path: Path, model: dict, list_key: str) -> None:
    """Compact JSON with one list entry per line: small files that are still diff/grep friendly."""
    head = {k: v for k, v in model.items() if k != list_key}
    rows = ",\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in model[list_key])
    head_json = json.dumps(head, ensure_ascii=False, separators=(",", ":"))[:-1]
    path.write_text(f'{head_json},"{list_key}":[\n{rows}\n]}}\n', encoding="utf-8")


CSV_FIELDS = ["rank", "term", "type", "importance", "vi", "en", "expansion", "cefr", "frequency", "lessons",
              "example", "example_lesson"]


def write_vocabulary(model: dict, folder: Path, max_terms: int) -> None:
    """vocabulary.csv: every selected term; vocabulary.json/.md: the `max_terms` most important ones."""
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "vocabulary.csv").open("w", encoding="utf-8-sig", newline="") as f:  # BOM so Excel reads UTF-8
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for t in model["terms"]:
            ex = t["example"]
            writer.writerow({**{k: t.get(k) for k in CSV_FIELDS if k in t},
                             "example": ex["text"] if ex else "",
                             "example_lesson": f"{ex['lesson']} @ {ex['time']}" if ex and ex["time"] else ""})

    top = {**model, "total_selected": len(model["terms"]), "terms": model["terms"][:max_terms]}
    write_compact_json(folder / "vocabulary.json", top, "terms")

    out = [f"# Từ vựng — {model['course']}", "",
           f"> Trình độ người học: {model['level']} · {len(top['terms'])} từ quan trọng nhất "
           f"(trên tổng {len(model['terms'])} từ được chọn; danh sách đầy đủ trong vocabulary.csv)", ""]
    for t in top["terms"]:
        head = f"## {t['rank']}. {t['term']}" + (f" ({t['expansion']})" if t.get("expansion") else "")
        meta = (f"*{t['type']}* · quan trọng {t['importance']}/100 · {t['frequency']} lần trong {t['lessons']} bài"
                + (f" · CEFR {t['cefr']}" if t.get("cefr") else ""))
        out += [head, "", meta, "", f"- **Nghĩa:** {t['vi']}", f"- **Definition:** {t['en']}"]
        ex = t["example"]
        if ex:
            out.append(f"- *\"{ex['text']}\"* — bài {ex['lesson']}" + (f" [{ex['time']}]" if ex["time"] else ""))
        out.append("")
    (folder / "vocabulary.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


ITEM_LABELS = {"definition": "Định nghĩa", "concept": "Khái niệm", "key_point": "Ý chính", "process": "Quy trình",
               "example": "Ví dụ", "advantage": "Ưu điểm", "disadvantage": "Nhược điểm", "relation": "Quan hệ",
               "warning": "Lưu ý"}


def write_knowledge(model: dict, folder: Path, languages: list[str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    write_compact_json(folder / "knowledge.json", model, "lessons")
    lang = languages[0]

    def text(value) -> str:
        return " / ".join(str(value[x]) for x in languages if value.get(x)) if isinstance(value, dict) else str(value)

    out = [f"# Kiến thức — {model['course']}", ""]
    chapter = None
    for lesson in model["lessons"]:
        if lesson["chapter"] != chapter:
            chapter = lesson["chapter"]
            out += [f"## {chapter}", ""]
        out += [f"### {lesson['n']}. {lesson['title']}", ""]
        for topic in lesson["topics"]:
            out += [f"#### {text(topic['title'])}" + (f" [{topic['time']}]" if topic["time"] else ""), ""]
            subtopic = None
            for it in topic["items"]:
                if it.get("subtopic") != subtopic:
                    subtopic = it.get("subtopic")
                    if subtopic:
                        out.append(f"- *{text(subtopic)}*")
                indent = "  " if subtopic else ""
                content = it["content"]
                if it["type"] == "process":
                    steps = content.get(lang) or next(iter(content.values()))
                    body = "; ".join(f"{i}) {s}" for i, s in enumerate(steps, 1))
                else:
                    body = text(content)
                when = f" [{it['time']}]" if it["time"] else ""
                out.append(f"{indent}- **{ITEM_LABELS.get(it['type'], it['type'])} — {text(it['title'])}**{when}: {body}")
            out.append("")
    if model.get("concepts"):
        out += ["## Khái niệm dùng chung", ""]
        out += [f"- **{c['name']}** — bài {', '.join(map(str, c['lessons'][:12]))}" for c in model["concepts"]]
        out.append("")
    (folder / "knowledge.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
