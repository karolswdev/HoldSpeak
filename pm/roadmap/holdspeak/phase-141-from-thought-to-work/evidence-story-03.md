# Evidence — HS-141-03 Develop this thought

**Result:** done; final technical and owner-glass counsel **RATIFY**.

## Shipped contract

- The ordinary Chair starts a thought with one local action and opens its owned
  working Note. Speak's operational controls remain behind explicit advanced
  capture disclosure.
- Every ordinary Note exposes **Develop this thought**. Adoption is atomic and
  in place: it verifies the visible Note's content hash and modification time,
  creates no clone, preserves the original bytes as revision one, and files the
  same qualified Note in Inbox.
- The owned Note exposes its source-true **Original kept** cue and resumes from
  both the Note and the Chair's bounded unfinished list after reload.
- Editor writes are serialized against aggregate cursors. A conflict installs
  the authoritative current state and cancels queued stale work; authority
  epochs prevent late success or older conflict responses from regressing a
  newer parent DTO.
- Sync validates adoption provenance against the exact source Note/ref/raw body.
  Generic Note/adoption races return a named conflict rather than escaping as a
  server error.
- A foreground pullout or editor suppresses Chair capture, so the active work
  surface owns the only primary action at desktop and phone widths.

## Design and adversarial proof

The ratified design is
[`assets/hs-141-03-design.md`](./assets/hs-141-03-design.md). Technical counsel
required atomic no-clone adoption, shared-lock conflict behavior, exact sync
provenance, and serialized cursor-safe saves. Cold-owner counsel required one
editor host, direct recovery copy, a visible source reveal, phone-sheet/dock
clearance, wrapped raw material, and removal of the competing background
primary. Every amendment was recaptured against the rebuilt product bundle.

## Genuine owner walk

The [story-03 asset record](./assets/story-03/README.md) documents the fresh
temporary HOME/database provenance. The final run produced 11 screenshots at
1440×900 and 393×900, asserted exact viewport widths, and recorded zero console
or page errors. No fixture seed or synthetic populated Desk was used.

## Local verification

Run by the orchestrator on the assembled tree:

```text
uv run pytest -q \
  tests/unit/test_refinement_thought_service.py \
  tests/unit/test_web_routes_thoughts.py \
  tests/unit/test_web_routes_sync_primitives.py

43 passed in 7.23s

npm --prefix web run test:web -- \
  src/desk/chair/ChairHome.test.tsx \
  src/desk/chair/ThoughtEntry.test.tsx \
  src/desk/pullouts/NotePullout.test.tsx \
  src/desk/pullouts/editors/ThoughtNoteEditor.test.tsx \
  src/desk/components/InlineEditor.test.tsx

32 passed

uv run pytest -q \
  tests/uat/test_build_ledger.py \
  tests/unit/test_doc_drift_guard.py \
  tests/unit/test_product_copy.py \
  tests/unit/test_api_surface.py

36 passed in 2.40s
```

`npm --prefix web run build -- --mode development`, `uv run python -m
compileall -q holdspeak`, and `git diff --check` passed. The build emitted only
the existing Vite dynamic-import/chunk-size warnings. GitHub Actions was not
watched or used as a gate.

## Honest boundary

This story performs no model call and offers no AI question, context attachment,
completion, proposal, or external tool action. HS-141-06 adds the local
**Good enough** completion/reopen path before HS-141-04 introduces a model turn.
