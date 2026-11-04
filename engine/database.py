"""SQLite schema (SPEC 2.0 §11) and shared data access helpers."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS course (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    source      TEXT NOT NULL,              -- udemy | local
    external_id TEXT,
    slug        TEXT NOT NULL UNIQUE,
    url         TEXT,
    host        TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson (
    id            INTEGER PRIMARY KEY,
    course_id     INTEGER NOT NULL REFERENCES course(id) ON DELETE CASCADE,
    external_id   TEXT NOT NULL,            -- Udemy lecture id, or the lesson name for hand-placed files
    position      INTEGER NOT NULL,
    chapter_index INTEGER,
    chapter       TEXT,
    title         TEXT NOT NULL,
    UNIQUE (course_id, external_id)
);

CREATE TABLE IF NOT EXISTS transcript (
    id              INTEGER PRIMARY KEY,
    lesson_id       INTEGER NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
    language        TEXT NOT NULL,
    caption_source  TEXT NOT NULL,          -- manual | auto | file
    filename        TEXT NOT NULL,          -- path relative to the course folder
    source_path     TEXT NOT NULL,          -- raw file path (relative to the project root when inside it)
    content_hash    TEXT NOT NULL,
    imported_at     TEXT NOT NULL,
    clean_path      TEXT,
    cleaner_version TEXT,
    sentence_count  INTEGER,
    word_count      INTEGER,
    UNIQUE (lesson_id, language)
);

CREATE TABLE IF NOT EXISTS processing_state (
    transcript_id INTEGER NOT NULL REFERENCES transcript(id) ON DELETE CASCADE,
    stage         TEXT NOT NULL,            -- clean | vocab_occurrences | knowledge
    input_hash    TEXT,
    version       TEXT,
    status        TEXT NOT NULL,            -- done | stale | failed
    updated_at    TEXT NOT NULL,
    PRIMARY KEY (transcript_id, stage)
);

CREATE TABLE IF NOT EXISTS ai_task (
    id             TEXT PRIMARY KEY,        -- <mode>-<first 12 chars of input_hash>
    mode           TEXT NOT NULL,           -- vocab_eval | knowledge_extract
    prompt_version TEXT NOT NULL,
    input_hash     TEXT NOT NULL,
    course_id      INTEGER NOT NULL REFERENCES course(id) ON DELETE CASCADE,
    task_path      TEXT NOT NULL,
    result_path    TEXT NOT NULL,
    status         TEXT NOT NULL,           -- pending | done | invalid | failed
    attempts       INTEGER NOT NULL DEFAULT 0,
    error          TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    UNIQUE (mode, prompt_version, input_hash)
);

CREATE TABLE IF NOT EXISTS vocab_term (
    id               INTEGER PRIMARY KEY,
    normalized_term  TEXT NOT NULL UNIQUE,
    display_term     TEXT NOT NULL,
    preliminary_type TEXT NOT NULL,
    zipf             REAL
);

CREATE TABLE IF NOT EXISTS vocab_candidate (
    id                    INTEGER PRIMARY KEY,
    course_id             INTEGER NOT NULL REFERENCES course(id) ON DELETE CASCADE,
    term_id               INTEGER NOT NULL REFERENCES vocab_term(id) ON DELETE CASCADE,
    frequency             INTEGER NOT NULL,
    lesson_count          INTEGER NOT NULL,
    keyness               REAL,
    filter_status         TEXT NOT NULL,    -- kept | filtered
    filter_reason         TEXT,             -- common_word | stopword | noise
    context_sentence_refs TEXT NOT NULL,    -- JSON [[transcript_id, sentence_id], ...]
    context_hash          TEXT NOT NULL,
    UNIQUE (course_id, term_id)
);

CREATE TABLE IF NOT EXISTS vocab_occurrence (
    candidate_id  INTEGER NOT NULL REFERENCES vocab_candidate(id) ON DELETE CASCADE,
    transcript_id INTEGER NOT NULL REFERENCES transcript(id) ON DELETE CASCADE,
    sentence_id   INTEGER NOT NULL,
    PRIMARY KEY (candidate_id, transcript_id, sentence_id)
);

CREATE TABLE IF NOT EXISTS vocab_entry (
    id                    INTEGER PRIMARY KEY,
    course_id             INTEGER NOT NULL REFERENCES course(id) ON DELETE CASCADE,
    term_id               INTEGER NOT NULL REFERENCES vocab_term(id) ON DELETE CASCADE,
    selected              INTEGER NOT NULL,
    term_type             TEXT,
    importance            INTEGER,
    rank                  INTEGER,
    reason                TEXT,
    vietnamese_meaning    TEXT,
    english_definition    TEXT,
    expansion             TEXT,
    cefr_level            TEXT,
    example_sentence_refs TEXT,             -- JSON [[transcript_id, sentence_id], ...]
    context_hash          TEXT,
    status                TEXT NOT NULL,    -- auto_approved | needs_review | approved | rejected
    confidence            REAL,
    review_notes          TEXT,
    reviewed_at           TEXT,
    prompt_version        TEXT,
    task_id               TEXT,
    UNIQUE (course_id, term_id)
);

CREATE TABLE IF NOT EXISTS knowledge_node (
    id             INTEGER PRIMARY KEY,
    transcript_id  INTEGER NOT NULL REFERENCES transcript(id) ON DELETE CASCADE,
    parent_id      INTEGER REFERENCES knowledge_node(id) ON DELETE CASCADE,
    node_type      TEXT NOT NULL,           -- topic | subtopic
    title_json     TEXT NOT NULL,
    position       INTEGER NOT NULL,
    sentence_start INTEGER NOT NULL,
    sentence_end   INTEGER NOT NULL,
    status         TEXT NOT NULL,
    confidence     REAL,
    review_notes   TEXT,
    reviewed_at    TEXT,
    prompt_version TEXT,
    task_id        TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_item (
    id             INTEGER PRIMARY KEY,
    node_id        INTEGER NOT NULL REFERENCES knowledge_node(id) ON DELETE CASCADE,
    position       INTEGER NOT NULL,
    item_type      TEXT NOT NULL,
    concept_name   TEXT,
    title_json     TEXT NOT NULL,
    content_json   TEXT NOT NULL,
    relation_json  TEXT,
    sentence_start INTEGER NOT NULL,
    sentence_end   INTEGER NOT NULL,
    status         TEXT NOT NULL,
    confidence     REAL,
    review_notes   TEXT,
    reviewed_at    TEXT
);

CREATE TABLE IF NOT EXISTS concept (
    id              INTEGER PRIMARY KEY,
    normalized_name TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concept_mention (
    concept_id        INTEGER NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    knowledge_item_id INTEGER NOT NULL REFERENCES knowledge_item(id) ON DELETE CASCADE,
    PRIMARY KEY (concept_id, knowledge_item_id)
);

CREATE TABLE IF NOT EXISTS concept_relation (
    concept_id         INTEGER NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    related_concept_id INTEGER NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    relation_type      TEXT NOT NULL,
    knowledge_item_id  INTEGER REFERENCES knowledge_item(id) ON DELETE CASCADE,
    PRIMARY KEY (concept_id, related_concept_id, relation_type)
);

CREATE TABLE IF NOT EXISTS review_log (
    id          INTEGER PRIMARY KEY,
    course_id   INTEGER NOT NULL REFERENCES course(id) ON DELETE CASCADE,
    mode        TEXT NOT NULL,              -- vocab | knowledge
    key         TEXT NOT NULL,              -- normalized_term, or <lesson external_id>|<normalized title>
    decision    TEXT NOT NULL,              -- approved | rejected
    edited_json TEXT,
    reviewed_at TEXT NOT NULL,
    UNIQUE (course_id, mode, key)
);
"""


class SchemaError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    has_tables = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    if has_tables and version != SCHEMA_VERSION:
        conn.close()
        raise SchemaError(
            f"{path} dùng schema cũ (version {version}). Dữ liệu chỉ là metadata dựng lại được: "
            f"xóa file này rồi chạy lại `python -m engine import data/input/<khóa>`."
        )
    conn.executescript(SCHEMA)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    return conn


def course_by_slug(conn, slug: str):
    row = conn.execute("SELECT * FROM course WHERE slug = ?", (slug,)).fetchone()
    if row is None:
        raise LookupError(f"Không có khóa học '{slug}' trong DB. Chạy `import` hoặc `fetch` trước.")
    return row


def upsert_course(conn, *, slug, title, source, external_id=None, url=None, host=None) -> int:
    existing = conn.execute("SELECT * FROM course WHERE slug = ?", (slug,)).fetchone()
    if existing and existing["source"] == "udemy" and source != "udemy":
        return existing["id"]  # hand-placed files never overwrite Udemy course metadata
    conn.execute(
        """INSERT INTO course (title, source, external_id, slug, url, host, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(slug) DO UPDATE SET
             title = excluded.title, source = excluded.source, external_id = excluded.external_id,
             url = excluded.url, host = excluded.host""",
        (title, source, external_id, slug, url, host, now()),
    )
    return conn.execute("SELECT id FROM course WHERE slug = ?", (slug,)).fetchone()["id"]


def upsert_lesson(conn, *, course_id, external_id, position, title, chapter=None, chapter_index=None) -> int:
    conn.execute(
        """INSERT INTO lesson (course_id, external_id, position, chapter_index, chapter, title)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(course_id, external_id) DO UPDATE SET
             position = excluded.position, chapter_index = excluded.chapter_index,
             chapter = excluded.chapter, title = excluded.title""",
        (course_id, external_id, position, chapter_index, chapter, title),
    )
    return conn.execute(
        "SELECT id FROM lesson WHERE course_id = ? AND external_id = ?", (course_id, external_id)
    ).fetchone()["id"]


def get_transcript(conn, lesson_id: int, language: str):
    return conn.execute(
        "SELECT * FROM transcript WHERE lesson_id = ? AND language = ?", (lesson_id, language)
    ).fetchone()


def register_transcript(conn, *, lesson_id, language, caption_source, filename, source_path, content_hash) -> int:
    conn.execute(
        """INSERT INTO transcript (lesson_id, language, caption_source, filename, source_path, content_hash,
                                   imported_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(lesson_id, language) DO UPDATE SET
             caption_source = excluded.caption_source, filename = excluded.filename,
             source_path = excluded.source_path, content_hash = excluded.content_hash,
             imported_at = excluded.imported_at""",
        (lesson_id, language, caption_source, filename, source_path, content_hash, now()),
    )
    return get_transcript(conn, lesson_id, language)["id"]


def get_state(conn, transcript_id: int, stage: str):
    return conn.execute(
        "SELECT * FROM processing_state WHERE transcript_id = ? AND stage = ?", (transcript_id, stage)
    ).fetchone()


def set_state(conn, transcript_id: int, stage: str, status: str, input_hash=None, version=None) -> None:
    conn.execute(
        """INSERT INTO processing_state (transcript_id, stage, input_hash, version, status, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(transcript_id, stage) DO UPDATE SET
             input_hash = excluded.input_hash, version = excluded.version,
             status = excluded.status, updated_at = excluded.updated_at""",
        (transcript_id, stage, input_hash, version, status, now()),
    )


def invalidate_extracted(conn, transcript_id: int) -> None:
    """Transcript re-cleaned with new content: sentence ids may change, so drop dependent extracted rows (SPEC 9.5)."""
    conn.execute("DELETE FROM vocab_occurrence WHERE transcript_id = ?", (transcript_id,))
    conn.execute("DELETE FROM knowledge_node WHERE transcript_id = ?", (transcript_id,))
    conn.execute(
        "UPDATE processing_state SET status = 'stale', updated_at = ? "
        "WHERE transcript_id = ? AND stage IN ('vocab_occurrences', 'knowledge')",
        (now(), transcript_id),
    )


def course_transcripts(conn, course_id: int, language_prefix: str | None = None) -> list:
    """Course transcripts joined with lesson info, ordered by lesson position."""
    sql = """SELECT t.*, l.position, l.title AS lesson_title, l.chapter, l.chapter_index,
                    l.external_id AS lesson_external_id
             FROM transcript t JOIN lesson l ON l.id = t.lesson_id
             WHERE l.course_id = ?"""
    params: list = [course_id]
    if language_prefix:  # 'en' matches 'en' and every 'en_*'; 'en_GB' matches exactly (case-insensitive)
        sql += " AND (t.language = ? OR t.language LIKE ? ESCAPE '!')"
        params += [language_prefix, f"{language_prefix}!_%"]
    return conn.execute(sql + " ORDER BY l.position, t.language", params).fetchall()


SOURCE_RANK = {"manual": 0, "auto": 1, "file": 2}


def pick_one_per_lesson(rows, lang: str) -> list:
    """One transcript per lesson, SPEC 3.1 precedence: manual > auto > file, then en_US (for 'en'), then alphabetical."""
    best: dict[int, object] = {}
    for row in rows:
        key = (SOURCE_RANK.get(row["caption_source"], 3), lang == "en" and row["language"] != "en_US", row["language"])
        current = best.get(row["lesson_id"])
        if current is None or key < current[0]:
            best[row["lesson_id"]] = (key, row)
    return sorted((v[1] for v in best.values()), key=lambda r: r["position"])


def stats(conn) -> dict:
    def count(sql: str, *params) -> int:
        return conn.execute(sql, params).fetchone()[0]

    def group(sql: str) -> dict:
        return dict(conn.execute(sql).fetchall())

    return {
        "courses": count("SELECT COUNT(*) FROM course"),
        "lessons": count("SELECT COUNT(*) FROM lesson"),
        "transcripts": count("SELECT COUNT(*) FROM transcript"),
        "cleaned": count("SELECT COUNT(*) FROM processing_state WHERE stage = 'clean' AND status = 'done'"),
        "sentences": count("SELECT COALESCE(SUM(sentence_count), 0) FROM transcript"),
        "words": count("SELECT COALESCE(SUM(word_count), 0) FROM transcript"),
        "ai_tasks": group("SELECT mode || ':' || status, COUNT(*) FROM ai_task GROUP BY mode, status ORDER BY 1"),
        "vocab_candidates": group(
            "SELECT filter_status, COUNT(*) FROM vocab_candidate GROUP BY filter_status ORDER BY 1"),
        "vocab_entries": group(
            "SELECT CASE selected WHEN 1 THEN 'selected' ELSE 'not_selected' END || ':' || status, COUNT(*) "
            "FROM vocab_entry GROUP BY 1 ORDER BY 1"),
        "knowledge_nodes": count("SELECT COUNT(*) FROM knowledge_node"),
        "knowledge_items": group("SELECT status, COUNT(*) FROM knowledge_item GROUP BY status ORDER BY 1"),
        "concepts": count("SELECT COUNT(*) FROM concept"),
    }
