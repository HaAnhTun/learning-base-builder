"""CLI: python -m engine <login|fetch|import|stats>."""
import argparse
import sys
from pathlib import Path

from engine import database
from engine.config import load_config, path_of


def _print_import(result) -> None:
    print(f"[{result.course_slug}] mới: {result.imported}, cập nhật: {result.updated}, "
          f"không đổi: {result.unchanged}")
    if result.empty:
        print(f"  Cảnh báo — file không có nội dung: {', '.join(result.empty)}")
    if result.ignored:
        print(f"  Bỏ qua {len(result.ignored)} file (ngoài _manifest.json hoặc trùng bài + ngôn ngữ): {', '.join(result.ignored[:5])}"
              + (" ..." if len(result.ignored) > 5 else ""))


def _import(cfg, folder: Path) -> None:
    from engine.importer import import_folder

    conn = database.connect(path_of(cfg, "database"))
    try:
        result = import_folder(conn, folder, default_lang=cfg["default_lang"],
                               max_words=cfg["chunking"]["max_words"])
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
    by_status = ", ".join(f"{k}: {v}" for k, v in s["transcripts_by_status"].items()) or "-"
    print(f"Khóa học:    {s['courses']}")
    print(f"Bài học:     {s['lessons']}")
    print(f"Transcript:  {s['transcripts']} ({by_status})")
    print(f"Chunk:       {s['chunks']} ({s['words']} từ)")
    print(f"Từ vựng:     {s['vocabulary']}")
    print(f"Khái niệm:   {s['concepts']}")
    print(f"Flashcard:   {s['flashcards']}")


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
    sub.add_parser("stats", help="Thống kê dữ liệu")
    args = parser.parse_args(argv)

    from engine.udemy_client import UdemyError

    cfg = load_config()
    handlers = {"login": cmd_login, "fetch": cmd_fetch, "import": cmd_import, "stats": cmd_stats}
    try:
        handlers[args.command](cfg, args)
    except (UdemyError, FileNotFoundError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
