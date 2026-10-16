# Thread lane — build report

Status: built, held for SHIP. Root owns the live captures and the final done call.
Worktree: `/Users/karol/dev/tools/wt-thread-ask-refinement-20261015`.
Branch: `feat/thread-ask-refinement-20261015`. Base: `9e45b3319`.

## Built

Thread opens at 660 × 700 by default, with the existing saved-size contract.
Its rows now sit in one paper SurfaceTraffic. Speaker facts are 12px mono;
user text is 13px UI and assistant text is 14px UI. The existing body remains
the transcript scroll owner and keeps follow-tail behavior. Message IDs and
`.thread-row-assistant .thread-row-body` annotation anchors remain in place.

Normal and inline editing use PadGadget. Title and annotation comment use
StringGadget. Each writer retains one MicButton and its existing append or
replace behavior. Thread composers use the original functional append path
with `mic={false}` on the pad, so a later capture result appends to the latest
draft and mic failures retain their visible recovery controls. Main Send is
primary; Stop keeps its existing abort writer. Draft persistence, acceptance
handling, @ and slash completion, and composition Enter behavior are covered
by the focused checks.

Inline editor blur checks the whole group, so transfers to Send, Cancel or
mic do not cancel the editor. User text has an explicit library Edit action.
First load uses SurfaceState loading. An absent detail says Thread not loaded
with real load Retry and the supplied Close callback. Failed/interrupted
answers use SurfaceState and existing regenerateThread, with exact server
diagnostics folded under Details. Branch position/count stays passive; the
arrows that only reloaded the same path are withheld.

Thread modes use FilterTokens, keeping recipe cache/order and click-active
unbind. Root authorized a small extra library seam: optional emptyLabel on
FilterTokens/StripMenuButton. Thread uses Choose mode when no mode is bound;
other callers retain their first-choice fallback. There is no new None choice.
The lane removed the left state rails and local all:unset Button skins.

Shared styles: `web/src/desk/surface/patterns/conversation.css`, scoped to
`.conversation-reading` and `.conversation-composer`. Ask imports these styles.
The narrow header stack uses the existing surface container at 520px.

## Focused proof

Collection: `.tmp/thread-ask/thread-list-final.log` — 171 named tests.
Run: `.tmp/thread-ask/thread-run-final.log` — 8 files, 171 tests passed.
Both commands run through `.venv/bin/python .tmp/thread-ask/locked.py`, with
an isolated HOME, machine lock, and `--maxWorkers=2`.

| File | Collected/passed |
| --- | ---: |
| ThreadComposer.test.tsx | 69 |
| ThreadPullout.test.tsx | 21 |
| ModeTabs.test.tsx | 5 |
| threadCompaction.test.tsx | 5 |
| ThreadToolRows.test.tsx | 48 |
| threadWindowName.test.tsx | 4 |
| askai.app.test.tsx | 11 |
| surface/__tests__/filterTokens.test.tsx | 8 |

Added direct coverage for internal editor focus transfer and pointer Send,
external blur cancellation, composition Enter, truthful first-load state,
load Retry/Close, failed-turn regenerate, user Edit/branch writer, passive
branch count, and the unbound menu caption with unchanged default fallback.
Existing draft/ack, tools, compaction, window naming, route and stream checks pass.
`git diff --check` is clear.

## Runtime limits

This worker did not claim browser, real speech, 1440/393 screenshots or a live
loop. Root owns those captures, the page build and quick check. Follow-tail,
annotation selection geometry, held decision/interview/call surfaces, long
content, mobile hit areas, and the folded mode menu still need the root's
actual product read. No model/API/backend behavior changed. No files staged
or committed.

## Mic guard alignment — root-authorized scope amendment

Changed only `scripts/ux_canon_scan.py` and `tests/unit/test_ux_canon_scan.py`
for this follow-up. Added `MIC_HOST_AUTHORITIES`: four exact path and own-tag
label needles for Ask's prompt, Thread's draft, Thread's inline editor, and
Thread's annotation comment. These opt-outs are accepted only when existing
`covered(offset)` finds an explicit MicButton in the same component. General
opt-out behavior remains strict. `MIC_ALLOWLIST` stays at its existing 24
entries; the ceiling file was not edited.

The 21 new focused cases cover each field with a same-component mic, without
a mic, with a mic in another component, with an unrelated nearby field, and
with the same label in another path; the last case checks the four authorities
are exact and present in the current source tree.

Collection: `.tmp/thread-ask/thread-mic-collect.log` — 66 tests collected.
Run: `.tmp/thread-ask/thread-mic-run.log` — `66 passed in 3.34s`.
Both use isolated HOME and the machine lock through locked.py, restricted to
`tests/unit/test_ux_canon_scan.py` and `tests/unit/test_ux_canon_ratchet.py`.
The unchanged mic ceiling is 0; the ratchet passed, so the live mic count is 0.
No product changes, stage or commit in this follow-up. Root owns the other
quick-check guard findings.
