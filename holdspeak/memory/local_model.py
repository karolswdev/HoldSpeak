"""The local source of the meaning-search model (MEMORY-DESIGN.md §4).

One model class has a source that needs no signed catalogue: the embedding
model for ``memory.embed``.  The hub gets the GGUF file in one of two ways:

* **Adopt:** a file already on this device whose sha256 is the pinned one.
* **Fetch:** a download from the model's public Hugging Face URL, only after
  the owner's press.  The download continues a partial file, and the complete
  file is used only when its sha256 is the pinned one.

No signature claim is made.  The pinned hash is the integrity check.  The
signed packaged catalogue (``inference_setup_catalog.py``) is not touched.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True)
class PinnedModel:
    name: str
    label: str
    repository: str
    revision: str
    filename: str
    sha256: str
    size: int
    license: str
    architecture: str
    context_ceiling: int

    @property
    def url(self) -> str:
        return f"https://huggingface.co/{self.repository}/resolve/{self.revision}/{self.filename}"

    @property
    def host(self) -> str:
        return "huggingface.co"


#: nomic-embed-text-v1.5, GGUF Q8_0.  The revision, the size and the sha256
#: were read from Hugging Face on 2026-10-04 (``x-repo-commit``,
#: ``x-linked-size``, ``x-linked-etag``) and are equal to the file slice 1
#: measured.
EMBED_MODEL = PinnedModel(
    name="nomic-embed-text-v1.5.Q8_0",
    label="nomic-embed-text v1.5",
    repository="nomic-ai/nomic-embed-text-v1.5-GGUF",
    revision="0188c9bf409793f810680a5a431e7b899c46104c",
    filename="nomic-embed-text-v1.5.Q8_0.gguf",
    sha256="3e24342164b3d94991ba9692fdc0dd08e3fd7362e0aacc396a9a5c54a544c3b7",
    size=146_146_432,
    license="Apache-2.0",
    architecture="nomic-bert",
    context_ceiling=2048,
)


class ModelFetchError(OSError):
    """The download did not give the pinned file."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class ModelFetchCancelled(Exception):
    """The owner stopped the download.  The partial file stays."""


def model_dir(home: Path) -> Path:
    """The hub's place for the embedding model."""
    return home / ".local" / "share" / "holdspeak" / "models" / "embed"


def candidate_paths(model: PinnedModel, home: Path) -> list[Path]:
    """Where a copy of the model can be on this device, in order."""
    paths = [model_dir(home) / model.filename, home / ".cache" / "holdspeak-models" / "embed" / model.filename]
    named = os.environ.get("HOLDSPEAK_MEMORY_EMBED_MODEL", "").strip()
    if named:
        paths.append(Path(named))
    return paths


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def is_pinned_file(model: PinnedModel, path: Path) -> bool:
    """True when ``path`` is a regular file with the pinned size and hash."""
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != model.size:
            return False
        return hash_file(path) == model.sha256
    except OSError:
        return False


def find_on_device(model: PinnedModel, home: Path) -> Optional[Path]:
    """The first copy on this device that has the pinned hash, or None."""
    for path in candidate_paths(model, home):
        if is_pinned_file(model, path):
            return path
    return None


def looks_on_device(model: PinnedModel, home: Path) -> bool:
    """A fast check (name and size, no hash) for a status read."""
    for path in candidate_paths(model, home):
        try:
            if path.is_file() and path.stat().st_size == model.size:
                return True
        except OSError:
            continue
    return False


def _allowed_host(host: str) -> bool:
    return host == "huggingface.co" or host.endswith(".hf.co") or host.endswith(".huggingface.co")


def fetch(
    model: PinnedModel,
    destination: Path,
    *,
    url: Optional[str] = None,
    opener: Callable[..., Any] = urlopen,
    allowed_host: Callable[[str], bool] = _allowed_host,
    on_progress: Callable[[int], None] = lambda done: None,
    cancelled: Callable[[], bool] = lambda: False,
) -> Path:
    """Download the pinned file to ``destination``; return it when verified.

    The bytes go to ``<destination>.part``.  A part file from an earlier try
    is continued with a ``Range`` request.  The complete file is renamed to
    ``destination`` only when its size and sha256 are the pinned ones; a file
    with a different hash is renamed to ``<destination>.invalid`` and is
    never used.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name(destination.name + ".part")
    offset = part.stat().st_size if part.is_file() else 0
    if offset > model.size:
        part.unlink()
        offset = 0
    if offset < model.size:
        headers = {"User-Agent": "HoldSpeak/meaning-search"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        with opener(Request(url or model.url, headers=headers), timeout=60) as response:
            final = urlparse(str(response.geturl()))
            if final.scheme not in {"https", "http"} or not allowed_host((final.hostname or "").lower()):
                raise ModelFetchError("network", "the download left the approved source")
            status = getattr(response, "status", None)
            if status is None and hasattr(response, "getcode"):
                status = response.getcode()
            content_range = str(response.headers.get("Content-Range", "") or "")
            append = bool(offset and status == 206 and content_range.startswith(f"bytes {offset}-"))
            total = offset if append else 0
            on_progress(total)
            with part.open("ab" if append else "wb") as output:
                while True:
                    if cancelled():
                        raise ModelFetchCancelled()
                    chunk = response.read(_CHUNK_BYTES)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > model.size:
                        break
                    output.write(chunk)
                    on_progress(total)
        if total < model.size:
            raise ModelFetchError("network", "the download stopped before the end of the file")
    if part.stat().st_size != model.size or hash_file(part) != model.sha256:
        os.replace(part, destination.with_name(destination.name + ".invalid"))
        raise ModelFetchError("integrity", "the downloaded file does not have the pinned sha256")
    with part.open("rb") as handle:
        if handle.read(4) != b"GGUF":
            os.replace(part, destination.with_name(destination.name + ".invalid"))
            raise ModelFetchError("integrity", "the downloaded file is not a GGUF file")
    os.replace(part, destination)
    return destination


__all__ = [
    "EMBED_MODEL",
    "ModelFetchCancelled",
    "ModelFetchError",
    "PinnedModel",
    "candidate_paths",
    "fetch",
    "find_on_device",
    "hash_file",
    "is_pinned_file",
    "looks_on_device",
    "model_dir",
]
