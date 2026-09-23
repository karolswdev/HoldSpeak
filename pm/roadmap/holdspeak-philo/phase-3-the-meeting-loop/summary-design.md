# PHILO-3-02 — Summary seam design

Status: CHECKED by Muad'Dib 2026-09-23 — RATIFY-WITH-CONDITIONS (`checks/summary-design-muaddib.md`): seams (a) install and (b) queue build now; the corrected canvas was OWNER RATIFIED on 2026-09-23 ("Ratify, build it"), published at https://claude.ai/artifact/KnASxYRZc4UXkAiFU1z5zX. Seams (c) and (d) now build exactly as drawn. Authority: the owner's ratified A2 and D1–D4, 2026-09-23. No criterion is changed.

Tuesday: the architect imports one meeting, runs its summary once, reads the result where he started, and finds the same result after a restart.

## Product seams

1. Reproduce README's `uv venv` / `uv pip install -e .` in a separate environment. If the ordinary installation lacks the endpoint model client, make that client part of the ordinary installation. Do not require the local model compiler or speaker extras for a LAN summary. Retain the failure and corrected installation; the package fix is the first commit.
2. The deferred queue does not emit the live session's `intel_complete` or `intel_status` frames. Announce its durable running and settled meeting changes through the existing `notify_desk_changed` composition seam. The existing trailing debounce then refreshes the desk. Publication follows the database and route receipt writes; no polling loop or new bus protocol. Test a real admitted job through success, scheduled retry and terminal failure, inspecting the persisted row when its event arrives.
3. Carry the existing persisted meeting detail into the Arrival row: length, transcript, `intel.summary`, durable status detail, and the current queue leaf's retry facts. Keep the list light: read the existing `/api/meetings/:id` detail for the visible top three meetings and refresh those reads when the desk refreshes; ignore stale responses by meeting identity and read generation. Reuse the existing recovery job projection, extending it with the current leaf's `last_error` and retry facts already available to the queue service. Include that projection as `intel_job` in the existing meeting response so the Chair stays within Muad'Dib's three-HTTP-reads-per-refresh condition; the existing recovery endpoint uses the same projection. Preserve the list's status detail in the TypeScript adapter. Do not manufacture a summary or infer an executed host from current configuration. A queued successor with a failed attempt remains RETRYING even when its scheduled time has passed; a terminal error is FAILED. Both display the cause, and neither sits under the all-clear headline. Failed detail reads remain named errors, not empty summaries.
4. Keep the Arrival's section, ordering, row, Run and Open locations. Compose its existing SurfaceLedgerRow, SurfaceWell, MeetingSummarySlab and library Buttons. The summary is visible beneath its row when it lands; the transcript remains available in that row. The receipt is rendered in every resulting state. Before Run, the planned RouteDisclosure stays beside the verb; afterwards the durable RunAttempts names the actual contact. Canvas artboards at 1440 and 393 precede implementation. No new window or modal.

## Proof seams

Use ONE synthetic architect meeting with a retained source, known decisions, owners and actions, and a generated audio fixture. The real import worker must produce its duration and transcript. Replace the pangram only in the A2 atlas cases; sealed pass artifacts remain unchanged.

Repair actual `case.j4.*`, `case.j5.*`, `case.j6.*`, `case.j7.*` recipes: wait for completed import; configure the real LAN engine at `http://192.168.1.43:8080`; close its setup window before observing Arrival; trigger Run exactly once; declare a retained failure reply at the provider boundary for the failure cases; use the rig's real restart step with before/after summary identity. Add only the harness operations the existing vocabulary cannot express. Observe the scoped Arrival summary and actual receipt, not a generic string elsewhere on the desk.

All repaired seams receive meaningful fences, collected and run before the fix with failures retained, then run after the fix. Frontend fences drive the rendered transitions using production wire shapes. Actual atlas runs follow focused checks, one hub at a time, every face at 1440 and 393. Retain every observation and inspect each shot. The summary/restart chain uses the real LAN engine and records its identity. Provider failure substitutions are labelled as such.

Technical completion and usefulness are separate: report the retained summary, host and restart equality; then map each planted decision, owner and action to the generated output, including omissions. The owner's own sitting remains a separate observation, never claimed from this fixture.

## Bounds

Tenets 1–3: the smallest existing seams, no new workflow. Tenets 4–6: plain state labels, the library and the existing Workbench face. Tenet 7: a useful architect meeting, not transport-only material. Article III: planned and actual egress at the meeting row. Out of scope: every deferred COUNCIL item and stories 01, 03 and 04.

All product runs and tests use an isolated HOME. No owner database, keychain, microphone or native delivery; no tree-cleaning git verbs. Workers hold for SHIP; Astra owns the full suite, evidence capture, story flip, gate, push and PR. Muad'Dib checks the design and built closure evidence.
