import json

from engine.export_notebooklm import Chapter, build_files, export_course, normalize_lang, render_lesson, safe_filename
from engine.importer import import_folder


def doc(position, title, words=10, chapter=1, timed=True):
    sentences = [{"id": i, "start": float(i * 10) if timed else None, "end": float(i * 10 + 5) if timed else None,
                  "text": f"Sentence {i} " + "word " * (words - 2)} for i in range(2)]
    return {"course": {"title": "Course T"}, "language": "en_US", "caption_source": "auto",
            "lesson": {"position": position, "title": title, "chapter_index": chapter},
            "word_count": words * 2, "sentences": sentences, "paragraphs": [[0, 0], [1, 1]]}


def test_safe_filename_and_normalize_lang():
    assert safe_filename('S3: "Lifecycle" / Rules?. ') == "S3 Lifecycle Rules"
    assert safe_filename("CON") == "_CON"
    assert (normalize_lang("EN"), normalize_lang("en-us"), normalize_lang("vi_vn")) == ("en", "en_US", "vi_VN")


def test_render_lesson_has_meta_and_paragraphs_without_time_markers():
    text = render_lesson(doc(12, "S3 Lifecycle Rules"), 384, "##")
    lines = text.splitlines()
    assert lines[0] == "## 12. S3 Lifecycle Rules"
    assert lines[2] == "> Course: Course T · Lesson 12/384 · en_US · auto caption"
    assert lines[4].startswith("Sentence 0")
    assert lines[6].startswith("Sentence 1")
    assert "**[" not in text


def chapters(n, lessons_per=2):
    return [Chapter(i, f"Chapter {i}", [doc(i * 10 + j, f"L{i}-{j}", chapter=i) for j in range(lessons_per)])
            for i in range(1, n + 1)]


def test_by_chapter_one_file_per_chapter():
    files, warnings = build_files("Course T", chapters(3), "chapter", 45, 200000)
    assert list(files) == ["01 - Chapter 1.md", "02 - Chapter 2.md", "03 - Chapter 3.md"]
    content = files["02 - Chapter 2.md"][0]
    assert content.startswith("# Chapter 2: Chapter 2\n")
    assert content.count("\n## ") == 2
    assert warnings == []


def test_many_chapters_are_merged_into_volumes_within_source_limit():
    files, _ = build_files("Course T", chapters(100, lessons_per=1), "chapter", 45, 200000)
    assert len(files) <= 45
    assert list(files)[0] == "Vol 01 (Chapters 1–3).md"
    assert sum(f.count("# Chapter ") for f, _ in files.values()) == 100


def test_word_limit_splits_into_parts_at_lesson_boundaries():
    files, _ = build_files("Course T", chapters(1, lessons_per=5), "chapter", 45, max_words=45)
    assert list(files) == ["01 - Chapter 1 (part 1).md", "01 - Chapter 1 (part 2).md", "01 - Chapter 1 (part 3).md"]
    assert all(f.startswith("# Chapter 1:") for f, _ in files.values())


def test_by_course_single_file():
    files, _ = build_files("Course: T", chapters(3), "course", 45, 200000)
    assert list(files) == ["Course T.md"]


def test_by_lesson_warns_over_tier_limits():
    files, warnings = build_files("Course T", chapters(60, lessons_per=2), "lesson", 45, 200000)
    assert len(files) == 120
    assert next(iter(files)).startswith("010 - L1-0")
    assert [w.split("gói ")[1].rstrip(".") for w in warnings] == ["Free", "Plus"]


def test_export_course_end_to_end_is_deterministic(conn, cfg, tmp_path):
    course_dir = tmp_path / "data" / "input" / "py"
    folder = course_dir / "en_US"
    folder.mkdir(parents=True)
    lectures = []
    for pos, (chapter_index, chapter) in enumerate([(1, "Intro"), (1, "Intro"), (2, "Basics")], 1):
        name = f"{pos:03d}-l{pos}.vtt"
        (folder / name).write_text(f"WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nLesson {pos} text.\n", encoding="utf-8")
        lectures.append({"lecture_id": pos, "position": pos, "chapter_title": chapter, "chapter_index": chapter_index,
                         "title": f"Lesson {pos}", "filename": name, "source": "auto"})
    (folder / "_manifest.json").write_text(json.dumps({
        "course_id": 1, "slug": "py", "title": "Py Course", "url": "/course/py/", "host": "x.udemy.com",
        "locale_id": "en_US", "lectures": lectures, "skipped": []}), encoding="utf-8")
    import_folder(conn, course_dir, cfg)

    r = export_course(conn, "py", cfg)
    out = tmp_path / "data" / "export" / "notebooklm" / "py" / "en"
    assert r.folder == out and r.lessons == 3
    assert sorted(p.name for p in out.iterdir()) == ["01 - Intro.md", "02 - Basics.md", "index.md"]
    intro = (out / "01 - Intro.md").read_text(encoding="utf-8")
    assert "## 1. Lesson 1" in intro and "## 2. Lesson 2" in intro and "\nLesson 1 text.\n" in intro
    index = (out / "index.md").read_text(encoding="utf-8")
    assert "# Py Course" in index and "- Chapter 2: Basics" in index and "  - 3. Lesson 3" in index

    before = {p.name: p.read_text(encoding="utf-8") for p in out.iterdir()}
    export_course(conn, "py", cfg)
    assert {p.name: p.read_text(encoding="utf-8") for p in out.iterdir()} == before

    export_course(conn, "py", cfg, by="course")
    assert sorted(p.name for p in out.iterdir()) == ["Py Course.md", "index.md"]  # previous export's files are replaced


def test_transcript_text_cannot_become_markdown_headings():
    d = doc(1, "A", timed=False)
    d["sentences"][0]["text"] = "# Chapter 9: Fake"
    files, _ = build_files("Course T", [Chapter(1, "Real", [d])], "chapter", 45, 200000)
    content = files["01 - Real.md"][0]
    assert "\\# Chapter 9: Fake" in content
    assert content.count("\n# Chapter") == 0 and content.startswith("# Chapter 1: Real")


def test_total_uses_course_positions_not_exported_count():
    files, _ = build_files("Course T", [Chapter(1, "C", [doc(5, "Five")])], "lesson", 45, 200000, total_lessons=7)
    assert "Lesson 5/7" in next(iter(files.values()))[0]
