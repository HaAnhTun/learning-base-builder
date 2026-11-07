"""`fetch` also saves a course's quizzes, practice exams and lecture attachments next to the captions.

data/input/<slug>/quizzes/<NN>-<title>.json   raw questions of one quiz + where it sits in the curriculum
data/input/<slug>/quizzes/_quizzes.json       index (also lists what could not be fetched)
data/input/<slug>/materials/<LLL>-<file>      downloaded attachments (File assets)
data/input/<slug>/materials/_materials.json   index: files, external links (never opened), lecture descriptions

Neither folder has a _manifest.json, so `import` never mistakes them for a locale folder.
"""
import hashlib
import json
from pathlib import Path

from engine.database import now
from engine.export_notebooklm import safe_filename
from engine.fetcher import slugify
from engine.udemy_client import AuthError, UdemyError

QUIZ_INDEX = "_quizzes.json"
MATERIAL_INDEX = "_materials.json"


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _download_url(asset: dict) -> str | None:
    """First CDN URL of a File asset: download_urls is {"File": [{"label": ..., "file": url}]}."""
    for entries in (asset.get("download_urls") or {}).values():
        for entry in entries or []:
            if entry.get("file"):
                return entry["file"]
    return None


def _fetch_quiz(client, item: dict, position: int, where: dict, width: int, folder: Path, skipped: list):
    """Write one quiz file; returns its index entry, or None (and records why) when it cannot be fetched."""
    title = item.get("title") or f"Quiz {item['id']}"
    try:
        assessments = client.get_quiz_assessments(item["id"], item.get("version") or 1)
    except AuthError:
        raise
    except UdemyError as exc:
        skipped.append({"id": item["id"], "title": title, "reason": str(exc)})
        return None
    fallback = "quiz-" + str(item["id"])
    filename = f"{position:0{width}d}-{slugify(title, fallback)}.json"
    data = {"quiz_id": item["id"], "title": title, "type": item.get("type"), "version": item.get("version") or 1,
            "pass_percent": item.get("pass_percent"), "description": item.get("description") or "",
            "position": position, **where, "assessments": assessments}
    text = json.dumps(data, ensure_ascii=False, indent=2)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / filename).write_text(text, encoding="utf-8")
    return {"position": position, "quiz_id": item["id"], "title": title, "filename": filename, **where,
            "questions": len(assessments), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def _fetch_attachments(client, item: dict, where: dict, folder: Path, skipped: list) -> list[dict]:
    """Index entries for one lecture's description and attachments; File assets are downloaded."""
    base = {"lecture_id": item["id"], "lecture_title": item.get("title"), **where}
    out = []
    if (item.get("description") or "").strip():
        out.append({**base, "kind": "description", "html": item["description"]})
    for asset in item.get("supplementary_assets") or []:
        kind, title = asset.get("asset_type"), asset.get("title")
        if kind == "ExternalLink":  # recorded only: nothing is opened or fetched
            out.append({**base, "kind": "link", "title": title, "url": asset.get("external_url") or title})
            continue
        url = _download_url(asset) if kind == "File" else None
        if url is None:
            skipped.append({"lecture_id": item["id"], "title": title, "reason": f"unsupported asset type {kind}"})
            continue
        try:
            data = client.download_bytes(url)
        except AuthError:
            raise
        except UdemyError as exc:
            skipped.append({"lecture_id": item["id"], "title": title, "reason": str(exc)})
            continue
        name = safe_filename(asset.get("filename") or "asset-" + str(asset["id"]))
        filename = f"{where['lecture_position']:03d}-{name}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / filename).write_bytes(data)
        out.append({**base, "kind": "file", "title": title, "filename": filename, "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest()})
    return out


def fetch_materials(client, course: dict, input_dir: Path, progress=lambda message: None) -> dict:
    """Save quizzes and attachments of the course; returns counts and what was skipped."""
    slug = course["published_title"]
    course_dir = Path(input_dir) / slug
    progress("Đang lấy quiz và tài liệu đính kèm...")
    items = client.get_course_items(course["id"])
    n_quizzes = sum(item.get("_class") == "quiz" for item in items)
    quiz_width = 3 if n_quizzes > 99 else 2

    chapter = {"chapter_index": None, "chapter_title": None}
    lectures = 0
    quizzes, attachments, skipped = [], [], []
    for item in items:
        kind = item.get("_class")
        if kind == "chapter":
            chapter = {"chapter_index": item.get("object_index"), "chapter_title": item.get("title")}
        elif kind == "lecture":
            lectures += 1
            attachments += _fetch_attachments(client, item, {**chapter, "lecture_position": lectures},
                                              course_dir / "materials", skipped)
        elif kind == "quiz":
            entry = _fetch_quiz(client, item, len(quizzes) + 1, {**chapter, "lectures_before": lectures}, quiz_width,
                                course_dir / "quizzes", skipped)
            if entry:
                quizzes.append(entry)
                progress(f"  {entry['title']}: {entry['questions']} câu")
        else:  # e.g. coding exercises ("practice")
            skipped.append({"id": item.get("id"), "title": item.get("title"), "reason": f"unsupported item {kind}"})

    head = {"course_id": course["id"], "slug": slug, "title": course.get("title") or slug, "url": course.get("url"),
            "host": client.host, "fetched_at": now()}
    if quizzes:
        _write_json(course_dir / "quizzes" / QUIZ_INDEX, {**head, "quizzes": quizzes})
    if attachments:
        _write_json(course_dir / "materials" / MATERIAL_INDEX, {**head, "items": attachments})
    return {"quizzes": len(quizzes), "questions": sum(q["questions"] for q in quizzes),
            "files": sum(a["kind"] == "file" for a in attachments),
            "links": sum(a["kind"] == "link" for a in attachments), "skipped": skipped}
