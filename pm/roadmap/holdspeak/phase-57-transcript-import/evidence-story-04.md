# Evidence — HS-57-04: Docs: transcript import

**Date:** 2026-06-11
**Branch:** `phase-57-transcript-import`

## 1. What shipped

**`docs/MEETING_MODE_GUIDE.md`** — the import section became "Import an
Existing Recording or Transcript" (TOC anchor updated; the anchor had no
other referrers, grep-verified) and gained an "Importing a transcript"
subsection, product-tense:

- the three formats (`.vtt` the common Teams/Zoom/Meet export, `.srt`,
  `.txt`) and the fast-path truth (nothing to transcribe, no model loads,
  sub-second imports);
- **the speaker honesty rule**: voice tags / `Name:` prefixes become real
  per-segment labels (and feed the History speaker filter); unlabeled
  files get one user-chosen label (default "Transcript"); HoldSpeak never
  invents a name;
- **the timestamp honesty rule**: vtt/srt cues keep their real times;
  plain text gets evenly spaced approximate times that are never presented
  as real moments;
- the refusal posture (no readable content → a clear message; an import
  never silently creates an empty meeting);
- file-not-retained + local-only + the explicit "recordings import exactly
  as they did before" statement (the user's constraint, in writing).

**`docs/README.md`** (the docs index): the Meet entry now says "recordings
and transcripts… vtt and srt keep their real timestamps and speaker names".

## 2. The guards

- Zero em/en dashes in the new text (grep over the new subsection and the
  index entry: no hits).
- Doc-guard slice green (77 passed: vocab guard, link check, image refs,
  the Qlippy locks — all unaffected).
- Humanizer checklist applied while writing (plain copulas, no filler
  openers, no rule-of-three padding, bold lead-ins per the guide's house
  style).

## 3. Tests + suite

```
$ uv run pytest -q tests/ -k "doc"
77 passed, 2 skipped
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2641 passed, 17 skipped
```

(Docs-only story; the suite count is unchanged.)
