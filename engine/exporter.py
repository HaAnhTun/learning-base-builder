"""Export Manager (SPEC 2.0 §10.2): serializes each mode's (lean) export model to JSON / CSV / Markdown."""
import csv
import json
from pathlib import Path


def write_compact_json(path: Path, model: dict, list_key: str) -> None:
    """Compact JSON with one list entry per line: small files that are still diff/grep friendly."""
    head = {k: v for k, v in model.items() if k != list_key}
    rows = ",\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in model[list_key])
    head_json = json.dumps(head, ensure_ascii=False, separators=(",", ":"))[:-1]
    path.write_text(f'{head_json},"{list_key}":[\n{rows}\n]}}\n', encoding="utf-8")


CSV_FIELDS = ["rank", "term", "ipa", "meaning", "pos", "domain", "domain_usage", "example", "example_vi", "compare",
              "expansion", "type", "importance", "en", "cefr", "frequency", "lessons"]
CARD_FIELDS = ["rank", "term", "ipa", "meaning", "pos", "domain", "example", "compare", "expansion", "type",
               "importance"]  # vocabulary.json: the study card only (format asked by the user 2026-11-08)


CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def in_study_list(importance: int, cefr: str | None, level: str | None, min_importance: int) -> bool:
    """Important enough, and not an everyday word tagged below the learner's level (e.g. a B2 word for C1)."""
    below = cefr in CEFR_ORDER and level in CEFR_ORDER and CEFR_ORDER.index(cefr) < CEFR_ORDER.index(level)
    return importance >= min_importance and not below


def write_vocabulary(model: dict, folder: Path) -> None:
    """vocabulary.csv: every selected term; vocabulary.json/.md: study cards for the study list (in_study_list —
    sized by the course content, not a fixed count), most important and longest first."""
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "vocabulary.csv").open("w", encoding="utf-8-sig", newline="") as f:  # BOM so Excel reads UTF-8
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for t in model["terms"]:
            domain, ex = t["domain"] or {}, t["example"] or {}
            writer.writerow({**{k: t.get(k) for k in CSV_FIELDS if k in t}, "domain": domain.get("field"),
                             "domain_usage": domain.get("text"), "example": ex.get("en"), "example_vi": ex.get("vi")})

    study = [{k: t[k] for k in CARD_FIELDS} for t in model["terms"]
             if in_study_list(t["importance"], t["cefr"], model["level"], model["min_importance"])]
    top = {**model, "total_selected": len(model["terms"]), "count": len(study), "terms": study}
    write_compact_json(folder / "vocabulary.json", top, "terms")

    out = [f"# Từ vựng — {model['course']}", "",
           f"> Trình độ người học: {model['level']} · {len(study)} từ cần học (mức quan trọng ≥ "
           f"{model['min_importance']}, bỏ từ phổ thông dưới trình độ; tổng {len(model['terms'])} từ được chọn nằm "
           f"trong vocabulary.csv)", ""]
    out += [line for t in study for line in vocabulary_card(t)]
    (folder / "vocabulary.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def vocabulary_card(t: dict) -> list[str]:
    """One term in the card format: heading with IPA, then Nghĩa / Từ loại / Trong IT / Ví dụ / Phân biệt."""
    head = t["term"] + (f" ({t['expansion']})" if t.get("expansion") else "") + (f" {t['ipa']}" if t.get("ipa") else "")
    out = [f"## {head}", "", f"- Nghĩa: {t['meaning']}"]
    if t.get("pos"):
        out.append(f"- Từ loại: {t['pos']}.")
    if t.get("domain"):
        out.append(f"- Trong {t['domain']['field']}: {t['domain']['text']}")
    if t.get("example"):
        out.append(f"- Ví dụ: {t['example']['en']} ({t['example']['vi']})")
    if t.get("compare"):
        out.append(f"- Phân biệt: {t['compare']}")
    return out + [""]


ITEM_LABELS = {"definition": "Định nghĩa", "concept": "Khái niệm", "key_point": "Ý chính", "process": "Quy trình",
               "example": "Ví dụ", "advantage": "Ưu điểm", "disadvantage": "Nhược điểm", "relation": "Quan hệ",
               "warning": "Lưu ý"}


CORE_IMPORTANCE = 80  # knowledge items marked ★ in knowledge.md


def write_knowledge(model: dict, folder: Path, languages: list[str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    write_compact_json(folder / "knowledge.json", model, "lessons")
    lang = languages[0]

    def text(value) -> str:
        return " / ".join(str(value[x]) for x in languages if value.get(x)) if isinstance(value, dict) else str(value)

    out = [f"# Kiến thức — {model['course']}", "", f"★ = cốt lõi (quan trọng ≥ {CORE_IMPORTANCE}/100).", ""]
    chapter = None
    for lesson in model["lessons"]:
        if lesson["chapter"] != chapter:
            chapter = lesson["chapter"]
            out += [f"## {chapter}", ""]
        out += [f"### {lesson['n']}. {lesson['title']}", ""]
        for topic in lesson["topics"]:
            out += [f"#### {text(topic['title'])}", ""]
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
                star = "★ " if it.get("importance", 0) >= CORE_IMPORTANCE else ""
                out.append(f"{indent}- {star}**{ITEM_LABELS.get(it['type'], it['type'])} — {text(it['title'])}**: {body}")
            out.append("")
    if model.get("concepts"):
        out += ["## Khái niệm dùng chung", ""]
        out += [f"- **{c['name']}** — bài {', '.join(map(str, c['lessons'][:12]))}" for c in model["concepts"]]
        out.append("")
    (folder / "knowledge.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
