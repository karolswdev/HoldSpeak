# PHILO-3-02 queue seam — Astra verification

The queue now calls the existing `notify_desk_changed("meeting", id, "update")`
after its committed claim and after its executor returns with durable state
and receipts. A recovered executor announces its settled result too. The
existing claim-refusal exception carries its meeting identity so a durable
refusal can announce the correct row. The notification helper preserves the
existing rule that an observer failure cannot undo a committed write. No new
frame shape, polling loop, or Arrival implementation is introduced.

Four fences admit jobs with `MeetingIntelService.run_intelligence`, then drain
the real queue. Database, broker, route admission, binder, claim and settlement
are real. The shared harness substitutes the provider and unrelated plugin
and router helpers. The refusal fence clears a real assignment through
`InferenceAssignmentService` after admission; it does not replace the binder.
Each notification observer reads the durable meeting, current job and receipt.

Astra independently ran these four tests before the fix: **4 failed**, exit 1,
because no notifications arrived. [Complete output](astra-pre-fix-raw.txt).
After reviewing the implementation, Astra collected and ran the new fences
plus `test_phase200_intel_drain.py`, `test_intel_queue.py`, and
`test_meeting_deferred_admission.py`: **77 collected, 77 passed in 32.53s**.
[Collection](astra-post-fix-collect-raw.txt), [run](astra-post-fix-run-raw.txt).

Commands used a new isolated HOME for each invocation:

```sh
HOME=$(mktemp -d) uv run --no-sync pytest --collect-only -q tests/unit/test_philo3_summary_queue.py tests/unit/test_phase200_intel_drain.py tests/unit/test_intel_queue.py tests/unit/test_meeting_deferred_admission.py
HOME=$(mktemp -d) uv run --no-sync pytest -q tests/unit/test_philo3_summary_queue.py tests/unit/test_phase200_intel_drain.py tests/unit/test_intel_queue.py tests/unit/test_meeting_deferred_admission.py
```

The worker independently collected and passed the same 77 cases; its command
and output are retained in `post-fix-focused-collect.txt` and
`post-fix-focused-run.txt`. No existing test was changed to accept the new
behavior. There is no observed a/b/c test fallout in these focused runs.

This proves the queue-to-notification seam. It does not prove a rendered
Arrival transition, a real LAN summary, restart identity, or usefulness. The
full suite and actual atlas closure remain part of the continuation after
the owner ratifies the corrected canvas. The story remains in progress.
