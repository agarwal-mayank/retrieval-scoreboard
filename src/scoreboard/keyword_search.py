"""Keyword search: turn text into searchable words (tokens)."""

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