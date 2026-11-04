from engine.parser import parse_text
from engine.segmenter import segment


def words(chunk):
    return len(chunk.split())


def test_short_lesson_is_single_chunk():
    units = ["Hello there.", "This is a short lesson."]
    assert segment(units, max_words=100) == ["Hello there. This is a short lesson."]


def test_empty_input():
    assert segment([], max_words=100) == []


def test_long_lesson_split_evenly_at_sentence_boundaries():
    sentence = "This sentence has exactly seven words here."
    units = [sentence] * 30  # 210 từ
    chunks = segment(units, max_words=100)
    assert len(chunks) == 3
    assert all(c.endswith(".") for c in chunks)
    assert all(words(c) <= 100 for c in chunks)
    assert sum(words(c) for c in chunks) == 210


def test_sentences_cross_cue_boundaries():
    # Câu bị cắt giữa hai cue vẫn được giữ nguyên trong một chunk.
    units = ["The first sentence", "continues here. Second", "sentence ends here."] * 20
    chunks = segment(units, max_words=40)
    for c in chunks:
        assert c.endswith(".")
        assert not c.startswith(("continues", "sentence ends"))


def test_unpunctuated_captions_split_at_cues():
    units = ["so today we are going to look at"] * 30  # 8 từ/cue, không dấu câu
    chunks = segment(units, max_words=100)
    assert len(chunks) == 3
    assert all(c.endswith("look at") for c in chunks)


def test_single_huge_piece_is_split_by_words():
    chunks = segment(["word " * 250], max_words=100)
    assert [words(c) for c in chunks] == [100, 100, 50]


def test_markdown_parsing():
    md = "# Course\n\n## 1. Intro\n\n> note\n\n---\n\nHello world.\n"
    assert parse_text(md, ".md") == ["Course", "1. Intro", "note", "Hello world."]


def test_no_chunk_exceeds_max_words():
    # Regression: mảnh vượt mốc target từng bị dồn vào chunk hiện tại (3500 từ với max 2500).
    units = ["a " * 1000, "b " * 2500]
    assert [words(c) for c in segment(units, max_words=2500)] == [1000, 2500]
    units = ["Thirty words in this sentence " * 6 + "end."] * 166 + ["Nine more words in the final sentence here ok."]
    assert all(words(c) <= 2500 for c in segment(units, max_words=2500))
