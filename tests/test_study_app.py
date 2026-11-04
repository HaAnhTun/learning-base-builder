"""End-to-end check of the static study app (study/) in headless Chrome; skipped without Playwright/Chrome."""
import json
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
STUDY = Path(__file__).resolve().parent.parent / "study" / "index.html"

VOCAB = {"kind": "vocabulary", "course": "Demo", "slug": "demo", "level": "B2", "total_selected": 2, "terms": [
    {"rank": 1, "term": "context window", "type": "collocation", "importance": 92, "vi": "cửa sổ ngữ cảnh",
     "en": "Max tokens a model reads at once.", "expansion": None, "cefr": None, "frequency": 9, "lessons": 3,
     "example": {"text": "The context window fills up.", "lesson": 2}},
    {"rank": 2, "term": "MCP", "type": "acronym", "importance": 87, "vi": "giao thức MCP", "en": "A protocol.",
     "expansion": "Model Context Protocol", "cefr": None, "frequency": 5, "lessons": 2, "example": None},
]}
KNOWLEDGE = {"kind": "knowledge", "course": "Demo", "slug": "demo", "languages": ["en", "vi"], "concepts": [],
             "relations": [], "lessons": [{"n": 1, "title": "Intro", "chapter": "Chapter 1: Basics", "topics": [
                 {"title": {"en": "Setup", "vi": "Cài đặt"}, "items": [
                     {"type": "process", "title": {"en": "Add a server", "vi": "Thêm server"},
                      "content": {"en": ["Install", "Register"], "vi": ["Cài đặt", "Đăng ký"]}},
                     {"type": "warning", "title": {"en": "No secrets", "vi": "Không lộ bí mật"},
                      "content": {"en": "Never expose keys.", "vi": "Không để lộ khóa."}, "subtopic": {
                          "en": "Safety", "vi": "An toàn"}}]}]}]}


@pytest.fixture
def page(tmp_path):
    (tmp_path / "vocabulary.json").write_text(json.dumps(VOCAB), encoding="utf-8")
    (tmp_path / "knowledge.json").write_text(json.dumps(KNOWLEDGE), encoding="utf-8")
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            pytest.skip("Chrome is not available for Playwright")
        pg = browser.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("dialog", lambda d: d.accept())
        pg.goto(STUDY.as_uri())
        pg.set_input_files("#file", [str(tmp_path / "vocabulary.json"), str(tmp_path / "knowledge.json")])
        yield pg
        assert not errors
        browser.close()


def test_bilingual_process_card_and_persistence(page):
    page.click("#tabs button:has-text('Kiến thức')")
    page.locator("#filters select").nth(1).select_option("both")
    page.keyboard.press("Space")
    back = page.inner_text("#back")
    assert "[object" not in back and "Install" in back and "Cài đặt" in back
    assert page.locator("#back ol").count() == 2  # one numbered list per language
    page.click("#known")
    assert "An toàn" in page.inner_text("#front")  # subtopic shown as context
    page.reload()
    assert "đã nhớ 1/2" in page.inner_text("#progress")  # last tab and progress restored


def test_vocabulary_card(page):
    page.click("#tabs button:has-text('Từ vựng')")
    assert page.inner_text("#front").strip().endswith("context window")
    page.keyboard.press("Space")
    back = page.inner_text("#back")
    assert "cửa sổ ngữ cảnh" in back and "bài 2" in back
    page.keyboard.press("ArrowLeft")  # "Chưa nhớ" → next card
    assert "MCP" in page.inner_text("#front") and "Model Context Protocol" in page.inner_text("#front")
