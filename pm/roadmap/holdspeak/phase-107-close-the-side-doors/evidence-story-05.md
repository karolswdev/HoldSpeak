# Evidence - HS-107-05

- **Story:** HS-107-05 - The register, honestly — what remains and why
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-29T07:26:59Z

- **Command:** `uv run pytest -q tests/unit/test_kernel_effect_fence.py tests/unit/test_dictation_commit_boundary.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 66e53dc7fa22a16a1d8743c6ca1ee2703e25a111

```text
..................                                                       [100%]
18 passed in 1.23s
```

### Captured run — 2026-07-29T07:27:01Z

- **Command:** `git diff --exit-code --stat -- holdspeak/kernel/broker.py holdspeak/kernel/admission.py holdspeak/kernel/journal.py holdspeak/kernel/model.py holdspeak/kernel/executor.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 66e53dc7fa22a16a1d8743c6ca1ee2703e25a111

```text
(no output)
```

## The audit, independently run (fresh-eyes agent; none of the migrations were theirs)

All 21 selectors resolve to real source statements; no unledgered
sites; three stale census_line values corrected (D09, C02, C03).
The migration stories' STRUCTURAL claims held. Their STATUS claims
did not: **eight rows demoted.** Demotions are this story working,
exactly as chartered.

| rows | claimed | audited | evidence |
|---|---|---|---|
| T01, T02 | covered | **mixed** | `coder_steering_support.py:218-251` performs the raw tmux send as a preflight before `submit_process_input`; `coder_steering_routes.py:459-468` calls `deliver_keys` directly — reachable routes around the kernel |
| C02, C03, C05 | read | **mixed** | read-authority enforcement exists but is OPTIONAL: `activity_github.py:116`, `activity_jira.py:108`, and all eight `missioncontrol_bridge.py` entry points default `principal=LOCAL_OWNER` — an ambient asserted-owner route remains |
| N10-N12 | exempt_computation | **bypass** (disputed — see below) | the auditor reads Article XI.1 as making the model invocation itself consequential; clause 5 exempts surrounding computation, not the invocation |
| D09, N03, N04 | covered | **upheld** (reasons strengthened) | sole production `TextTyper.type_text` call sits inside the admission/warrant/recheck/receipt chokepoint; no raw sender route around `run_external_egress`; `_default_post` only reachable as the kernel-wrapped opener |
| A01-A09, A10 | bypass / dormant | **upheld** | closing condition added to every row: RFC §5b confinement (or deletion, for the A10 AppleScript helper) |

**The honest register: 21 total / 3 covered / 18 debt.** Every
mixed/bypass/dormant row now carries a non-empty closing condition,
asserted by the fence; a named-demotion test pins the eight demoted
rows as not covered. The retroactive corollary: the Phase 106
baseline was **2 covered of 40 (38 debt)**, not 4/36 — T01/T02 were
never fully covered. The corrected progression:
40/2/38 → (02) 31/3/28 → (03) 29/3/26 → (04) 21/3/18.

## The N10-N12 dispute — held for the owner, not absorbed

The phase charter and HS-107-04 ratified transcription as
clause-5-exempt computation (RFC §12 keeps it on the low-latency path
permanently). The independent auditor reads clause 1 as naming the
model invocation itself consequential regardless of where its output
goes. This is a constitutional interpretation question, and only the
owner interprets the Constitution. Pending that ruling the register
carries the CONSERVATIVE status (bypass — more declared debt, never
less); the owner may re-ratify the exemption at the sitting, which
restores exempt_computation with his authority behind it. Their
closing conditions are written either way: admit and receipt the
invocation while leaving response parsing on the low-latency path.

## Clause 6 status

The clause SURVIVES, governing 18 named debt sites: T01/T02 (tmux
routes not yet universal), C02/C03/C05 (principal must become
mandatory), N10-N12 (pending the owner's ruling), A01-A10 (§5b
confinement or deletion). It self-repeals only at an empty register.

## Historical documents

Earlier evidence files (02/03/04) record what was claimed at the
time and are NOT rewritten; this file and the charter carry the
audited corrections. Current-truth docs (charter, README,
docs/SECURITY.md) are reconciled to 21/3/18 — SECURITY.md's stale
40/4/36 is HS-107-06's explicit work list, recorded there.

Post-apply on this branch: unit suite 3403 passed, fence 9 passed,
spine diff exit 0.
