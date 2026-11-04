from engine.parser import parse_text
from engine.vtt_parser import Cue, parse_timestamp, parse_vtt

SAMPLE = """\ufeffWEBVTT
Kind: captions

NOTE this is a comment
spanning two lines

STYLE
::cue { color: red }

1
00:00:00.000 --> 00:00:02.500 align:start
<v Instructor>Welcome to the <b>course</b>.</v>

2
00:00:02.500 --> 00:00:04.000
Welcome to the course.

00:01:04.000 --> 00:01:06.000
Let&#39;s get
started &amp; have fun!

1:00:06,000 --> 1:00:08.000
<00:00:06.100><c>Final</c> words.
"""


def test_parses_cues_with_timing_and_strips_markup():
    assert parse_vtt(SAMPLE) == [
        Cue(0.0, 2.5, ["Welcome to the course."]),
        Cue(2.5, 4.0, ["Welcome to the course."]),  # the parser does not de-duplicate
        Cue(64.0, 66.0, ["Let's get", "started & have fun!"]),
        Cue(3606.0, 3608.0, ["Final words."]),
    ]


def test_handles_crlf():
    assert parse_vtt(SAMPLE.replace("\n", "\r\n")) == parse_vtt(SAMPLE)


def test_timestamps():
    assert parse_timestamp("00:01.500") == 1.5
    assert parse_timestamp("01:02:03.250") == 3723.25
    assert parse_timestamp("00:00:04,000") == 4.0


def test_unicode_preserved():
    vtt = "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nXin chào các bạn — 日本語\n"
    assert parse_vtt(vtt)[0].lines == ["Xin chào các bạn — 日本語"]


def test_empty_file():
    assert parse_vtt("WEBVTT\n") == []


def test_plain_text_keeps_paragraph_breaks():
    cues = parse_text("Line one.\nLine two.\n\nNew para.\n", ".txt")
    assert [(c.lines[0], c.para_break, c.start) for c in cues] == [
        ("Line one.", True, None), ("Line two.", False, None), ("New para.", True, None),
    ]


def test_markdown_strips_markers():
    cues = parse_text("# Course\n\n## 1. Intro\n\n> note\n\n---\n\nHello world.\n", ".md")
    assert [c.text for c in cues] == ["Course", "1. Intro", "note", "Hello world."]
