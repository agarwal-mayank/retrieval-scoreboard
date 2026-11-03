"""Generate the synthetic IT help article library with Claude Haiku.

Run once, then commit the output so the dataset is versioned:

    uv run --env-file .env python scripts/generate_articles.py

Writes data/articles.jsonl (200 articles) and data/articles.meta.json
(the exact prompts, model, settings, token usage and date used).

Finished categories are checkpointed to runs/articles_checkpoint.jsonl, so an
interrupted run resumes. Delete that file to generate a fresh library.

To swap out a single bad article (keeps its id, logs the repair):

    uv run --env-file .env python scripts/generate_articles.py --replace KB0112 --reason "..."
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from pydantic import BaseModel

MODEL = "claude-haiku-5-5"
EFFORT = "low"  # short, simple writing; keeps cost down
MAX_TOKENS = 16000
PRICE_PER_MTOK = {"input": 0.10, "output": 0.50}  # USD, Haiku 5.5 list price

CATEGORIES = [
    "Passwords & sign-in",
    "Multi-factor authentication",
    "VPN & remote access",
    "Email & calendar",
    "Printers & scanning",
    "Laptops & hardware",
    "Wi-Fi & network",
    "Software install & access",
    "Chat & video meetings",
    "Security & phishing",
]
BATCHES_PER_CATEGORY = 2
ARTICLES_PER_BATCH = 10
MIN_WORDS, MAX_WORDS = 100, 300
ATTEMPTS = 5

# Real product and company names we keep out of the synthetic data.
BANNED_WORDS = [
    "Microsoft", "Outlook", "Teams", "Office 365", "Windows", "macOS", "Apple",
    "iPhone", "Android", "Google", "Gmail", "Zoom", "Slack", "Cisco", "Okta",
    "Duo", "Dell", "Lenovo", "HP ", "Citrix", "ServiceNow",
]

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CHECKPOINT = ROOT / "runs" / "articles_checkpoint.jsonl"  # git-ignored

SYSTEM_PROMPT = """You write internal IT help desk knowledge articles for a fictional company.
Rules:
- Synthetic content only. Never use real company, product or brand names. Use generic names such as "the company VPN app", "your email app", "the chat app", "your laptop", "the authenticator app".
- Each article body is 120 to 250 words, plain text, in this order: "Symptoms:", "Cause:", "Steps:" (numbered), "Still stuck?".
- Write for non-technical staff. Be specific and practical.
- Every article in a batch covers a different problem."""

USER_PROMPT = """Write {n} help articles for the category "{category}".
{avoid}
Return each article with a short, specific title and the body."""

AVOID_FIRST = "Cover the most common problems in this category."
AVOID_LATER = """These titles already exist in this category:
{titles}
Do not repeat them. Cover different problems, but make 3 of your articles close neighbours of existing ones (same area, different problem, e.g. "won't connect" vs "keeps disconnecting")."""


class Article(BaseModel):
    title: str
    body: str


class Batch(BaseModel):
    articles: list[Article]


def problem(article: Article, existing_titles: list[str]) -> str | None:
    """Return why an article fails the quality gate, or None if it passes."""
    words = len(article.body.split())
    if not MIN_WORDS <= words <= MAX_WORDS:
        return f"'{article.title}' has {words} words"
    for w in BANNED_WORDS:
        if re.search(rf"\b{re.escape(w.strip())}\b", article.title + " " + article.body):
            return f"'{article.title}' mentions '{w.strip()}'"
    if article.title.lower() in (t.lower() for t in existing_titles):
        return f"'{article.title}' is a duplicate title"
    return None


def generate_batch(client, category, existing_titles, usage, other_titles=(), count=ARTICLES_PER_BATCH):
    """Return `count` good articles. Keeps the good ones from each attempt and
    only asks again for the shortfall. other_titles: titles from other
    categories, checked only for duplicates."""
    kept = []
    for attempt in range(1, ATTEMPTS + 1):
        needed = count - len(kept)
        titles_so_far = existing_titles + [a.title for a in kept]
        avoid = (
            AVOID_LATER.format(titles="\n".join(f"- {t}" for t in titles_so_far))
            if titles_so_far
            else AVOID_FIRST
        )
        prompt = USER_PROMPT.format(n=needed, category=category, avoid=avoid)
        print(f"  attempt {attempt}: asking Haiku for {needed} articles...", flush=True)
        started = time.monotonic()
        try:
            response = client.messages.parse(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                output_config={"effort": EFFORT},
                messages=[{"role": "user", "content": prompt}],
                output_format=Batch,
            )
        except (
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
            anthropic.RateLimitError,
            anthropic.InternalServerError,
        ) as e:
            wait = 5 * attempt
            print(f"  attempt {attempt}: {type(e).__name__}, retrying in {wait}s", flush=True)
            time.sleep(wait)
            continue
        print(f"  attempt {attempt}: answered in {time.monotonic() - started:.0f}s", flush=True)
        usage["input_tokens"] += response.usage.input_tokens
        usage["output_tokens"] += response.usage.output_tokens
        usage["requests"] += 1
        if response.stop_reason != "end_turn" or response.parsed_output is None:
            print(f"  attempt {attempt}: stopped with {response.stop_reason}, retrying")
            continue
        rejected = []
        for a in response.parsed_output.articles:
            if len(kept) == count:
                break
            reason = problem(a, [*other_titles, *existing_titles, *(k.title for k in kept)])
            if reason:
                rejected.append(reason)
            else:
                kept.append(a)
        if len(kept) == count:
            return kept
        detail = f" ({'; '.join(rejected[:3])})" if rejected else ""
        print(f"  attempt {attempt}: have {len(kept)}/{count}{detail}, asking for the rest")
    sys.exit(f"Giving up on '{category}' after {ATTEMPTS} attempts.")


def main():
    # Give up on a stuck request after 90 seconds (the SDK default is 10 minutes).
    # Retries are handled visibly in generate_batch, so the SDK's silent ones are off.
    client = anthropic.Anthropic(max_retries=0, timeout=90.0)
    usage = {"requests": 0, "input_tokens": 0, "output_tokens": 0}
    articles = []

    # Checkpoint: each finished category is saved, so an interrupted run
    # picks up where it stopped instead of starting over.
    CHECKPOINT.parent.mkdir(exist_ok=True)
    done = {}
    if CHECKPOINT.exists():
        for line in CHECKPOINT.read_text(encoding="utf-8").splitlines():
            saved = json.loads(line)
            done[saved["category"]] = saved
            for k in usage:
                usage[k] += saved["usage"][k]

    for category in CATEGORIES:
        if category in done:
            print(f"{category}: already done (from checkpoint)")
            articles.extend(done[category]["articles"])
            continue
        before = dict(usage)
        titles, batch_articles = [], []
        for b in range(BATCHES_PER_CATEGORY):
            print(f"{category}: batch {b + 1}/{BATCHES_PER_CATEGORY}")
            # Titles must be unique across the whole library, including
            # categories already saved in the checkpoint.
            other_titles = [a["title"] for a in articles] + [
                a["title"] for d in done.values() for a in d["articles"]
            ]
            for a in generate_batch(client, category, titles, usage, other_titles):
                titles.append(a.title)
                batch_articles.append({"title": a.title, "category": category, "body": a.body})
        articles.extend(batch_articles)
        spent = {k: usage[k] - before[k] for k in usage}
        with open(CHECKPOINT, "a", encoding="utf-8", newline="\n") as f:
            record = {"category": category, "articles": batch_articles, "usage": spent}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    for i, a in enumerate(articles, start=1):
        a["id"] = f"KB{i:04d}"

    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / "articles.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for a in articles:
            row = {"id": a["id"], "title": a["title"], "category": a["category"], "body": a["body"]}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    cost = (
        usage["input_tokens"] * PRICE_PER_MTOK["input"]
        + usage["output_tokens"] * PRICE_PER_MTOK["output"]
    ) / 1_000_000
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": MODEL,
        "effort": EFFORT,
        "temperature": "model default (not settable on this model)",
        "max_tokens": MAX_TOKENS,
        "categories": CATEGORIES,
        "batches_per_category": BATCHES_PER_CATEGORY,
        "articles_per_batch": ARTICLES_PER_BATCH,
        "word_range": [MIN_WORDS, MAX_WORDS],
        "banned_words": [w.strip() for w in BANNED_WORDS],
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt_template": USER_PROMPT,
        "avoid_first": AVOID_FIRST,
        "avoid_later_template": AVOID_LATER,
        "usage": usage,
        "estimated_cost_usd": round(cost, 4),
        "price_per_mtok_usd": PRICE_PER_MTOK,
    }
    (DATA_DIR / "articles.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nWrote {len(articles)} articles. Tokens: {usage}. Estimated cost: ${cost:.4f}")


def replace(article_id, reason):
    """Swap one article for a fresh one in the same category, keeping its id.
    The repair is logged in articles.meta.json so the dataset history stays honest."""
    path = DATA_DIR / "articles.jsonl"
    articles = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    target = next((a for a in articles if a["id"] == article_id), None)
    if target is None:
        sys.exit(f"No article with id {article_id}.")
    category = target["category"]
    same = [a["title"] for a in articles if a["category"] == category and a is not target]
    others = [a["title"] for a in articles if a["category"] != category]

    client = anthropic.Anthropic(max_retries=0, timeout=90.0)
    usage = {"requests": 0, "input_tokens": 0, "output_tokens": 0}
    print(f"Replacing {article_id} ({category}: '{target['title']}')")
    new = generate_batch(client, category, same, usage, others, count=1)[0]

    old_title = target["title"]
    target["title"], target["body"] = new.title, new.body
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for a in articles:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    cost = (
        usage["input_tokens"] * PRICE_PER_MTOK["input"]
        + usage["output_tokens"] * PRICE_PER_MTOK["output"]
    ) / 1_000_000
    meta_path = DATA_DIR / "articles.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.setdefault("repairs", []).append({
        "id": article_id,
        "reason": reason,
        "old_title": old_title,
        "new_title": new.title,
        "repaired_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "usage": usage,
        "estimated_cost_usd": round(cost, 4),
    })
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n{article_id}: '{old_title}' -> '{new.title}'. Tokens: {usage}. Estimated cost: ${cost:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--replace", metavar="ID", help="regenerate one article, e.g. KB0112")
    parser.add_argument("--reason", default="manual repair", help="why, recorded in the meta file")
    args = parser.parse_args()
    if args.replace:
        replace(args.replace, args.reason)
    else:
        main()
