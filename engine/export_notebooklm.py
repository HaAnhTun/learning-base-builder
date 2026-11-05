"""Use case 1 (SPEC 2.0 §6): export the Clean Dataset as Markdown for NotebookLM. No AI; deterministic output."""
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from engine import database
from engine.cleaner import load_document

INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM\d|LPT\d)$", re.IGNORECASE)
MARKDOWN_LEADER = re.compile(r"^([#>])")
SOURCE_LIMITS = {"Free": 50, "Plus": 100, "Pro": 300}


@dataclass
class Chapter:
    index: int
    title: str
    lessons: list[dict] = field(default_factory=list)  # Clean Dataset documents


@dataclass
class ExportResult:
    folder: Path
    files: list[str]
    lessons: int
    warnings: list[str]


def normalize_lang(value: str) -> str:
    """'EN' -> 'en', 'en-us' / 'en_us' -> 'en_US' (same form as Udemy locale ids)."""
    parts = value.strip().replace("-", "_").split("_")
    return parts[0].lower() + (f"_{parts[1].upper()}" if len(parts) > 1 else "")


def safe_filename(name: str, max_len: int = 120) -> str:
    name = INVALID_FILENAME.sub("", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(". ")
    name = name[:max_len].rstrip(". ") or "untitled"
    return f"_{name}" if WINDOWS_RESERVED.match(name) else name


def _escape(text: str) -> str:
    """Keep transcript text from turning into Markdown headings/quotes."""
    return MARKDOWN_LEADER.sub(r"\\\1", text)


def render_lesson(doc: dict, total_lessons: int, heading: str) -> str:
    lesson = doc["lesson"]
    meta = (f"> Course: {doc['course']['title']} · Lesson {lesson['position']}/{total_lessons} · "
            f"{doc['language']} · {doc['caption_source']} caption")
    out = [f"{heading} {lesson['position']}. {lesson['title']}", "", meta, ""]
    sentences = doc["sentences"]
    for start, end in doc["paragraphs"]:  # no time markers (user request 2026-11-05); timestamps stay in Clean Dataset
        out += [_escape(" ".join(s["text"] for s in sentences[start:end + 1])), ""]
    return "\n".join(out)


def render_chapters(chapters: list[Chapter], total_lessons: int) -> str:
    parts = []
    for ch in chapters:
        parts.append(f"# Chapter {ch.index}: {ch.title}\n")
        parts.extend(render_lesson(doc, total_lessons, "##") for doc in ch.lessons)
    return "\n".join(parts).rstrip() + "\n"


def _chapter_parts(chapters: list[Chapter], max_words: int) -> list[list[Chapter]]:
    """Split a group of chapters into parts of <= max_words, cutting only at lesson boundaries."""
    parts, words = [[]], 0
    for ch in chapters:
        for doc in ch.lessons:
            if parts[-1] and words + doc["word_count"] > max_words:
                parts.append([])
                words = 0
            if not parts[-1] or parts[-1][-1].index != ch.index:
                parts[-1].append(Chapter(ch.index, ch.title))
            parts[-1][-1].lessons.append(doc)
            words += doc["word_count"]
    return parts


def _with_parts(name: str, parts: list) -> list[tuple[str, list[Chapter]]]:
    if len(parts) == 1:
        return [(f"{name}.md", parts[0])]
    return [(f"{name} (part {i}).md", part) for i, part in enumerate(parts, 1)]


def build_files(course_title: str, chapters: list[Chapter], by: str, max_sources: int, max_words: int,
                total_lessons: int | None = None) -> tuple[dict[str, tuple[str, list[Chapter]]], list[str]]:
    """Return ({file name: (content, chapters in the file)}, warnings)."""
    total = total_lessons or sum(len(ch.lessons) for ch in chapters)
    files: dict[str, tuple[str, list[Chapter]]] = {}
    warnings: list[str] = []
    if by == "lesson":
        width = max(3, len(str(total)))
        for ch in chapters:
            for doc in ch.lessons:
                name = safe_filename(f"{doc['lesson']['position']:0{width}d} - {doc['lesson']['title']}")
                files[f"{name}.md"] = (render_lesson(doc, total, "#").rstrip() + "\n",
                                       [Chapter(ch.index, ch.title, [doc])])
        for tier, limit in SOURCE_LIMITS.items():
            if len(files) > limit:
                warnings.append(f"{len(files)} file > giới hạn {limit} nguồn/notebook của gói {tier}.")
        return files, warnings

    if by == "course":
        groups = [(safe_filename(course_title), chapters)]
    else:  # chapter
        if len(chapters) <= max_sources:
            groups = [(safe_filename(f"{i:02d} - {ch.title}"), [ch]) for i, ch in enumerate(chapters, 1)]
        else:
            size = math.ceil(len(chapters) / max_sources)
            groups = [(f"Vol {v:02d} (Chapters {chapters[i].index}–{chapters[min(i + size, len(chapters)) - 1].index})",
                       chapters[i:i + size]) for v, i in enumerate(range(0, len(chapters), size), 1)]
    for name, group in groups:
        for filename, part in _with_parts(name, _chapter_parts(group, max_words)):
            files[filename] = (render_chapters(part, total), part)
    if len(files) > max_sources:
        warnings.append(f"{len(files)} file > notebooklm.max_sources ({max_sources}).")
    return files, warnings


def render_index(course, lang: str, by: str, files: dict[str, tuple[str, list[Chapter]]]) -> str:
    lessons = sum(len(ch.lessons) for _, chs in files.values() for ch in chs)
    source = course["source"] + (f" ({course['host']}{course['url']})" if course["url"] else "")
    out = [f"# {course['title']}", "", f"- Nguồn: {source}", f"- Ngôn ngữ: {lang}", f"- Đơn vị xuất: {by}",
           f"- Số bài: {lessons} · Số file: {len(files)}", ""]
    for filename, (_, chapters) in files.items():
        out += [f"## {filename}", ""]
        for ch in chapters:
            out.append(f"- Chapter {ch.index}: {ch.title}")
            out += [f"  - {doc['lesson']['position']}. {doc['lesson']['title']}" for doc in ch.lessons]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def load_chapters(conn, course, lang: str, root: Path) -> list[Chapter]:
    rows = database.pick_one_per_lesson(database.course_transcripts(conn, course["id"], lang), lang.split("_")[0])
    chapters: dict[tuple, Chapter] = {}
    for row in rows:
        if not row["clean_path"]:
            continue
        doc = load_document(root, row["clean_path"])
        key = (row["chapter_index"] or 1, row["chapter"] or course["title"])
        if key not in chapters:
            chapters[key] = Chapter(key[0], key[1])
        chapters[key].lessons.append(doc)
    return sorted(chapters.values(), key=lambda ch: ch.index)


def course_languages(conn, course_id: int) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT t.language FROM transcript t JOIN lesson l ON l.id = t.lesson_id WHERE l.course_id = ? "
        "ORDER BY 1", (course_id,))]


def export_course(conn, course_slug: str, cfg: dict, *, by: str | None = None, lang: str | None = None) -> ExportResult:
    root: Path = cfg["root"]
    nb = cfg["notebooklm"]
    by = by or nb["by"]
    lang = normalize_lang(lang or cfg["default_lang"])
    course = database.course_by_slug(conn, course_slug)
    chapters = load_chapters(conn, course, lang, root)
    if not chapters:
        raise LookupError(f"Khóa '{course_slug}' không có transcript đã làm sạch cho ngôn ngữ '{lang}'.")
    total = conn.execute("SELECT MAX(position) FROM lesson WHERE course_id = ?", (course["id"],)).fetchone()[0]
    files, warnings = build_files(course["title"], chapters, by, nb["max_sources"], nb["max_words_per_file"], total)
    folder = root / cfg["paths"]["export_dir"] / "notebooklm" / course_slug / lang
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.md"):  # re-export replaces everything the previous export wrote
        old.unlink()
    for name, (content, _) in files.items():
        (folder / name).write_text(content, encoding="utf-8")
    (folder / "index.md").write_text(render_index(course, lang, by, files), encoding="utf-8")
    return ExportResult(folder, list(files), sum(len(ch.lessons) for ch in chapters), warnings)
