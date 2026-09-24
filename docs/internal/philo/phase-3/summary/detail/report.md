# PHILO-3-02 summary detail backend lane

The real MeetingService and MeetingIntelService reads now carry the current
intel job leaf in `intel_job` for both meeting list and detail payloads. The
recovery response uses the same seven-field job projection and retains its
planned route and run receipt fields.

The projection reports `running` for a claimed producer job, `succeeded` for a
settled success, and `failed` for a terminal failure. It reports `retrying`
only when the current queued leaf has a durable failed predecessor with a
`scheduled_retry` attempt event. The status stays `retrying` after the stored
retry timestamp is due. Enqueue reasons do not populate `last_error` unless
the producer recorded a failed predecessor, so an initial enqueue remains
ordinary `queued` work and a manual successor exposes its producer state
without a copied failure. Error text and attempt counts come from the queue
row; no attempt is inferred from copy or clock.

The fixture `tests/fixtures/philo3_summary_wire.json` was emitted from the
real import, queue admission, bound claim and provider boundary for
imported/off, running, success, retry and terminal failure states. Every case
uses the retained WAV import producer, the deterministic meeting id
`m-philo3-summary`, and the same two imported transcript segments. Each case
retains the full list, detail and recovery reads, including `planned_route`,
`run_receipt`, and `last_refusal`. After the successful local execution, the
real profile and assignment services change the current plan to
`cloud.example`; its durable receipt still records the actual `same_device`
host. The fixture test mints those cases again and compares the complete wire
after normalising only volatile ids and timestamps, so the host, causes,
statuses, attempts and receipt outcomes remain fenced.

The manual-after-failure fence also records the producer's `reserved` successor
(`awaiting_parent_terminal`) with zero attempts and no retry cause. The
first/manual enqueue remains ordinary `queued` work. This keeps the wire
truthful when the producer parks a user retry behind its failed parent.

Frontend handoff: use the complete fixture as the transition source. The
success case deliberately has `planned_route` host `cloud.example` after the
assignment change while `run_receipt.attempts[0].host` remains `same_device`.

Pre-fix evidence is retained in `pre-fix-collect.txt` and `pre-fix-failure.txt`:
all four original producer fences failed with `KeyError: 'intel_job'`. Post-fix
collection and run tails are retained beside them. The focused matrix passed
56 tests, including route, receipt, recovery, and HS-172 wire checks.

Unknown: the Arrival frontend has not yet consumed this wire in this lane, and
the real LAN completion/restart walk remains with the orchestrator.
