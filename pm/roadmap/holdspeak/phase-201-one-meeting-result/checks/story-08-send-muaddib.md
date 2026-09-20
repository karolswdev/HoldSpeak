# HS-201-08 — Interrupted-send descriptor assumption

CLI confirms claude-fable-5-1 session 416adc59-a8c4-43b4-9a49-e9db0e8faf36. Root accepts conditions; implementation pending.

**Check — Muad'Dib (claude-fable-5-1), continuation ruling on the INTERRUPTED SEND family for HS-201-08, 2026-09-20.**

- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran no tests, made no edits and used no workers.
- **What I read:**
  - `tests/integration/test_process_input_real_hub.py:2-24`, its imports;
  - the same file at `:250-285`, the select wait;
  - a grep of `holdspeak/`, `scripts/`, `uat/` and `tests/` for other `select.select(` callers;
  - `ulimit -n` in this shell.
- **Not read:** Luna's logs and the `fd_pressure.py` probe. Root's readings of them stand as root's claims.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The mechanism and classification (a) are correct.
   - `:266` calls `select.select([ready_read], [], [], 10)`. CPython's select() raises
     ValueError for any fd at or above FD_SETSIZE, which is 1024.
   - This shell's `ulimit -n` is 1048576, so the OS will hand out fds above 1023 to a
     worker that is holding many of them.
   - The pipe fd then falls out of range. The test dies BEFORE the `typed` read, the
     kill, or any reconciliation assertion.
   - So the red is in the wait primitive. It says nothing about the delivery contract.
   - Root's probe fits FD_SETSIZE exactly: 1050 open fds reproduces it, 900 does not,
     and KqueueSelector accepts 1053.
   - "Low fd numbers" is an invalid platform assumption, and the law under test is
     unchanged. Class (a) holds.
   - Root is right not to call it (c). Nobody has named a polluter, and
     two-serial-green cannot name one.

2. The proposed edit is the right size.
   - Replace `import select` with `import selectors`.
   - Register `ready_read` for EVENT_READ in a `with DefaultSelector()` block.
   - Call `select(timeout=10)`.
   - Leave every other line as it is. That covers:
     - the `typed` byte check;
     - SIGKILL and the exit-code assertion;
     - the landed-file poll;
     - `hub_state == "unknown"`;
     - the single reconcile probe;
     - the restarted processor.
   - My grep found no other `select.select(` caller anywhere in holdspeak/, scripts/,
     uat/ or tests/.
   - The product therefore has no FD_SETSIZE exposure of this kind, and this is the
     only test with the defect.
   - Tenets 1-3 are satisfied. There is no product edit, no skip, no xfail, and no
     weakened assertion.

CONDITIONS:
S1. The edit is confined to the wait.
    - It changes the import and the wait block at :264-267. Nothing else in the file
      changes.
    - The assertion's meaning stays the same: the selector must report readiness within
      10 s, AND the 16-byte read must equal b"typed".
    - An empty selector result must still fail the test. Do not make the timeout branch
      permissive.
    - Close the selector before the kill and reconcile steps, or keep those steps
      outside the `with`. The selector's own fd must not stay open past the wait.
S2. Proof goes through `dw evidence capture`, in this order:
    - the red that root already captured at 06:52:13Z under the 1050-fd probe;
    - the SAME probe, green after the edit;
    - the whole file, green and scoped, under an isolated HOME.
    - The probe must close every fd it opened in a `finally`, as root says it does.
      State that in evidence, because a leaking probe would itself pollute a shared
      worker.
S3. Evidence wording:
    - say "invalid platform assumption in the test's wait primitive";
    - do not say "flake";
    - do not claim any leak fix;
    - do not claim that fd pressure has been resolved.
S4. Ledger the real open question with a home.
    - In the final worksteal run, a pytest-xdist worker reached more than 1024
      simultaneously open fds.
    - Something in the suite or the product is accumulating fds in a long-lived process.
      Candidates:
      - hub servers not fully torn down;
      - SQLite connections;
      - Playwright pipes;
      - sockets from real-hub rigs.
    - This story does not diagnose it. It is NOT closed by this edit.
S5. The closing sequence restarts after any change to a test input, and F1-F6 stand
    unchanged.
    - Take a fresh T1.
    - Rerun the eleven docs commands under Python 3.12.
    - Run a new complete final run to 100% with zero failed and zero errors.
    - Amend the story and the PR body to show this as a separate repair family.

MISSED (ranked by cost to the owner):
1. The fd accumulation matters more than this test.
   - His hub is one long-lived process.
   - If a product path leaks fds per meeting, per restart-in-process or per conductor
     tick, he would see it as a hub that degrades after days of uptime. That is the
     Tuesday failure mode.
   - S4 must name it as a product-risk follow-up, and not only as suite hygiene.
   - One cheap first step for that follow-up: an fd count per test module under the
     worksteal run would show where the count climbs.
2. I raised the worksteal side effect in my scheduler ruling: worksteal changes which
   tests share a process.
   - This failure is the first instance.
   - Under `load`, the test probably landed in a worker with fewer open fds.
   - It is a newly exposed fault, which is the outcome K5 anticipated. Fixing the
     primitive and keeping the scheduler is the right response.
3. This test is in tests/integration/.
   - CI runs it on macos-14 without xdist (test.yml:180), where fd numbers stay low.
   - It would never have gone red there.
   - The PR's CI run cannot confirm this repair. Only the local high-fd probe does.
     Say so in the PR body.

TUESDAY: Not applicable. The edit touches a test's wait primitive, and no owner-facing
face or path changes.

UNKNOWN:
- I did not read Luna's collect and serial logs, root's probe, or the trace at
  full-worksteal.log:163-273.
- What is holding the fds, and whether the source is product code or rig code.
- Whether other tests fail in less visible ways under the same fd pressure.
  - One example is a socket or subprocess call that degrades without raising.
  - Root's complete final run is the only available signal.
- The two remaining families are still unchecked: the remote-settings pair and the
  daily-loop pair.
```
