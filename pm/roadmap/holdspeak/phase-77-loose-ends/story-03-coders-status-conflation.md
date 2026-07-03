# HS-77-03 — The coders-status conflation dies

- **Status:** done
- **Severity:** MED
- **Depends on:** —
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)

## What

(The contract lives in the phase status doc's exit-criteria row; this
file carries the build notes and the Done record.)

## Test plan

- Story tests per the criteria row; the schema-sensitive guards
  (snapshot/matrix/serialization) updated per the documented recipes when
  they fire; full suite green at ship.

## Done

Shipped. Consumers verified first (the block was a dead contract: the
iPad never decoded it; the web gates on aftercare's flag); the flags
moved to their own domain (GET /api/desk/actuators/status, booleans only,
the HSM-14 credential rule kept); /api/coders/status is sessions-only;
the three pinning tests migrated. 53 slice-green; manifest 5/5; suite
3095/37. See [evidence-story-03.md](./evidence-story-03.md).
