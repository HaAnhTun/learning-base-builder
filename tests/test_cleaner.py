from engine.cleaner import clean_cues, remove_rolling
from engine.vtt_parser import Cue


def clean(cues, pause=1.5, max_sentences=6):
    return clean_cues(cues, pause_seconds=pause, max_sentences=max_sentences)


# --- rolling captions (SPEC 5.1) ---

def test_intentional_repeat_in_consecutive_cues_is_kept():
    cues = [Cue(0.0, 1.0, ["No."]), Cue(1.0, 2.0, ["No."])]
    assert [c.text for c in remove_rolling(cues)] == ["No.", "No."]


def test_overlapping_identical_cue_is_dropped_and_time_extended():
    out = remove_rolling([Cue(0.0, 2.0, ["Hello there."]), Cue(1.5, 3.0, ["Hello there."])])
    assert [(c.start, c.end, c.text) for c in out] == [(0.0, 3.0, "Hello there.")]


def test_flash_cue_is_dropped():
    out = remove_rolling([Cue(0.0, 2.0, ["Hello there."]), Cue(2.0, 2.01, ["Hello there."])])
    assert len(out) == 1


def test_youtube_style_two_line_rolling():
    cues = [
        Cue(0.0, 2.0, ["so today we"]),
        Cue(2.0, 4.0, ["so today we", "will learn about"]),
        Cue(4.0, 6.0, ["will learn about", "Python basics"]),
    ]
    assert [c.text for c in remove_rolling(cues)] == ["so today we", "will learn about", "Python basics"]


def test_repeated_lines_not_removed_when_not_adjacent_in_time():
    cues = [Cue(0.0, 2.0, ["so today we"]), Cue(5.0, 7.0, ["so today we", "again"])]
    assert [c.text for c in remove_rolling(cues)] == ["so today we", "so today we again"]


# --- sentences and timestamps ---

def test_sentences_across_cues_take_first_start_and_last_end():
    cues = [Cue(0.0, 2.0, ["Before we start, I want to cover"]),
            Cue(2.0, 4.0, ["what the exam is. It is"]),
            Cue(4.0, 6.0, ["sixty questions."])]
    sentences, _ = clean(cues)
    assert [(s["id"], s["start"], s["end"], s["text"]) for s in sentences] == [
        (0, 0.0, 4.0, "Before we start, I want to cover what the exam is."),
        (1, 2.0, 6.0, "It is sixty questions."),
    ]


def test_order_and_intentional_repeats_preserved():
    cues = [Cue(0.0, 1.0, ["Yes."]), Cue(1.0, 2.0, ["Yes."]), Cue(2.0, 3.0, ["Exactly."])]
    sentences, _ = clean(cues)
    assert [s["text"] for s in sentences] == ["Yes.", "Yes.", "Exactly."]


def test_unpunctuated_captions_use_one_sentence_per_cue():
    cues = [Cue(float(i), float(i + 1), ["so today we are going to look at some things"]) for i in range(10)]
    sentences, _ = clean(cues)
    assert len(sentences) == 10
    assert sentences[3]["start"] == 3.0


# --- paragraphs ---

def test_paragraphs_break_on_pause_and_max_sentences():
    cues = [Cue(0.0, 1.0, ["A."]), Cue(1.0, 2.0, ["B."]), Cue(5.0, 6.0, ["C."]),  # 3s pause before C
            Cue(6.0, 7.0, ["D."]), Cue(7.0, 8.0, ["E."]), Cue(8.0, 9.0, ["F."])]
    _, paragraphs = clean(cues, pause=1.5, max_sentences=3)
    assert paragraphs == [[0, 1], [2, 4], [5, 5]]


def test_plain_text_paragraphs_follow_blank_lines():
    cues = [Cue(None, None, ["First line."], True), Cue(None, None, ["Same para."]),
            Cue(None, None, ["Second para."], True)]
    sentences, paragraphs = clean(cues)
    assert [s["start"] for s in sentences] == [None, None, None]
    assert paragraphs == [[0, 1], [2, 2]]


def test_empty():
    assert clean([]) == ([], [])


def test_cjk_sentences_split_without_spaces():
    sentences, _ = clean([Cue(0.0, 2.0, ["你好。我很好。谢谢！"])])
    assert [s["text"] for s in sentences] == ["你好。", "我很好。", "谢谢！"]
