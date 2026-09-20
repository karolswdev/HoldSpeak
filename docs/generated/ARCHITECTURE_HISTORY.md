# Why the architecture has this shape

Research source: `675401a857b85336d4acaa8c65383dfc9636e4c8`.
The commits below were inspected with `git log` and selected `git show` output.
Dates identify repository history, not release availability or owner acceptance.

| Question | Evidence | Architectural consequence |
| --- | --- | --- |
| Why is the Desk the product shell? | `049d12fc`, 2026-07-17, updated public guides and frontend architecture under Phase 95 and the Constitution | The older route-world guidance is historical; features open in the Desk contract. |
| Why are physics and surfaces shared? | `84ea9d8a` and `531cb684`, 2026-07-18, recorded window and Surface floors | New faces inherit interaction contracts instead of designing their own window behavior. |
| When did the kernel become concrete? | `a150036d`, 2026-07-26, introduced the broker and journal; `5347a340`, 2026-07-27, moved actuator egress through it | Kernel means an operation/authority substrate, not just the Process view. |
| Why does inference have child operations? | `45e737c1`, 2026-08-09, admitted invocation runner; `7adb98e9` and `1efbf0a5`, 2026-08-10/13, meeting/session/plugin adoption | Model work is correlated through admitted operations; business runners still own their outputs. |
| Why do assignments differ from model inventory? | `dcc36eb9`, 2026-08-21, added assignment authority, schema and tests; `64aca6e2`, 2026-08-26, added the assignment experience | Owning a model and selecting it for a capability are separate operations. Legacy routes require explicit migration analysis. |
| How did meeting imports join intelligence? | `d88d5009`, 2026-07-04, connected imports to the plugin chain; `f3546f8d`, 2026-08-23, moved installed plugins through the routed queue | Import and capture should converge on retained meeting work, but queueing is not completion. |
| Why separate observing a Coder from controlling it? | `de4c1c46`, `b121c6f7`, `86beae66`, 2026-07-07, separate attachment, arming and steering; `e35e0199`, 2026-07-26, adds tool-call Gate | Session presence, a reply grant and a tool decision are distinct capabilities. |
| Why not maintain another table of prose claims? | `33090cdb`, 2026-09-17, binds documentation claims to executable predicates | Extend the existing claims registry and preserve known-false findings rather than copying them. |
| Why lead with one meeting result? | `675401a8`, 2026-09-19, merges the Phase 201 charter; its status cites the Seven Tenets | The documentation programme must not delay the first useful observed job. |

## Terminology reconciliation

Desk is the operating surface. Workbench can also name a specific runnable
domain object; it is not a synonym for the whole Desk. A model profile, execution
engine, destination and capability assignment describe different facts. A
Thread, Agent identity, Coder session and Interview mode do not share one
universal conversation schema. See the domain and subsystem references before
renaming them.

## Historical authority

Older plans remain useful evidence of intent. Their existence does not make
their requirements accepted, implemented or released. The document inventory
preserves declared status and a disposition for each file. Current Constitution
and UX Canon outrank an older design plan. Executable disagreement remains a
named code or documentation defect, not a silent amendment.
