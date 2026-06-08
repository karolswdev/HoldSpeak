# Evidence — HS-51-01: Leak inventory + vocabulary policy

Write-once record of the map for Phase 51. This story produces no code and no doc
edits: it produces the inventory that the scrub (HS-51-02) and the guard (HS-51-03)
both follow. The deliverable is `leak-inventory.md`.

## What was done

Ran the AGENT-BRIEF grep over the user/operator-facing docs (root `README.md` +
`docs/`, excluding `docs/internal/` and `docs/evidence/`):

```
grep -rInE '\bHS-[0-9]{2}-?[0-9]*\b|\bPhase[ -][0-9]+\b|\bPMO\b|\bcloseout\b|the current roadmap' \
  README.md docs/ --include='*.md' | grep -v 'docs/internal/' | grep -v 'docs/evidence/'
```

Read every hit in context, classified each as **banned** or **keep**, and recorded
a product-tense rewrite for each banned line.

## Findings

The scan found **more than the scaffold-time list** in the AGENT-BRIEF. Beyond the
expected `CONNECTOR_DEVELOPMENT.md`, `DEVICE_PROTOCOL.md`, `INTELLIGENT_TYPING_GUIDE.md`,
and `RELEASING.md`, two more in-scope guides leak and one out-of-scope asset readme:

- **`docs/SECURITY.md`** (6 hits) uses story IDs as decision provenance
  (`HS-25-03`, `HS-25-02`, `HS-25-01`) and forward-roadmap phase refs (`Phase 25`,
  `Phase 15` x2) that mean nothing to a reader of a threat model.
- **`docs/PLUGIN_AUTHORING.md:631-632`** tags the reference connectors `Phase-37` /
  `Phase-38`.
- **`docs/assets/pixellab/README.md:9`** has `HS-33-05` in a heading. Ruled
  **out of guard scope** (asset provenance, nested, not a user-journey doc); an
  optional courtesy scrub in HS-51-02.

The **root `README.md` is clean** (only legitimate `actuator` nouns). `docs/README.md`
only carries the `MIR-01` / `DIR-01` spec names, which are **KEEP**.

Total: **20 banned hits** across 6 in-scope guides, 1 optional out-of-scope hit, and
2 KEEP `MIR/DIR` lines. Every banned line has a recorded product-tense rewrite in
`leak-inventory.md`.

## Decisions recorded (open to veto)

- **Scope:** IN = `README.md` + `docs/*.md` (top-level). OUT and never scanned =
  `pm/roadmap/**`, `docs/internal/**`, `docs/evidence/**`, `docs/assets/**`.
- **`RELEASING.md` is in scope** even though it is maintainer-facing: it is a
  top-level guide and `Phase 50 evidence` reads as a leak. Scrub to "release evidence".
- **`SECURITY.md` story-ID provenance is scrubbed**, not kept: the IDs are
  meaningless to a user; the decision content stays.
- **Guard patterns** are `HS-\d{2}(-\d+)?`, `Phase[ -]\d+`, `PMO`,
  `the current roadmap`, `closeout`. Narrow enough that `MIR-01`/`DIR-01` never trip.
- **Honest limitation:** bare process-speak with no number (`a separate phase`)
  is removed by the human scrub, not the regex; the guard backstops the tagged leaks.

## Tests run

No code or doc-prose changed in this story, so there is no suite impact. The
"test" for an inventory is the grep itself: re-ran it and confirmed the inventory in
`leak-inventory.md` matches its output exactly (no in-scope file missed, no
internal-corpus file wrongly included). The post-scrub empty-grep is HS-51-02's
acceptance check, not this story's.

## Not done here (by design)

- The edits themselves are HS-51-02.
- The guard test is HS-51-03; this story only specifies its pattern + scope.
