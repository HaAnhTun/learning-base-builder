"""Deterministic vocabulary candidate extraction (SPEC 2.0 §7.1–7.3): spaCy → normalize → aggregate → filter."""
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from engine import database
from engine.cleaner import load_document
from engine.normalizer import DASHES, is_abbreviation, is_acronym, normalize_tokens

EXTRACTOR_VERSION = "2"
FREQUENCY_FILE = Path(__file__).resolve().parent.parent.parent / "resources" / "word_frequency_en.tsv"
CONTENT_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}
LEADING_DROP_POS = {"DET", "PRON", "PART", "NUM", "ADP", "CCONJ", "SCONJ", "PUNCT", "AUX", "INTJ"}
# Leading quantifier-like modifiers dropped from noun chunks. Content words that spaCy lists as stop words
# ("front", "least", "side", "empty"...) are kept: "least privilege", "front end".
LEADING_QUANTIFIERS = {"next", "same", "other", "own", "more", "most", "many", "much", "few", "several", "such",
                       "various", "certain", "another", "first", "last", "every", "each", "any", "some", "all"}
FILLERS = {"um", "uh", "okay", "ok", "alright", "yeah", "gonna", "wanna", "hmm", "oh"}
MAX_PHRASE_TOKENS = 5


@lru_cache(maxsize=1)
def word_frequencies() -> dict[str, float]:
    freqs = {}
    for line in FREQUENCY_FILE.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            word, zipf = line.split("\t")
            freqs[word] = float(zipf)
    return freqs


@lru_cache(maxsize=1)
def nlp():
    import spacy

    return spacy.load("en_core_web_sm", disable=["ner"])


@dataclass
class Aggregate:
    displays: Counter = field(default_factory=Counter)
    types: Counter = field(default_factory=Counter)
    occurrences: list[tuple[int, int, int]] = field(default_factory=list)  # (lesson_position, transcript_id, sentence_id)


@lru_cache(maxsize=8192)
def _isolated_lemma(word: str) -> str:
    """Lemma of a lowercase word read as a noun ('the <word>'); plural fallback via the frequency list."""
    lemma = nlp()(f"the {word}")[1].lemma_.lower()
    if lemma == word and word.endswith("s") and len(word) > 3 and word[:-1] in word_frequencies():
        lemma = word[:-1]
    return lemma


def _lemma(tok) -> str:
    """spaCy keeps the surface form as lemma for PROPN ("Tokens"); lemmatize the lowercase word instead."""
    if tok.pos_ == "PROPN" and not is_acronym(tok.text):
        return _isolated_lemma(tok.text.lower())
    return tok.lemma_


def _wordlike(tok) -> bool:
    return tok.is_alpha or is_acronym(tok.text) or is_abbreviation(tok.text)


def _is_hyphen_link(doc, i: int) -> bool:
    """doc[i] is a '-' glued to word tokens on both sides (e.g. 'multi-agent')."""
    return (doc[i].text == "-" and 0 < i < len(doc) - 1 and not doc[i - 1].whitespace_ and not doc[i].whitespace_
            and _wordlike(doc[i - 1]) and _wordlike(doc[i + 1]))


def hyphen_compounds(doc) -> list[tuple[int, int]]:
    """Inclusive token spans of hyphenated compounds such as 'sub-agent' or 'state-of-the-art'."""
    spans, i = [], 0
    while i < len(doc):
        if i + 1 < len(doc) and _is_hyphen_link(doc, i + 1):
            start = i
            while i + 1 < len(doc) and _is_hyphen_link(doc, i + 1):
                i += 2
            spans.append((start, i))
        i += 1
    return spans


def normalize_span(tokens) -> tuple[str, str]:
    """(normalized, display) of a multi-token phrase: only the head (last word) is lemmatized."""
    parts = []
    for i, tok in enumerate(tokens):
        if tok.text == "-":
            parts.append("-")
            continue
        parts.append(normalize_tokens([(tok.text, _lemma(tok) if i == len(tokens) - 1 else None)]))
        if tok.whitespace_ and i < len(tokens) - 1:
            parts.append(" ")
    normalized = DASHES.sub("-", "".join(parts)).strip()
    display = "".join(t.text + t.whitespace_ for t in tokens).strip()
    return normalized, display


def _phrase(tokens) -> list:
    """Strip leading function words / quantifiers, a leading possessor ("the model's") and trailing punctuation."""
    tokens = list(tokens)
    possessive = [i for i, t in enumerate(tokens) if t.tag_ == "POS"]
    if possessive:
        tokens = tokens[possessive[-1] + 1:]
    doc = tokens[0].doc if tokens else None
    while tokens and (tokens[0].pos_ in LEADING_DROP_POS or tokens[0].lower_ in LEADING_QUANTIFIERS) \
            and not is_acronym(tokens[0].text) \
            and not (tokens[0].i + 1 < len(doc) and _is_hyphen_link(doc, tokens[0].i + 1)):  # keep 'few-shot'
        tokens.pop(0)
    while tokens and tokens[-1].pos_ == "PUNCT" and tokens[-1].text != "-":
        tokens.pop()
    return tokens


def sentence_candidates(doc) -> list[tuple[str, str, str]]:
    """Return (normalized, display, preliminary_type) found in one parsed sentence."""
    found = []
    compounds = hyphen_compounds(doc)
    in_compound = {i for start, end in compounds for i in range(start, end + 1)}
    for start, end in compounds:
        tokens = list(doc[start:end + 1])
        normalized, display = normalize_span(tokens)
        technical = any(t.pos_ == "PROPN" or is_acronym(t.text) for t in tokens)
        found.append((normalized, display, "technical_term" if technical else "collocation"))
    for tok in doc:
        text = tok.text
        if tok.i in in_compound:  # 'sub' / 'agent' of 'sub-agent' are fragments, not words of their own
            pass
        elif is_acronym(text):
            found.append((normalize_tokens([(text, None)]), text, "acronym"))
        elif is_abbreviation(text):
            found.append((text.lower(), text, "abbreviation"))
        elif tok.pos_ in CONTENT_POS and tok.is_alpha:
            found.append((normalize_tokens([(text, _lemma(tok))]), text, "general"))
        if tok.dep_ == "prt" and tok.head.pos_ == "VERB":
            verb = tok.head
            found.append((f"{verb.lemma_.lower()} {text.lower()}", f"{verb.text} {text}", "phrasal_verb"))
    for chunk in doc.noun_chunks:
        tokens = _phrase(chunk)
        words = [t for t in tokens if t.text != "-"]
        if tokens and tokens[0].text != "-" and 2 <= len(words) <= MAX_PHRASE_TOKENS and all(
                _wordlike(t) or _is_hyphen_link(doc, t.i) for t in tokens) and not (
                tokens[0].i, tokens[-1].i) in compounds:
            normalized, display = normalize_span(tokens)
            technical = any(t.pos_ == "PROPN" or is_acronym(t.text) for t in tokens)
            found.append((normalized, display, "technical_term" if technical else "collocation"))
    return found


def merge_case_variants(aggregates: dict, stop_words: set[str]) -> None:
    """Merge single-word keys that differ only by case into the acronym form (JSON/json, STDIO/stdio)."""
    by_fold: dict[str, list[str]] = defaultdict(list)
    for key in aggregates:
        if " " not in key and "-" not in key:
            by_fold[key.casefold()].append(key)
    for fold, keys in by_fold.items():
        acronyms = [k for k in keys if is_acronym(k)]
        if not acronyms or len(keys) < 2 or fold in stop_words:
            continue
        target = max(acronyms, key=lambda k: (len(aggregates[k].occurrences), k))
        for key in keys:
            if key != target:
                agg = aggregates.pop(key)
                aggregates[target].displays.update(agg.displays)
                aggregates[target].types.update({"acronym": sum(agg.types.values())})
                aggregates[target].occurrences.extend(agg.occurrences)


def _keyness(frequency: int, total_words: int, zipf: float | None) -> float:
    per_million = frequency / max(total_words, 1) * 1_000_000
    general = 10 ** (zipf - 3) if zipf is not None else 0.0
    return math.log2((per_million + 1) / (general + 1))


def filter_reason(normalized: str, ptype: str, frequency: int, total_words: int, zipf: float | None,
                  stop_words: set[str], zipf_threshold: float, keyness_min: float,
                  phrase_min_frequency: int) -> tuple[str | None, float]:
    """Return (reason or None, keyness). Token length is never used as a criterion (SPEC 7.3)."""
    keyness = _keyness(frequency, total_words, zipf)
    if not any(c.isalpha() for c in normalized) or normalized.lower() in FILLERS:
        return "noise", keyness
    if ptype in ("acronym", "abbreviation"):
        return None, keyness
    if " " in normalized:  # multi-word term or phrasal verb
        return (None if frequency >= phrase_min_frequency else "low_frequency"), keyness
    if normalized.lower() in stop_words:
        return "stopword", keyness
    if zipf is not None and zipf >= zipf_threshold and keyness < keyness_min:
        return "common_word", keyness
    return None, keyness


def pick_contexts(occurrences: list[tuple[int, int, int]], limit: int) -> list[list[int]]:
    """Deterministic: first occurrence in each distinct lesson (lesson order), then fill from the earliest ones."""
    ordered = sorted(set(occurrences))
    chosen, seen_lessons = [], set()
    for occ in ordered:
        if occ[0] not in seen_lessons:
            seen_lessons.add(occ[0])
            chosen.append(occ)
        if len(chosen) == limit:
            break
    for occ in ordered:
        if len(chosen) == limit:
            break
        if occ not in chosen:
            chosen.append(occ)
    return [[tid, sid] for _, tid, sid in sorted(chosen)]


def english_transcripts(conn, course_id: int) -> list:
    rows = database.course_transcripts(conn, course_id, "en")
    return [r for r in database.pick_one_per_lesson(rows, "en") if r["clean_path"]]


def config_version(cfg: dict) -> str:
    level = cfg["learner"]["cefr_level"]
    voc = cfg["vocabulary"]
    return (f"{EXTRACTOR_VERSION}|level={level}|zipf={voc['zipf_threshold_by_level'][level]}"
            f"|keyness={voc['keyness_min']}|phrase_min={voc['phrase_min_frequency']}"
            f"|contexts={voc['contexts_per_candidate']}")


def extract_course_candidates(conn, course_id: int, cfg: dict, progress=lambda message: None) -> dict:
    """Recompute the course's candidate set from the Clean Dataset (deterministic, idempotent)."""
    level = cfg["learner"]["cefr_level"]
    if not level:
        raise ValueError("learner.cefr_level chưa được đặt (A2/B1/B2/C1).")
    voc = cfg["vocabulary"]
    zipf_threshold = voc["zipf_threshold_by_level"][level]
    transcripts = english_transcripts(conn, course_id)
    if not transcripts:
        raise LookupError("Khóa học không có transcript tiếng Anh đã làm sạch.")

    model = nlp()
    stop_words = set(model.Defaults.stop_words)
    freqs = word_frequencies()
    aggregates: dict[str, Aggregate] = defaultdict(Aggregate)
    sentence_text: dict[tuple[int, int], str] = {}
    total_words = 0
    for i, row in enumerate(transcripts, 1):
        doc = load_document(cfg["root"], row["clean_path"])
        texts = [s["text"] for s in doc["sentences"]]
        total_words += doc["word_count"]
        for sentence, parsed in zip(doc["sentences"], model.pipe(texts, batch_size=64)):
            sentence_text[(row["id"], sentence["id"])] = sentence["text"]
            for normalized, display, ptype in sentence_candidates(parsed):
                agg = aggregates[normalized]
                agg.displays[display] += 1
                agg.types[ptype] += 1
                agg.occurrences.append((row["position"], row["id"], sentence["id"]))
        if i % 20 == 0 or i == len(transcripts):
            progress(f"  spaCy {i}/{len(transcripts)} bài")

    merge_case_variants(aggregates, stop_words)
    version = config_version(cfg)
    kept = filtered = 0
    with conn:
        existing = {r["term_id"]: r["id"] for r in conn.execute(
            "SELECT id, term_id FROM vocab_candidate WHERE course_id = ?", (course_id,))}
        conn.execute("DELETE FROM vocab_occurrence WHERE candidate_id IN "
                     "(SELECT id FROM vocab_candidate WHERE course_id = ?)", (course_id,))
        current_terms = set()
        for normalized in sorted(aggregates):
            agg = aggregates[normalized]
            ptype = agg.types.most_common(1)[0][0]
            display = sorted(agg.displays.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            zipf = freqs.get(normalized.lower()) if " " not in normalized else None
            frequency = len(agg.occurrences)
            reason, keyness = filter_reason(normalized, ptype, frequency, total_words, zipf, stop_words,
                                            zipf_threshold, voc["keyness_min"], voc["phrase_min_frequency"])
            conn.execute(
                """INSERT INTO vocab_term (normalized_term, display_term, preliminary_type, zipf) VALUES (?, ?, ?, ?)
                   ON CONFLICT(normalized_term) DO UPDATE SET display_term = excluded.display_term,
                     preliminary_type = excluded.preliminary_type, zipf = excluded.zipf""",
                (normalized, display, ptype, zipf))
            term_id = conn.execute("SELECT id FROM vocab_term WHERE normalized_term = ?", (normalized,)).fetchone()[0]
            current_terms.add(term_id)
            contexts = pick_contexts(agg.occurrences, voc["contexts_per_candidate"]) if reason is None else []
            ctx_hash = context_hash([[tid, sid, sentence_text[(tid, sid)]] for tid, sid in contexts])
            conn.execute(
                """INSERT INTO vocab_candidate (course_id, term_id, frequency, lesson_count, keyness, filter_status,
                                                filter_reason, context_sentence_refs, context_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(course_id, term_id) DO UPDATE SET frequency = excluded.frequency,
                     lesson_count = excluded.lesson_count, keyness = excluded.keyness,
                     filter_status = excluded.filter_status, filter_reason = excluded.filter_reason,
                     context_sentence_refs = excluded.context_sentence_refs, context_hash = excluded.context_hash""",
                (course_id, term_id, frequency, len({o[1] for o in agg.occurrences}), round(keyness, 3),
                 "kept" if reason is None else "filtered", reason, json.dumps(contexts), ctx_hash))
            if reason is None:
                kept += 1
                candidate_id = conn.execute("SELECT id FROM vocab_candidate WHERE course_id = ? AND term_id = ?",
                                            (course_id, term_id)).fetchone()[0]
                conn.executemany(
                    "INSERT OR IGNORE INTO vocab_occurrence (candidate_id, transcript_id, sentence_id) VALUES (?, ?, ?)",
                    [(candidate_id, tid, sid) for _, tid, sid in agg.occurrences])
            else:
                filtered += 1
        stale = [cid for term_id, cid in existing.items() if term_id not in current_terms]
        conn.executemany("DELETE FROM vocab_candidate WHERE id = ?", [(cid,) for cid in stale])
        for row in transcripts:
            database.set_state(conn, row["id"], "vocab_occurrences", "done", row["content_hash"], version)
        from engine.vocab.mode import rerank  # local import: mode depends on this module

        rerank(conn, course_id)  # entries of removed/filtered candidates lose their rank
    return {"transcripts": len(transcripts), "words": total_words, "kept": kept, "filtered": filtered,
            "removed": len(stale)}


def context_hash(contexts: list[list]) -> str:
    """Hash of [[transcript_id, sentence_id, text], ...] — identifies the context set shown to the model."""
    return hashlib.sha256(json.dumps(contexts).encode()).hexdigest()


def candidates_fresh(conn, course_id: int, cfg: dict) -> bool:
    """True when every English transcript has up-to-date candidates for the current config."""
    version = config_version(cfg)
    for row in english_transcripts(conn, course_id):
        state = database.get_state(conn, row["id"], "vocab_occurrences")
        if state is None or state["status"] != "done" or state["version"] != version \
                or state["input_hash"] != row["content_hash"]:
            return False
    return True
