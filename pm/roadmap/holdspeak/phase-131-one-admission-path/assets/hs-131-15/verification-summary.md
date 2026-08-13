# HS-131-15 verification summary

All Python verification ran under a scratch-isolated `HOME`; the owner's real
database was never opened or migrated.

## Final focused proof

- Complete hostile speech/kernel/web/schema set: **501 passed**.
- Full impacted speech-side set: **304 passed**.
- Speech-side-door file: **36 passed**.
- One-path census: **28 passed**; **105 sites / 4 findings / 4 families / 0
  unregistered** with 27 admitted seams across 18 scopes.
- Web: TypeScript `tsc --noEmit` passed; **45 tests passed**.
- Static: `git diff --check` and Python `compileall` passed.
- Mutation: removing the `admission=` handoff from the browser dry-run and CLI
  command was caught by the exact `dictation-dry-run` and `dictation-command`
  fences; both sources were restored before the green census.
- Independent hostile verdict: **SHIP-CANDIDATE**.

## Full-gate accounting

The official two-lane gate remains inherited red and is not described as green.
The HS-131-14 baseline was:

```text
67 failed, 5083 passed, 8 skipped
10 failed, 239 passed, 36 skipped, 16 deselected, 14 errors
```

The first final HS-131-15 gate found three current-diff regressions beyond that
ledger:

- `dictation_capture.py` exceeded the 600-line runtime concern budget;
- `journal.py` and `parent_run.py` exceeded the 300-line kernel concern budget;
- the old mesh adoption test still exercised the newly forbidden unadmitted
  construction path.

Production concerns were carved into `dictation_processing.py`,
`parent_terminal.py`, and `publication_transition.py`; the mesh test now proves
construction from the frozen admitted revision. All three guards pass.

The post-fix two-lane gate reported:

```text
65 failed, 5139 passed, 8 skipped
10 failed, 239 passed, 36 skipped, 16 deselected, 14 errors
```

Its only two current-diff names were stale monkeypatch locations caused by the
runtime concern carve. Both tests now patch `dictation_processing`, and the
combined five-regression set passes.

A final current-tree backend lane reported 66 failures. The three apparent new
names were unrelated Slack tests blocked behind one xdist worker's leaked
journal append lock after a timeout; all three pass together immediately in
serial (**3 passed**). No current-diff product failure remains. Four previously
inherited source-location failures are repaired by this story. Lane two varies
only in inherited live/browser/LAN failures and has no HS-131-15 product name.

## Kernel hygiene

Tests inspect parent, child, revision, warrant, claim, and receipt rows. They
assert that no audio, dictated/input text, prompt, completion, token stream,
rewritten body, API key, bearer token, or raw provider exception enters kernel
operations, journal events, parent metadata, or receipts.
