"""Transcript Cleaner (SPEC 2.0 §5): cues → timestamped sentences + paragraphs, written as Clean Dataset JSON.

Deterministic, no AI. Raw files are never modified.
"""
import json
import re
from dataclasses import replace
from pathlib import Path

from engine import database
from engine.parser import parse_file
from engine.vtt_parser import Cue

CLEANER_VERSION = "2"
SCHEMA_VERSION = 1
ADJACENT_SECONDS = 0.05      # two cues are adjacent when start <= previous end + 0.05s
FLASH_CUE_SECONDS = 0.1      # very short "flash" cue emitted by rolling captions
MAX_AVG_SENTENCE_WORDS = 40  # above this the caption is treated as unpunctuated → one sentence per cue
# Latin enders need whitespace after them; CJK enders split even without whitespace.
SENTENCE_END = re.compile(r"(?<=[.!?…])\s+|(?<=[。！？])\s*")


def _repeated_prefix(prev_lines: list[str], lines: list[str]) -> int:
    """Number of leading lines of this cue that repeat the previous cue's trailing lines verbatim.

    At least one new line must remain after them, otherwise it is not a rolling caption.
    """
    for k in range(min(len(prev_lines), len(lines) - 1), 0, -1):
        if lines[:k] == prev_lines[-k:]:
            return k
    return 0


def remove_rolling(cues: list[Cue]) -> list[Cue]:
    """Drop only rolling-caption repeats (SPEC 5.1); intentional repeats in non-overlapping cues are kept."""
    out: list[Cue] = []
    prev: Cue | None = None  # previous original (untrimmed) cue, used for comparison
    for cue in cues:
        adjacent = (prev is not None and cue.start is not None and prev.end is not None
                    and cue.start <= prev.end + ADJACENT_SECONDS)
        if adjacent and cue.lines == prev.lines:
            if cue.start < prev.end or cue.end - cue.start < FLASH_CUE_SECONDS:
                out[-1] = replace(out[-1], end=max(out[-1].end, cue.end))
                prev = replace(prev, end=max(prev.end, cue.end))
                continue
        elif adjacent:
            k = _repeated_prefix(prev.lines, cue.lines)
            if k:
                out.append(replace(cue, lines=cue.lines[k:]))
                prev = cue
                continue
        out.append(replace(cue))
        prev = cue
    return out


def _words(text: str) -> int:
    return len(text.split())


def _sentences_of_group(cues: list[Cue]) -> list[tuple[str, float | None, float | None]]:
    spans, pieces, pos = [], [], 0
    for cue in cues:
        text = cue.text
        spans.append((pos, pos + len(text), cue))
        pieces.append(text)
        pos += len(text) + 1
    full = " ".join(pieces)
    bounds, start = [], 0
    for m in SENTENCE_END.finditer(full):
        if m.end() > start:
            bounds.append((start, m.start()))
            start = m.end()
    bounds.append((start, len(full)))
    bounds = [(s, e) for s, e in bounds if full[s:e].strip()]
    if not bounds:
        return []
    if _words(full) / len(bounds) > MAX_AVG_SENTENCE_WORDS:
        return [(cue.text, cue.start, cue.end) for cue in cues]
    out, first = [], 0
    for s, e in bounds:
        while spans[first][1] <= s:  # first cue containing the sentence start
            first += 1
        last = first
        while last + 1 < len(spans) and spans[last + 1][0] < e:
            last += 1
        out.append((full[s:e].strip(), spans[first][2].start, spans[last][2].end))
    return out


def clean_cues(cues: list[Cue], *, pause_seconds: float, max_sentences: int) -> tuple[list[dict], list[list[int]]]:
    """Return (sentences, paragraphs); paragraphs are inclusive [start_id, end_id] ranges."""
    cues = remove_rolling(cues)
    groups: list[list[Cue]] = []
    for cue in cues:
        if cue.para_break or not groups:
            groups.append([])
        groups[-1].append(cue)

    sentences: list[dict] = []
    paragraphs: list[list[int]] = []
    timed = bool(cues) and cues[0].start is not None
    for group in groups:
        group_start = len(sentences)
        for text, start, end in _sentences_of_group(group):
            sentences.append({"id": len(sentences), "start": start, "end": end, "text": text})
        if timed:
            for s in sentences[group_start:]:
                prev = sentences[s["id"] - 1] if s["id"] > group_start else None
                if (prev is None or s["start"] - prev["end"] >= pause_seconds
                        or s["id"] - paragraphs[-1][0] >= max_sentences):
                    paragraphs.append([s["id"], s["id"]])
                else:
                    paragraphs[-1][1] = s["id"]
        elif len(sentences) > group_start:
            paragraphs.append([group_start, len(sentences) - 1])
    return sentences, paragraphs


def slug_for(title: str, fallback: str) -> str:
    from engine.fetcher import slugify

    return slugify(title, fallback)


def clean_path_for(clean_dir: Path, course_slug: str, row) -> Path:
    name = f"{row['position']:03d}-{slug_for(row['lesson_title'], 'lesson-' + str(row['lesson_external_id']))}.json"
    return clean_dir / course_slug / row["language"] / name


def build_document(course, row, sentences, paragraphs) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "cleaner_version": CLEANER_VERSION,
        "course": {"slug": course["slug"], "title": course["title"], "source": course["source"],
                   "external_id": course["external_id"]},
        "lesson": {"external_id": row["lesson_external_id"], "position": row["position"],
                   "chapter_index": row["chapter_index"], "chapter_title": row["chapter"],
                   "title": row["lesson_title"]},
        "language": row["language"],
        "caption_source": row["caption_source"],
        "source_file": row["source_path"],
        "source_sha256": row["content_hash"],
        "word_count": sum(_words(s["text"]) for s in sentences),
        "sentences": sentences,
        "paragraphs": paragraphs,
    }


def load_document(root: Path, clean_path: str) -> dict:
    return json.loads((root / clean_path).read_text(encoding="utf-8"))


def clean_course(conn, course_id: int, cfg: dict, *, force: bool = False) -> dict:
    """Clean new/changed transcripts (or all with force) and refresh metadata-only changes.

    Extracted data is invalidated only when the raw content or cleaner_version changed (SPEC 9.5), because
    only then can sentence ids change.
    """
    root: Path = cfg["root"]
    clean_dir = root / cfg["paths"]["clean_dir"]
    course = conn.execute("SELECT * FROM course WHERE id = ?", (course_id,)).fetchone()
    result = {"cleaned": 0, "refreshed": 0, "unchanged": 0, "empty": []}
    for row in database.course_transcripts(conn, course_id):
        state = database.get_state(conn, row["id"], "clean")
        target = clean_path_for(clean_dir, course["slug"], row)
        old_path = root / row["clean_path"] if row["clean_path"] else None
        content_current = (state is not None and state["status"] == "done"
                           and state["input_hash"] == row["content_hash"] and state["version"] == CLEANER_VERSION)
        if content_current and not force and old_path is not None and old_path.exists():
            old = json.loads(old_path.read_text(encoding="utf-8"))
            doc = build_document(course, row, old["sentences"], old["paragraphs"])
            if doc == old and old_path == target:
                result["unchanged"] += 1
                continue
            _write(conn, root, row, doc, target, old_path)  # metadata/path refresh, sentence ids unchanged
            result["refreshed"] += 1
            continue
        source = Path(row["source_path"])
        cues = parse_file(source if source.is_absolute() else root / source)
        sentences, paragraphs = clean_cues(cues, pause_seconds=cfg["clean"]["paragraph_pause_seconds"],
                                           max_sentences=cfg["clean"]["max_sentences_per_paragraph"])
        if not sentences:
            result["empty"].append(row["filename"])
        doc = build_document(course, row, sentences, paragraphs)
        content_changed = state is not None and not content_current and (
            state["input_hash"] != row["content_hash"] or state["version"] != CLEANER_VERSION)
        _write(conn, root, row, doc, target, old_path, invalidate=content_changed)
        result["cleaned"] += 1
    return result


def _write(conn, root: Path, row, doc: dict, target: Path, old_path: Path | None, invalidate: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    if old_path is not None and old_path != target and old_path.exists():
        old_path.unlink()  # lesson renamed or moved → clean file name changed
    with conn:
        conn.execute(
            "UPDATE transcript SET clean_path = ?, cleaner_version = ?, sentence_count = ?, word_count = ? WHERE id = ?",
            (target.relative_to(root).as_posix(), CLEANER_VERSION, len(doc["sentences"]), doc["word_count"], row["id"]))
        if invalidate:
            database.invalidate_extracted(conn, row["id"])
        database.set_state(conn, row["id"], "clean", "done", row["content_hash"], CLEANER_VERSION)
