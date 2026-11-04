"""Đọc file đầu vào thành danh sách đơn vị văn bản (cue VTT hoặc dòng TXT/MD)."""
import re
from pathlib import Path

from engine.vtt_parser import parse_vtt

SUPPORTED = {".vtt", ".txt", ".md"}
MD_PREFIX = re.compile(r"^(?:#{1,6}|>)\s*")
MD_RULE = re.compile(r"^\s*([-*_])\s*(?:\1\s*){2,}$")


def _parse_plain(text: str, markdown: bool) -> list[str]:
    units = []
    for line in text.splitlines():
        line = line.strip()
        if markdown:
            if MD_RULE.match(line):
                continue
            line = MD_PREFIX.sub("", line).strip()
        if line:
            units.append(line)
    return units


def parse_text(text: str, suffix: str) -> list[str]:
    suffix = suffix.lower()
    if suffix == ".vtt":
        return parse_vtt(text)
    if suffix in (".txt", ".md"):
        return _parse_plain(text.lstrip("﻿"), markdown=suffix == ".md")
    raise ValueError(f"Định dạng không hỗ trợ: {suffix}")


def parse_file(path: Path) -> list[str]:
    return parse_text(path.read_text(encoding="utf-8-sig", errors="replace"), path.suffix)
