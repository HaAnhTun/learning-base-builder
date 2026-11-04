"""Phân đoạn thích ứng: cả bài là một chunk; bài dài chia đều theo ranh giới câu/cue."""
import math
import re

SENTENCE_END = re.compile(r"(?<=[.!?…。！？])\s+")
# Trung bình câu dài hơn ngưỡng này => coi như không có dấu câu (caption tự động), cắt theo cue.
MAX_AVG_SENTENCE_WORDS = 40


def _words(text: str) -> int:
    return len(text.split())


def _split_long(piece: str, max_words: int) -> list[str]:
    words = piece.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def _pieces(units: list[str], max_words: int) -> list[str]:
    text = " ".join(units)
    sentences = [s for s in SENTENCE_END.split(text) if s.strip()]
    if sentences and _words(text) / len(sentences) <= MAX_AVG_SENTENCE_WORDS:
        pieces = sentences
    else:
        pieces = units
    out = []
    for piece in pieces:
        out.extend(_split_long(piece, max_words) if _words(piece) > max_words else [piece])
    return out


def segment(units: list[str], max_words: int) -> list[str]:
    pieces = _pieces(units, max_words)
    total = sum(_words(p) for p in pieces)
    if total == 0:
        return []
    if total <= max_words:
        return [" ".join(pieces)]

    n = math.ceil(total / max_words)
    target = total / n
    chunks: list[str] = []
    current: list[str] = []
    current_words = seen = 0
    for piece in pieces:
        words = _words(piece)
        if current and current_words + words > max_words:  # giới hạn cứng
            chunks.append(" ".join(current))
            current, current_words = [], 0
        current.append(piece)
        current_words += words
        seen += words
        if len(chunks) < n - 1 and seen >= target * (len(chunks) + 1):
            chunks.append(" ".join(current))
            current, current_words = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks
