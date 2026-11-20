"""Keyword search: turn text into searchable words (tokens), then rank with BM25."""

from rank_bm25 import BM25Okapi

# Very common words that carry little meaning on their own.
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do", "for",
    "from", "has", "have", "how", "i", "if", "in", "is", "it", "its", "me", "my",
    "of", "on", "or", "so", "that", "the", "then", "this", "to", "was", "what",
    "when", "with", "you", "your",
}


def tokenize(text: str) -> list[str]:
    """Turn text into a list of lowercase words, ready for keyword search.

    1. Lowercase everything ("Printer" and "printer" are the same word).
    2. Treat any character that isn't a letter or a digit as a space,
       so "Wi-Fi!" becomes "wi fi ".
    3. Split into words.
    4. Drop the stop words.

    Example: "My Wi-Fi keeps dropping!" -> ["wi", "fi", "keeps", "dropping"]
    """
    lowered = text.lower()
    cleaned = ""
    for ch in lowered:
        if ch.isalnum():
            cleaned += ch      # keep this character
        else:
            cleaned += " "      # anything else → a space
    words = cleaned.split()
    return [w for w in words if w not in STOP_WORDS]   # the list at the top of the file


class BM25Index:
    """A BM25 keyword index over the articles, using our tokenizer.

    BM25 itself (word rarity, diminishing returns, length fairness) comes from
    the standard rank-bm25 library with its default settings, so the
    keyword baseline isn't weakened by home-made maths.
    """

    def __init__(self, articles):
        self.ids = [a["id"] for a in articles]
        self.bm25 = BM25Okapi([tokenize(f"{a['title']} {a['body']}") for a in articles])

    def top_k(self, question: str, k: int = 5) -> list[str]:
        """The ids of the k best-matching articles for a question, best first."""
        scores = self.bm25.get_scores(tokenize(question))
        ranked = sorted(range(len(self.ids)), key=lambda i: scores[i], reverse=True)
        return [self.ids[i] for i in ranked[:k]]
