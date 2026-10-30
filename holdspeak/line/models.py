"""The Line's two speech models on this machine (RECIPE LINE-6).

The signed catalogue (``holdspeak/inference_setup_catalog.py``, kind
``speech_model_preset``) pins each model: a Hugging Face revision and every
file the Line's engines load, with its size and SHA-256. This module is the
one place that fetches them and says their state, so ``holdspeak line
models`` and the Engines window's "Phone speech" rows share one state.

- **Where**: ``<the Line's folder>/models/<preset id>/<file path>``
  (``HOLDSPEAK_LINE_HOME``, else ``~/.holdspeak/line``).
- **Ready**: every pinned file is there and its SHA-256 matches. A file is
  hashed once; ``.verified.json`` keeps (size, mtime, sha256) so a later
  read does not hash 650 MB again. A file that changed is hashed again.
- **Fetch**: each missing file streams from
  ``https://huggingface.co/<repo>/resolve/<revision>/<path>`` into
  ``<file>.part``, hashed as it comes; a wrong size or digest removes the
  part and fails the fetch. ``fetch`` is injectable (tests use a fake; no
  test reaches Hugging Face).
- **Jobs**: :func:`start` runs one fetch per model in a thread and keeps its
  progress for the Engines row (:func:`rows`).
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Optional

from ..logging_config import get_logger
from .supervisor import state_dir

log = get_logger("line.models")

HOST = "huggingface.co"
#: The hello's model ids (the hub's Line card reads them) → the catalogue's.
HELLO_IDS = {"stt": "line-stt", "tts": "line-tts"}

READY = "ready"
MISSING = "missing"
PARTIAL = "partial"
DOWNLOADING = "downloading"
FAILED = "failed"

#: ``fetch(url) -> an iterable of byte chunks`` (the default streams over HTTPS).
Fetch = Callable[[str], Iterable[bytes]]
#: ``progress(received_bytes, total_bytes)``.
Progress = Callable[[int, int], None]

_CHUNK = 1 << 20
_STAMP = ".verified.json"
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def presets() -> tuple[dict[str, Any], ...]:
    from ..inference_setup_catalog import speech_presets

    return speech_presets()


def preset(preset_id: str) -> dict[str, Any]:
    for row in presets():
        if row["id"] == preset_id:
            return row
    raise KeyError(preset_id)


def models_dir() -> Path:
    return state_dir() / "models"


def model_dir(row: Mapping[str, Any]) -> Path:
    return models_dir() / str(row["id"])


def file_url(row: Mapping[str, Any], path: str) -> str:
    source = row["source"]
    return f"https://{HOST}/{source['repository']}/resolve/{source['revision']}/{path}"


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(_CHUNK), b""):
            sha.update(block)
    return "sha256:" + sha.hexdigest()


def _read_stamp(folder: Path) -> dict[str, Any]:
    try:
        data = json.loads((folder / _STAMP).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_stamp(folder: Path, stamp: Mapping[str, Any]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / (_STAMP + ".tmp")
    tmp.write_text(json.dumps(dict(stamp), sort_keys=True), encoding="utf-8")
    os.replace(tmp, folder / _STAMP)


def _mark(stamp: dict[str, Any], path: Path, rel: str, sha: str) -> None:
    info = path.stat()
    stamp[rel] = {"bytes": info.st_size, "mtime_ns": info.st_mtime_ns, "sha256": sha}


def _verified(folder: Path, item: Mapping[str, Any], stamp: dict[str, Any]) -> Optional[bool]:
    """True: the file is there and its digest is the pin; False: it is there
    and wrong; None: it is not there."""
    path = folder / item["path"]
    try:
        info = path.stat()
    except OSError:
        return None
    if info.st_size != item["bytes"]:
        return False
    seen = stamp.get(item["path"])
    if isinstance(seen, dict) and seen.get("bytes") == info.st_size and seen.get("mtime_ns") == info.st_mtime_ns:
        return seen.get("sha256") == item["sha256"]
    sha = _digest(path)
    _mark(stamp, path, item["path"], sha)
    return sha == item["sha256"]


def state(row: Mapping[str, Any]) -> dict[str, Any]:
    """The model's state on disk: ``ready`` | ``partial`` | ``missing``, with
    the verified bytes of the pinned total."""
    folder = model_dir(row)
    stamp = _read_stamp(folder)
    before = dict(stamp)
    have = 0
    wrong: list[str] = []
    for item in row["source"]["files"]:
        verdict = _verified(folder, item, stamp)
        if verdict:
            have += int(item["bytes"])
        elif verdict is False:
            wrong.append(item["path"])
    if stamp != before:
        try:
            _write_stamp(folder, stamp)
        except OSError as exc:
            log.info(f"line models: stamp not written ({exc})")
    total = int(row["source"]["download_bytes"])
    word = READY if have == total and not wrong else MISSING if have == 0 and not wrong else PARTIAL
    out: dict[str, Any] = {"state": word, "received": have, "total": total}
    if wrong:
        out["reason"] = "A file does not match its SHA-256. Download again."
    return out


def ready(row: Mapping[str, Any]) -> bool:
    return state(row)["state"] == READY


def _matches(item: Mapping[str, Any], size: int, digest: str) -> bool:
    """The fetched file is the pinned one: its size and its SHA-256."""
    return size == item["bytes"] and digest == item["sha256"]


def _http_chunks(url: str) -> Iterator[bytes]:
    import httpx

    with httpx.stream("GET", url, follow_redirects=True, timeout=httpx.Timeout(30.0, read=120.0)) as response:
        response.raise_for_status()
        yield from response.iter_bytes(_CHUNK)


def fetch(row: Mapping[str, Any], *, fetch: Optional[Fetch] = None, progress: Optional[Progress] = None) -> dict[str, Any]:
    """Fetch every pinned file that is not verified yet; the state after.

    Raises ``ValueError`` on a wrong size or digest (the part is removed)."""
    get = fetch or _http_chunks
    folder = model_dir(row)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = _read_stamp(folder)
    total = int(row["source"]["download_bytes"])
    received = 0
    for item in row["source"]["files"]:
        if _verified(folder, item, stamp):
            received += int(item["bytes"])
            if progress:
                progress(received, total)
            continue
        target = folder / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_name(target.name + ".part")
        sha = hashlib.sha256()
        size = 0
        try:
            with part.open("wb") as handle:
                for chunk in get(file_url(row, item["path"])):
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > item["bytes"]:
                        raise ValueError(f"{item['path']} is larger than its pin")
                    sha.update(chunk)
                    handle.write(chunk)
                    if progress:
                        progress(received + size, total)
            if not _matches(item, size, "sha256:" + sha.hexdigest()):
                raise ValueError(f"{item['path']} does not match its SHA-256")
            os.replace(part, target)
        except BaseException:
            part.unlink(missing_ok=True)
            raise
        _mark(stamp, target, item["path"], item["sha256"])
        _write_stamp(folder, stamp)
        received += size
    return state(row)


# ── the jobs the Engines window starts ───────────────────────────────


def start(preset_id: str, *, fetch_fn: Optional[Fetch] = None) -> dict[str, Any]:
    """Start (or join) the fetch of one model; its row at once."""
    row = preset(preset_id)
    with _jobs_lock:
        job = _jobs.get(preset_id)
        if job and job["state"] == DOWNLOADING:
            return model_row(row)
        _jobs[preset_id] = {"state": DOWNLOADING, "received": 0, "total": int(row["source"]["download_bytes"])}

    def moved(received: int, total: int) -> None:
        with _jobs_lock:
            _jobs[preset_id].update({"received": received, "total": total})

    def run() -> None:
        try:
            fetch(row, fetch=fetch_fn, progress=moved)
            with _jobs_lock:
                _jobs.pop(preset_id, None)
        except Exception as exc:
            log.warning(f"line model {preset_id} not fetched: {exc}")
            with _jobs_lock:
                _jobs[preset_id] = {"state": FAILED, "received": 0, "total": int(row["source"]["download_bytes"]),
                                    "reason": "The download stopped. Nothing half-done is kept. Try again."}

    threading.Thread(target=run, name=f"line-model-{preset_id}", daemon=True).start()
    return model_row(row)


def wait(preset_id: str, seconds: float = 10.0) -> None:
    """Tests: wait until the model's job is over."""
    import time

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        with _jobs_lock:
            job = _jobs.get(preset_id)
        if not job or job["state"] != DOWNLOADING:
            return
        time.sleep(0.01)


def forget_jobs() -> None:
    with _jobs_lock:
        _jobs.clear()


def model_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """One Engines row: the catalogue's facts, the disk state, a job's progress."""
    source = row["source"]
    with _jobs_lock:
        job = dict(_jobs.get(row["id"]) or {})
    disk = state(row) if job.get("state") != DOWNLOADING else {}
    out = {
        "id": row["id"], "role": row["role"], "label": row["label"], "summary": row["summary"],
        "bytes": int(source["download_bytes"]), "license": source["license"], "code_license": source["code_license"],
        "attribution": source["attribution"], "host": HOST, "revision": source["revision"],
        **(disk or {}), **job,
    }
    return out


def rows() -> list[dict[str, Any]]:
    return [model_row(row) for row in presets()]


def hello_models(*, loaded: bool = False) -> list[dict[str, str]]:
    """The hello's ``models``: ``ready`` once loaded, else the disk word
    (``downloaded`` when verified, else ``missing``)."""
    out = []
    for row in presets():
        word = "ready" if loaded else ("downloaded" if ready(row) else "missing")
        out.append({"id": HELLO_IDS[row["role"]], "name": row["label"], "state": word})
    return out


__all__ = [
    "DOWNLOADING", "FAILED", "HOST", "MISSING", "PARTIAL", "READY", "fetch", "file_url", "forget_jobs",
    "hello_models", "model_dir", "model_row", "models_dir", "preset", "presets", "ready", "rows", "start",
    "state", "wait",
]
