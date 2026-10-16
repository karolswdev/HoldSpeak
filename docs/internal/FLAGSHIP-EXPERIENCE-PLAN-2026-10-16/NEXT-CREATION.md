# Next creation batch — retain a Thread task command

Bounded read-only triage, 2026-10-16. Subsequent reachability inspection in
`briefs/notice-settings.md` establishes that the Ambient proposal-button branch
is dormant: current non-learning frames use durable projection Review source.
That candidate is excluded from implementation; no live failure is inferred. Root requested this record while shipping
the first delivery. No product edits, tests, browser, build or owner-state reads.
This is source evidence and a proposed scope, not a reproduced live failure or
an implementation GO. Anchors describe current source and can drift.

Tuesday: the architect turns a conversation into a task, keeps the exact words
when creation is refused, and returns to the same Thread without losing newer
work. Tenet3 and Constitution VI. Existing composer, draft store and receipt
components suffice; no new conversation or command framework.

## Checked candidates

| Candidate | Current source evidence | Classification and disposition |
| --- | --- | --- |
| Thread `/todo` input and return | `web/src/desk/components/ThreadComposer.tsx:652` clears the draft before POST at659; both non-ok and thrown outcomes append strings at666/669. System rows are component-local at400; the real draft is Thread-keyed at385. | Still present, concrete loss mechanism. Recommend next. Ordinary return retains text/refs through the existing store; command acceptance currently bypasses that useful discipline. |
| Ask/Thread context choice reads | `web/src/desk/components/AskPanel.tsx:187` parses `/api/projects` without checking HTTP success and substitutes `[]` at194; those projects feed grounding choices at216. Thread mode read catches silently at472; prompt/guardrail/People helpers return `[]` at252/282/318. | Still present source candidates. Failed choices can read as no choices. Keep for a separate grounded-question job; no new live failure/geometry claim. |
| Exact Approve/Decline notice | `web/src/components/AmbientLayer.tsx:408` closes over the displayed card, awaits POST, then removes `cards[0]` through `dismiss()` at389/416; only `finally` handles rejection at417. Dismiss remains available at486 and Decline has no busy guard at477. Projection Dismiss already retains exact row/pending/refusal at390–406/441. | Still present source candidate. Do not reissue the already repaired projection Dismiss/journal exclusion. A newer-card race and missing proposal-specific failure remain source-inferred; need a bounded actual case before build. |
| Remote access Reload/Retry | `web/src/pages/cores/SettingsCore.tsx:778` and910 place write failures in shared error. Its Retry at1229 only calls `fetchRemote`; successful GET clears error at758. First-read Retry at924 is correct. | Still present naming/operation-ownership candidate. A read can establish current state, but cannot be reported as a retried write. Separate Settings job; preserve row grant refusals and one-time token behavior. |

## Recommended coherent owner job

**Create one task from a Thread and keep the unaccepted command.** The exact
current trigger is `/todo Send the platform plan` followed by Enter/Send while
the writer rejects or fails. Current code erases the session-backed draft first;
the only remaining UI is a local status string. This defeats the existing draft
store, which already survives window remounts and separates Thread identities
(`web/src/desk/threadComposerDrafts.ts:99`, `:118`).

Proposed behavior for root to settle with one populated actual-library pose:

- Keep the submitted text and original Thread identity until the writer returns
  its actual status. Pending belongs to that snapshot and blocks a duplicate
  submission, while later speech/newer work remains owned by the current draft.
- Clear only the accepted submitted draft; a newer draft is retained. A known
  refusal keeps the words and names the task locally. Return to another Thread
  and back preserves its words and exact failed subject.
- Reuse the existing Button/SurfaceState or ActionNotice and Thread draft store.
  A Retry must use the captured Thread/text, never whatever the composer holds
  later. Keep normal Send, refs, slash palette and source-opening behavior.

Concrete limit before promising transport-failure Retry: the current endpoint
accepts only `text` (`holdspeak/web/routes/threads.py:472`) and the service creates
a fresh tool-call and operation ID on every invocation
(`holdspeak/services/thread_service.py:870`, `:878`). A lost response therefore
does not establish that replay creates only one task. This batch can retain
words, expose the unknown outcome and permit inspection of the existing Thread
receipt. Root must settle any broader replay claim explicitly; no backend
idempotency retrofit is included in the three-file input-retention scope.

## Three-file implementation boundary and focused proof

1. `web/src/desk/components/ThreadComposer.tsx`: `/todo` acceptance/pending/
   refusal composition and exact captured command. Keep `/compact`, helper
   loaders, ordinary Send and shared UI species outside this concern.
2. `web/src/desk/threadComposerDrafts.ts`: only the smallest Thread-keyed command
   state needed for return/newer-draft ownership; preserve session-storage custody
   and the rule that an in-flight flag is never restored after reload.
3. `web/src/desk/__tests__/ThreadComposer.test.tsx`: real composer outcomes through
   the actual draft store; existing focused file, no broad suite.

Focused regression cases: pending command retains its exact words and duplicate
press does not submit twice; refused result/HTTP failure retains words; accepted
result clears only that submitted draft; newer typing/late speech survives a
late success or refusal; switching/remounting Threads cannot move failure or
Retry onto the new Thread; successful-empty command usage does not create work.
Use recorded real wire shape for any new backend-shaped fixture. Run collection
and this file only under the machine lock/isolated HOME once root grants build.
An actual 1440/393/narrow case must then prove the rendered task result, refusal,
return and input recovery. No new test run occurred in this triage.

## Keep healed; name unknown

Already represented in current source/tests: ordinary Send waits for acceptance
and keeps refused words (`ThreadComposer.tsx:792–802`; existing
`ThreadComposer.test.tsx:593`, `:605`); Thread drafts/refs survive remount per
Thread (`:428`), pending ordinary Send survives return (`:444`), and reload
rehydrates text without a stale sending flag (`threadComposerDrafts.ts:67`).
The prior audit's delivered Ask transmission/Keep lineage, grounded citations,
Thread reply/load recovery, Workbench exact Add/Coder recovery and Settings
preference/Calendar recovery remain closed as previously evidenced. This pass
neither reran nor invalidated them.

Unknown: actual `/todo` refused/pending/source-result geometry, provider outcome,
post-submit receipt visibility and transport replay semantics; current physical
input behavior and owner visual acceptance; whether Ask/helper unavailable poses
are frequent in normal use. No broad audit or speculative redesign follows from
those unknowns. Root settles the next actual direction after first release.
