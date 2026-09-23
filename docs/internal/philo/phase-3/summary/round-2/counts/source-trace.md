# PHILO-3-02 round two — queue count source trace

The stale `1 QUEUED` chip has two readers of the same durable count:

`GET /api/intel/summary` → `MeetingIntelService.queue_summary()` →
`IntelRepository.get_intel_queue_summary()`
(`holdspeak/web/routes/meetings/intel.py:67-69`,
`holdspeak/services/meeting_intel_service.py:137-138`,
`holdspeak/db/intel.py:2694-2736`).

The ambient HUD receives `runtime_queue` from
`build_runtime_queue_frame()` (`holdspeak/intel_queue.py:42-79`), which
also reads that repository summary. A real terminal failure therefore reads
`queued_jobs=0, failed_jobs=1`; a scheduled retry reads
`queued_jobs=1, scheduled_retry_jobs=1`. Before this correction, the stale
glass observation came from the frame stream: admission published the
queued frame, while the settlement path published `desk_changed` and did
not replace that frame. The correction at
`holdspeak/intel_queue.py:82-101` now publishes the fresh `runtime_queue`
frame after the durable transition.

The focused fence is
`tests/unit/test_philo3_summary_counts.py`. It admits through
`MeetingIntelService`, drains through `process_next_intel_job`, then checks
both the runtime frame and the `/api/intel/summary` service projection.
The pre-fix run failed because no `runtime_queue` frame reached the captured
broadcaster after the drain; the post-fix run emits the terminal and retry
counts from the same durable read.
