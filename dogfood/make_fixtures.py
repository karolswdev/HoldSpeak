#!/usr/bin/env python3
"""Render dogfood scenarios into audio fixtures with the macOS `say` voices.

Reads every `scenarios/*.yaml` file and, for each, synthesises 16 kHz mono PCM
WAV audio (Whisper's native format) using `say`. Meeting scenarios are
concatenated into one combined WAV (with brief inter-speaker silence) suitable
for `holdspeak import`. Dictation scenarios emit one WAV per utterance.

Nothing here calls an LLM or Whisper — it only produces audio + a ground-truth
script next to each clip so the tester can eyeball transcription/intel quality.
Output lands in `_audio/` (gitignored); regenerate any time.

Usage:
  python dogfood/make_fixtures.py --list
  python dogfood/make_fixtures.py --dry-run
  python dogfood/make_fixtures.py                       # render everything
  python dogfood/make_fixtures.py --only meeting-pylon-incident-warroom
  python dogfood/make_fixtures.py --kind dictation
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - guidance only
    sys.exit("PyYAML is required. Run inside the repo venv: .venv/bin/python dogfood/make_fixtures.py")

ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = ROOT / "scenarios"
DEFAULT_OUT = ROOT / "_audio"

# Whisper-native: little-endian int16, 16 kHz, mono.
SAY_FORMAT = "LEI16@16000"
SAMPLE_RATE = 16000
GAP_SECONDS = 0.45  # silence between speakers in a meeting clip

# Voices we lean on; if a scenario names a voice that is not installed we fall
# back to this list (round-robin) so the harness never hard-fails on a fresh Mac.
FALLBACK_VOICES = ["Samantha", "Alex", "Daniel", "Karen", "Moira"]


def installed_voices() -> set[str]:
    try:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return set()
    return {line.split()[0] for line in out.splitlines() if line.strip()}


def load_scenarios() -> list[dict]:
    scenarios = []
    for path in sorted(SCENARIOS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        if not data:
            continue
        data["_path"] = str(path)
        scenarios.append(data)
    return scenarios


def _resolve_voice(name: str | None, have: set[str], idx: int) -> str:
    if name and (not have or name in have):
        return name
    # requested voice missing — fall back deterministically
    for cand in FALLBACK_VOICES:
        if not have or cand in have:
            return cand
    return name or "Samantha"


def _say_to_wav(text: str, voice: str, out: Path) -> None:
    subprocess.run(
        ["say", "-v", voice, f"--data-format={SAY_FORMAT}", "-o", str(out), text],
        check=True,
    )


def _silence_frames(seconds: float) -> bytes:
    return b"\x00\x00" * int(SAMPLE_RATE * seconds)


def _concat_wavs(parts: list[Path], dest: Path, gap: float) -> None:
    with wave.open(str(dest), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        gap_bytes = _silence_frames(gap)
        for i, part in enumerate(parts):
            with wave.open(str(part), "rb") as w:
                out.writeframes(w.readframes(w.getnframes()))
            if i != len(parts) - 1:
                out.writeframes(gap_bytes)


def render_meeting(sc: dict, out_dir: Path, have: set[str], dry: bool) -> dict:
    sid = sc["id"]
    lines = sc.get("lines", [])
    script_lines = []
    manifest = {
        "id": sid,
        "kind": "meeting",
        "repo": sc.get("repo"),
        "profile": sc.get("profile"),
        "title": sc.get("title", sid),
        "wav": str((out_dir / f"{sid}.wav").relative_to(ROOT)),
        "segments": len(lines),
    }
    if dry:
        print(f"  [meeting] {sid}: {len(lines)} lines -> {manifest['wav']} (profile={sc.get('profile')})")
        return manifest

    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for i, line in enumerate(lines):
            voice = _resolve_voice(line.get("voice"), have, i)
            text = line["text"]
            speaker = line.get("speaker", f"S{i+1}")
            part = Path(tmp) / f"{i:03d}.wav"
            _say_to_wav(text, voice, part)
            parts.append(part)
            script_lines.append(f"[{speaker} / {voice}] {text}")
        dest = out_dir / f"{sid}.wav"
        _concat_wavs(parts, dest, GAP_SECONDS)

    (out_dir / f"{sid}.script.txt").write_text(
        f"# Ground truth — {sc.get('title', sid)}\n"
        f"# repo={sc.get('repo')}  profile={sc.get('profile')}\n"
        f"# {sc.get('description', '').strip()}\n\n"
        + "\n".join(script_lines)
        + "\n"
    )
    print(f"  [meeting] {sid}: {len(lines)} segments -> {manifest['wav']}")
    return manifest


def render_dictation(sc: dict, out_dir: Path, have: set[str], dry: bool) -> dict:
    sid = sc["id"]
    utterances = sc.get("utterances", [])
    voice = _resolve_voice(sc.get("voice"), have, 0)
    wavs = []
    manifest = {
        "id": sid,
        "kind": "dictation",
        "repo": sc.get("repo"),
        "language": sc.get("language", "en"),
        "voice": voice,
        "wavs": [],
        "utterances": len(utterances),
    }
    if dry:
        print(f"  [dictation] {sid}: {len(utterances)} utterances (voice={voice}, lang={sc.get('language','en')})")
        return manifest

    script_lines = []
    for i, utt in enumerate(utterances):
        text = utt if isinstance(utt, str) else utt["text"]
        dest = out_dir / f"{sid}__{i:02d}.wav"
        _say_to_wav(text, voice, dest)
        wavs.append(str(dest.relative_to(ROOT)))
        script_lines.append(f"[{i:02d}] {text}")
    manifest["wavs"] = wavs
    (out_dir / f"{sid}.script.txt").write_text(
        f"# Ground truth — {sid}\n"
        f"# repo={sc.get('repo')}  voice={voice}  language={sc.get('language','en')}\n"
        f"# {sc.get('description', '').strip()}\n\n"
        + "\n".join(script_lines)
        + "\n"
    )
    print(f"  [dictation] {sid}: {len(utterances)} clips ({voice}, {sc.get('language','en')})")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list scenarios and exit")
    ap.add_argument("--dry-run", action="store_true", help="show the render plan without calling say")
    ap.add_argument("--only", action="append", default=[], help="render only this scenario id (repeatable)")
    ap.add_argument("--kind", choices=["meeting", "dictation"], help="render only this kind")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output dir (default dogfood/_audio)")
    args = ap.parse_args()

    scenarios = load_scenarios()
    if not scenarios:
        print(f"No scenarios found in {SCENARIOS_DIR}", file=sys.stderr)
        return 1

    if args.list:
        for sc in scenarios:
            print(f"{sc['id']:42s} {sc.get('kind','?'):10s} repo={sc.get('repo','-'):12s} "
                  f"profile={sc.get('profile', sc.get('language','-'))}")
        return 0

    have = installed_voices()
    if not args.dry_run and not shutil.which("say"):
        print("`say` not found — this harness needs macOS. Use the committed transcripts/ instead.", file=sys.stderr)
        return 2

    selected = [
        sc for sc in scenarios
        if (not args.only or sc["id"] in args.only)
        and (not args.kind or sc.get("kind") == args.kind)
    ]
    if not selected:
        print("No scenarios matched the filters.", file=sys.stderr)
        return 1

    out_dir = args.out
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Rendering {len(selected)} scenario(s) -> {out_dir}{' (dry run)' if args.dry_run else ''}")
    manifest = []
    for sc in selected:
        kind = sc.get("kind")
        if kind == "meeting":
            manifest.append(render_meeting(sc, out_dir, have, args.dry_run))
        elif kind == "dictation":
            manifest.append(render_dictation(sc, out_dir, have, args.dry_run))
        else:
            print(f"  ! skipping {sc['id']}: unknown kind {kind!r}", file=sys.stderr)

    if not args.dry_run:
        (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Wrote {out_dir / 'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
