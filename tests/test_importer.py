import json

import pytest

from engine import database
from engine.importer import import_folder, split_locale

VTT = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\n{text}\n"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(conn, cfg, folder):
    return import_folder(conn, folder, cfg)


def clean_doc(cfg, conn, language="en_US", position=1):
    row = conn.execute(
        "SELECT t.clean_path FROM transcript t JOIN lesson l ON l.id = t.lesson_id "
        "WHERE t.language = ? AND l.position = ?", (language, position)).fetchone()
    return json.loads((cfg["root"] / row["clean_path"]).read_text(encoding="utf-8"))


def test_split_locale():
    assert split_locale("002-setup.en_US") == ("002-setup", "en_US")
    assert split_locale("lesson.vi") == ("lesson", "vi")
    assert split_locale("lesson-01") == ("lesson-01", None)
    assert split_locale("intro-to-node.js") == ("intro-to-node.js", None)
    assert split_locale("notes.vi") == ("notes", "vi")


def test_local_folder_import_cleans_and_is_idempotent(conn, cfg, tmp_path):
    folder = tmp_path / "my-course"
    write(folder / "lesson-01.vtt", VTT.format(text="First lesson."))
    write(folder / "lesson-02.txt", "Second lesson.\n")
    write(folder / "lesson-02.vi.txt", "Bài hai.\n")
    write(folder / "notes.pdf", "ignored")

    r = run(conn, cfg, folder)
    assert (r.imported, r.updated, r.unchanged, r.cleaned) == (3, 0, 0, 3)
    s = database.stats(conn)
    assert (s["courses"], s["lessons"], s["transcripts"], s["cleaned"]) == (1, 2, 3, 3)
    rows = conn.execute(
        "SELECT l.position, l.title, t.language, t.caption_source, t.clean_path FROM transcript t "
        "JOIN lesson l ON l.id = t.lesson_id ORDER BY l.position, t.language").fetchall()
    assert [tuple(x) for x in rows] == [
        (1, "lesson-01", "en", "file", "data/clean/my-course/en/001-lesson-01.json"),
        (2, "lesson-02", "en", "file", "data/clean/my-course/en/002-lesson-02.json"),
        (2, "lesson-02", "vi", "file", "data/clean/my-course/vi/002-lesson-02.json"),
    ]
    doc = clean_doc(cfg, conn, "en", 1)
    assert doc["sentences"] == [{"id": 0, "start": 0.0, "end": 2.0, "text": "First lesson."}]
    assert doc["source_file"] == "my-course/lesson-01.vtt"  # tmp_path is the project root in tests

    r = run(conn, cfg, folder)
    assert (r.imported, r.updated, r.unchanged, r.cleaned) == (0, 0, 3, 0)
    assert database.stats(conn) == s


def test_raw_files_are_never_modified(conn, cfg, tmp_path):
    folder = tmp_path / "c"
    raw = VTT.format(text="Untouched.")
    write(folder / "a.vtt", raw)
    run(conn, cfg, folder)
    assert (folder / "a.vtt").read_text(encoding="utf-8") == raw


def test_changed_file_is_recleaned_and_dependents_invalidated(conn, cfg, tmp_path):
    folder = tmp_path / "c"
    write(folder / "a.vtt", VTT.format(text="Old text."))
    run(conn, cfg, folder)
    tid = conn.execute("SELECT id FROM transcript").fetchone()["id"]
    with conn:
        database.set_state(conn, tid, "knowledge", "done", "h", "v1")
        conn.execute("INSERT INTO knowledge_node (transcript_id, node_type, title_json, position, sentence_start, "
                     "sentence_end, status) VALUES (?, 'topic', '{}', 0, 0, 0, 'auto_approved')", (tid,))

    write(folder / "a.vtt", VTT.format(text="New text."))
    r = run(conn, cfg, folder)
    assert (r.updated, r.cleaned) == (1, 1)
    assert clean_doc(cfg, conn, "en")["sentences"][0]["text"] == "New text."
    assert conn.execute("SELECT COUNT(*) FROM knowledge_node").fetchone()[0] == 0
    assert database.get_state(conn, tid, "knowledge")["status"] == "stale"


def write_locale(course_dir, locale, files, source):
    """Locale folder shaped like fetch output: files = {filename: text}."""
    folder = course_dir / locale
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


def test_manifest_metadata_course_folder(conn, cfg, tmp_path):
    course_dir = tmp_path / "python-bootcamp"
    write_locale(course_dir, "en_US", {"001-intro.vtt": "Hello."}, "manual")
    write_locale(course_dir, "vi_VN", {"001-intro.vtt": "Xin chào."}, "auto")

    r = run(conn, cfg, course_dir)
    assert (r.course_slug, r.imported, r.cleaned) == ("python-bootcamp", 2, 2)
    course = conn.execute("SELECT * FROM course").fetchone()
    assert (course["title"], course["source"], course["external_id"]) == ("Python Bootcamp", "udemy", "123")
    lesson = conn.execute("SELECT * FROM lesson").fetchone()
    assert (lesson["external_id"], lesson["title"], lesson["chapter"], lesson["chapter_index"]) == (
        "999", "Giới thiệu", "Bắt đầu", 1)
    doc = clean_doc(cfg, conn, "vi_VN")
    assert doc["lesson"]["chapter_title"] == "Bắt đầu"
    assert doc["caption_source"] == "auto"
    assert run(conn, cfg, course_dir).unchanged == 2


def test_single_locale_folder(conn, cfg, tmp_path):
    folder = write_locale(tmp_path / "py", "en_US", {"001-intro.vtt": "Hello."}, "auto")
    assert (run(conn, cfg, folder).course_slug, database.stats(conn)["cleaned"]) == ("py", 1)


def test_missing_folder(conn, cfg, tmp_path):
    with pytest.raises(FileNotFoundError):
        run(conn, cfg, tmp_path / "nope")


def test_manifest_folder_ignores_unlisted_files(conn, cfg, tmp_path):
    folder = write_locale(tmp_path / "c", "en_US", {"001-intro.vtt": "A.", "stray.vtt": "B."}, "auto")
    r = run(conn, cfg, folder)
    assert (r.imported, r.ignored) == (1, ["en_US/stray.vtt"])


def test_hand_placed_files_in_fetched_course_are_ignored(conn, cfg, tmp_path):
    course_dir = tmp_path / "py"
    write_locale(course_dir, "en_US", {"001-intro.vtt": "Hello."}, "auto")
    write(course_dir / "vi" / "001-intro.txt", "Xin chào.\n")
    write(course_dir / "extra.txt", "Loose file.\n")
    r = run(conn, cfg, course_dir)
    assert r.imported == 1
    assert sorted(r.ignored) == ["extra.txt", "vi/001-intro.txt"]
    assert conn.execute("SELECT source FROM course").fetchone()["source"] == "udemy"


def test_local_language_subfolders(conn, cfg, tmp_path):
    course_dir = tmp_path / "my-course"
    write(course_dir / "en" / "lesson-01.vtt", VTT.format(text="Hello."))
    write(course_dir / "vi" / "lesson-01.txt", "Xin chào.\n")
    write(course_dir / "lesson-02.txt", "Flat file.\n")
    r = run(conn, cfg, course_dir)
    assert (r.imported, r.ignored) == (3, [])
    rows = conn.execute(
        "SELECT l.position, l.title, t.language, t.filename FROM transcript t "
        "JOIN lesson l ON l.id = t.lesson_id ORDER BY l.position, t.language").fetchall()
    assert [tuple(x) for x in rows] == [
        (1, "lesson-01", "en", "en/lesson-01.vtt"),
        (1, "lesson-01", "vi", "vi/lesson-01.txt"),
        (2, "lesson-02", "en", "lesson-02.txt"),
    ]


def test_local_same_lesson_and_language_keeps_first_file(conn, cfg, tmp_path):
    folder = tmp_path / "c"
    write(folder / "a.txt", "From txt.\n")
    write(folder / "a.vtt", VTT.format(text="From vtt."))
    r = run(conn, cfg, folder)
    assert (r.imported, r.ignored) == (1, ["a.vtt"])
    assert run(conn, cfg, folder).unchanged == 1


def test_old_schema_database_is_rejected(tmp_path):
    import sqlite3

    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE chunk (id INTEGER)")
    old.commit()
    old.close()
    with pytest.raises(database.SchemaError, match="schema cũ"):
        database.connect(path)


def test_markdown_heading_is_its_own_paragraph(conn, cfg, tmp_path):
    write(tmp_path / "c" / "a.md", "# Title\nSome text here.\n")
    run(conn, cfg, tmp_path / "c")
    doc = clean_doc(cfg, conn, "en")
    assert [s["text"] for s in doc["sentences"]] == ["Title", "Some text here."]
    assert doc["paragraphs"] == [[0, 0], [1, 1]]


def test_local_folder_with_udemy_slug_is_not_merged(conn, cfg, tmp_path):
    write_locale(tmp_path / "input" / "crs", "en_US", {"001-intro.vtt": "Udemy text."}, "auto")
    run(conn, cfg, tmp_path / "input" / "crs")
    write(tmp_path / "notes" / "crs" / "en_US" / "Intro.txt", "My own notes.\n")
    r = run(conn, cfg, tmp_path / "notes" / "crs")
    assert r.imported == 0 and r.warnings and r.ignored == ["en_US/Intro.txt"]
    assert clean_doc(cfg, conn, "en_US")["sentences"][0]["text"] == "Udemy text."
    assert database.stats(conn)["lessons"] == 1


def test_metadata_change_refreshes_clean_file_without_invalidating(conn, cfg, tmp_path):
    folder = write_locale(tmp_path / "py", "en_US", {"001-intro.vtt": "Hello."}, "auto")
    run(conn, cfg, folder)
    tid = conn.execute("SELECT id FROM transcript").fetchone()["id"]
    with conn:
        conn.execute("INSERT INTO knowledge_node (transcript_id, node_type, title_json, position, sentence_start, "
                     "sentence_end, status) VALUES (?, 'topic', '{}', 0, 0, 0, 'approved')", (tid,))
    manifest = json.loads((folder / "_manifest.json").read_text(encoding="utf-8"))
    manifest["lectures"][0].update(title="New title", position=2)
    (folder / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    run(conn, cfg, folder)
    path = conn.execute("SELECT clean_path FROM transcript").fetchone()["clean_path"]
    assert path.endswith("en_US/002-new-title.json")
    doc = json.loads((cfg["root"] / path).read_text(encoding="utf-8"))
    assert (doc["lesson"]["title"], doc["lesson"]["position"]) == ("New title", 2)
    assert not (cfg["root"] / "data/clean/py/en_US/001-gioi-thieu.json").exists()
    assert conn.execute("SELECT COUNT(*) FROM knowledge_node").fetchone()[0] == 1


def test_force_clean_with_same_content_keeps_extracted_data(conn, cfg, tmp_path):
    from engine.cleaner import clean_course

    write(tmp_path / "c" / "a.vtt", VTT.format(text="Same."))
    run(conn, cfg, tmp_path / "c")
    tid = conn.execute("SELECT id FROM transcript").fetchone()["id"]
    with conn:
        conn.execute("INSERT INTO knowledge_node (transcript_id, node_type, title_json, position, sentence_start, "
                     "sentence_end, status) VALUES (?, 'topic', '{}', 0, 0, 0, 'approved')", (tid,))
    assert clean_course(conn, 1, cfg, force=True)["cleaned"] == 1
    assert conn.execute("SELECT COUNT(*) FROM knowledge_node").fetchone()[0] == 1


def test_renamed_raw_file_with_same_content_updates_source_path(conn, cfg, tmp_path):
    folder = write_locale(tmp_path / "py", "en_US", {"001-intro.vtt": "Hello."}, "auto")
    run(conn, cfg, folder)
    (folder / "001-intro.vtt").rename(folder / "002-intro.vtt")
    manifest = json.loads((folder / "_manifest.json").read_text(encoding="utf-8"))
    manifest["lectures"][0]["filename"] = "002-intro.vtt"
    (folder / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert run(conn, cfg, folder).unchanged == 1
    row = conn.execute("SELECT filename, source_path FROM transcript").fetchone()
    assert (row["filename"], row["source_path"]) == ("en_US/002-intro.vtt", "py/en_US/002-intro.vtt")


def test_pick_one_per_lesson_prefers_en_us_only_for_english(conn, cfg, tmp_path):
    rows = [{"lesson_id": 1, "caption_source": "manual", "language": lang, "position": 1}
            for lang in ("es_US", "es_ES")]
    assert database.pick_one_per_lesson(rows, "es")[0]["language"] == "es_ES"
    rows = [{"lesson_id": 1, "caption_source": "manual", "language": lang, "position": 1}
            for lang in ("en_GB", "en_US")]
    assert database.pick_one_per_lesson(rows, "en")[0]["language"] == "en_US"
