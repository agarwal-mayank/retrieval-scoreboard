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


def build_prompt(question, candidates):
    """candidates: list of articles (dicts with title and body), in their original order."""
    numbered = "\n\n".join(
        f"[{i}] {a['title']}\n{a['body']}" for i, a in enumerate(candidates, start=1)
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
    def __init__(self, model="qwen2.5:7b", host="http://localhost:11434"):
        self.model = model
        self.host = host
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
                "prompt": build_prompt(question, candidates),
                "stream": False,
                "options": {"temperature": 0, "num_ctx": 8192},
            },
        )["response"]
        order = parse_order(reply, len(candidates))
        if order is None:
            self.fallbacks += 1
            return list(candidates)
        return [candidates[i] for i in order]
