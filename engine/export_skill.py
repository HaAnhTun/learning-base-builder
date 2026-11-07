"""Package a course as a Claude skill: lecture transcripts, quiz bank with answers, practice exams, attachments.

Output: <export_dir>/skills/<slug>/SKILL.md + references/{course,quizzes,materials}/. No AI; deterministic.
Copy the folder into .claude/skills/ (project) or ~/.claude/skills/ (every project) to use it.
"""
import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from engine import database
from engine.export_notebooklm import Chapter, build_files, load_chapters, normalize_lang, safe_filename
from engine.fetcher import slugify
from engine.materials import MATERIAL_INDEX, QUIZ_INDEX

BLOCK_END = re.compile(r"</(?:p|div|li|h[1-6]|ul|ol)>|<br\s*/?>", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")


@dataclass
class SkillResult:
    folder: Path
    chapters: int
    quizzes: int
    questions: int
    attachments: int
    words: int


def html_to_text(value: str) -> str:
    """The HTML Udemy uses in quiz text (paragraphs, lists, code) as plain Markdown-ish text."""
    text = re.sub(r"</?pre[^>]*>", "\n```\n", value or "", flags=re.IGNORECASE)
    text = re.sub(r"</?code[^>]*>", "`", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = html.unescape(TAG.sub("", BLOCK_END.sub("\n", text))).replace("\xa0", " ")
    out, in_code, prev_prose = [], False, False
    for line in text.splitlines():
        if line.strip() == "```":
            in_code = not in_code
            out.append("```")
            prev_prose = False
        elif in_code:
            out.append(line.rstrip())  # keep code indentation
        elif line.strip():
            if prev_prose:
                out.append("")  # blank line between paragraphs
            out.append(re.sub(r"[ \t]+", " ", line).strip())
            prev_prose = True
    return "\n".join(out).strip()


def _one_line(value: str) -> str:
    return " ".join(html_to_text(value).split())


def _letters(codes: list[str]) -> list[int]:
    return [ord(code.lower()) - ord("a") for code in codes]


def render_quiz(quiz: dict, course_title: str) -> str:
    """One quiz as Markdown with its answer key (the skill tells Claude not to reveal it before the learner answers)."""
    questions = quiz["assessments"]
    out = [f"# {quiz['title']}", "",
           f"> Course: {course_title} · {quiz.get('chapter_title') or 'Quiz'} · {len(questions)} questions"
           + (f" · pass mark {quiz['pass_percent']}%" if quiz.get("pass_percent") else "")
           + " · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies", ""]
    for n, item in enumerate(questions, 1):
        prompt = item["prompt"]
        section = f" [{item['section']}]" if item.get("section") else ""
        out += [f"## Question {n}{section}", "", html_to_text(prompt["question"]), ""]
        out += [f"{chr(65 + i)}. {_one_line(answer)}" for i, answer in enumerate(prompt["answers"])]
        correct = _letters(item.get("correct_response") or [])
        feedbacks = prompt.get("feedbacks") or []
        out += ["", "**Answer:** " + ", ".join(chr(65 + i) for i in correct)]
        notes = {i: _one_line(text) for i, text in enumerate(feedbacks) if text and _one_line(text)}
        out += [f"**Explanation:** {text}" for i, text in notes.items() if i in correct]
        out += [f"**Why not {chr(65 + i)}:** {text}" for i, text in notes.items() if i not in correct]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def load_quizzes(course_dir: Path) -> list[dict]:
    """Quiz files saved by `fetch`, in curriculum order; [] when the course has none."""
    index = course_dir / "quizzes" / QUIZ_INDEX
    if not index.exists():
        return []
    entries = json.loads(index.read_text(encoding="utf-8"))["quizzes"]
    return [json.loads((course_dir / "quizzes" / e["filename"]).read_text(encoding="utf-8")) for e in entries]


def render_materials(items: list[dict]) -> str:
    out = ["# Attachments and extras", "",
           "Files are in this folder. External links were recorded only — they were not opened or fetched.", ""]
    for item in items:
        where = f"lesson {item['lecture_position']} “{item['lecture_title']}” ({item['chapter_title']})"
        if item["kind"] == "file":
            out.append(f"- File `{item['filename']}` — {item['title']}; attached to {where}.")
        elif item["kind"] == "link":
            out.append(f"- Link {item['url']} — attached to {where}.")
        else:
            out.append(f"- Lesson description of {where}: {_one_line(item['html'])}")
    return "\n".join(out) + "\n"


def _skill_name(slug: str) -> str:
    return (slug[:64].strip("-")) or "course"


def render_skill_md(course: dict, chapter_files: list[tuple[Chapter, list[str]]], quizzes: list[dict],
                    exam_quizzes: list[dict], quiz_names: dict[int, str], has_materials: bool, lang: str) -> str:
    title = course["title"]
    all_quizzes = quizzes + exam_quizzes
    n_questions = sum(len(q["assessments"]) for q in all_quizzes)
    lessons = sum(len(ch.lessons) for ch, _ in chapter_files)
    parts = [f"{lessons} lessons in {len(chapter_files)} chapters"]
    if all_quizzes:
        parts.append(f"{n_questions} quiz questions with answers and explanations in {len(all_quizzes)} quizzes/exams")
    uses = ("answer questions about the course, quiz the learner, run a mock exam, or review weak topics" if all_quizzes
            else "answer questions about the course and look up what a lesson says")
    description = f"Study material of the Udemy course “{title}”: full lecture transcripts ({', '.join(parts)}). Use it to {uses}."
    header = "| Chapter | Transcript | Quiz | Questions |" if all_quizzes else "| Chapter | Transcript |"
    out = ["---", f"name: {_skill_name(course['slug'])}", f"description: {json.dumps(description, ensure_ascii=False)}", "---", "",
           f"# {title}", "",
           f"Material of an Udemy course, language `{lang}`: {'; '.join(parts)}. Every file below is plain Markdown under `references/`.", "",
           "## Files", "", header, "|---" * (header.count("|") - 1) + "|"]
    by_chapter: dict[int, list[dict]] = {}
    for quiz in quizzes:
        by_chapter.setdefault(quiz.get("chapter_index"), []).append(quiz)
    for chapter, names in chapter_files:
        own = by_chapter.get(chapter.index, [])
        row = f"| {chapter.index}. {chapter.title} | " + ", ".join(f"`references/course/{n}`" for n in names) + " |"
        if all_quizzes:
            row += (" " + (", ".join(f"`references/quizzes/{quiz_names[q['quiz_id']]}`" for q in own) or "—")
                    + f" | {sum(len(q['assessments']) for q in own) or '—'} |")
        out.append(row)
    if exam_quizzes:
        out += ["", "Practice exams (no transcript):", ""]
        out += [f"- `references/quizzes/{quiz_names[q['quiz_id']]}` — {len(q['assessments'])} questions"
                + (f", pass mark {q['pass_percent']}%" if q.get("pass_percent") else "") for q in exam_quizzes]
    if has_materials:
        out += ["", "Attachments and links: `references/materials/index.md`."]
    out += ["", "## What to do", "",
            "- **Answer a question about the course:** find the chapter in the table, read that transcript file (only the file(s) "
            "you need — never load every chapter), answer from it, and name the chapter and lesson number. Say so when the "
            "transcript does not cover the question."]
    if all_quizzes:
        out += ["- **Quiz me:** pick the quiz of the requested chapter (or random questions across quizzes). Ask ONE question at a time with "
                "its choices A–D, wait for the learner's answer, then say correct or wrong and give the **Explanation** from the file "
                "plus the chapter to re-read. Keep a running score.",
                "- **Mock exam:** run a practice exam file from the first question to the last, with no feedback until the end. Then give the "
                "total score against the pass mark and a score per domain tag (`[D1]`, `[D2]`, … on each question).",
                "- **Review weak spots:** list the questions answered wrong, group them by chapter, and point to the transcript sections to re-read."]
    out += ["", "## Rules", ""]
    if all_quizzes:
        out.append("- Quiz files contain the answer key. Show the question and choices only; reveal **Answer** and **Explanation** "
                   "after the learner replies.")
    out += ["- Answer in the language the learner writes in; keep technical terms in English.",
            "- Transcripts are automatic captions and keep their recognition errors (for example “clod code” for Claude Code); "
            "read through them rather than correcting the learner."]
    return "\n".join(out) + "\n"


def export_skill(conn, course_slug: str, cfg: dict, *, lang: str | None = None) -> SkillResult:
    root: Path = cfg["root"]
    lang = normalize_lang(lang or cfg["default_lang"])
    course = database.course_by_slug(conn, course_slug)
    chapters = load_chapters(conn, course, lang, root)
    if not chapters:
        raise LookupError(f"Khóa '{course_slug}' không có transcript đã làm sạch cho ngôn ngữ '{lang}'.")
    course_dir = root / cfg["paths"]["input_dir"] / course_slug
    quizzes = load_quizzes(course_dir)
    total = conn.execute("SELECT MAX(position) FROM lesson WHERE course_id = ?", (course["id"],)).fetchone()[0]
    files, _ = build_files(course["title"], chapters, "chapter", max(len(chapters), 1), cfg["notebooklm"]["max_words_per_file"], total)

    folder = root / cfg["paths"]["export_dir"] / "skills" / course_slug
    shutil.rmtree(folder / "references", ignore_errors=True)  # a re-export replaces what the previous one wrote
    (folder / "references" / "course").mkdir(parents=True)
    for name, (content, _) in files.items():
        (folder / "references" / "course" / name).write_text(content, encoding="utf-8")
    chapter_files = [(ch, [name for name, (_, chs) in files.items() if any(c.index == ch.index for c in chs)])
                     for ch in chapters]

    quiz_names = {q["quiz_id"]: safe_filename(f"{q['position']:02d} - {q['title']}") + ".md" for q in quizzes}
    if quizzes:
        (folder / "references" / "quizzes").mkdir()
        for quiz in quizzes:
            (folder / "references" / "quizzes" / quiz_names[quiz["quiz_id"]]).write_text(
                render_quiz(quiz, course["title"]), encoding="utf-8")
    known = {ch.index for ch in chapters}
    exams = [q for q in quizzes if q.get("chapter_index") not in known]

    items, attachments = [], 0
    index = course_dir / "materials" / MATERIAL_INDEX
    if index.exists():
        items = json.loads(index.read_text(encoding="utf-8"))["items"]
        (folder / "references" / "materials").mkdir()
        for item in items:
            if item["kind"] == "file":
                shutil.copyfile(course_dir / "materials" / item["filename"], folder / "references" / "materials" / item["filename"])
                attachments += 1
        (folder / "references" / "materials" / "index.md").write_text(render_materials(items), encoding="utf-8")

    (folder / "SKILL.md").write_text(
        render_skill_md(course, chapter_files, [q for q in quizzes if q not in exams], exams, quiz_names, bool(items), lang),
        encoding="utf-8")
    return SkillResult(folder, len(chapters), len(quizzes), sum(len(q["assessments"]) for q in quizzes), attachments,
                       sum(doc["word_count"] for ch in chapters for doc in ch.lessons))
