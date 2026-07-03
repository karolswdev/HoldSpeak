# Evidence — HSM-19-01 — Meeting aftercare: the file-issue action closes the loop

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-19-01-file-issue`. The read half
merged pre-open (PR #155); this closes the story: the accepted-item **File issue** action,
the inline repo row, and the honest proposed state — proven against a live hub.

## 1. The action UI (`CompanionShellApp.swift`)

- **Accepted-only gating:** the "File issue" chip renders only when
  `item.reviewState == "accepted"` (the hub 400s anything else — the button never offers
  what the hub would refuse).
- **The inline repo row** (no modal): a mono `owner/name` field + **File** + cancel,
  opened per item; the repo is remembered for the session so filing three items types it
  once. Busy/disabled states honest; a 400 maps to the accepted+repo reason, other codes
  surface numerically, unreachable is named.
- **The proposed state:** on success the item wears the `proposed` pill (the same
  `statusPill` grammar as artifacts). Approval is a separate act — the review queue
  (19-05), never this button.
- **The prose note died:** "Accepted actions become issue proposals you approve" is now
  the affordance itself (the no-prose rule).
- Demo seeds: `HS_SHELL_DEMO=aftercare` marks item a1 accepted;
  `=aftercare-filing` opens the repo row (layout proof). New screenshot-run affordance
  `HS_SHELL_OPEN_MEETING=<id>` lands on a meeting's digest without a tap (the
  `HS_SHELL_TAB` pattern).

Screenshots: [`hsm-19-01-file-issue-affordance.png`](./screenshots/hsm-19-01-file-issue-affordance.png)
(the chip on the accepted item only) ·
[`hsm-19-01-file-issue-row.png`](./screenshots/hsm-19-01-file-issue-row.png) (the inline row).

## 2. The live-hub proof (real routes, scratch DB, no seeded UI)

A real `MeetingWebServer` over a scratch temp DB (two meetings; `c1` accepted, `c2`
pending), loopback :8123 — the owner's config/DB untouched:

```
1. GET aftercare -> 200; open=2, accepted=['c1']
2. file-issue(c1 accepted) -> 200; success=True, proposal.status=proposed, id=eb7a28bb…
3. file-issue(c1 again)    -> 200; idempotent=YES (same id)
4. file-issue(c2 pending)  -> 400; error='Only an accepted action item can be filed as an issue'
5. GET proposals -> 200; queue=[('eb7a28bb…', 'proposed')]
```

Check 5 is the 19-05 handshake: the filed issue is sitting in the review queue the next
story renders.

The connected simulator rendered that live hub (not a seed):
[`hsm-19-01-live-hub-aftercare.png`](./screenshots/hsm-19-01-live-hub-aftercare.png) —
`Desktop · 127.0.0.1` chip, the real meeting list, the live digest with **File issue** on
the accepted item only. (The live artifacts card also renders the seeded decisions
artifact with a dimmed 0-ring — `record_artifact` seeded no confidence; `nil` renders
dimmed, never invented. Honest at the edge.)

## Honest boundaries

- The **tap itself** (File → the POST leaving a real iPad) is not simulatable headlessly;
  the client verb is URL-and-decode-locked by `AftercareClientTests` (a `StubProtocol`
  route on the exact path) and the route behavior is live-proven above. The on-device tap
  rides the 19-07 walk (W1).
- Approving the filed proposal is 19-05's story, deliberately not this button.

## Suites

`swift test` **425 passed / 8 skipped / 0 failures** · companion-shell simulator build
(iPad Air 13-inch M4) **BUILD SUCCEEDED** — both after the UI change.
