# Evidence — HSM-19-05 — The proposals review queue: the split, made visible

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-19-05-proposals-review`. The
Wave-3 clients gain their surface: every actuator proposal for a meeting — wherever it was
created — is reviewable and decidable from the iPad, with honest states and the cloud mark
where approval executes.

## 1. The queue card (`CompanionShellApp.swift`)

- `proposalsCard(_:)` on the meeting digest (beside artifacts/aftercare; loaded on the
  same tap): per proposal, target · action, the hub's human `preview`, the status pill
  (proposed=warn, approved/executed=green, rejected/failed=red), and the proposal's own
  `error` when it carries one.
- **Approve / Reject only on `proposed`** — decided proposals render their state, never a
  dead button. Per-proposal busy state; a refused decision surfaces
  `ProposalDecision.error` (the hub's illegal-transition reason), never a silent miss.
- **The slack approve wears `Cloud · slack`** (the desk `EgressBadge` grammar — a label,
  never a sentence): approving a slack target executes immediately (the hub's consent
  model, HS-61 — by design, not fixed).
- The desk's `DioSendCard` stays as is: it already inserts a visible receipt before its
  own propose+approve. This card is the split for everyone else's proposals — the web's,
  live in-meeting ones, and 19-01's filed issues.

Screenshot: [`hsm-19-05-review-queue.png`](./screenshots/hsm-19-05-review-queue.png)
(`HS_SHELL_DEMO=proposals` — all four states, the cloud mark on both slack rows).

## 2. The audit-trail fix the proof surfaced

The live run showed an iPad decision landing as `decided_by=web-user` (the hub's default;
the Wave-3 client sent only `{decision}` while the desk link sends `ipad-desk`).
`HTTPDesktopClient+Proposals.swift` now sends `decided_by: "ipad-companion"`, and both
`ProposalsClientTests` body tests assert it — an iPad decision is attributable in the
actuator audit again (the Phase-56 audit-parity value).

## 3. The live-hub proof (real routes, scratch DB)

Two REAL proposals created through the 19-01 file-issue route (not seeds), then the
decision route the Approve/Reject buttons call:

```
1. GET proposals -> 200; [('github', 'proposed'), ('github', 'proposed')]
2. decide(approved)  -> 200; success=True, status=approved, decided_by=web-user  ← the gap §2 fixed
3. decide again      -> 400; error='illegal actuator proposal transition: approved -> approved'
4. decide(rejected)  -> 200; success=True, status=rejected
5. GET proposals -> 200; [('github', 'approved'), ('github', 'rejected')]
```

The connected simulator rendered that live queue (not a seed):
[`hsm-19-05-live-hub-decided.png`](./screenshots/hsm-19-05-live-hub-decided.png) — the
hub's real previews ("Open a GitHub issue in karolswdev/HoldSpeak: …"), approved and
rejected pills, above the aftercare card whose File issue chips created them. The
19-01 → 19-05 loop is closed end to end on one screen.

## Honest boundaries

- The Approve **tap** itself is not simulatable headlessly; the verb is URL-, body-, and
  decode-locked by `ProposalsClientTests` (incl. the new `decided_by` assertions) and the
  route behavior is live-proven above. The on-device tap — including a real slack execute —
  rides the 19-07 walk (W5).
- A slack proposal in the live proof would have needed a configured webhook; the executed
  state is layout-proven via the seed and the execute path is HS-61's production call site,
  unchanged here.

## Suites

`swift test` **425 passed / 8 skipped / 0 failures** (incl. the extended
`ProposalsClientTests`) · companion-shell simulator build (iPad Air 13-inch M4)
**BUILD SUCCEEDED** — both after the change.
