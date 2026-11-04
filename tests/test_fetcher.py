import json

import pytest

from engine.fetcher import fetch_course, parse_langs, select_captions, slugify
from engine.udemy_client import AuthError, UdemyError

EN_US_AUTO = {"locale_id": "en_US", "source": "auto", "url": "u/en_auto", "label": "English [Auto]"}
EN_US = {"locale_id": "en_US", "source": "manual", "url": "u/en_us"}
EN_GB = {"locale_id": "en_GB", "source": "manual", "url": "u/en_gb"}
VI = {"locale_id": "vi_VN", "source": "auto", "url": "u/vi"}


def test_parse_langs():
    assert parse_langs("en") == ["en"]
    assert parse_langs("en, vi_VN") == ["en", "vi_VN"]
    assert parse_langs("en,all") == ["all"]


def test_manual_preferred_over_auto():
    assert select_captions([EN_US_AUTO, EN_US], ["en"]) == [EN_US]


def test_auto_used_when_no_manual():
    assert select_captions([EN_US_AUTO, VI], ["en"]) == [EN_US_AUTO]


def test_short_code_prefers_en_us_among_manual():
    assert select_captions([EN_GB, EN_US], ["en"]) == [EN_US]


def test_full_locale_must_match_exactly():
    assert select_captions([EN_US, EN_GB], ["en_GB"]) == [EN_GB]
    assert select_captions([EN_US], ["en_GB"]) == []


def test_multiple_and_all():
    assert select_captions([EN_US, VI], ["en", "vi"]) == [EN_US, VI]
    assert select_captions([EN_US_AUTO, EN_US, EN_GB, VI], ["all"]) == [EN_GB, EN_US, VI]


def test_captions_without_url_ignored():
    assert select_captions([{"locale_id": "en_US", "url": None}], ["en"]) == []


def test_slugify():
    assert slugify("Giới thiệu về Python — Đặc biệt!", "x") == "gioi-thieu-ve-python-dac-biet"
    assert slugify("日本語", "lecture-1") == "lecture-1"
    assert len(slugify("a" * 200, "x")) == 60


class FakeClient:
    host = "www.udemy.com"

    def __init__(self, curriculum, texts, lecture_captions=None):
        self.curriculum = curriculum
        self.texts = texts
        self.lecture_captions = lecture_captions or {}
        self.downloaded = []

    def get_curriculum(self, course_id):
        return self.curriculum

    def get_lecture_captions(self, course_id, lecture_id):
        return self.lecture_captions[lecture_id]

    def download_text(self, url):
        self.downloaded.append(url)
        value = self.texts[url]
        if isinstance(value, Exception):
            raise value
        return value


COURSE = {"id": 1, "published_title": "py-course", "title": "Py Course", "url": "/course/py-course/"}


def curriculum():
    return [
        {"_class": "chapter", "id": 10, "title": "Getting Started", "object_index": 1},
        {"_class": "lecture", "id": 100, "title": "Giới thiệu",
         "asset": {"asset_type": "Video", "captions": [EN_US_AUTO, EN_US, VI]}},
        {"_class": "lecture", "id": 101, "title": "Reading", "asset": {"asset_type": "Article", "captions": []}},
        {"_class": "quiz", "id": 5, "title": "Quiz"},
        {"_class": "chapter", "id": 11, "title": "Basics", "object_index": 2},
        {"_class": "lecture", "id": 102, "title": "Variables", "asset": {"asset_type": "Video"}},
        {"_class": "lecture", "id": 103, "title": "Loops", "asset": {"asset_type": "Video", "captions": [VI]}},
    ]


def manifest_of(folder):
    return json.loads((folder / "_manifest.json").read_text(encoding="utf-8"))


def test_fetch_course_writes_one_folder_per_locale(tmp_path):
    client = FakeClient(
        curriculum(),
        {"u/en_us": "WEBVTT\n\nA", "u/en_gb": "WEBVTT\n\nB", "u/vi": "WEBVTT\n\nC"},
        lecture_captions={102: [EN_GB]},
    )
    folders = fetch_course(client, COURSE, ["en"], tmp_path)

    course_dir = tmp_path / "py-course"
    assert folders == [course_dir / "en_GB", course_dir / "en_US"]
    assert sorted(p.name for p in course_dir.iterdir()) == ["en_GB", "en_US"]  # không có vi_VN
    assert sorted(p.name for p in (course_dir / "en_US").iterdir()) == ["001-gioi-thieu.vtt", "_manifest.json"]
    assert (course_dir / "en_US" / "001-gioi-thieu.vtt").read_text(encoding="utf-8") == "WEBVTT\n\nA"
    assert client.downloaded == ["u/en_us", "u/en_gb"]  # chỉ tải ngôn ngữ được yêu cầu

    m = manifest_of(course_dir / "en_US")
    assert (m["course_id"], m["slug"], m["host"], m["locale_id"], m["requested_langs"]) == (
        1, "py-course", "www.udemy.com", "en_US", ["en"])
    assert [(lec["lecture_id"], lec["position"], lec["chapter_title"], lec["title"], lec["source"])
            for lec in m["lectures"]] == [(100, 1, "Getting Started", "Giới thiệu", "manual")]
    assert {(s["lecture_id"], s["reason"]) for s in m["skipped"]} == {
        (101, "non_video"), (102, "no_caption_for_lang"), (103, "no_caption_for_lang"),
    }
    assert [lec["filename"] for lec in manifest_of(course_dir / "en_GB")["lectures"]] == ["003-variables.vtt"]


def test_no_matching_caption_writes_nothing(tmp_path):
    client = FakeClient(curriculum(), {}, lecture_captions={102: []})
    assert fetch_course(client, COURSE, ["ja"], tmp_path) == []
    assert not (tmp_path / "py-course").exists()


def test_download_error_recorded_but_auth_error_aborts(tmp_path):
    texts = {"u/en_us": UdemyError("HTTP 404: /x", 404), "u/en_gb": "WEBVTT"}
    [en_gb, en_us] = fetch_course(FakeClient(curriculum(), texts, {102: [EN_GB]}), COURSE, ["en"], tmp_path)
    m = manifest_of(en_us)
    assert m["lectures"] == []
    assert {"lecture_id": 100, "title": "Giới thiệu", "reason": "http_404"} in m["skipped"]

    client = FakeClient(curriculum(), {"u/en_us": AuthError("expired")}, lecture_captions={102: []})
    with pytest.raises(AuthError):
        fetch_course(client, COURSE, ["en"], tmp_path)


VTT = "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello there.\n"
TEXTS = {"u/en_us": VTT, "u/vi": VTT, "u/en_gb": VTT}


def test_fetched_course_folder_imports_all_languages(tmp_path):
    from engine import database
    from engine.importer import import_folder

    fetch_course(FakeClient(curriculum(), TEXTS, {102: [EN_GB]}), COURSE, ["en", "vi"], tmp_path)
    conn = database.connect(tmp_path / "db.sqlite")
    r = import_folder(conn, tmp_path / "py-course", default_lang="en", max_words=2500)
    assert (r.course_slug, r.imported, r.ignored) == ("py-course", 4, [])  # 100: en_US+vi_VN, 102: en_GB, 103: vi_VN
    assert database.stats(conn)["lessons"] == 3
    files = {row[0] for row in conn.execute("SELECT filename FROM transcript")}
    assert "en_US/001-gioi-thieu.vtt" in files
    conn.close()


def test_refetch_other_language_leaves_existing_folder_untouched(tmp_path):
    """fetch en,vi rồi fetch en: thư mục vi_VN giữ nguyên, import không tạo lesson trùng."""
    from engine import database
    from engine.importer import import_folder

    conn = database.connect(tmp_path / "db.sqlite")
    fetch_course(FakeClient(curriculum(), TEXTS, {102: [EN_GB]}), COURSE, ["en", "vi"], tmp_path)
    vi_manifest = (tmp_path / "py-course" / "vi_VN" / "_manifest.json").read_text(encoding="utf-8")
    import_folder(conn, tmp_path / "py-course", default_lang="en", max_words=2500)

    for folder in fetch_course(FakeClient(curriculum(), TEXTS, {102: [EN_GB]}), COURSE, ["en"], tmp_path):
        r = import_folder(conn, folder, default_lang="en", max_words=2500)
        assert (r.imported, r.ignored) == (0, [])
    assert (tmp_path / "py-course" / "vi_VN" / "_manifest.json").read_text(encoding="utf-8") == vi_manifest
    assert database.stats(conn)["lessons"] == 3
    conn.close()


def test_progress_messages(tmp_path):
    messages = []
    fetch_course(FakeClient(curriculum(), TEXTS, {102: [EN_GB]}), COURSE, ["en"], tmp_path, progress=messages.append)
    assert messages[0].startswith("Đang lấy danh sách bài giảng")
    assert messages[1:] == ["4 bài giảng, tải 2 file caption...", "  2/2"]
