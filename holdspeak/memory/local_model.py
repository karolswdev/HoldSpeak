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
import stat
import threading
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
    #: The first bytes the verified file must start with (a GGUF file starts
    #: with ``GGUF``).  Empty: the sha256 alone is the check (a Whisper
    #: ``config.json`` or ``weights.npz``).
    magic: bytes = b"GGUF"

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


def _open_regular(path: Path) -> int:
    """Open ``path`` for reading only when it is a regular file, not a link."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise OSError("not a regular file")
    return fd


def hash_file(path: Path) -> str:
    """sha256 of a regular file.  A symbolic link is refused, not followed."""
    digest = hashlib.sha256()
    with os.fdopen(_open_regular(path), "rb") as handle:
        while chunk := handle.read(_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


#: (path, size, mtime_ns, pinned sha256) -> True when the file has that hash.
_VERIFIED: dict[tuple[str, int, int, str], bool] = {}
_VERIFIED_LOCK = threading.Lock()


def is_pinned_file(model: PinnedModel, path: Path) -> bool:
    """True when ``path`` is a regular file (not a link) with the pinned size
    and the pinned sha256.

    The file is hashed once; the answer is kept for that path, size and
    modification time, so a status read can ask every time.
    """
    try:
        info = os.lstat(path)
        if not stat.S_ISREG(info.st_mode) or info.st_size != model.size:
            return False
        key = (str(path), int(info.st_size), int(info.st_mtime_ns), model.sha256)
        with _VERIFIED_LOCK:
            held = _VERIFIED.get(key)
        if held is None:
            held = hash_file(path) == model.sha256
            with _VERIFIED_LOCK:
                if len(_VERIFIED) > 64:
                    _VERIFIED.clear()
                _VERIFIED[key] = held
        return held
    except OSError:
        return False


def find_on_device(model: PinnedModel, home: Path) -> Optional[Path]:
    """The first copy on this device that has the pinned hash, or None.

    This is the one decision both the status and the press use: "on this
    device" is said only for a file whose hash is verified.
    """
    for path in candidate_paths(model, home):
        if not path.parent.is_symlink() and is_pinned_file(model, path):
            return path
    return None


def check_destination(destination: Path) -> None:
    """Refuse a download place that holds a symbolic link.

    The hub writes only into its own model directory, and never through a
    link: not the directory, not the part file, not the final file.
    """
    directory = destination.parent
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink() or not stat.S_ISDIR(os.lstat(directory).st_mode):
        raise ModelFetchError("unsafe", "the model directory is not a plain directory")
    for entry in (directory / (destination.name + ".part"), destination):
        if entry.is_symlink() or (entry.exists() and not stat.S_ISREG(os.lstat(entry).st_mode)):
            raise ModelFetchError("unsafe", f"{entry.name} in the model directory is not a regular file")


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
    directory = destination.parent
    part = directory / (destination.name + ".part")
    invalid = directory / (destination.name + ".invalid")
    check_destination(destination)
    offset = os.lstat(part).st_size if part.exists() else 0
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
            if not append and part.exists():
                part.unlink()
            # O_NOFOLLOW: a link put there after the check is refused, not
            # followed.  O_EXCL: a new part file is one this call made.
            flags = os.O_WRONLY | os.O_NOFOLLOW | (os.O_APPEND if append else os.O_CREAT | os.O_EXCL)
            with os.fdopen(os.open(part, flags, 0o644), "ab" if append else "wb") as output:
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
    if os.lstat(part).st_size != model.size or hash_file(part) != model.sha256:
        os.replace(part, invalid)
        raise ModelFetchError("integrity", "the downloaded file does not have the pinned sha256")
    if model.magic:
        with os.fdopen(_open_regular(part), "rb") as handle:
            magic = handle.read(len(model.magic))
        if magic != model.magic:
            os.replace(part, invalid)
            raise ModelFetchError("integrity", "the downloaded file does not start with the expected bytes")
    os.replace(part, destination)
    return destination


__all__ = [
    "EMBED_MODEL",
    "ModelFetchCancelled",
    "ModelFetchError",
    "PinnedModel",
    "candidate_paths",
    "check_destination",
    "fetch",
    "find_on_device",
    "hash_file",
    "is_pinned_file",
    "model_dir",
]
