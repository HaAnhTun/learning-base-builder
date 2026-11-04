"""Schema SQLite và các thao tác dữ liệu."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

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
    id          INTEGER PRIMARY KEY,
    course_id   INTEGER NOT NULL REFERENCES course(id) ON DELETE CASCADE,
    external_id TEXT NOT NULL,              -- lecture id Udemy, hoặc tên file gốc khi import local
    position    INTEGER NOT NULL,
    chapter     TEXT,
    title       TEXT NOT NULL,
    UNIQUE (course_id, external_id)
);

CREATE TABLE IF NOT EXISTS transcript (
    id             INTEGER PRIMARY KEY,
    lesson_id      INTEGER NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
    language       TEXT NOT NULL,
    caption_source TEXT NOT NULL,           -- manual | auto | file
    filename       TEXT NOT NULL,
    content_hash   TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'imported',  -- imported | extracted | reviewed
    imported_at    TEXT NOT NULL,
    processed_at   TEXT,
    UNIQUE (lesson_id, language)
);

CREATE TABLE IF NOT EXISTS chunk (
    id            INTEGER PRIMARY KEY,
    transcript_id INTEGER NOT NULL REFERENCES transcript(id) ON DELETE CASCADE,
    idx           INTEGER NOT NULL,
    text          TEXT NOT NULL,
    word_count    INTEGER NOT NULL,
    UNIQUE (transcript_id, idx)
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id              INTEGER PRIMARY KEY,
    term            TEXT NOT NULL,
    normalized_term TEXT NOT NULL UNIQUE,
    part_of_speech  TEXT,
    cefr_level      TEXT
);

CREATE TABLE IF NOT EXISTS vocabulary_meaning (
    id                 INTEGER PRIMARY KEY,
    vocabulary_id      INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    english_definition TEXT,
    vietnamese_meaning TEXT,
    example_sentence   TEXT,
    context            TEXT,
    status             TEXT NOT NULL DEFAULT 'pending_review',  -- pending_review | approved
    confidence         REAL
);

CREATE TABLE IF NOT EXISTS concept (
    id                     INTEGER PRIMARY KEY,
    name                   TEXT NOT NULL,
    normalized_name        TEXT NOT NULL UNIQUE,
    explanation            TEXT,
    vietnamese_explanation TEXT,
    example                TEXT,
    status                 TEXT NOT NULL DEFAULT 'pending_review',
    confidence             REAL
);

CREATE TABLE IF NOT EXISTS concept_relation (
    concept_id         INTEGER NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    related_concept_id INTEGER NOT NULL REFERENCES concept(id) ON DELETE CASCADE,
    PRIMARY KEY (concept_id, related_concept_id)
);

CREATE TABLE IF NOT EXISTS knowledge_source (
    id             INTEGER PRIMARY KEY,
    knowledge_type TEXT NOT NULL,           -- vocabulary_meaning | concept
    knowledge_id   INTEGER NOT NULL,
    lesson_id      INTEGER NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
    UNIQUE (knowledge_type, knowledge_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS flashcard (
    id             INTEGER PRIMARY KEY,
    card_type      TEXT NOT NULL,           -- vocab_en_vi | vocab_vi_en | concept
    front          TEXT NOT NULL,
    back           TEXT NOT NULL,
    knowledge_type TEXT NOT NULL,           -- vocabulary | vocabulary_meaning | concept
    knowledge_id   INTEGER NOT NULL,
    created_at     TEXT NOT NULL,
    UNIQUE (card_type, knowledge_type, knowledge_id)
);

CREATE TABLE IF NOT EXISTS extraction_cache (
    content_hash   TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    result_json    TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    PRIMARY KEY (content_hash, prompt_version)
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def upsert_course(conn, *, slug, title, source, external_id=None, url=None, host=None) -> int:
    conn.execute(
        """INSERT INTO course (title, source, external_id, slug, url, host, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(slug) DO UPDATE SET
             title = excluded.title, source = excluded.source, external_id = excluded.external_id,
             url = excluded.url, host = excluded.host""",
        (title, source, external_id, slug, url, host, now()),
    )
    return conn.execute("SELECT id FROM course WHERE slug = ?", (slug,)).fetchone()["id"]


def upsert_lesson(conn, *, course_id, external_id, position, title, chapter=None) -> int:
    conn.execute(
        """INSERT INTO lesson (course_id, external_id, position, chapter, title)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(course_id, external_id) DO UPDATE SET
             position = excluded.position, chapter = excluded.chapter, title = excluded.title""",
        (course_id, external_id, position, chapter, title),
    )
    return conn.execute(
        "SELECT id FROM lesson WHERE course_id = ? AND external_id = ?", (course_id, external_id)
    ).fetchone()["id"]


def get_transcript(conn, lesson_id: int, language: str):
    return conn.execute(
        "SELECT * FROM transcript WHERE lesson_id = ? AND language = ?", (lesson_id, language)
    ).fetchone()


def save_transcript(conn, *, lesson_id, language, caption_source, filename, content_hash, chunks) -> int:
    """Ghi transcript + thay toàn bộ chunk, đưa status về 'imported'. Gọi trong một transaction."""
    conn.execute(
        """INSERT INTO transcript (lesson_id, language, caption_source, filename, content_hash,
                                   status, imported_at, processed_at)
           VALUES (?, ?, ?, ?, ?, 'imported', ?, NULL)
           ON CONFLICT(lesson_id, language) DO UPDATE SET
             caption_source = excluded.caption_source, filename = excluded.filename,
             content_hash = excluded.content_hash, status = 'imported',
             imported_at = excluded.imported_at, processed_at = NULL""",
        (lesson_id, language, caption_source, filename, content_hash, now()),
    )
    transcript_id = get_transcript(conn, lesson_id, language)["id"]
    conn.execute("DELETE FROM chunk WHERE transcript_id = ?", (transcript_id,))
    conn.executemany(
        "INSERT INTO chunk (transcript_id, idx, text, word_count) VALUES (?, ?, ?, ?)",
        [(transcript_id, i, text, len(text.split())) for i, text in enumerate(chunks)],
    )
    return transcript_id


def stats(conn) -> dict:
    def count(sql: str) -> int:
        return conn.execute(sql).fetchone()[0]

    return {
        "courses": count("SELECT COUNT(*) FROM course"),
        "lessons": count("SELECT COUNT(*) FROM lesson"),
        "transcripts": count("SELECT COUNT(*) FROM transcript"),
        "transcripts_by_status": dict(
            conn.execute("SELECT status, COUNT(*) FROM transcript GROUP BY status ORDER BY status").fetchall()
        ),
        "chunks": count("SELECT COUNT(*) FROM chunk"),
        "words": count("SELECT COALESCE(SUM(word_count), 0) FROM chunk"),
        "vocabulary": count("SELECT COUNT(*) FROM vocabulary"),
        "concepts": count("SELECT COUNT(*) FROM concept"),
        "flashcards": count("SELECT COUNT(*) FROM flashcard"),
    }
