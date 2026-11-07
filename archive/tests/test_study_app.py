"""End-to-end check of the static study app (study/) in headless Chrome; skipped without Playwright/Chrome."""
import json
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
STUDY = Path(__file__).resolve().parent.parent / "study" / "index.html"

VOCAB = {"kind": "vocabulary", "course": "Demo", "slug": "demo", "level": "B2", "total_selected": 2, "terms": [
    {"rank": 1, "term": "Malformed", "ipa": "/ˌmælˈfɔːrmd/", "meaning": "Sai định dạng, bị lỗi cấu trúc.",
     "pos": "Tính từ", "domain": {"field": "IT", "text": "Malformed JSON = JSON sai cấu trúc."},
     "example": {"en": "The request is malformed.", "vi": "Yêu cầu có định dạng không hợp lệ."},
     "compare": "Invalid = Không hợp lệ; Malformed = Sai cấu trúc.", "expansion": None, "type": "general",
     "importance": 92},
    {"rank": 2, "term": "MCP", "ipa": None, "meaning": "Giao thức MCP.", "pos": "Từ viết tắt", "domain": None,
     "example": None, "compare": None, "expansion": "Model Context Protocol", "type": "acronym", "importance": 87},
]}
KNOWLEDGE = {"kind": "knowledge", "course": "Demo", "slug": "demo", "languages": ["en", "vi"], "concepts": [],
             "relations": [], "lessons": [{"n": 1, "title": "Intro", "chapter": "Chapter 1: Basics", "topics": [
                 {"title": {"en": "Setup", "vi": "Cài đặt"}, "items": [
                     {"type": "process", "title": {"en": "Add a server", "vi": "Thêm server"}, "importance": 60,
                      "question": {"en": "How to add a server?", "vi": "Các bước thêm server?"},
                      "content": {"en": ["Install", "Register"], "vi": ["Cài đặt", "Đăng ký"]}},
                     {"type": "warning", "title": {"en": "No secrets", "vi": "Không lộ bí mật"}, "importance": 95,
                      "question": {"en": "What must never be exposed?", "vi": "Điều gì không được để lộ?"},
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
    assert "Điều gì không được để lộ?" in page.inner_text("#front")  # most important first, question on the front
    page.locator("#filters select").nth(2).select_option("lesson")
    page.locator("#filters select").nth(1).select_option("both")
    assert "How to add a server? / Các bước thêm server?" in page.inner_text("#front")  # lesson order, bilingual
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
    front = page.inner_text("#front")
    assert "Malformed" in front and "/ˌmælˈfɔːrmd/" in front and "Tính từ" in front
    page.keyboard.press("Space")
    back = page.inner_text("#back")
    assert "Sai định dạng" in back and "Trong IT: Malformed JSON = JSON sai cấu trúc." in back
    assert "The request is malformed." in back and "Yêu cầu có định dạng không hợp lệ." in back
    assert "Phân biệt: Invalid" in back and "[object" not in back and "null" not in back
    page.keyboard.press("ArrowLeft")  # "Chưa nhớ" → next card
    assert "MCP" in page.inner_text("#front") and "Model Context Protocol" in page.inner_text("#front")
    page.keyboard.press("Space")
    assert "Giao thức MCP." in page.inner_text("#back")  # a card without the optional lines still renders
