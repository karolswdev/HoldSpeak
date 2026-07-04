# Evidence — HS-82-01 — Design: the conveyor and its consumption seam

**Status:** done (2026-07-04).

## The design exists and its claims are verified

[`docs/internal/MISSION_CONTROL_DESK.md`](../../../../docs/internal/MISSION_CONTROL_DESK.md)
pins the bridge shape (§1), the conveyor UX and polling stance
(§2), the sessions/events rendering rules (§3), the approval leg's
route through the native `decide_proposal` + gated-connector
machinery (§4), and the joint-proof legs the counterpart's
WLA-13-05 will cite (§5) — every claim carrying the
verified/cited/decided mark discipline of the counterpart
contract.

Stories HS-82-02..05 are re-pinned in this same commit: each cites
the design-doc section it implements.

## Verified live on this desk (2026-07-04, dw 1.9.0)

Run in the delivery-workbench checkout
(`~/dev/code/delivery-workbench`):

```text
== dw version ==
__version__ = "1.9.0"
== feed ==
feed_schema: 1
project: work-log-automation | phases: 14 | next: WLA-13-05
== sessions ==
sessions_schema: 1 | registry: ok | records: 5
== events tail 2 ==
2026-07-04T16:57:40Z	contract_generated	-	-
2026-07-04T16:57:40Z	gate_pass	-	-
```

The declared schema versions (`feed_schema` 1, `sessions_schema`
1) match what the CLI emits on this desk; the correlation field
list in the doc's declaration section matches the records
observed. The next actionable story the feed names — WLA-13-05 —
is the counterpart story this phase exists to unblock, which is
the kind of detail you could not make up.

## Decisions this story owns, recorded in the doc

Bridge routes and status envelope (§1); project map =
`~/.holdspeak/delivery_workbench.json`, no new config surface
(§1); CLI resolution order inherited from the Phase-12 pack (§1);
30 s subprocess timeout, injected runner (§1); 15-second
single-flight conveyor poll owned by the conveyor slice (§2);
approval leg rides `db.actuators` + `decide_proposal` + a
two-argv-prefix gated connector, argv from stored payload only
(§4); iOS and pi compatibility notes stated up front.
