# Attention popup dismissal

Owner reports that the pictured Dictation needs review popup cannot go away.
Read-only live API observation: 13 dictation warnings already dismissed;19
more remain, first four with the same generic wording. Existing Dismiss
writes work but immediately surfaces the next identical historical row.
Tenets3/6: a dismiss control must let the owner resume work.

Settled behavior: Dismiss persists the visible row through the existing
presentation writer, then closes the popup presenter for attention whose
timestamps are no later than the dismissal. Keep this cutoff in sessionStorage
per tab, guarded for unavailable storage. Refresh/remount does not replay the
old backlog. Genuinely newer attention may show. Untouched older items remain
in the Attention reader with unchanged source state. No batch dismissal, no
source deletion, no global presence-setting change.

Show loading while the writer runs, and local refusal/Retry if it fails; do
not silently hide a failed write. Existing library Button and SurfaceState,
no new appearance or overlay. Preserve the doorless-projection safety.
Implement a narrow successful-result return from store.present rather than
reading a stale shared error. Filter also respects dismissed rows.

This is a behavior repair in the owner's shown face, not a redesign. Prove
multiple identical rows, refresh/remount, newer attention, failed write/Retry
and storage refusal. Live verification uses isolated state, never owner DB
fixtures. Hold for SHIP; root commits/merges/deploys.

## Owner amendment — useful interruptions

The owner questions whether this popup has a valid use case at all. Generic
dictation journal warnings do not earn an interruption: exclude all
`source_kind=dictation_journal` from Qlippy selection. They remain in journal
and Attention, with no changed records. Mixed feeds may show other genuinely
actionable sources. This is deliberately not a new warning taxonomy or a
new dictation notification. The original narrow Dismiss repair remains for
the other existing sources.
