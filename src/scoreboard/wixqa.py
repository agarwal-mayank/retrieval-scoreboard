"""Load WixQA (a public help-centre question set, MIT licence) into the scoreboard's shapes.

WixQA has one article library and two question files. Questions can name
1-3 correct articles, so the first becomes the answer and the rest go in
also_relevant, which the lenient marking already understands.
"""

import json

MAX_TITLE_CHARS = 120


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def first_line(text):
    """The first non-empty line of text, trimmed to MAX_TITLE_CHARS."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:MAX_TITLE_CHARS]
    return ""


def to_articles(rows):
    """Corpus rows (id, contents, article_type) -> {"id", "title", "category", "body"}."""
    return [
        {
            "id": r["id"],
            "title": first_line(r["contents"]),
            "category": r["article_type"],
            "body": r["contents"],
        }
        for r in rows
    ]


def to_questions(rows, prefix, kind):
    """Question rows -> {"id", "question", "answer_article_id", "type", "also_relevant"}.

    Ids count up in file order: E001, E002... (prefix "E"), S001... (prefix "S").
    """
    return [
        {
            "id": f"{prefix}{n:03d}",
            "question": r["question"],
            "answer_article_id": r["article_ids"][0],
            "type": kind,
            "also_relevant": r["article_ids"][1:],
        }
        for n, r in enumerate(rows, start=1)
    ]


def load_wixqa(folder="runs/wixqa"):
    """(articles, questions) from the three downloaded files in folder."""
    articles = to_articles(read_jsonl(f"{folder}/wix_kb_corpus.jsonl"))
    questions = to_questions(read_jsonl(f"{folder}/expertwritten.jsonl"), "E", "expert")
    questions += to_questions(read_jsonl(f"{folder}/simulated.jsonl"), "S", "simulated")
    return articles, questions
