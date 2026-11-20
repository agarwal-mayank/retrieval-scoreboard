"""Unit tests for the tokenizer (written before the code) and BM25 ranking."""

from scoreboard.keyword_search import STOP_WORDS, BM25Index, tokenize


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


# --- BM25 ranking -----------------------------------------------------------------

ARTICLES = [
    {"id": "KB0001", "title": "Low toner warning", "body": "Replace the toner cartridge in the printer."},
    {"id": "KB0002", "title": "Forgot my password", "body": "Reset your password from the sign-in page."},
    {"id": "KB0003", "title": "VPN keeps dropping", "body": "Reconnect the company VPN app on stable Wi-Fi."},
    {"id": "KB0004", "title": "Mailbox full", "body": "Delete old email and empty the deleted folder."},
]


def test_bm25_finds_the_article_with_the_rare_word():
    assert BM25Index(ARTICLES).top_k("toner", k=1) == ["KB0001"]


def test_bm25_uses_the_tokenizer_on_questions():
    assert BM25Index(ARTICLES).top_k("My VPN keeps DROPPING!", k=1) == ["KB0003"]


def test_bm25_returns_k_ids():
    assert len(BM25Index(ARTICLES).top_k("password", k=3)) == 3
