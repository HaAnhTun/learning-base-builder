"""Shared term / concept-name normalizer for Vocabulary and Knowledge Mode (SPEC 2.0 §7.2)."""
import re
import unicodedata

# Acronym / technical symbol: starts uppercase and has >=2 uppercase letters or a digit (S3, EC2, IAM, IPv4, OAuth).
ACRONYM = re.compile(r"^(?=(?:[^A-Z]*[A-Z]){2}|.*\d)[A-Z][A-Za-z0-9&]*$")
# Lowercase technical abbreviation containing digits (k8s, i18n).
ABBREVIATION = re.compile(r"^[a-z]+\d+[a-z0-9]*$")
DASHES = re.compile(r"\s*[-‐‑‒–—]\s*")
ACRONYM_PLURAL = re.compile(r"^([A-Z][A-Z0-9]+)s$")  # APIs -> API, IDs -> ID
EDGE_PUNCT = re.compile(r"^[^\w]+|[^\w]+$")


def is_acronym(text: str) -> bool:
    return len(text) >= 2 and bool(ACRONYM.match(text))


def is_abbreviation(text: str) -> bool:
    return bool(ABBREVIATION.match(text))


def _token(text: str, lemma: str | None) -> str:
    text = EDGE_PUNCT.sub("", unicodedata.normalize("NFKC", text))
    if is_acronym(text):
        plural = ACRONYM_PLURAL.match(text)
        return plural.group(1) if plural else text
    return (lemma if lemma else text).lower()


def normalize_tokens(tokens: list[tuple[str, str | None]]) -> str:
    """tokens: [(text, lemma)]. Acronyms keep their casing; everything else becomes the lowercase lemma."""
    parts = [p for p in (_token(text, lemma) for text, lemma in tokens) if p]
    return DASHES.sub("-", " ".join(parts)).strip()


def normalize_name(name: str) -> str:
    """Normalize a free-form name (e.g. a concept name) without spaCy: keep acronyms, lowercase the rest."""
    return normalize_tokens([(word, None) for word in DASHES.sub("-", name).split()])
