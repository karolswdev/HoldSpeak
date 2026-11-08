"""The two engines the benchmark uses.

* ``LlamaCppEmbedder`` runs the real GGUF model in this process.  The fixture
  script and the nightly test use it.  It is test tooling: in the product the
  model runs behind the ``memory.embed`` capability.
* ``FixtureEmbedder`` reads real-model vectors from ``vectors.npz``, keyed by
  a hash of the prefixed text.  A text with no vector is an error.  The FAST
  tests use it, so they measure real meaning with no model.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Sequence

import numpy as np

from holdspeak.memory.embedder import (
    DOCUMENT_PREFIX, MEMORY_EMBED_DIM, cut_unit, model_id_for, query_text, text_key,
)


class MissingFixtureVector(KeyError):
    """A text has no vector in the fixture file."""


class LlamaCppEmbedder:
    """The GGUF model in this process, through ``llama-cpp-python``."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        dim: int = MEMORY_EMBED_DIM,
        model_name: str | None = None,
        n_ctx: int = 2048,
    ) -> None:
        self.model_path = Path(model_path)
        self.dim = int(dim)
        self.model_id = model_id_for(model_name or self.model_path.stem, self.dim)
        self._n_ctx = int(n_ctx)
        self._lock = threading.Lock()
        self._model = None

    def _load(self):
        if self._model is None:
            from llama_cpp import Llama  # optional extra; imported on first use

            self._model = Llama(
                model_path=str(self.model_path),
                embedding=True,
                n_ctx=self._n_ctx,
                n_batch=self._n_ctx,
                # An encoder model needs the whole input in one micro-batch.
                # With the default (512) llama.cpp ABORTS the process on a
                # batch of more than 512 tokens, so this is not optional.
                n_ubatch=self._n_ctx,
                verbose=False,
            )
        return self._model

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        with self._lock:
            model = self._load()
            raw = model.embed(list(texts), normalize=False, truncate=True)
        return cut_unit(np.asarray(raw, dtype=np.float32), self.dim)

    def embed_full(self, prefixed_texts: Sequence[str]) -> np.ndarray:
        """Full-size raw vectors (the fixture script and the 768 measure)."""
        with self._lock:
            model = self._load()
            raw = model.embed(list(prefixed_texts), normalize=False, truncate=True)
        return np.asarray(raw, dtype=np.float32)

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._embed([DOCUMENT_PREFIX + str(text) for text in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([query_text(text)])[0]

    def close(self) -> None:
        with self._lock:
            model, self._model = self._model, None
        if model is not None:
            try:
                model.close()
            except Exception:  # pragma: no cover - best effort
                pass


class FixtureEmbedder:
    """Real-model vectors from a file, keyed by the hash of the prefixed text."""

    def __init__(self, path: str | Path, *more: str | Path) -> None:
        self._vectors: dict[str, np.ndarray] = {}
        models: set[str] = set()
        for one in (path, *more):
            with np.load(str(one), allow_pickle=False) as data:
                models.add(str(data["model_id"]))
                keys = [str(key) for key in data["keys"]]
                vectors = np.asarray(data["vectors"], dtype=np.float32)
            self._vectors.update({key: vectors[index] for index, key in enumerate(keys)})
        if len(models) != 1:
            raise ValueError(f"fixture files of more than one model: {sorted(models)}")
        self.model_id = models.pop()
        self.dim = int(vectors.shape[1])
        self.calls = 0

    def _one(self, prefixed: str) -> np.ndarray:
        try:
            return self._vectors[text_key(prefixed)]
        except KeyError:
            raise MissingFixtureVector(prefixed[:120]) from None

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        self.calls += 1
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._one(DOCUMENT_PREFIX + str(text)) for text in texts])

    def embed_query(self, text: str) -> np.ndarray:
        self.calls += 1
        return self._one(query_text(text))


# ── extraction (memory slice 3) ─────────────────────────────────────────


class MissingFixtureFacts(KeyError):
    """A prompt has no recorded answer in the facts fixture."""


def fixture_key(payload: dict) -> str:
    """The key of one recorded answer: the hash of the two prompt texts, with
    the "Date of the source", "Days with no month" and "Days with a month"
    lines left out.  The corpus producers stamp a
    thread with the wall clock, so that one line changes every day; every
    other word of the prompt is in the key, so a changed prompt or corpus
    must be recorded again."""
    import re

    from holdspeak.memory.extract import payload_key

    user = re.sub(r"(?m)^Date of the source: .*$", "Date of the source: <date>", str(payload.get("user_prompt") or ""))
    # The two dates of a day with no month come from the source date too.
    user = re.sub(r"(?m)^Days with no month: .*$", "Days with no month: <dates>", user)
    user = re.sub(r"(?m)^Days with a month: .*$", "Days with a month: <dates>", user)
    return payload_key({"system_prompt": payload.get("system_prompt"), "user_prompt": user})


class FixtureExtractor:
    """Recorded real-model answers for ``memory.extract``, keyed by the hash
    of the two prompt texts (``fixture_key``).  A prompt with no
    answer is an error, so a changed prompt or corpus must be recorded again
    (``make_facts.py``).  It keeps every payload it received."""

    boundary = "local"

    def __init__(self, path: str | Path, *more: str | Path) -> None:
        import json

        self._answers: dict[str, dict] = {}
        models: set[tuple[str, int]] = set()
        for one in (path, *more):
            data = json.loads(Path(one).read_text())
            models.add((str(data["model"]), int(data["extractor_version"])))
            self._answers.update(data["answers"])
        if len(models) != 1:
            raise ValueError(f"fixture files of more than one model or version: {sorted(models)}")
        model, version = models.pop()
        self.model_id = model
        self.extractor_version = version
        self.payloads: list[dict] = []
        self.calls = 0

    def extract(self, payload: dict) -> dict:
        self.calls += 1
        self.payloads.append(payload)
        try:
            return self._answers[fixture_key(payload)]
        except KeyError:
            raise MissingFixtureFacts(str(payload.get("user_prompt", ""))[:160]) from None


class EndpointExtractor:
    """The real model at an OpenAI-compatible endpoint (test tooling: the
    fixture script and the optional real-engine probe).  In the product the
    call is one admitted ``memory.extract`` child of the runner."""

    boundary = "private_network"

    def __init__(self, base_url: str, model: str, *, key: str = "local", timeout: float = 300.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_id = model
        self.key = key
        self.timeout = timeout
        self.answers: dict[str, dict] = {}
        self.calls = 0

    def extract(self, payload: dict) -> dict:
        import json
        import urllib.request

        from holdspeak.services.thread_practice import _extract_structured_json

        body = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": payload["system_prompt"]},
                {"role": "user", "content": payload["user_prompt"]},
            ],
            "temperature": payload.get("temperature", 0.0),
            "max_tokens": payload.get("max_tokens"),
            "response_format": payload.get("response_format"),
            "chat_template_kwargs": {"enable_thinking": False},
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            answer = json.load(response)
        self.calls += 1
        parsed = _extract_structured_json(str(answer["choices"][0]["message"]["content"] or ""))
        if parsed is None:
            parsed = {"facts": []}
        self.answers[fixture_key(payload)] = parsed
        print(f"call {self.calls}: {len(parsed.get('facts') or [])} facts", flush=True)
        return parsed
