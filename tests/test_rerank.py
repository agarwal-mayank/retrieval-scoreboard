"""Tests for the reranker's prompt and reply parsing (no Ollama needed)."""

from scoreboard.rerank import build_prompt, parse_order

ARTICLES = [
    {"title": "Printer offline", "body": "Restart it."},
    {"title": "Toner low", "body": "Replace the cartridge."},
    {"title": "Paper jam", "body": "Open the tray."},
]


def test_prompt_numbers_every_article_and_includes_the_question():
    prompt = build_prompt("my printer says toner", ARTICLES)
    assert "my printer says toner" in prompt
    assert "[1] Printer offline" in prompt and "[3] Paper jam" in prompt
    assert "all 3 numbers" in prompt


def test_a_clean_reply_is_parsed():
    assert parse_order("2, 1, 3", 3) == [1, 0, 2]


def test_extra_words_around_the_numbers_are_ignored():
    assert parse_order("Ranking: 3, 2, 1.", 3) == [2, 1, 0]


def test_missing_numbers_are_added_in_original_order():
    assert parse_order("3", 3) == [2, 0, 1]


def test_repeats_and_out_of_range_numbers_are_skipped():
    assert parse_order("2, 2, 9, 1", 3) == [1, 0, 2]


def test_no_usable_numbers_means_fall_back():
    assert parse_order("I'm not sure.", 3) is None
