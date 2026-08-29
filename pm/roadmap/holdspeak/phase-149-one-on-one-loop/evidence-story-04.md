# Evidence - HS-149-04

- **Story:** HS-149-04 - The brief (Prep lens + PREP on the rail)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T19:14:16Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/story-04-rig.py && H2=$(mktemp -d); HOME=$H2 HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H2/pk.json uv run --python 3.13.11 pytest -q tests/unit/test_people_brief.py tests/unit/test_people_mcp.py tests/unit/test_people_no_leaks.py tests/unit/test_door_read_model.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d3a67d72663b3b416d9f22c7b5138c7470da28a1

```text
shots=/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/story-04-shots
.........................................                                [100%]
41 passed in 4.43s
```

## Orchestrator triage note (2026-08-29)

Verified beyond the builder: 68 Python + 54 web re-run and read;
the decision chain finding (decision_record_sources join, not a
direct column) checked against decision_record_service.py:96-97;
the F6 proof read (planted "PRIVATE SECRET" absent from the MCP
response, access-off refusal named, F7 policy block asserting
shared_intent_only + employment_decisions prohibited); the
write-count spy covers BOTH stores. The rig run in this capture is
the Prep lens on real glass — the frame shows the manager's
Tuesday whole (NEXT 1:1 header, YOU OWE with its visibility tag,
THEIR AGENDA, LAST 1:1s with the plaintext action item BY
REFERENCE) while the Door's NOW column behind the window carries
the SAME action-item card — the two commitment worlds coexisting
unmerged, exactly the D6 ruling, photographed.

**Interrogated claim, verified TRUE with a twist:** the builder
named SIX "pre-existing" web failures; three were NEW names beyond
the known trio. Stash-compared AND diffed to main: all three
(InlineEditor / MicButton / workbenchAutomations, one dating to
HS-132-05) are byte-identical-to-main inherited debt. THE WEB
BLIND-SPOT LEDGER GROWS 3→6 KNOWN NAMES — the 148 discovery's case
for a web baseline file strengthens; carried to the close counsel.
Orchestrator self-catch: the REBUILD-FIRST rig law was violated by
its own author one story after writing it (stale bundle, empty
Prep tab) — rebuilt, re-run, the law now has a scar to point at.
person_relationship_id on the wire ruled additive-and-necessary
(the PREP navigation needs it; read-time only, no store crossing).
