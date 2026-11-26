"""Reranking: a second, more careful judge re-orders a search method's shortlist.

Here the judge is a local chat model (qwen2.5 in Ollama) asked to put the
numbered candidates in order ("listwise" reranking). If its reply can't be
read, the original order is kept and the fallback is counted.
"""

import json
import re
import urllib.error
import urllib.request

PROMPT = """You are ranking IT help desk articles for a user's question.

Question: {question}

Articles:
{articles}

List the article numbers from most to least relevant to the question, as a comma-separated list of all {n} numbers and nothing else. Example: 3, 1, 2"""


def trim_words(text, max_words):
    """The first max_words words of text (all of it if max_words is None or it's short)."""
    if max_words is None:
        return text
    words = text.split()
    return text if len(words) <= max_words else " ".join(words[:max_words])


def build_prompt(question, candidates, max_words=None):
    """candidates: list of articles (dicts with title and body), in their original order.

    max_words trims each article's body to its first max_words words, so long
    articles don't swamp the prompt.
    """
    numbered = "\n\n".join(
        f"[{i}] {a['title']}\n{trim_words(a['body'], max_words)}" for i, a in enumerate(candidates, start=1)
    )
    return PROMPT.format(question=question, articles=numbered, n=len(candidates))


def parse_order(reply, n):
    """Turn a reply like "3, 1, 2" into 0-based positions [2, 0, 1].

    Keeps the first mention of each valid number (1..n), then appends any the
    model left out in their original order. Returns None if the reply has no
    valid numbers at all, so the caller can fall back.
    """
    seen = []
    for token in re.findall(r"\d+", reply):
        number = int(token)
        if 1 <= number <= n and number - 1 not in seen:
            seen.append(number - 1)
    if not seen:
        return None
    return seen + [i for i in range(n) if i not in seen]


class OllamaReranker:
    def __init__(self, model="qwen2.5:7b", host="http://localhost:11434", max_words=None):
        self.model = model
        self.host = host
        self.max_words = max_words
        self.fallbacks = 0
        self.digest = self._digest()

    def _call(self, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(self.host + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                return json.load(response)
        except urllib.error.URLError as e:
            raise SystemExit(f"Can't reach Ollama at {self.host} ({e.reason}). Is the Ollama app running?") from e

    def _digest(self):
        for m in self._call("/api/tags")["models"]:
            if m["name"] == self.model or m["name"].split(":")[0] == self.model:
                return m["digest"]
        raise SystemExit(f"Model '{self.model}' isn't in Ollama. Run: ollama pull {self.model}")

    def rerank(self, question, candidates):
        """Return the candidates re-ordered, most relevant first."""
        reply = self._call(
            "/api/generate",
            {
                "model": self.model,
                "prompt": build_prompt(question, candidates, self.max_words),
                "stream": False,
                "options": {"temperature": 0, "num_ctx": 8192},
            },
        )["response"]
        order = parse_order(reply, len(candidates))
        if order is None:
            self.fallbacks += 1
            return list(candidates)
        return [candidates[i] for i in order]


# Claude Haiku prices, US$ per million tokens.
HAIKU_INPUT_PER_M = 0.10
HAIKU_OUTPUT_PER_M = 0.50
HAIKU_TOKENIZER_FACTOR = 1.3  # the newer tokenizer counts ~30% more than characters/4


def estimate_haiku_cost(prompts, output_tokens_per_call=300):
    """(input tokens, US$) for sending these prompts, before spending anything.

    Input tokens = characters / 4 x 1.3. Output is a generous guess per call.
    """
    input_tokens = int(sum(len(p) for p in prompts) / 4 * HAIKU_TOKENIZER_FACTOR)
    return input_tokens, haiku_cost(input_tokens, output_tokens_per_call * len(prompts))


def haiku_cost(input_tokens, output_tokens):
    return input_tokens / 1e6 * HAIKU_INPUT_PER_M + output_tokens / 1e6 * HAIKU_OUTPUT_PER_M


class HaikuReranker:
    """The same listwise reranking, with Claude Haiku as the judge (needs ANTHROPIC_API_KEY).

    Same interface as OllamaReranker. Tracks token totals so the cost is known.
    """

    def __init__(self, client=None, model="claude-haiku-5-5", max_words=400):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.client = client
        self.model = model
        self.max_words = max_words
        self.fallbacks = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def prompt(self, question, candidates):
        return build_prompt(question, candidates, self.max_words)

    def rerank(self, question, candidates):
        """Return the candidates re-ordered, most relevant first."""
        # No temperature/top_p/top_k: this model rejects them.
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": self.prompt(question, candidates)}],
        )
        self.input_tokens += response.usage.input_tokens
        self.output_tokens += response.usage.output_tokens
        reply = "".join(b.text for b in response.content if b.type == "text")
        order = parse_order(reply, len(candidates))
        if order is None:
            self.fallbacks += 1
            return list(candidates)
        return [candidates[i] for i in order]

    @property
    def cost(self):
        return haiku_cost(self.input_tokens, self.output_tokens)


HAIKU_BUDGET = 1.00  # US$ for the whole project session; runs/haiku_spend.json keeps the running total
SPEND_LEDGER = "runs/haiku_spend.json"


def spent_so_far(ledger=SPEND_LEDGER):
    try:
        with open(ledger, encoding="utf-8") as f:
            return json.load(f)["total_usd"]
    except FileNotFoundError:
        return 0.0


def record_spend(cost, ledger=SPEND_LEDGER):
    total = round(spent_so_far(ledger) + cost, 6)  # read before the "w" open empties the file
    with open(ledger, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"total_usd": total}, f)


def check_haiku_budget(prompts, ledger=SPEND_LEDGER, budget=HAIKU_BUDGET):
    """Print the estimated cost of these prompts; stop the run if the total would pass the budget."""
    tokens, cost = estimate_haiku_cost(prompts)
    spent = spent_so_far(ledger)
    print(f"Haiku estimate: ~{tokens:,} input tokens, up to ${cost:.3f} (already spent ${spent:.3f}, budget ${budget:.2f})")
    if spent + cost > budget:
        raise SystemExit("Estimated Haiku spend would pass the budget. Stopping before any calls.")
