import json

import pytest

from engine import database
from engine.importer import import_folder, split_locale

VTT = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\n{text}\n"


@pytest.fixture
def conn(tmp_path):
    c = database.connect(tmp_path / "test.db")
    yield c
    c.close()


def write(path, text):
    path.write_text(text, encoding="utf-8")


def run(conn, folder):
    return import_folder(conn, folder, default_lang="en", max_words=2500)


def test_split_locale():
    assert split_locale("002-setup.en_US") == ("002-setup", "en_US")
    assert split_locale("lesson.vi") == ("lesson", "vi")
    assert split_locale("lesson-01") == ("lesson-01", None)


def test_local_folder_import_and_idempotency(conn, tmp_path):
    folder = tmp_path / "my-course"
    folder.mkdir()
    write(folder / "lesson-01.vtt", VTT.format(text="First lesson."))
    write(folder / "lesson-02.txt", "Second lesson.\n")
    write(folder / "lesson-02.vi.txt", "Bài hai.\n")
    write(folder / "notes.pdf", "ignored")

    r = run(conn, folder)
    assert (r.imported, r.updated, r.unchanged) == (3, 0, 0)
    s = database.stats(conn)
    assert (s["courses"], s["lessons"], s["transcripts"], s["chunks"]) == (1, 2, 3, 3)

    langs = conn.execute(
        "SELECT l.position, l.title, t.language, t.caption_source FROM transcript t "
        "JOIN lesson l ON l.id = t.lesson_id ORDER BY l.position, t.language"
    ).fetchall()
    assert [tuple(x) for x in langs] == [
        (1, "lesson-01", "en", "file"),
        (2, "lesson-02", "en", "file"),
        (2, "lesson-02", "vi", "file"),
    ]

    r = run(conn, folder)
    assert (r.imported, r.updated, r.unchanged) == (0, 0, 3)
    assert database.stats(conn) == s


def test_changed_file_replaces_chunks_and_resets_status(conn, tmp_path):
    folder = tmp_path / "c"
    folder.mkdir()
    write(folder / "a.vtt", VTT.format(text="Old text."))
    run(conn, folder)
    conn.execute("UPDATE transcript SET status = 'extracted'")
    conn.commit()

    write(folder / "a.vtt", VTT.format(text="New text."))
    r = run(conn, folder)
    assert r.updated == 1
    row = conn.execute("SELECT status FROM transcript").fetchone()
    assert row["status"] == "imported"
    assert [x["text"] for x in conn.execute("SELECT text FROM chunk")] == ["New text."]


def write_locale(course_dir, locale, files, source):
    """Thư mục ngôn ngữ giống fetch tạo: files = {filename: text}."""
    folder = course_dir / locale
    folder.mkdir(parents=True)
    for name, text in files.items():
        write(folder / name, VTT.format(text=text))
    manifest = {
        "course_id": 123, "slug": course_dir.name, "title": "Python Bootcamp",
        "url": f"/course/{course_dir.name}/", "host": "www.udemy.com", "locale_id": locale,
        "lectures": [{"lecture_id": 999, "position": 1, "chapter_title": "Bắt đầu", "chapter_index": 1,
                      "title": "Giới thiệu", "filename": "001-intro.vtt", "source": source}],
        "skipped": [],
    }
    write(folder / "_manifest.json", json.dumps(manifest, ensure_ascii=False))
    return folder


def test_manifest_metadata_course_folder(conn, tmp_path):
    course_dir = tmp_path / "python-bootcamp"
    write_locale(course_dir, "en_US", {"001-intro.vtt": "Hello."}, "manual")
    write_locale(course_dir, "vi_VN", {"001-intro.vtt": "Xin chào."}, "auto")

    r = run(conn, course_dir)
    assert (r.course_slug, r.imported) == ("python-bootcamp", 2)
    course = conn.execute("SELECT * FROM course").fetchone()
    assert (course["title"], course["source"], course["external_id"]) == ("Python Bootcamp", "udemy", "123")
    lesson = conn.execute("SELECT * FROM lesson").fetchone()
    assert (lesson["external_id"], lesson["title"], lesson["chapter"]) == ("999", "Giới thiệu", "Bắt đầu")
    rows = conn.execute("SELECT language, caption_source, filename FROM transcript ORDER BY language").fetchall()
    assert [tuple(x) for x in rows] == [
        ("en_US", "manual", "en_US/001-intro.vtt"), ("vi_VN", "auto", "vi_VN/001-intro.vtt"),
    ]
    assert run(conn, course_dir).unchanged == 2


def test_single_locale_folder(conn, tmp_path):
    folder = write_locale(tmp_path / "py", "en_US", {"001-intro.vtt": "Hello."}, "auto")
    r = run(conn, folder)
    assert (r.course_slug, r.imported) == ("py", 1)


def test_missing_folder(conn, tmp_path):
    with pytest.raises(FileNotFoundError):
        run(conn, tmp_path / "nope")


def test_manifest_folder_ignores_unlisted_files(conn, tmp_path):
    folder = write_locale(tmp_path / "c", "en_US", {"001-intro.vtt": "A.", "stray.vtt": "B."}, "auto")
    r = run(conn, folder)
    assert (r.imported, r.ignored) == (1, ["en_US/stray.vtt"])
    assert database.stats(conn)["lessons"] == 1


def test_local_language_subfolders(conn, tmp_path):
    course_dir = tmp_path / "my-course"
    (course_dir / "en").mkdir(parents=True)
    (course_dir / "vi").mkdir()
    write(course_dir / "en" / "lesson-01.vtt", VTT.format(text="Hello."))
    write(course_dir / "vi" / "lesson-01.txt", "Xin chào.\n")
    write(course_dir / "lesson-02.txt", "Flat file.\n")

    r = run(conn, course_dir)
    assert (r.imported, r.ignored) == (3, [])
    rows = conn.execute(
        "SELECT l.position, l.title, t.language, t.filename FROM transcript t "
        "JOIN lesson l ON l.id = t.lesson_id ORDER BY l.position, t.language"
    ).fetchall()
    assert [tuple(x) for x in rows] == [
        (1, "lesson-01", "en", "en/lesson-01.vtt"),
        (1, "lesson-01", "vi", "vi/lesson-01.txt"),
        (2, "lesson-02", "en", "lesson-02.txt"),
    ]


def test_local_same_lesson_and_language_keeps_first_file(conn, tmp_path):
    folder = tmp_path / "c"
    folder.mkdir()
    write(folder / "a.txt", "From txt.\n")
    write(folder / "a.vtt", VTT.format(text="From vtt."))
    r = run(conn, folder)
    assert (r.imported, r.ignored) == (1, ["a.vtt"])
    assert run(conn, folder).unchanged == 1
