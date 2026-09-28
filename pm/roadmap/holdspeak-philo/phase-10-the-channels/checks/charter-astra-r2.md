VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The dispatch boundary prevents duplicates, but recovery still needs a scoped kernel change.** I reran the real Room kernel and GitHub connector with a recording runner and a modeled send record. The original path dispatched twice; the proposed boundary reduced that to **one dispatch**. Immediate takeover settled UNKNOWN. However, the next replay raised `ProjectKernelRefused(interrupted)` instead of returning that result. With the real reaper run before takeover, the kernel became `indeterminate`, while the modeled send remained `dispatching`, with no delivery row.

   The cause is `holdspeak/services/project_kernel.py:388`: terminal states other than `succeeded` never reach the service. The `holdspeak/kernel/desk_broker.py:158` does not settle a send record; startup invokes reaping through `holdspeak/kernel/projection_stager.py:343`. Thus `pm/roadmap/holdspeak-philo/phase-10-the-channels/design/send-lifecycle.md:41` cannot work solely by reading the row inside the service. **Yes, that path must change.** [Probe results](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo10-astra-r2-p9lglqrl/result.json). **Tenets 3, 7; Articles V, VI.**

2. **The frozen GitHub “account” is a mutable connection reference.** `pm/roadmap/holdspeak-philo/phase-10-the-channels/design/send-lifecycle.md:7` freezes a `watch_provider_connections` ID. GitHub always uses `holdspeak/services/github_provider.py:220`, whose `holdspeak/services/github_provider.py:311`. Through the real provider, synthetic auth responses changed that row from `work-owner` to `personal-owner`; the proposed destination digest stayed identical. Rechecking the destination row therefore cannot establish the account that will post. Freeze the concrete host and login, and verify the effective CLI identity before dispatch. [Probe results](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo10-astra-r2-account-00_zeyfu/result.json). **Tenets 3, 7; Article XI.**

3. **Confluence’s title escapes both the frozen payload and the no-text-in-argv rule.** `pm/roadmap/holdspeak-philo/phase-10-the-channels/design/send-lifecycle.md:26` contains XHTML, while `pm/roadmap/holdspeak-philo/phase-10-the-channels/current-phase-status.md:67` still passes `--title <t>`. Running that modeled command through the real gated seam exposed the synthetic private title in its native receipt; the body digest does not bind it. Freeze title and body together. The captured help already offers `docs/internal/philo/phase-10/grounding/transport-probe.out.txt:23`; probe that transport before settling its shape. **Tenets 3, 7.**

CONDITIONS:

The scope is suitable for owner discussion, with this check attached. Do not describe findings 1–5 as fully settled or brief implementation workers until these three corrections are recorded:

- Specify send recovery and terminal replay across takeover **and reaping**, preserving one dispatch, one terminal receipt, and the corresponding history row. Cover both explicit `send_id` and the owner’s inline-send form.
- Bind the concrete GitHub identity.
- Include Confluence’s title in the frozen, private transport payload.

The design is otherwise proportionate to **Tenet 1**: saved destinations, one send lifecycle record, reused history, existing connector plumbing, and an explicit file writer. These corrections need small changes at those seams.

**Q1–Q4 are genuine product forks**, with the revised recommendations sound. **Q5 mostly restates the owner’s existing preparation ruling**; retain the recommended default without another grant screen. **Q6 is a genuine authorization/evidence choice**, but option (b) must leave remote delivery explicitly unverified at close. It cannot satisfy the real-send criterion.

MISSED:

Ranked by owner cost: a dispatched send whose history never settles after reaping; posting under a changed GitHub identity; a title exposed outside the frozen payload.

For the canvases, interpret “shows these bytes” carefully: a tired owner needs a readable preview derived from the frozen payload. Raw Mail JSON or Confluence XHTML would fail Tenets 3 and 4.

TUESDAY:

The pick–preview–Send flow fits his job; I would not yet trust its restart outcome or saved GitHub account.

UNKNOWN:

Reviewed `99e4f3b1..e10118ff` in a fresh, clean worktree; changed no tree files. The probes used real kernel/provider/connector code, modeled the unbuilt send records, and recorded effects without sending remotely. No screenshots, atlas runs or full suite were performed. Mail launch-context behavior, offline handling, actual service limits, and Atlassian response shapes remain unverified. The estimate remains provisional.