"""Làm sạch WebVTT: bỏ header, NOTE/STYLE, cue id, timestamp, tag và cue lặp."""
import html
import re

TIMING = re.compile(r"^\s*(?:\d+:)?\d{2}:\d{2}[.,]\d{3}\s*-->")
TAG = re.compile(r"<[^>]*>")
SPACES = re.compile(r"\s+")


def _clean_line(line: str) -> str:
    return SPACES.sub(" ", html.unescape(TAG.sub("", line))).strip()


def parse_vtt(text: str) -> list[str]:
    """Trả về danh sách văn bản của từng cue theo thứ tự, đã loại cue trùng liên tiếp."""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    cues: list[str] = []
    prev = ""
    for block in re.split(r"\n[ \t]*\n", text):
        lines = block.split("\n")
        timing_at = next((i for i, line in enumerate(lines) if TIMING.match(line)), None)
        if timing_at is None:  # header WEBVTT, NOTE, STYLE, REGION
            continue
        cue = " ".join(filter(None, (_clean_line(line) for line in lines[timing_at + 1:])))
        if not cue or cue == prev:
            continue
        # Caption cuộn: cue mới lặp lại toàn bộ cue trước rồi nối thêm chữ.
        emitted = cue[len(prev) + 1:] if prev and cue.startswith(prev + " ") else cue
        cues.append(emitted)
        prev = cue
    return cues
