# Phase 59 — Agent Brief (read this first)

You are picking up **Phase 59 — Speak Your Language (languages + the
spoken-symbol dictionary)** for HoldSpeak. Self-contained: mission, verified
seams, rules, per-story success. If this brief disagrees with the live tree,
the **codebase wins**.

---

## 0. Mission

Backlog candidate **K**, picked by the user ("K, then O"). One thesis: **the
input layer adapts to you.**

1. **Languages.** Whisper speaks ~99 languages; HoldSpeak exposes none of
   it. Today both backends silently auto-detect per utterance (no
   `language` is ever passed), which works until a short utterance in one
   language gets detected as a neighbor. A `model.language` knob ("auto"
   default = today's behavior, byte-identical) pins transcription for
   dictation AND meetings through the one shared `Transcriber`.
2. **The spoken-symbol dictionary.** The punctuation table is a hardcoded
   class attribute. Personal vocabulary ("tilde" → `~`, "arrow" → `→`) is
   classic daily-driver value: user-defined spoken→symbol entries with the
   same attach semantics the built-ins use, user wins on conflict.

## 1. The one thing you must not get wrong

**"auto" must stay byte-identical.** Today's behavior IS auto-detect; the
default config must produce the exact same backend calls as before (no
`language` kwarg → pass `None`, never the string "auto", to a backend).
Same for an empty symbol dictionary: `TextProcessor` output byte-identical.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate** (7 boxes, fresh per commit; evidence with done-flips;
  `final-summary.md` with phase exit). No `Co-Authored-By`; no `--no-verify`.
- **Operating cadence**: story header + phase status + project README per
  shipping commit. One PR per phase, branch `phase-59-languages`, merged on
  green.
- **Tests**: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **Web bundle gitignored**: edit `web/src`, build, commit source only.
- **Docs obey the canon** (`docs/internal/POSITIONING.md`): product-tense,
  zero em/en dashes in prose, the AI-vocab and canonical-name guards are
  LIVE tests now — new user-facing surfaces add their canonical-name row
  to the canon in the phase that ships them ("the spoken-symbol
  dictionary" is that row here).
- **Real-metal closeout**: a real non-English utterance through real
  Whisper with the language pinned (macOS `say` has international voices;
  probe with `say -v '?'` and pick what is installed), and the symbol
  dictionary through the real pipeline.

---

## 3. Ground truth (verified at scaffold, 2026-06-11)

**The Transcriber** (`holdspeak/transcribe.py`):
- `Transcriber(model_name, device, compute_type, backend, timeout_seconds)`
  facade at `:307` wraps `_MlxTranscriber` / `_FasterWhisperTranscriber`.
- mlx: `self._mlx_whisper.transcribe(audio, path_or_hf_repo=…, verbose=None)`
  at `:234` — **no language** (the only `language="en"` in the file is the
  silent warm-up call at `:200`, which is fine to leave or align).
- faster-whisper: `self._model.transcribe(audio, vad_filter=False)` at
  `:296` — **no language**. Its API takes `language=None|code`.
- Both backends accept a `language` kwarg upstream; `None` = auto-detect.

**Construction sites that must thread the knob** (grep `Transcriber(`):
- `holdspeak/web_runtime.py:297` (the live runtime: dictation + meetings),
- `holdspeak/main.py:447` (a CLI path — check which),
- `holdspeak/web/routes/meeting_import.py:59` (`_default_transcriber_factory`),
- `holdspeak/commands/import_recording.py:74` (the import CLI).

**Config** (`holdspeak/config.py`): `ModelConfig` at `:81`
(name/warm_on_start/backend/transcribe_timeout_seconds). Add
`language: str = "auto"`. The `/api/settings` round-trip carries dataclass
fields automatically (the Phase-56 `PresenceConfig.mascot` precedent);
`config_version` coercion keeps older configs working (Phase 50).

**The punctuation layer** (`holdspeak/text_processor.py`): `TextProcessor`
with class-attr tables `ATTACH_LEFT` / `ATTACH_RIGHT` / `ATTACH_BOTH` /
`NEWLINES` and regex word-boundary replacement (longest command first).
Constructed bare at `web_runtime.py:174`. The symbol dictionary becomes
constructor input merged over the built-ins (user wins), one entry =
`{spoken, symbol, attach}` with attach ∈ left/right/both/none (none =
plain replacement, spacing untouched — the safe default).

**Settings UI**: `web/src/pages/settings.astro` (sectioned + searchable,
Phase 43; the model section and the dictation section both exist — find
the patterns, reuse the row/toggle/editor styles; JS-rendered DOM styles
are `is:global` per the frontend doc).

**Language validation**: validate at the settings/config boundary against
a vendored frozen set of Whisper language codes (do NOT import
mlx/faster-whisper at config time). Accept "auto" + ISO codes; normalize
lowercase. An invalid code fails the settings write with an actionable
message, not a mid-dictation surprise.

---

## 4. Per-story definition of success

- **HS-59-01 — The language knob, end to end.** `ModelConfig.language`
  ("auto" default); `Transcriber(language=…)` → both backends pass
  `language=None` for auto (byte-identical) or the code; the warm-up call
  aligned; every construction site threads `config.model.language`; a
  settings field (model section) with validation against the vendored
  code set; `/api/settings` round-trip. Tests: fake-backend kwarg
  assertions both ways, the auto/None invariant, config round-trip +
  coercion, validation accept/reject, a settings page lock.
- **HS-59-02 — The spoken-symbol dictionary.** Config model
  (`dictation.spoken_symbols`, default empty), `TextProcessor` merge
  (user wins on conflict; attach semantics honored; longest-first still
  holds across merged tables), `web_runtime` wiring, the settings editor
  (add/remove rows: spoken phrase, symbol, attach mode), round-trip with
  a clean 400 on malformed entries. Empty dict byte-identical (locked).
  POSITIONING.md gains the canonical-name row. Tests: processor unit
  matrix, override-the-builtin, config validation, page locks.
- **HS-59-03 — Docs.** The typing guide learns both (where the language
  knob lives, what auto means, the honest short-utterance note; the
  dictionary with attach semantics and examples); README's Dictate cell +
  where-next touched if it earns it. Canon-clean (the voice guard is
  live).
- **HS-59-04 — Closeout.** Real-metal dogfood: a real non-English spoken
  utterance (`say` international voice) through real Whisper with the
  language pinned vs. auto; the symbol dictionary through the real
  pipeline (dry-run is fine — it is the same path); flag-default
  byte-identical proof; full suite; `final-summary.md`; BACKLOG K
  flipped; PR merged on green.

---

## 5. Gotchas

- **mlx-whisper vs faster-whisper language kwargs differ** in call shape;
  test each backend's fake separately.
- **The warm-up call** at `transcribe.py:200` hardcodes `language="en"` —
  harmless (silent audio) but align it for coherence.
- **Don't import whisper libs in config.py** — vendor the code list.
- **The symbol regex**: built-ins rely on `\b` word boundaries; a symbol
  like "→" is fine as a replacement, but a spoken phrase with
  regex-special chars must be escaped (`re.escape`, as the built-ins do).
- **Longest-first matching must consider merged tables** so a user's
  "open square bracket" beats a built-in "open" prefix collision.
- **Meeting import + meetings share the Transcriber** — the language knob
  applies to them automatically once threaded; say so in docs honestly.
- **The voice guard is live**: any new user-facing doc prose must be
  dash-free, AI-vocab-free, and use canonical names, or CI fails.

## 6. Where to start

HS-59-01. The language knob is the headline and touches the most sites;
the dictionary (02) is independent after that; docs (03), closeout (04).
