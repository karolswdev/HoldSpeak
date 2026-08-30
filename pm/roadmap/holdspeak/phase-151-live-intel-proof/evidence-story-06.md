# Evidence - HS-151-06

- **Story:** HS-151-06 - The walk, the attended leg, and the close
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T03:07:13Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-03-rig.py 2>&1 | tail -4 && H2=$(mktemp -d); HOME=$H2 HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H2/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/riadmap 2>/dev/null; HOME=$H2 HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H2/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-04-rig.py 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6de1966d845ae032469d7a0daac9b76a7b5c6482

```text
============================================================
  ALL ASSERTIONS PASSED

Done file: /Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-03-done.json

--- Failures: none ---

DONE (exit 0)
```

## Close sweep — 2026-08-30 (readable: scratchpad/hs151-close-sweep.log + hs151-webbase.log)

**Process note, owned honestly**: the FIRST sweep was invalidated by
the orchestrator's own hand — the close counsel's S1 fix and two
census registrations were applied WHILE it ran (the quiet-tree law
violated by its author; the 149 rebuild-first precedent repeating).
The re-sweep below ran on a genuinely quiet tree and is the record.

**Pytest (quiet tree):** 12 failed / 7030 passed / 53 skipped
(8:38, -n auto, isolated HOME). Verdict: **11 inherited-baseline +
1 dispositioned = zero unresolved branch-new.**

The disposition: test_phase143_routing_authority_census
::test_ast_census — TWO stale profile_id fixture entries
(models/__init__.py :684→:685, :1122→:1123). Attribution: the
SAME +1 shift as Phase 150's delegated_at field; the census
asserts SEQUENTIALLY, so 150's heal of the pointer assert UNMASKED
these in the profile_ids assert — an incomplete remap inherited
from my own last arc (the fixture is byte-identical stale on main).
Completed now; 10/10 ×2 serial. Lesson: healing a sequential-assert
census requires re-running the WHOLE file after each remap, not
trusting the first named mismatch.

Also healed this close, with attribution: the S1 warning shifted
engine.py (+6) → capability census remapped 17 entries 1:1; the
new _response_format_compatibility_retry registered in the
surface-fallback census as a provider-dialect decision (owner
151-01), whose owner-format regex lawfully widened past its
143-only birth assumption.

**Web (the story-150-04 checker, --run):** 1419 passed / 6 failed —
**"baseline-subset/exact, zero branch-new"** (verdict verbatim, the
six names each matched). Prior-phase asset dirs (141–150) restored
after every glass run.

### Captured run — 2026-08-30T08:58:46Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_phase151_fired_session_admission.py tests/unit/test_web_server_conductor_wiring.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_surface_fallback_census.py && python3 -c "
import json
d = json.load(open(\"pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-06-attended-record.json\"))
assert d[\"intel_ready\"] is True, d
assert d[\"failures\"] == [], d[\"failures\"]
assert d[\"segment_count\"] > 0, d[\"segment_count\"]
assert \"simulated meeting\" in d[\"honesty_header\"] and \"real capture path\" in d[\"honesty_header\"]
print(\"ATTENDED RECORD VALID:\", d[\"segment_count\"], \"segments;\", len(d[\"action_items\"]), \"action items; honesty header verbatim\")
"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d5ce4fd64f708ed67d205123359fd71968bdc6d

```text
........................................................................ [ 97%]
..                                                                       [100%]
74 passed in 39.54s
ATTENDED RECORD VALID: 22 segments; 1 action items; honesty header verbatim
```

## THE ATTENDED LEG — 2026-08-30, GREEN (the fourteen-take ladder + the fifteenth)

**HONESTY (counsel M6, verbatim on every artifact): simulated
meeting (played recording — "Sample one on one meeting with
Ms. Rachel Peller and Dr. Peter Bakken", the owner's pick), real
capture path (live mic + PortAudio through the production
`holdspeak web` runtime), real transcription (mlx-whisper), real
intel (.43:8080, the owner's pinned resident 35B).**

- The GREEN run (the finisher's, record JSON validated in the
  stamped capture above): the real [Record this] tap → the
  conductor countdown → the fire ADMITTED under the delegated
  SERVICE lane → 22 real segments from the live mic → the deferred
  queue → the 35B — whose summary describes the ACTUAL
  conversation (the Wisconsin Early Childhood Association grant;
  the "color of the day" tradition) — one grounded action item
  (owner "Me"); NO named owner emitted → the map-gesture leg
  recorded as an honest finding, never faked. Frames:
  assets/story-06-attended-shots/ (armed / recording-live /
  door-after-intel, 1440).
- The orchestrator's OWN verification run: capture green (20
  segments), LIVE intel green all through the session (topic
  analyses hitting the 35B each minute — the first live
  intelligence ever to run on a fired recording), one TRANSIENT
  deferred-provider refusal at the tail — re-driven through the
  production queue minutes later to intel_status=ready (the box
  healthy throughout; the refusal did not reproduce). Zero action
  items in that run's slice: that stretch of conversation contains
  no commitments — honest variance, recorded.
- The fourteen-take forensic ladder (defects #7–#13, all fixed and
  pinned; the counsel ADDENDUM ratified every delta with zero
  must/should-fix) lives in the phase log, the commit messages,
  and final-summary.md — the leg's failures are its product.

## Post-ladder close sweep — 2026-08-30 (readable: scratchpad/hs151-*3.log)

Pytest 16 failed / 7033 passed = 11 inherited + 5 dispositioned,
zero unresolved branch-new: the routing census (+ capability
census ×2) remapped for the finisher's same-symbol line shifts
(the sequential-assert lesson applied — looped to green ×2);
test_node_link_two_process serial ×2 green (xdist flake,
unmodified vs main — the flake family's newest member); the new
conductor-wiring pin serial green and its fixture HARDENED against
the process-global singleton under xdist (the exact fragility it
guards). Web checker verdict verbatim: baseline-subset/exact, zero
branch-new. Prior-phase asset dirs restored.
