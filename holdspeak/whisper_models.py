"""Where the Whisper model is on this device (owner ruling 2026-10-05).

Two questions, both answered from the disk only (no network):

* ``local_whisper_dir(repo)``: the directory that holds the model files for a
  Whisper repository id, or ``None``.  First the HoldSpeak model folder
  (the files "Set up local AI" downloads, sha-pinned), then the Hugging Face
  cache (a model an earlier HoldSpeak or another tool downloaded).
* ``whisper_on_disk(name, backend)``: is the configured model on this device?
  The boot warm asks this.  When the answer is no, the boot does not load the
  model, so it does not download it either.  "Set up local AI" downloads it,
  with one egress receipt.

``pinned_whisper(name, backend)`` names the exact files (revision, size,
sha256) that "Set up local AI" downloads for one model.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .memory.local_model import PinnedModel, is_pinned_file


def _pinned(repository: str, revision: str, filename: str, sha256: str, size: int) -> PinnedModel:
    return PinnedModel(
        name=f"{repository}/{filename}",
        label=repository.split("/", 1)[1],
        repository=repository,
        revision=revision,
        filename=filename,
        sha256=sha256,
        size=size,
        license="MIT",
        architecture="whisper",
        context_ceiling=0,
        magic=b"",
    )


#: Read from Hugging Face on 2026-10-05 (``x-repo-commit``, ``x-linked-size``,
#: ``x-linked-etag``) and equal to the hashes of a copy on the owner's Mac.
_MLX_BASE_REPO = "mlx-community/whisper-base-mlx"
_MLX_BASE_REV = "1e3e249fb8d01c655324bd6841b1deadffd6d04c"
_FW_BASE_REPO = "Systran/faster-whisper-base"
_FW_BASE_REV = "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66"

_PINNED: dict[tuple[str, str], tuple[PinnedModel, ...]] = {
    ("mlx", "base"): (
        _pinned(_MLX_BASE_REPO, _MLX_BASE_REV, "config.json",
                "737220a6d958b3ad48e78f840fa991556266983c84ea2ca40e413389c62e4c2f", 262),
        _pinned(_MLX_BASE_REPO, _MLX_BASE_REV, "weights.npz",
                "2f57d5f3ef473054c638961f90716f4ee415e8108de81313eccb2c5fd62eff0b", 143_724_204),
    ),
    ("faster-whisper", "base"): (
        _pinned(_FW_BASE_REPO, _FW_BASE_REV, "config.json",
                "56a6d8110d311f19c8f0471e562832c7527f146b567275bfca59fcf7c184da9a", 2309),
        _pinned(_FW_BASE_REPO, _FW_BASE_REV, "model.bin",
                "d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9", 145_217_532),
        _pinned(_FW_BASE_REPO, _FW_BASE_REV, "tokenizer.json",
                "fb7b63191e9bb045082c79fd742a3106a12c99513ab30df4a0d47fa6cb6fd0ab", 2_203_239),
        _pinned(_FW_BASE_REPO, _FW_BASE_REV, "vocabulary.txt",
                "34ce3fe1c5041027b3f8d42912270993f986dbc4bb34cf27f951e34a1e453913", 459_861),
    ),
}

#: The files a model folder must hold before a backend can load it WITHOUT
#: the network.  faster-whisper's ``WhisperModel`` reads ``model.bin``,
#: ``config.json`` and the vocabulary from the folder; when the folder has no
#: ``tokenizer.json`` it calls ``tokenizers.Tokenizer.from_pretrained(
#: "openai/whisper-tiny")`` (a Rust downloader).  So the tokenizer is
#: required: a folder without it is "not on this device".
#: (``preprocessor_config.json`` is optional and read only from the folder.)
_REQUIRED = {
    "mlx": (("config.json",), ("weights.npz", "weights.safetensors")),
    "faster-whisper": (
        ("config.json",), ("model.bin",), ("tokenizer.json",), ("vocabulary.txt", "vocabulary.json"),
    ),
}


def pinned_whisper(name: str, backend: str) -> tuple[PinnedModel, ...]:
    """The sha-pinned files for one Whisper model, or ``()`` when none is pinned."""
    return _PINNED.get((str(backend or "").strip().lower(), str(name or "").strip().lower()), ())


def whisper_root(home: Optional[Path] = None) -> Path:
    return (home or Path.home()) / ".local" / "share" / "holdspeak" / "models" / "whisper"


def pinned_whisper_dir(repository: str, home: Optional[Path] = None) -> Path:
    """The HoldSpeak folder for one Whisper repository (``org--name``)."""
    return whisper_root(home) / repository.replace("/", "--")


def _hub_cache(home: Path) -> Path:
    explicit = os.environ.get("HF_HUB_CACHE", "").strip()
    if explicit:
        return Path(explicit).expanduser()
    hf_home = os.environ.get("HF_HOME", "").strip()
    if hf_home:
        return Path(hf_home).expanduser() / "hub"
    return home / ".cache" / "huggingface" / "hub"


def _backend_for(repository: str) -> str:
    return "faster-whisper" if "faster-whisper" in repository else "mlx"


def _complete(folder: Path, backend: str) -> bool:
    try:
        return all(any((folder / name).is_file() for name in group) for group in _REQUIRED[backend])
    except OSError:
        return False


def _pinned_folder_ready(repository: str, home: Path) -> Optional[Path]:
    folder = pinned_whisper_dir(repository, home)
    files = _pins_for(repository)
    if not files or folder.is_symlink():
        return None
    if all(is_pinned_file(item, folder / item.filename) for item in files) and _complete(
        folder, _backend_for(repository)
    ):
        return folder
    return None


def _pins_for(repository: str) -> list[PinnedModel]:
    return [item for group in _PINNED.values() for item in group if item.repository == repository]


def _verified_in(folder: Path, model: PinnedModel) -> bool:
    """The file in ``folder`` has the pinned size and sha256.

    A Hugging Face snapshot holds links to its blobs, so the link is resolved
    first and the blob itself (a regular file) is checked.
    """
    try:
        target = (folder / model.filename).resolve(strict=True)
    except OSError:
        return False
    return is_pinned_file(model, target)


def _hub_snapshot(repository: str, home: Path) -> Optional[Path]:
    root = _hub_cache(home) / ("models--" + repository.replace("/", "--"))
    snapshots = root / "snapshots"
    if not snapshots.is_dir():
        return None
    backend = _backend_for(repository)
    ordered: list[Path] = []
    try:
        ref = (root / "refs" / "main").read_text(encoding="utf-8").strip()
        if ref:
            ordered.append(snapshots / ref)
    except OSError:
        pass
    try:
        ordered.extend(sorted(path for path in snapshots.iterdir() if path.is_dir()))
    except OSError:
        return None
    pins = _pins_for(repository)
    for folder in ordered:
        if not folder.is_dir() or not _complete(folder, backend):
            continue
        if pins:
            # A pinned model counts only when every file has the pinned bytes:
            # a truncated or changed cache copy is not "on this device".
            if all(_verified_in(folder, item) for item in pins):
                return folder
        else:
            return folder
    return None


def pinned_file_on_device(model: PinnedModel, *, home: Optional[Path] = None) -> bool:
    """One pinned Whisper file is on this device with its pinned bytes."""
    where = home or Path.home()
    if is_pinned_file(model, pinned_whisper_dir(model.repository, where) / model.filename):
        return True
    return _hub_snapshot(model.repository, where) is not None


def local_whisper_dir(
    repository: str, *, home: Optional[Path] = None, backend: Optional[str] = None,
) -> Optional[Path]:
    """The folder on this device that holds ``repository``, or ``None``.

    ``repository`` is a Hugging Face id (``org/name``) or a local path.  This
    reads the disk only; it never makes a network request.  A folder counts
    only when it holds every file its backend loads (``_REQUIRED``), so the
    loader has nothing to fetch.
    """
    clean = str(repository or "").strip()
    if not clean:
        return None
    as_path = Path(clean).expanduser()
    if as_path.is_absolute() or clean.startswith(("~", ".")):
        # An explicitly selected folder obeys the same completeness rule.
        backends = (backend,) if backend in _REQUIRED else tuple(_REQUIRED)
        if as_path.is_dir() and any(_complete(as_path, item) for item in backends):
            return as_path
        return None
    if "/" not in clean:
        return None
    where = home or Path.home()
    return _pinned_folder_ready(clean, where) or _hub_snapshot(clean, where)


def repositories_for(name: str, backend: str) -> list[str]:
    """The repository ids a backend loads for a model name, in order."""
    clean = str(name or "").strip()
    if not clean:
        return []
    if backend == "faster-whisper":
        if "/" in clean or Path(clean).expanduser().exists():
            return [clean]
        return [f"Systran/faster-whisper-{clean.lower()}"]
    from .transcribe import _model_repo_candidates

    return _model_repo_candidates(clean)


def whisper_on_disk(name: str, backend: str, *, home: Optional[Path] = None) -> bool:
    """True when the model ``name`` for ``backend`` is on this device."""
    return any(
        local_whisper_dir(repo, home=home, backend=backend) is not None
        for repo in repositories_for(name, backend)
    )


#: The reason code a meeting with no transcript carries when the speech model
#: was not on this device (the faces say "No transcript: speech is not set up").
SPEECH_NOT_SET_UP = "speech_not_set_up"

#: The two states in which speech can run on this device.
SPEECH_READY_STATES = frozenset({"on_device", "on_device_unpinned"})


def speech_readiness(name: str, backend: str, *, home: Optional[Path] = None) -> dict:
    """The ONE speech-readiness truth (PHILO-17 speech): is the speech model
    on this device, so that Speak, Record, Runs on and Setup can use it?

    Disk only; never a network request.  ``state`` is one of:

    * ``on_device``: the loader finds this (pinned) model on this disk;
    * ``on_device_unpinned``: the owner's own copy of a model with no pins;
    * ``will_download``: pinned files are missing; "Set up speech" gets them;
    * ``not_covered``: no pins and no copy; setup cannot get this model.

    ``bytes`` is the size "Set up speech" downloads (0 when nothing is missing).
    """
    where = home or Path.home()
    clean_name = str(name or "").strip() or "base"
    pins = pinned_whisper(clean_name, backend)
    # The loader's own question: can it load this model from this disk?
    if whisper_on_disk(clean_name, backend, home=where):
        state, missing = ("on_device" if pins else "on_device_unpinned"), 0
    elif pins:
        state = "will_download"
        missing = sum(model.size for model in pins if not pinned_file_on_device(model, home=where))
    else:
        state, missing = "not_covered", 0
    return {
        "model": clean_name,
        "backend": backend,
        "state": state,
        "ready": state in SPEECH_READY_STATES,
        "bytes": missing,
    }


def configured_speech_readiness(*, config=None, home: Optional[Path] = None) -> dict:
    """``speech_readiness`` for the configured Whisper model (name + backend)."""
    from .transcribe import resolve_backend_or_raw

    if config is None:
        from .config import Config

        config = Config.load()
    model = getattr(config, "model", None)
    name = str(getattr(model, "name", "") or "base")
    backend = resolve_backend_or_raw(str(getattr(model, "backend", "") or "auto"))
    return speech_readiness(name, backend, home=home)


__all__ = [
    "SPEECH_NOT_SET_UP",
    "SPEECH_READY_STATES",
    "configured_speech_readiness",
    "local_whisper_dir",
    "pinned_file_on_device",
    "pinned_whisper",
    "pinned_whisper_dir",
    "repositories_for",
    "speech_readiness",
    "whisper_on_disk",
    "whisper_root",
]
