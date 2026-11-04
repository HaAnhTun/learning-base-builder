"""`import` command: register a course folder in SQLite (one transaction per file), then clean it (SPEC 3.2)."""
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from engine import database
from engine.cleaner import clean_course
from engine.parser import SUPPORTED

MANIFEST = "_manifest.json"
LOCALE_SUFFIX = re.compile(r"\.([a-z]{2}(?:_[A-Z]{2})?)$")
# A bare 2-letter suffix counts as a language only for common ISO 639-1 codes (so "node.js.md" stays a title).
KNOWN_LANGS = {"ar", "cs", "da", "de", "el", "en", "es", "fa", "fi", "fr", "he", "hi", "hu", "id", "it", "ja", "ko",
               "ms", "nl", "no", "pl", "pt", "ro", "ru", "sv", "th", "tr", "uk", "vi", "zh"}


@dataclass
class ImportResult:
    course_slug: str
    imported: int = 0
    updated: int = 0
    unchanged: int = 0
    cleaned: int = 0
    empty: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def split_locale(stem: str) -> tuple[str, str | None]:
    """'002-setup.en_US' -> ('002-setup', 'en_US'); no recognised suffix -> (stem, None)."""
    m = LOCALE_SUFFIX.search(stem)
    if m is None or ("_" not in m.group(1) and m.group(1) not in KNOWN_LANGS):
        return stem, None
    return stem[:m.start()], m.group(1)


def _files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)


def _manifest_group(folder: Path) -> tuple[dict, list, list]:
    """A locale folder created by fetch: only files listed in its manifest are imported."""
    manifest = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    course = {"slug": manifest["slug"], "title": manifest["title"], "source": "udemy",
              "external_id": str(manifest["course_id"]), "url": manifest.get("url"), "host": manifest.get("host")}
    listed = {lec["filename"]: lec for lec in manifest["lectures"]}
    entries, ignored = [], []
    for path in _files(folder):
        lec = listed.get(path.name)
        if lec is None:
            ignored.append(f"{folder.name}/{path.name}")
            continue
        entries.append((path, {
            "external_id": str(lec["lecture_id"]),
            "position": lec["position"],
            "chapter": lec.get("chapter_title"),
            "chapter_index": lec.get("chapter_index"),
            "title": lec["title"],
            "language": manifest["locale_id"],
            "caption_source": lec.get("source", "file"),
            "filename": f"{folder.name}/{path.name}",
        }))
    return course, entries, ignored


def _local_group(folder: Path, subdirs: list[Path], default_lang: str) -> tuple[dict, list, list]:
    """Hand-placed files: flat in the course folder, or in <lang>/ subfolders (folder name = language)."""
    files = [(p, None) for p in _files(folder)] + [(p, sub.name) for sub in subdirs for p in _files(sub)]
    bases = sorted({split_locale(p.stem)[0] for p, _ in files})
    course = {"slug": folder.name, "title": folder.name, "source": "local"}
    entries, ignored, taken = [], [], set()
    for path, sub_lang in files:
        base, suffix_lang = split_locale(path.stem)
        language = sub_lang or suffix_lang or default_lang
        filename = f"{sub_lang}/{path.name}" if sub_lang else path.name
        if (base, language) in taken:  # e.g. a.vtt and a.txt: keep the first file, skip the next
            ignored.append(filename)
            continue
        taken.add((base, language))
        entries.append((path, {
            "external_id": base,
            "position": bases.index(base) + 1,
            "chapter": None,
            "chapter_index": None,
            "title": base,
            "language": language,
            "caption_source": "file",
            "filename": filename,
        }))
    return course, entries, ignored


def import_folder(conn, folder: Path, cfg: dict) -> ImportResult:
    """folder: a course folder (all locales) or a single locale folder that has a _manifest.json."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {folder}")
    if (folder / MANIFEST).exists():
        groups = [_manifest_group(folder)]
    else:
        subdirs = sorted(p for p in folder.iterdir() if p.is_dir())
        groups = [_manifest_group(sub) for sub in subdirs if (sub / MANIFEST).exists()]
        local_subdirs = [sub for sub in subdirs if not (sub / MANIFEST).exists()]
        local = _local_group(folder, local_subdirs, cfg["default_lang"])
        if groups:  # never mix hand-placed files into a fetched course (SPEC 3)
            groups[-1][2].extend(info["filename"] for _, info in local[1])
            groups[-1][2].extend(local[2])
        else:
            groups.append(local)

    result = ImportResult(course_slug=groups[0][0]["slug"])
    course_ids = []
    for course, entries, ignored in groups:
        result.ignored.extend(ignored)
        existing = conn.execute("SELECT source FROM course WHERE slug = ?", (course["slug"],)).fetchone()
        if existing and existing["source"] == "udemy" and course["source"] != "udemy":
            result.warnings.append(f"Bỏ qua thư mục tự đặt: slug '{course['slug']}' đã là khóa Udemy.")
            result.ignored.extend(info["filename"] for _, info in entries)
            continue
        with conn:
            course_id = database.upsert_course(conn, **course)
        course_ids.append(course_id)
        for path, info in entries:
            _register_file(conn, course_id, path, info, cfg["root"], result)
    for course_id in dict.fromkeys(course_ids):
        cleaned = clean_course(conn, course_id, cfg)
        result.cleaned += cleaned["cleaned"]
        result.empty.extend(cleaned["empty"])
    return result


def _source_path(path: Path, root: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _register_file(conn, course_id: int, path: Path, info: dict, root: Path, result: ImportResult) -> None:
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    source_path = _source_path(path, root)
    with conn:  # one file = one transaction = one checkpoint
        lesson_id = database.upsert_lesson(
            conn, course_id=course_id, external_id=info["external_id"], position=info["position"],
            title=info["title"], chapter=info["chapter"], chapter_index=info["chapter_index"],
        )
        existing = database.get_transcript(conn, lesson_id, info["language"])
        if existing and existing["content_hash"] == content_hash:
            if (existing["filename"], existing["source_path"], existing["caption_source"]) != (
                    info["filename"], source_path, info["caption_source"]):
                conn.execute("UPDATE transcript SET filename = ?, source_path = ?, caption_source = ? WHERE id = ?",
                             (info["filename"], source_path, info["caption_source"], existing["id"]))
            result.unchanged += 1
            return
        database.register_transcript(
            conn, lesson_id=lesson_id, language=info["language"], caption_source=info["caption_source"],
            filename=info["filename"], source_path=source_path, content_hash=content_hash,
        )
        if existing:
            result.updated += 1
        else:
            result.imported += 1
