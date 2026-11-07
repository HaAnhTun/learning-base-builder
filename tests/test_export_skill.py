import json

import yaml

from engine.export_skill import export_skill, html_to_text, render_quiz
from engine.importer import import_folder
from engine.materials import fetch_materials
from tests.test_materials import FakeClient, assessment

COURSE = {"id": 1, "published_title": "py", "title": "Py Course", "url": "/course/py/"}


def question(n, section="", correct=("b",), feedbacks=("", "<p>Because &amp; so.</p>", "", "<p>Wrong: D is slow.</p>")):
    q = assessment(n, correct=correct[0])
    q["section"], q["correct_response"] = section, list(correct)
    q["prompt"]["feedbacks"] = list(feedbacks)
    return q


def test_html_to_text():
    assert html_to_text("<p>One &amp; two&nbsp;three</p><p>Run <code>ls -l</code></p>") == "One & two three\n\nRun `ls -l`"
    assert html_to_text("<p>Code:</p><pre>x = 1\n  y = 2</pre><p>After</p>") == "Code:\n```\nx = 1\n  y = 2\n```\nAfter"
    assert html_to_text("<p>Use &lt;context&gt; tags</p>") == "Use <context> tags"  # escaped tags are content, not HTML


def test_render_quiz_has_answer_key_and_explanations():
    quiz = {"title": "1A Quiz", "chapter_title": "D1: Basics", "pass_percent": 70,
            "assessments": [question(1, section="D1"), question(2, correct=("a", "c"), feedbacks=("<p>Both.</p>", "", "", ""))]}
    text = render_quiz(quiz, "Py Course")
    assert text.startswith("# 1A Quiz\n\n> Course: Py Course · D1: Basics · 2 questions · pass mark 70% · ANSWER KEY INCLUDED")
    assert "## Question 1 [D1]\n\nQuestion 1?\n\nA. A1\nB. A2\nC. A3\nD. A4\n\n**Answer:** B\n**Explanation:** Because & so.\n" \
           "**Why not D:** Wrong: D is slow.\n" in text
    assert "## Question 2\n" in text and "**Answer:** A, C\n**Explanation:** Both." in text  # no tag without a section


def make_course(conn, cfg, tmp_path, with_quizzes=True):
    course_dir = tmp_path / "data" / "input" / "py"
    folder = course_dir / "en_US"
    folder.mkdir(parents=True)
    lectures = []
    for pos, (index, chapter) in enumerate([(1, "Intro"), (1, "Intro"), (2, "Basics")], 1):
        name = f"{pos:03d}-l{pos}.vtt"
        (folder / name).write_text(f"WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nLesson {pos} text.\n", encoding="utf-8")
        lectures.append({"lecture_id": pos, "position": pos, "chapter_title": chapter, "chapter_index": index,
                         "title": f"Lesson {pos}", "filename": name, "source": "auto"})
    (folder / "_manifest.json").write_text(json.dumps({
        "course_id": 1, "slug": "py", "title": "Py Course", "url": "/course/py/", "host": "x.udemy.com",
        "locale_id": "en_US", "lectures": lectures, "skipped": []}), encoding="utf-8")
    import_folder(conn, course_dir, cfg)
    if with_quizzes:
        items = [
            {"_class": "chapter", "id": 10, "title": "Intro", "object_index": 1},
            {"_class": "lecture", "id": 1, "title": "Lesson 1", "supplementary_assets": [
                {"id": "9", "asset_type": "File", "title": "Diagram", "filename": "diagram.png",
                 "download_urls": {"File": [{"file": "https://cdn/d"}]}}]},
            {"_class": "lecture", "id": 2, "title": "Lesson 2"},
            {"_class": "quiz", "id": 50, "title": "1A Quiz", "type": "simple-quiz", "pass_percent": 70},
            {"_class": "chapter", "id": 11, "title": "Basics", "object_index": 2},
            {"_class": "lecture", "id": 3, "title": "Lesson 3"},
            {"_class": "chapter", "id": 12, "title": "Exams", "object_index": 3},
            {"_class": "quiz", "id": 51, "title": "Exam 1", "type": "practice-test", "pass_percent": 72}]
        client = FakeClient(items, {50: [question(1), question(2)], 51: [question(3, section="D1")]},
                            {"https://cdn/d": b"PNG"})
        fetch_materials(client, COURSE, tmp_path / "data" / "input")


def skill_md(folder):
    text = (folder / "SKILL.md").read_text(encoding="utf-8")
    _, front, body = text.split("---\n", 2)
    return yaml.safe_load(front), body


def test_export_skill_end_to_end(conn, cfg, tmp_path):
    make_course(conn, cfg, tmp_path)
    r = export_skill(conn, "py", cfg)
    folder = tmp_path / "data" / "export" / "skills" / "py"
    assert r.folder == folder and (r.chapters, r.quizzes, r.questions, r.attachments) == (2, 2, 3, 1)

    front, body = skill_md(folder)
    assert front["name"] == "py" and "Py Course" in front["description"] and "3 quiz questions" in front["description"]
    assert "| 1. Intro | `references/course/01 - Intro.md` | `references/quizzes/01 - 1A Quiz.md` | 2 |" in body
    assert "| 2. Basics | `references/course/02 - Basics.md` | — | — |" in body
    assert "Practice exams (no transcript):\n\n- `references/quizzes/02 - Exam 1.md` — 1 questions, pass mark 72%" in body
    assert "references/materials/index.md" in body

    ref = folder / "references"
    assert sorted(p.name for p in (ref / "course").iterdir()) == ["01 - Intro.md", "02 - Basics.md"]
    assert "Lesson 1 text." in (ref / "course" / "01 - Intro.md").read_text(encoding="utf-8")
    assert "## Question 1\n" in (ref / "quizzes" / "01 - 1A Quiz.md").read_text(encoding="utf-8")
    assert "## Question 1 [D1]" in (ref / "quizzes" / "02 - Exam 1.md").read_text(encoding="utf-8")
    assert (ref / "materials" / "001-diagram.png").read_bytes() == b"PNG"
    assert "lesson 1 “Lesson 1” (Intro)" in (ref / "materials" / "index.md").read_text(encoding="utf-8")

    before = {p.relative_to(folder): p.read_bytes() for p in folder.rglob("*") if p.is_file()}
    export_skill(conn, "py", cfg)
    assert {p.relative_to(folder): p.read_bytes() for p in folder.rglob("*") if p.is_file()} == before  # deterministic
    (ref / "quizzes" / "stale.md").write_text("old", encoding="utf-8")
    export_skill(conn, "py", cfg)
    assert not (ref / "quizzes" / "stale.md").exists()  # a re-export replaces the previous output


def test_course_without_quizzes_is_a_transcript_only_skill(conn, cfg, tmp_path):
    make_course(conn, cfg, tmp_path, with_quizzes=False)
    r = export_skill(conn, "py", cfg)
    front, body = skill_md(r.folder)
    assert "quiz" not in front["description"] and (r.quizzes, r.attachments) == (0, 0)
    assert "| 1. Intro | `references/course/01 - Intro.md` |\n" in body
    assert not (r.folder / "references" / "quizzes").exists() and "Quiz me" not in body and "answer key" not in body.lower()
