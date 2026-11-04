from engine.vtt_parser import parse_vtt

SAMPLE = """﻿WEBVTT
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

1:00:06.000 --> 1:00:08.000
<00:00:06.100><c>Final</c> words.
"""


def test_strips_header_notes_styles_ids_timings_and_tags():
    assert parse_vtt(SAMPLE) == [
        "Welcome to the course.",
        "Let's get started & have fun!",
        "Final words.",
    ]


def test_handles_crlf():
    assert parse_vtt(SAMPLE.replace("\n", "\r\n")) == parse_vtt(SAMPLE)


def test_rolling_captions_keep_only_new_text():
    vtt = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:01.000\nso today we\n\n"
        "00:00:01.000 --> 00:00:02.000\nso today we will learn\n\n"
        "00:00:02.000 --> 00:00:03.000\nPython basics\n"
    )
    assert parse_vtt(vtt) == ["so today we", "will learn", "Python basics"]


def test_unicode_preserved():
    vtt = "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nXin chào các bạn — 日本語\n"
    assert parse_vtt(vtt) == ["Xin chào các bạn — 日本語"]


def test_empty_file():
    assert parse_vtt("WEBVTT\n") == []
