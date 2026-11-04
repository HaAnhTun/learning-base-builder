"""Lệnh fetch: tải caption của một khóa Udemy vào data/input/<slug>/ kèm _manifest.json."""
import hashlib
import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from engine.database import now
from engine.importer import MANIFEST
from engine.udemy_client import AuthError, UdemyError


def parse_langs(value: str) -> list[str]:
    langs = [x.strip() for x in value.split(",") if x.strip()]
    return ["all"] if "all" in langs else langs


def _rank(caption: dict) -> tuple:
    # manual trước auto; trong cùng loại ưu tiên en_US rồi theo alphabet.
    return (caption.get("source") == "auto", caption["locale_id"] != "en_US", caption["locale_id"])


def select_captions(captions: list[dict], langs: list[str]) -> list[dict]:
    """Mỗi ngôn ngữ yêu cầu lấy đúng một track tốt nhất."""
    usable = [c for c in captions if c.get("url") and c.get("locale_id")]
    if langs == ["all"]:
        groups: dict[str, list[dict]] = {}
        for c in usable:
            groups.setdefault(c["locale_id"], []).append(c)
        return [min(group, key=_rank) for _, group in sorted(groups.items())]

    selected: dict[str, dict] = {}
    for lang in langs:
        if "_" in lang:
            candidates = [c for c in usable if c["locale_id"].lower() == lang.lower()]
        else:
            candidates = [c for c in usable if c["locale_id"].split("_")[0].lower() == lang.lower()]
        if candidates:
            best = min(candidates, key=_rank)
            selected.setdefault(best["locale_id"], best)
    return list(selected.values())


def slugify(title: str, fallback: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", title.replace("đ", "d").replace("Đ", "D"))
    text = text.encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:max_len].strip("-")
    return slug or fallback


def fetch_course(client, course: dict, langs: list[str], input_dir: Path, max_concurrency: int = 4,
                 progress=lambda message: None) -> list[Path]:
    """Tải caption theo langs vào <input_dir>/<slug>/<locale>/; trả về các thư mục ngôn ngữ đã ghi.

    Mỗi thư mục ngôn ngữ có _manifest.json riêng; ngôn ngữ không được yêu cầu không bị đụng tới.
    Lỗi xác thực dừng toàn bộ. progress(message) nhận thông báo tiến độ.
    """
    course_id = course["id"]
    slug = course["published_title"]
    # Udemy dựng danh sách caption phía server ở lần gọi đầu: khóa ~400 bài mất 1–2 phút, lần sau vài giây.
    progress("Đang lấy danh sách bài giảng (lần đầu với khóa lớn có thể mất 1–2 phút)...")
    items = client.get_curriculum(course_id)

    lectures, jobs, no_caption_reason = [], [], {}
    chapter_title, chapter_index, position = None, None, 0
    for item in items:
        kind = item.get("_class")
        if kind == "chapter":
            chapter_title, chapter_index = item.get("title"), item.get("object_index")
            continue
        if kind != "lecture":
            continue
        position += 1
        asset = item.get("asset") or {}
        captions = asset["captions"] if "captions" in asset else client.get_lecture_captions(course_id, item["id"])
        lecture = {
            "lecture_id": item["id"],
            "position": position,
            "chapter_title": chapter_title,
            "chapter_index": chapter_index,
            "title": item.get("title") or f"Lecture {item['id']}",
        }
        lectures.append(lecture)
        if "video" not in (asset.get("asset_type") or "").lower() and not captions:
            no_caption_reason[item["id"]] = "non_video"
        jobs.extend((lecture, caption) for caption in select_captions(captions or [], langs))

    def download(job):
        lecture, caption = job
        try:
            return job, client.download_text(caption["url"]), None
        except AuthError:
            raise
        except UdemyError as exc:
            return job, None, f"http_{exc.status}" if exc.status else str(exc)

    progress(f"{len(lectures)} bài giảng, tải {len(jobs)} file caption...")
    results = []
    with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        for done, result in enumerate(pool.map(download, jobs), 1):
            results.append(result)
            if done % 50 == 0 or done == len(jobs):
                progress(f"  {done}/{len(jobs)}")

    by_locale: dict[str, dict] = {}
    for (lecture, caption), text, error in results:
        by_locale.setdefault(caption["locale_id"], {})[lecture["lecture_id"]] = (caption, text, error)

    width = 4 if position > 999 else 3
    folders = []
    for locale, got in sorted(by_locale.items()):
        folder = Path(input_dir) / slug / locale
        folder.mkdir(parents=True, exist_ok=True)
        entries, skipped = [], []
        for lecture in lectures:
            caption, text, error = got.get(lecture["lecture_id"], (None, None, None))
            if text is None:
                reason = error or no_caption_reason.get(lecture["lecture_id"], "no_caption_for_lang")
                skipped.append({"lecture_id": lecture["lecture_id"], "title": lecture["title"], "reason": reason})
                continue
            name_slug = slugify(lecture["title"], f"lecture-{lecture['lecture_id']}")
            filename = f"{lecture['position']:0{width}d}-{name_slug}.vtt"
            data = text.encode("utf-8")
            (folder / filename).write_bytes(data)
            entries.append({
                **lecture,
                "filename": filename,
                "source": "auto" if caption.get("source") == "auto" else "manual",
                "label": caption.get("label") or caption.get("video_label"),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
        manifest = {
            "course_id": course_id,
            "slug": slug,
            "title": course.get("title") or slug,
            "url": course.get("url"),
            "host": client.host,
            "locale_id": locale,
            "fetched_at": now(),
            "requested_langs": langs,
            "lectures": entries,
            "skipped": skipped,
        }
        (folder / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        folders.append(folder)
    return folders
