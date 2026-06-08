# Evidence — HS-51-02: Scrub user-facing docs (phase-relative -> product-tense)

Write-once record of the scrub. The roadmap vocabulary mapped in `leak-inventory.md`
is now gone from the user/operator-facing docs, rewritten into product-tense so the
meaning survives for a reader who has never heard of a "phase".

## A correctness catch before scrubbing

The HS-51-01 inventory grep was case-**sensitive**. Re-running it case-insensitively
surfaced 5 lowercase-only leaks the first pass missed, all in `DEVICE_PROTOCOL.md`
and `CONNECTOR_DEVELOPMENT.md`:

- `DEVICE_PROTOCOL.md:3` "phase-14 substrate", `:4` "the subject of phase 15",
  `:22` "Cross-network reach is phase 15", `:387` heading "What phase 15 will need
  to revisit".
- `CONNECTOR_DEVELOPMENT.md:435` "deferred to phase 14".

These were added to the scrub. The consequence for HS-51-03: **the guard must be
case-insensitive.**

## What shipped (edits by file)

All 6 in-scope guides plus the 1 optional out-of-scope asset readme were edited.
Every change is a vocabulary swap into product-tense; no structure or technical
content changed.

- **docs/DEVICE_PROTOCOL.md** (9 lines): status line, two table cells (`HS-17-05`,
  `HS-17-08 / HS-17-13`), the Recording-tick paragraph, the "section 8" heading,
  the TLS-termination and per-device-PSK bullets, and the two `127.0.0.1` /
  cross-network sentences. "Phase 14/15" became "today" / "future work" / "A future
  tunnel layer"; the section-8 heading became "What cross-network reach will need to
  revisit".
- **docs/CONNECTOR_DEVELOPMENT.md** (5 lines): the intro blockquote, the
  "Phase 13 additions ..." heading (also dropped its em dash), the "Phase 11 shipped
  ... phase 13 turns it on" paragraph, the "deferred to phase 14" line, and the
  external-distribution paragraph. Phase-relative claims became product-tense
  ("HoldSpeak ships ...", "out of scope today").
- **docs/SECURITY.md** (7 lines): the status line, the encryption-at-rest heading,
  and five inline `HS-25-0x` / `Phase 15` references. Story IDs were used as decision
  provenance and meant nothing to a reader; the decision content stays, the tags are
  gone.
- **docs/RELEASING.md** (1 line): "the Phase 50 evidence" -> "the release evidence".
- **docs/INTELLIGENT_TYPING_GUIDE.md** (1 line): "Known-good local dogfood profile
  from HS-19 closeout:" -> "A known-good local profile:".
- **docs/PLUGIN_AUTHORING.md** (1 line): dropped the `Phase-37` / `Phase-38` tags;
  named the references by what they are (outbox / GitHub / webhook).
- **docs/assets/pixellab/README.md** (1 line, optional): dropped `HS-33-05` from the
  brand-identity heading. Out of the guard's scan scope, scrubbed as a courtesy.

`MIR-01` / `DIR-01` in `docs/README.md:78-79` were left intact (architecture spec
names, KEEP). The root `README.md` needed no change (already clean).

## Humanizer pass

The `humanizer` skill was invoked over all 15 rewritten passages. The audit found no
AI tells: no em or en dashes (replacements use periods, commas, semicolons, and
parentheses), no rule-of-three padding, no promotional or hedging phrasing. No
further fixes were required. Pre-existing em dashes elsewhere in these guides were
left alone; a full dash purge is not this phase's thesis.

## Tests run

```
# in-scope leak grep (case-insensitive) must be empty:
grep -rInE '\bHS-[0-9]{2}-?[0-9]*\b|\bphase[ -][0-9]+\b|\bPMO\b|\bcloseout\b|the current roadmap' \
  README.md docs/*.md -i | grep -v 'docs/internal/'
-> (no output: clean)

uv run pytest -q -k "doc_drift or doc_guard or link or doc" --ignore=tests/e2e/test_metal.py
-> 75 passed, 2 skipped
```

The dangling-link and image-ref guards passing confirms the two heading rewrites
(`CONNECTOR_DEVELOPMENT.md` and `DEVICE_PROTOCOL.md` section 8) did not break any
in-doc anchor link. 0 `_built/` tracked.

## Not done here (by design)

- The guard that keeps this clean is HS-51-03 (and must be case-insensitive, per the
  catch above).
- The `DOCS_STYLE.md` rule is HS-51-04.
