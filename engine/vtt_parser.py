"""Parse WebVTT into timestamped cues. No de-duplication here — rolling-caption rules live in the cleaner."""
import html
import re
from dataclasses import dataclass

TIMING = re.compile(r"^\s*((?:\d+:)?\d{1,2}:\d{2}[.,]\d{3})\s*-->\s*((?:\d+:)?\d{1,2}:\d{2}[.,]\d{3})")
TAG = re.compile(r"<[^>]*>")
SPACES = re.compile(r"\s+")


@dataclass
class Cue:
    start: float | None
    end: float | None
    lines: list[str]
    para_break: bool = False  # starts a new paragraph (TXT/MD only)

    @property
    def text(self) -> str:
        return " ".join(self.lines)


def parse_timestamp(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    seconds = float(parts[-1])
    for i, part in enumerate(reversed(parts[:-1]), 1):
        seconds += int(part) * 60 ** i
    return seconds


def _clean_line(line: str) -> str:
    return SPACES.sub(" ", html.unescape(TAG.sub("", line))).strip()


def parse_vtt(text: str) -> list[Cue]:
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    cues: list[Cue] = []
    for block in re.split(r"\n[ \t]*\n", text):
        lines = block.split("\n")
        timing_at = next((i for i, line in enumerate(lines) if TIMING.match(line)), None)
        if timing_at is None:  # WEBVTT header, NOTE, STYLE, REGION blocks
            continue
        m = TIMING.match(lines[timing_at])
        payload = [x for x in (_clean_line(line) for line in lines[timing_at + 1:]) if x]
        if payload:
            cues.append(Cue(parse_timestamp(m.group(1)), parse_timestamp(m.group(2)), payload))
    return cues
