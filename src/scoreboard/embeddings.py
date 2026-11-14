"""Turn text into embeddings, and cache the article vectors on disk.

Any embedder works if it has a `name` and an `embed(texts)` method, so a
different model (e.g. a paid API) can be swapped in later without touching
the rest of the code.
"""

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


class OllamaEmbedder:
    """nomic-embed-text (or another embedding model) served by a local Ollama."""

    # nomic-embed-text was trained with these task labels; leaving them off lowers accuracy.
    document_prefix = "search_document: "
    query_prefix = "search_query: "

    def __init__(self, model="nomic-embed-text", host="http://localhost:11434", batch_size=32):
        self.model = model
        self.host = host
        self.batch_size = batch_size
        self.digest = self._digest()
        self.name = f"{model.split(':')[0]}_{self.digest[:12]}"

    def _call(self, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            self.host + path, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except urllib.error.URLError as e:
            raise SystemExit(
                f"Can't reach Ollama at {self.host} ({e.reason}). Is the Ollama app running?"
            ) from e

    def _digest(self):
        for m in self._call("/api/tags")["models"]:
            if m["name"].split(":")[0] == self.model.split(":")[0]:
                return m["digest"]
        raise SystemExit(f"Model '{self.model}' isn't in Ollama. Run: ollama pull {self.model}")

    def embed(self, texts):
        vectors = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            vectors.extend(self._call("/api/embed", {"model": self.model, "input": batch})["embeddings"])
        return vectors

    def embed_documents(self, texts):
        return self.embed([self.document_prefix + t for t in texts])

    def embed_queries(self, texts):
        return self.embed([self.query_prefix + t for t in texts])


def article_text(article):
    """What gets embedded for an article: its title, then its body."""
    return f"{article['title']}\n\n{article['body']}"


def load_or_build_article_vectors(embedder, articles, cache_dir):
    """Return {article id: vector}. Reuses the cached file for this embedder if
    it covers exactly these articles; otherwise embeds them and writes the cache."""
    cache_dir = Path(cache_dir)
    vectors_path = cache_dir / f"{embedder.name}.jsonl"
    meta_path = cache_dir / f"{embedder.name}.meta.json"
    ids = [a["id"] for a in articles]

    if vectors_path.exists():
        rows = [json.loads(line) for line in vectors_path.read_text(encoding="utf-8").splitlines()]
        if [r["id"] for r in rows] == ids:
            return {r["id"]: r["vector"] for r in rows}

    vectors = embedder.embed_documents([article_text(a) for a in articles])
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(vectors_path, "w", encoding="utf-8", newline="\n") as f:
        for article_id, vector in zip(ids, vectors):
            f.write(json.dumps({"id": article_id, "vector": vector}) + "\n")
    meta = {
        "embedder": embedder.name,
        "model": getattr(embedder, "model", embedder.name),
        "digest": getattr(embedder, "digest", None),
        "document_prefix": getattr(embedder, "document_prefix", ""),
        "dimensions": len(vectors[0]),
        "articles": len(ids),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return dict(zip(ids, vectors))
