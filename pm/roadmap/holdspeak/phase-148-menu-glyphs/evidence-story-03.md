# Evidence - HS-148-03

- **Story:** HS-148-03 - The mock exhibit (the owner's variant gate)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T16:40:30Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-148-menu-glyphs/assets/story-03-rig.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bd1141d5c2ba42c0de299d0fcced80297c4b52a8

```text
shots=/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-148-menu-glyphs/assets/story-03-exhibit
```

## Orchestrator triage note + the delivery record (2026-08-29)

The rig (assets/story-03-rig.py, orchestrator-authored) boots the
real hub with the production bundle and flips the localStorage
variant BEFORE app boot — nine truthful shots, zero findings on the
capture run. Cross-read by the orchestrator: the Go triptych shows
the SAME items/keycaps/separator in all three states with only the
column differing; the C hybrid reads as a real launcher (every
program wearing its deck glyph over true keycap wells) while A is
the same grammar text-pure; the Object comparison shows verb purity
under C vs the glyphed column under B.

**DELIVERED TO THE OWNER** (SendUserFile, 8 shots: the sterile
before + A/C/B triptych + the Object and Desk comparisons + C at
393) with the recommendation (C) and the one-line cost statement
(any verdict is a one-attribute flip, forever). C is the shipped
default per the settled design; a later flinch is a redo by law.
The gate this story exists for is thereby satisfied: mocks in front
of the owner before any live-menu claim closes the phase.
