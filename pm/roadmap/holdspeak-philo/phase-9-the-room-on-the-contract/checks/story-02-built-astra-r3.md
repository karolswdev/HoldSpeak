VERDICT: **RATIFY-WITH-CONDITIONS** — PR #684 at `588fb994`. **A–D are paid. One separate transport defect remains before merge.**

FINDINGS:

1. **P2 — `nudge.send` loses its comment receipt on both transports.** The real sender stores the comment URL, reviewer and timestamp. HTTP and MCP overwrite that receipt with the kernel receipt. The new shape fence checks the service result before this overwrite. Evidence: `holdspeak/web/routes/steward.py:228`, `holdspeak/mcp/families/project.py:1726`, `tests/unit/test_philo5_the_loop_r2.py:412`; [reproduction](/tmp/holdspeak-counsel-684-r3-nudge-response.py), [HTTP/MCP results and stored receipts](/tmp/holdspeak-counsel-684-r3-nudge-response.out). This probe uses the committed proposed-step fixture, the real sender and a canned `gh` process boundary. **Tenets 3/7; Article VI.**

2. **A–D paid.** One command-answer store remains. Publication, answer and receipt roll back together; retries succeed once and preserve the answer. Policy retries preserve their original terms on both transports. Approved children expire before their parent. Scheduled model drafts reach the provider boundary through the real inference runner with correct parentage. Evidence: `project_kernel.py:435`, `broker.py:253`, `steward_contract.py:199`; [nine collected fences](/tmp/holdspeak-counsel-684-r3-collect.log), [nine assertion failures on `7119cfd9`](/tmp/holdspeak-counsel-684-r3-red.log). Seven additional command-write rollback/replay probes also [passed](/tmp/holdspeak-counsel-684-r3-atomic-class.out).

3. **The stated replay exceptions are lawful.** Delivery answers its immutable row; stop preserves its original request acknowledgment after the run ends. Run and trigger return the same identities with current terminal state and receipts, without launching more work. These handles should not freeze their initial pending state. Evidence: `project_update_service.py:1955`, `steward_contract.py:222`, `:480`, `:565`; [independent replay results](/tmp/holdspeak-counsel-684-r3-nonusers.out).

4. **The restore-route test change is honest.** It now asserts successful archive setup through the service. The HTTP restore assertions remain intact, including `result_kind == "restored"` and `is_archived is False`. Authenticated archive-route coverage remains separately exercised. Evidence: `tests/unit/test_project_revision_law.py:483`.

Independent verification: [242 focused tests](/tmp/holdspeak-counsel-684-r3-focused.log) and [188 regression tests](/tmp/holdspeak-counsel-684-r3-kernel.log) passed. All four actual atlas cases passed on clean `588fb994`; all six committed shots were inspected. All six original r2 scripts were rerun: three passed unchanged; three reference removed internals and are covered by the ported fences.

CONDITIONS:

Preserve both native comment evidence and the kernel receipt in the transported nudge response. Fence HTTP and MCP response contents, and update the declared shape with the fix. **CI is not a condition.**

MISSED:

1. The nudge shape fence does not prove the full production path. My real watch→steward probe produced `no_waiting_reviews` and no proposed nudge; classify that separately from the seeded-step send proof. [Probe result](/tmp/holdspeak-counsel-684-r3-nudge.out).
2. Proposal acceptance logs a pipeline-observer database-lock warning and incurs about five seconds of delay. It also reproduces at `7119cfd9`; this revision did not introduce it. [Baseline proof](/tmp/holdspeak-counsel-684-r3-observer-baseline.out).

TUESDAY: Core retries and steward lifecycle now pass; the nudge send response still omits the comment details.

UNKNOWN: I did not rerun the full suite or all mutations, send an external nudge, generate with a real model, or exercise story 07 grants. No reviewed source or evidence files changed; the review worktree is clean.