"""CLI: python -m engine <command> — see `python -m engine --help`."""
import argparse
import sys
from pathlib import Path

from engine import database
from engine.config import load_config, path_of


def _print_import(result) -> None:
    print(f"[{result.course_slug}] mới: {result.imported}, cập nhật: {result.updated}, "
          f"không đổi: {result.unchanged}, làm sạch: {result.cleaned}")
    for warning in result.warnings:
        print(f"  Cảnh báo: {warning}")
    if result.empty:
        print(f"  Cảnh báo — file không có nội dung: {', '.join(result.empty)}")
    if result.ignored:
        print(f"  Bỏ qua {len(result.ignored)} file (ngoài _manifest.json, trùng bài + ngôn ngữ, "
              f"hoặc file tự đặt trong khóa đã fetch): {', '.join(result.ignored[:5])}"
              + (" ..." if len(result.ignored) > 5 else ""))


def _import(cfg, folder: Path) -> None:
    from engine.importer import import_folder

    conn = database.connect(path_of(cfg, "database"))
    try:
        result = import_folder(conn, folder, cfg)
    finally:
        conn.close()
    _print_import(result)


def cmd_import(cfg, args) -> None:
    _import(cfg, Path(args.folder))


def cmd_stats(cfg, args) -> None:
    conn = database.connect(path_of(cfg, "database"))
    try:
        s = database.stats(conn)
    finally:
        conn.close()
    print(f"Khóa học:        {s['courses']}")
    print(f"Bài học:         {s['lessons']}")
    print(f"Transcript:      {s['transcripts']} (đã làm sạch: {s['cleaned']}, {s['sentences']} câu, {s['words']} từ)")


def cmd_clean(cfg, args) -> None:
    from engine.cleaner import clean_course

    conn = database.connect(path_of(cfg, "database"))
    try:
        course = database.course_by_slug(conn, args.course)
        r = clean_course(conn, course["id"], cfg, force=args.force)
    finally:
        conn.close()
    print(f"[{args.course}] làm sạch: {r['cleaned']}, cập nhật metadata: {r['refreshed']}, không đổi: {r['unchanged']}")
    if r["empty"]:
        print(f"  Cảnh báo — transcript rỗng: {', '.join(r['empty'])}")


def cmd_export(cfg, args) -> None:
    from engine.export_notebooklm import course_languages, export_course
    from engine.fetcher import parse_langs

    conn = database.connect(path_of(cfg, "database"))
    try:
        langs = parse_langs(args.lang or cfg["default_lang"])
        if langs == ["all"]:
            langs = course_languages(conn, database.course_by_slug(conn, args.course)["id"])
        for lang in langs:
            r = export_course(conn, args.course, cfg, by=args.by, lang=lang)
            print(f"Đã xuất {r.lessons} bài thành {len(r.files)} file + index.md vào {r.folder}")
            for warning in r.warnings:
                print(f"  Cảnh báo: {warning}")
    finally:
        conn.close()


def cmd_login(cfg, args) -> None:
    from engine.udemy_auth import login

    path = login(cfg["udemy"]["base_url"], path_of(cfg, "auth_dir") / "browser-profile", cfg["root"])
    print(f"Đã lưu access_token vào {path.name}.")


def cmd_fetch(cfg, args) -> None:
    from engine.fetcher import fetch_course, parse_langs
    from engine.udemy_client import UdemyClient

    client = UdemyClient(cfg["udemy"]["base_url"], cfg["udemy"].get("access_token"))
    if not args.course:
        for c in client.list_courses():
            print(f"{c['id']:>10}  {c.get('published_title', ''):<50}  {c.get('title', '')}")
        print("\nChạy: python -m engine fetch <id|slug|url> [--lang en]")
        return
    course = client.resolve_course(args.course)
    langs = parse_langs(args.lang or cfg["default_lang"])
    print(f"Đang tải: {course.get('title')} (id {course['id']}, ngôn ngữ: {','.join(langs)})", flush=True)
    folders = fetch_course(client, course, langs, path_of(cfg, "input_dir"),
                           max_concurrency=cfg["udemy"].get("max_concurrency", 4),
                           progress=lambda message: print(message, flush=True))
    if not folders:
        print(f"Khóa học không có caption cho ngôn ngữ: {','.join(langs)}")
        return
    for folder in folders:
        print(f"Đã lưu vào {folder}")
        _import(cfg, folder)


def _with_db(cfg, fn):
    conn = database.connect(path_of(cfg, "database"))
    try:
        return fn(conn)
    finally:
        conn.close()


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="python -m engine")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("login", help="Đăng nhập Udemy trong trình duyệt và lưu token")
    p = sub.add_parser("fetch", help="Tải transcript một khóa Udemy rồi import")
    p.add_argument("course", nargs="?", help="course id, slug hoặc URL; bỏ trống để liệt kê khóa đã đăng ký")
    p.add_argument("--lang", help="en (mặc định), en,vi, en_GB, hoặc all")
    p = sub.add_parser("import", help="Nhập thư mục .vtt/.txt/.md vào SQLite")
    p.add_argument("folder")
    p = sub.add_parser("clean", help="Làm sạch lại transcript của một khóa (Clean Dataset)")
    p.add_argument("course", help="slug khóa học")
    p.add_argument("--force", action="store_true", help="làm sạch lại toàn bộ dù không đổi")
    p = sub.add_parser("export", help="Xuất dữ liệu")
    exp = p.add_subparsers(dest="target", required=True)
    p = exp.add_parser("notebooklm", help="Markdown cho NotebookLM")
    p.add_argument("course", help="slug khóa học")
    p.add_argument("--by", choices=["chapter", "course", "lesson"], help="đơn vị file (mặc định theo config)")
    p.add_argument("--lang", help="en (mặc định default_lang), en_US, en,vi, hoặc all")
    sub.add_parser("stats", help="Thống kê dữ liệu")
    args = parser.parse_args(argv)

    from engine.udemy_client import UdemyError

    cfg = load_config()
    handlers = {"login": cmd_login, "fetch": cmd_fetch, "import": cmd_import, "stats": cmd_stats,
                "clean": cmd_clean, "export": cmd_export}
    try:
        handlers[args.command](cfg, args)
    except (UdemyError, FileNotFoundError, LookupError, ValueError, database.SchemaError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
