import json

import pytest

from engine.materials import fetch_materials
from engine.udemy_client import AuthError, UdemyError

COURSE = {"id": 1, "published_title": "py-course", "title": "Py Course", "url": "/course/py-course/"}


def assessment(n, correct="b"):
    return {"_class": "assessment", "id": n, "assessment_type": "multiple-choice", "section": "D1",
            "prompt": {"question": f"<p>Question {n}?</p>", "answers": ["<p>A1</p>", "<p>A2</p>", "<p>A3</p>", "<p>A4</p>"],
                       "feedbacks": ["", "<p>Because.</p>", "", ""]}, "correct_response": [correct]}


class FakeClient:
    host = "x.udemy.com"

    def __init__(self, items, quizzes=None, files=None):
        self.items, self.quizzes, self.files = items, quizzes or {}, files or {}
        self.downloaded = []

    def get_course_items(self, course_id):
        return self.items

    def get_quiz_assessments(self, quiz_id, version=1):
        value = self.quizzes[quiz_id]
        if isinstance(value, Exception):
            raise value
        return value

    def download_bytes(self, url):
        self.downloaded.append(url)
        value = self.files[url]
        if isinstance(value, Exception):
            raise value
        return value


def items():
    return [
        {"_class": "chapter", "id": 10, "title": "D1: Basics", "object_index": 1},
        {"_class": "lecture", "id": 100, "title": "Intro", "description": "<p>Read this</p>",
         "supplementary_assets": [
             {"id": "9", "asset_type": "File", "title": "Diagram", "filename": "a/b diagram.png",
              "download_urls": {"File": [{"label": "download", "file": "https://cdn/diagram"}]}},
             {"id": "8", "asset_type": "ExternalLink", "title": "Promo", "external_url": "https://promo.example/x"},
             {"id": "7", "asset_type": "E-Book", "title": "Book"}]},
        {"_class": "lecture", "id": 101, "title": "More", "supplementary_assets": []},
        {"_class": "quiz", "id": 50, "title": "1A Quiz", "type": "simple-quiz", "version": 1, "pass_percent": 70},
        {"_class": "chapter", "id": 11, "title": "Practice Exams", "object_index": 2},
        {"_class": "quiz", "id": 51, "title": "Practice Exam 1", "type": "practice-test", "pass_percent": 70},
        {"_class": "practice", "id": 60, "title": "Code it"},
    ]


def test_quizzes_and_attachments_are_saved_with_indexes(tmp_path):
    client = FakeClient(items(), {50: [assessment(1), assessment(2)], 51: [assessment(3)]},
                        {"https://cdn/diagram": b"PNGDATA"})
    messages = []
    got = fetch_materials(client, COURSE, tmp_path, progress=messages.append)

    quizzes = tmp_path / "py-course" / "quizzes"
    assert sorted(p.name for p in quizzes.iterdir()) == ["01-1a-quiz.json", "02-practice-exam-1.json", "_quizzes.json"]
    quiz = json.loads((quizzes / "01-1a-quiz.json").read_text(encoding="utf-8"))
    assert (quiz["title"], quiz["chapter_title"], quiz["lectures_before"], quiz["pass_percent"]) == ("1A Quiz", "D1: Basics", 2, 70)
    assert [a["id"] for a in quiz["assessments"]] == [1, 2]  # raw questions are kept as they came
    index = json.loads((quizzes / "_quizzes.json").read_text(encoding="utf-8"))
    assert [(q["position"], q["title"], q["questions"], q["chapter_title"]) for q in index["quizzes"]] == [
        (1, "1A Quiz", 2, "D1: Basics"), (2, "Practice Exam 1", 1, "Practice Exams")]

    materials = tmp_path / "py-course" / "materials"
    assert (materials / "001-ab diagram.png").read_bytes() == b"PNGDATA"  # characters invalid in file names are dropped
    items_index = json.loads((materials / "_materials.json").read_text(encoding="utf-8"))["items"]
    assert [(i["kind"], i.get("title")) for i in items_index] == [
        ("description", None), ("file", "Diagram"), ("link", "Promo")]
    assert items_index[2]["url"] == "https://promo.example/x" and client.downloaded == ["https://cdn/diagram"]
    assert (got["quizzes"], got["questions"], got["files"], got["links"]) == (2, 3, 1, 1)
    assert {s["reason"] for s in got["skipped"]} == {"unsupported asset type E-Book", "unsupported item practice"}
    assert not (tmp_path / "py-course" / "_manifest.json").exists() and not (quizzes / "_manifest.json").exists()


def test_failed_quiz_is_skipped_but_auth_error_aborts(tmp_path):
    client = FakeClient(items(), {50: UdemyError("HTTP 404: /quizzes/50/assessments/", 404), 51: [assessment(3)]},
                        {"https://cdn/diagram": b"x"})
    got = fetch_materials(client, COURSE, tmp_path)
    assert got["quizzes"] == 1 and any("404" in s["reason"] for s in got["skipped"])
    assert [p.name for p in (tmp_path / "py-course" / "quizzes").iterdir() if p.suffix == ".json" and p.name[0] != "_"] == [
        "01-practice-exam-1.json"]  # numbering follows the quizzes that were saved

    client = FakeClient(items(), {50: AuthError("expired")}, {"https://cdn/diagram": b"x"})
    with pytest.raises(AuthError):
        fetch_materials(client, COURSE, tmp_path / "other")


def test_course_without_quizzes_or_attachments_writes_nothing(tmp_path):
    plain = [{"_class": "chapter", "id": 1, "title": "C", "object_index": 1},
             {"_class": "lecture", "id": 2, "title": "L", "supplementary_assets": []}]
    got = fetch_materials(FakeClient(plain), COURSE, tmp_path)
    assert (got["quizzes"], got["files"]) == (0, 0) and not (tmp_path / "py-course").exists()
