# Evidence - HS-146-04

- **Story:** HS-146-04 - Rail provenance + seed repairs
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-28T22:41:31Z

- **Command:** `zsh -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_door_read_model.py tests/unit/test_calendar_ingest_conductor.py tests/unit/test_door_transport_parity.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ab9776cf23f43f22df75902d9ae8d51797df8443

```text
.......................                                                  [100%]
23 passed in 6.39s
```

## Orchestrator triage note

Captured: the door read model (source_label projection, the
label→hostname→LOCAL fallback chain, the no-dedupe proof), the
conductor (multi-source + resolved-label stamping), transport parity
(golden set gaining source_id/source_label — attributed here: the
fields are this story's projection; the story-03 worker surfaced the
omission first under the shared tree). The worker's own round ran the
full chain green: 14 unit + 7 conductor + 20 vitest + BOTH door e2e
files serial (9 + 2) + the 7-leg cold walk PASS, with the three
old-wire seeds flipped to the sources wire and walk leg 5 rewritten
against the settings API (TODO(HS-146-05) notes mark where the
story-03 editor's glass gets asserted at the close).

Orchestrator glass verification (shot rig,
`assets/story-0304-shots/rail-*.png`, all eyeballed): two labeled
sources → four EVENT rows with WORK/HOME chips including the
cross-feed duplicate shown twice (no-dedupe live); one source → zero
chips; both widths. TWO findings fixed in-round by orchestrator
hands: (1) the chip stretched full-row (a grid child stretches by
default) — `justify-self: start; width: max-content` makes it hug
its label; re-shot and verified; (2) the shot rig itself initially
photographed the settings window OVER the chair while the rail
assertions passed against elements BEHIND it — the walk-law trap;
fresh-context rig fix, shots retaken honestly.

Ruled divergence disposition: the worker skipped the multi-source
rail e2e leg (vitest+unit cover the chip rules); the orchestrator's
live shot rig IS the glass proof for this round, and story 05's walk
adds the durable leg.

Sweep note: full close sweep deferred to the next checkpoint per the
phase cadence; the in-round serial e2e + walk record stands in.
