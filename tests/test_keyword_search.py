"""Unit tests for the tokenizer. Written before the code."""

from scoreboard.keyword_search import STOP_WORDS, tokenize


def test_lowercases_everything():
    assert tokenize("Printer OFFLINE") == ["printer", "offline"]


def test_punctuation_splits_words():
    assert tokenize("Wi-Fi keeps dropping!") == ["wi", "fi", "keeps", "dropping"]


def test_numbers_are_kept():
    assert tokenize("Battery says 60 percent") == ["battery", "says", "60", "percent"]


def test_extra_spaces_are_ignored():
    assert tokenize("  toner    warning  ") == ["toner", "warning"]


def test_stop_words_are_dropped():
    assert tokenize("My password is not accepted") == ["password", "not", "accepted"]


def test_full_example_from_the_docstring():
    assert tokenize("My Wi-Fi keeps dropping!") == ["wi", "fi", "keeps", "dropping"]


def test_empty_text_gives_no_words():
    assert tokenize("") == []


def test_only_stop_words_gives_no_words():
    assert tokenize("The and is to my") == []


def test_stop_word_list_is_lowercase():
    assert all(word == word.lower() for word in STOP_WORDS)
