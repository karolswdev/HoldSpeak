# HS-67-01 — The isolated harness scaffold

- **Project:** holdspeak
- **Phase:** 67
- **Status:** built (awaiting commit)
- **Depends on:** none
- **Owner:** unassigned

## Problem

A dogfooding run must drive a real HoldSpeak without polluting the owner's real
config and DB, and must reuse the already-downloaded Whisper/GGUF models. There
is no existing way to run the installed `holdspeak` against a throwaway home.

## Scope

- **In:** `dogfood/setup.sh` (build a sandbox `HOME` at `dogfood/_home`, write a
  tier-1 or tier-2 `config.json`, symlink `~/.cache/huggingface` + `~/Models`),
  `dogfood/hs` (run the venv's `holdspeak` with `HOME` = sandbox), `dogfood/env.sh`
  (sourceable `hs` function), `dogfood/.gitignore` (ignore `_audio/`, `_home/`,
  `results/*.md`), `dogfood/README.md`.
- **Out:** the scenarios, repos, protocol (later stories). Any product code.

## Acceptance criteria

- [ ] `dogfood/setup.sh` creates `_home/.config/holdspeak/config.json`; `--tier1`
      writes a no-LLM config, default writes a tier-2 `.43` config; `--force`
      overwrites; without it, an existing config is preserved.
- [ ] Cache symlinks are created when the real `~/.cache/huggingface` / `~/Models`
      exist; absent ones are skipped without error.
- [ ] `dogfood/hs doctor` runs the installed `holdspeak` with the sandbox `HOME`
      and refuses to run if the sandbox is uninitialised.
- [ ] A run writes only under `dogfood/_home` (protocol X-05).

      See `evidence-story-01.md`.

## Test plan

- Manual: `dogfood/setup.sh`; `dogfood/hs doctor`; confirm config path under
  `_home`; confirm real `~/.config/holdspeak` untouched (stat before/after).
- Unit: n/a (shell tooling; the plumbing pytest in HS-67-03 covers layout).

## Notes / open questions

- `HOME` is the only isolation lever (config + DB both key off `Path.home()`);
  there is no env override for those paths.
