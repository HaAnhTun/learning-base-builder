"""Read input files as Cues: VTT with timestamps; TXT/MD one cue per line, blank line = paragraph break."""
import re
from pathlib import Path

from engine.vtt_parser import Cue, parse_vtt

SUPPORTED = {".vtt", ".txt", ".md"}
MD_HEADING = re.compile(r"^#{1,6}\s+")
MD_QUOTE = re.compile(r"^(?:>\s*)+")
MD_RULE = re.compile(r"^\s*([-*_])\s*(?:\1\s*){2,}$")


def _parse_plain(text: str, markdown: bool) -> list[Cue]:
    cues, para_break = [], True
    for line in text.splitlines():
        line = line.strip()
        heading = False
        if markdown:
            if MD_RULE.match(line):
                para_break = True
                continue
            heading = bool(MD_HEADING.match(line))
            line = MD_QUOTE.sub("", MD_HEADING.sub("", line)).strip()
        if not line:
            para_break = True
            continue
        cues.append(Cue(None, None, [line], para_break or heading))
        para_break = heading  # a heading is its own paragraph
    return cues


def parse_text(text: str, suffix: str) -> list[Cue]:
    suffix = suffix.lower()
    if suffix == ".vtt":
        return parse_vtt(text)
    if suffix in (".txt", ".md"):
        return _parse_plain(text.lstrip("\ufeff"), markdown=suffix == ".md")
    raise ValueError(f"Định dạng không hỗ trợ: {suffix}")


def parse_file(path: Path) -> list[Cue]:
    return parse_text(path.read_text(encoding="utf-8-sig", errors="replace"), path.suffix)
