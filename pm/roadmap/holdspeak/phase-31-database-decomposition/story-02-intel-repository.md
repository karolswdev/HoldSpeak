# HS-31-02 — `IntelRepository` extract

- **Project:** holdspeak
- **Phase:** 31
- **Status:** done (2026-06-02). Evidence: [evidence-story-02.md](./evidence-story-02.md).

## Goal

Migrate the deferred-intel cluster out of `MeetingDatabase` into `IntelRepository`,
following the HS-31-01 pattern. Verbatim move, facade delegates.

## Scope

- Move the intel cluster into `IntelRepository`: `intel_jobs`, `intel_job_attempts`,
  `intel_snapshots` — including the enqueue / `claim_*` / `mark_*` / attempt-recording
  methods that `intel_queue.py` depends on.
- Update `intel_queue.py` and other intel call sites to `db.intel.<method>(...)`;
  remove those methods from `MeetingDatabase`.
- No change to the job lifecycle, claim semantics, or attempt accounting.

## Test plan

- Rewrite the intel portion of `test_db.py` + any `intel_queue` tests to the repo API.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.

## Done when

- [x] Intel cluster lives in `IntelRepository`; call sites use `db.intel.*`.
- [x] Those methods removed from `MeetingDatabase`; full suite green (2062); ruff clean.
