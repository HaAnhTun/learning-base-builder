"""Lệnh import: nhập một thư mục khóa học vào SQLite, mỗi file một transaction (checkpoint)."""
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from engine import database
from engine.parser import SUPPORTED, parse_text
from engine.segmenter import segment

MANIFEST = "_manifest.json"
LOCALE_SUFFIX = re.compile(r"\.([a-z]{2}(?:_[A-Z]{2})?)$")


@dataclass
class ImportResult:
    course_slug: str
    imported: int = 0
    updated: int = 0
    unchanged: int = 0
    empty: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)


def split_locale(stem: str) -> tuple[str, str | None]:
    """'002-setup.en_US' -> ('002-setup', 'en_US'); không có hậu tố -> (stem, None)."""
    m = LOCALE_SUFFIX.search(stem)
    return (stem[:m.start()], m.group(1)) if m else (stem, None)


def _files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)


def _manifest_group(folder: Path) -> tuple[dict, list, list]:
    """Thư mục một ngôn ngữ do fetch tạo: chỉ import các file manifest liệt kê."""
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
            "title": lec["title"],
            "language": manifest["locale_id"],
            "caption_source": lec.get("source", "file"),
            "filename": f"{folder.name}/{path.name}",
        }))
    return course, entries, ignored


def _local_group(folder: Path, subdirs: list[Path], default_lang: str) -> tuple[dict, list, list]:
    """File tự đặt: phẳng trong thư mục khóa, hoặc trong thư mục con <lang>/ (tên thư mục = ngôn ngữ)."""
    files = [(p, None) for p in _files(folder)] + [(p, sub.name) for sub in subdirs for p in _files(sub)]
    bases = sorted({split_locale(p.stem)[0] for p, _ in files})
    course = {"slug": folder.name, "title": folder.name, "source": "local"}
    entries, ignored, taken = [], [], set()
    for path, sub_lang in files:
        base, suffix_lang = split_locale(path.stem)
        language = sub_lang or suffix_lang or default_lang
        filename = f"{sub_lang}/{path.name}" if sub_lang else path.name
        if (base, language) in taken:  # ví dụ a.vtt và a.txt: giữ file đầu, bỏ qua file sau
            ignored.append(filename)
            continue
        taken.add((base, language))
        entries.append((path, {
            "external_id": base,
            "position": bases.index(base) + 1,
            "chapter": None,
            "title": base,
            "language": language,
            "caption_source": "file",
            "filename": filename,
        }))
    return course, entries, ignored


def import_folder(conn, folder: Path, *, default_lang: str, max_words: int) -> ImportResult:
    """folder: thư mục khóa học (mọi ngôn ngữ) hoặc thư mục một ngôn ngữ có _manifest.json."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {folder}")
    if (folder / MANIFEST).exists():
        groups = [_manifest_group(folder)]
    else:
        subdirs = sorted(p for p in folder.iterdir() if p.is_dir())
        groups = [_manifest_group(sub) for sub in subdirs if (sub / MANIFEST).exists()]
        local_subdirs = [sub for sub in subdirs if not (sub / MANIFEST).exists()]
        local = _local_group(folder, local_subdirs, default_lang)
        if local[1] or local[2] or not groups:
            groups.append(local)

    result = ImportResult(course_slug=groups[0][0]["slug"])
    for course, entries, ignored in groups:
        result.ignored.extend(ignored)
        with conn:
            course_id = database.upsert_course(conn, **course)
        for path, info in entries:
            _import_file(conn, course_id, path, info, max_words, result)
    return result


def _import_file(conn, course_id: int, path: Path, info: dict, max_words: int, result: ImportResult) -> None:
    data = path.read_bytes()
    content_hash = hashlib.sha256(data).hexdigest()
    with conn:  # một file = một transaction = một checkpoint
        lesson_id = database.upsert_lesson(
            conn, course_id=course_id, external_id=info["external_id"], position=info["position"],
            title=info["title"], chapter=info["chapter"],
        )
        existing = database.get_transcript(conn, lesson_id, info["language"])
        if existing and existing["content_hash"] == content_hash:
            result.unchanged += 1
            return
        chunks = segment(parse_text(data.decode("utf-8-sig", errors="replace"), path.suffix), max_words)
        if not chunks:
            result.empty.append(info["filename"])
        database.save_transcript(
            conn, lesson_id=lesson_id, language=info["language"], caption_source=info["caption_source"],
            filename=info["filename"], content_hash=content_hash, chunks=chunks,
        )
        if existing:
            result.updated += 1
        else:
            result.imported += 1
