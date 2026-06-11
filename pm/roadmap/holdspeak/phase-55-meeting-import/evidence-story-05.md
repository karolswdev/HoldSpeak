# Evidence — HS-55-05: Docs — import + facets

**Date:** 2026-06-11
**Branch:** `phase-55-meeting-import`

## 1. What shipped

Two new sections in `docs/MEETING_MODE_GUIDE.md` (the meeting journey's home;
TOC renumbered):

- **"Import an Existing Recording"** — the web flow (History → Import a
  recording → drop/browse → live progress → resolves in place; failed
  imports say why and are removable) and the CLI
  (`holdspeak import path.wav --title --speaker --tag`), with the three
  honest truths stated plainly in prose: WAV out of the box + the explicit
  `ffmpeg` requirement for compressed formats (refused with a clear message
  without it); one user-chosen speaker label with the *why* (a single mixed
  file has no separate mic/system streams, and HoldSpeak does not guess
  boundaries it cannot verify); the audio file read, transcribed locally,
  and not retained — nothing leaves the machine. Plus the
  mtime-as-start-time behavior so old recordings sort where they happened.
- **"Find Meetings in Your Archive"** — the filter row (date range, speaker,
  tag, open actions), that filters run server-side over the whole archive,
  and that they compose with each other and full-text search.

Index + README touches: the docs-index Meet entry now mentions import +
facets (active voice), and the root README's meeting-intelligence section
gains the one-liner ("Recordings you already have count too…").

Placement decision (per the story): extended `MEETING_MODE_GUIDE.md` rather
than a separate guide — import and facets are steps in the existing meeting
journey, and the guide already owns `/history`.

## 2. Humanizer pass (run, findings fixed)

The skill audit found a real cluster in the first draft and it was rewritten:
the "Three things to know, plainly:" announcement + exactly three bold
inline-header bullets (patterns #28/#10/#16) became three plain prose
paragraphs; a "not only for meetings you capture live" opener (pattern #9)
became a direct statement; the diff-anchored "the list behaves exactly as
before" (pattern #30) became "the list shows your newest meetings first";
the docs-index passive "can be imported" became active. The facet list keeps
the guide's established bold-lead list style (matching the surrounding
aftercare section — a deliberate false-positive exemption).

## 3. Guards (actually run, actually read)

- New sections contain **zero em/en dashes** (verified by grep over the new
  section range and over the staged diff; the 13 pre-existing dashes
  elsewhere in the guide are out of scope).
- No roadmap vocabulary in any touched user-facing doc.

```
$ uv run pytest -q tests/unit -k "doc or drift"
69 passed, 1963 deselected in 2.12s

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2568 passed, 17 skipped in 85.33s (0:01:25)
```
