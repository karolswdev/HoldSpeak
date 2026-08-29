# Evidence - HS-149-03

- **Story:** HS-149-03 - The gesture (picker + rail person chip)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T18:50:56Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/story-03-rig.py && (cd web && npx vitest run src/pages/cores/__tests__/peopleCore.test.tsx src/desk/chair/lanes/DoorBoardLane.test.tsx)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a639d977f5e235d3b0d9f082037cca7a7fffdb26

```text
shots=/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/story-03-shots

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  2 passed (2)
      Tests  49 passed (49)
   Start at  12:51:09
   Duration  1.56s (transform 447ms, setup 130ms, import 747ms, tests 1.11s, environment 601ms)
```

## Orchestrator triage note (2026-08-29)

The capture IS the historic run: the first headless
populated-People glass in this repo — setup, the relationship, the
REAL picker gesture (SUGGESTED tag verified in-frame), NEXT 1:1,
and the rail person chip, zero keychain interaction by
construction. Verified beyond the builder: 63 Python + 49 web
re-run orchestrator-read; the uid addition to the door wire
confirmed additive with the parity tests updated honestly.

**Two orchestrator catches at ship time:** (1) the hub bundle
predated the story's web work — rebuilt before the rig (the
walk-brief lesson extended: SHOT RIGS REBUILD FIRST); (2) the
first chip shot hit the BURNED-TWICE walk trap — the persisted
People window sat over the rail while the assertion passed against
the element behind it; the rig now takes chip shots in a FRESH
context AND carries an occlusion tell that fails the run if a
People window is present in-frame. The re-shot chip frame is the
value era's first money shot: EVENT · 1:1 w/ Ewa · Record this ·
[Ewa] on one row.
