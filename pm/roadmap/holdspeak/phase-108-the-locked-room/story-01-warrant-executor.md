# HS-108-01 - The warrant room - a real executor boundary

- **Project:** holdspeak
- **Phase:** 108
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-108-02
- **Owner:** unassigned

## The thesis

Raw desktop input must begin only after a process other than the ordinary
runtime independently accepts the exact broker-minted authority.

## Recipe

1. Add a small spawned executor reached through an anonymous duplex pipe.
2. Validate an exact message and request shape in the child.
3. Verify HMAC, policy version, operation ID, payload hash, target,
   placement, issue/claim/execution deadlines, and exactly one use.
4. Re-read focused-window identity inside the child immediately before
   importing any raw driver.
5. Consume the warrant on focus refusal, driver failure, or effect attempt.
6. Treat pipe loss or timeout as indeterminate and never retry.

## Acceptance

- Forgery, replay, payload swap, expiry, policy drift, malformed shape,
  and focus change never invoke the raw driver.
- A spawned-process test exercises the actual anonymous pipe.
- No TCP port, filesystem socket, or public execute endpoint exists.

## Test plan

`tests/unit/test_privileged_desktop_executor.py`, plus the effect fence's
raw-import assertion.
