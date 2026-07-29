# HS-107-03 - The subprocess family — five sites

- **Project:** holdspeak
- **Phase:** 107
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-107-05
- **Owner:** unassigned

## The thesis (the bar)

Five sites that shell out, and they are not one thing:

| id | site | shape |
|---|---|---|
| C01 | `connector_runtime.py:125` | connector subprocess (mixed) |
| C02 | `activity_github.py:132` | `gh` read |
| C03 | `activity_jira.py:124` | tracker read |
| C04 | `plugins/gated_connector.py:224` | gated connector subprocess (mixed) |
| C05 | `missioncontrol_bridge.py:38` | `dw` read |

The bar: **triage before migration, the same discipline as the egress
family.** C02, C03 and C05 look like *reads* — running `gh`, a tracker
query, and `dw` to learn facts. Article XI clause 5 exempts reads from
admission and receipts, but not from authentication and read
authority. Spawning a subprocess to perform a read is still spawning a
subprocess, and the honest question is whether the consequence is the
*process control* or the *information*.

Get that judgement right and the register tells the truth. Get it
wrong and either every `dw context` call pays kernel ceremony, or a
connector quietly shells out unrecorded.

## Problem

Any of these can execute an external binary with the runtime's ambient
authority, and nothing admits or records it. `connector_runtime.
PermissionGate` covers two of them partially and says of itself that
it is honest enforcement, not a security boundary.

## Recipe

1. **Triage.** For each site: is the consequence *executing a process*
   (consequential — Article XI clause 1 names process control
   explicitly) or *obtaining information* (a read)? Argue each in
   writing. The `dw` bridge and the `gh`/Jira readers are the arguable
   ones; the connector subprocesses are the clear consequential cases.
2. **Migrate the consequential ones** through a typed operation
   deriving the binary, arguments and working directory at admission,
   with the receipt naming what ran and its outcome — including
   non-zero exit and the indeterminate case.
3. **Reads stay cheap** but must still pass principal and read
   authority (clause 5's second sentence). A read that shells out is
   not exempt from *who is asking* — an agent principal running `gh`
   against the owner's credentials is precisely the confused-deputy
   shape HS-106-02 closed at the HTTP edge.
4. **The two `mixed` sites are the priority.** Mixed means partially
   covered, which is the worst state: it reads as protected and isn't.
   Migrating them must leave **one** decision, not the kernel's plus
   `PermissionGate`'s.
5. **Arguments are payload.** Bind them immutably at admission —
   a decision that could alter the argv after approval is the
   payload-swap Article XI clause 3 forbids.
6. **Remove each site from the register in the same commit** as its
   migration or re-classification.

## Out of scope

- Replacing `gh`, `dw`, or any connector.
- The connector plugin API.
- §5b confinement — these sites can still be called directly by
  in-process Python after this story, and that stays true until
  confinement.

## Acceptance

- All five resolved: migrated, or re-classified as a read with an
  argued reason and read-authority enforcement.
- The two `mixed` sites end with exactly **one** policy decision each,
  census-proven — not the kernel's *and* the gate's.
- A migrated subprocess proves: success receipt, non-zero-exit receipt,
  and an indeterminate outcome that is not blindly retried.
- Argv immutability proven — a decision cannot alter what runs.
- An agent principal is refused a subprocess it has no right to,
  by name.
- Register shrinks to match; fence green without loosening.
- Spine byte-unchanged (`git diff --exit-code`, exit 0).

## Test plan

- **Unit:** triage classification; argv binding; exit-code receipts.
- **Integration:** the two mixed sites, proving single-decision.
- **Live (evidence):** a real connector subprocess with its receipt; a
  real failure; an agent-principal refusal by name.
- **Census:** one-decision proof; register consistency.

## Chef's notes

- `missioncontrol_bridge.py` runs `dw` — the delivery rails' own CLI.
  If that pays admission ceremony, the conveyor gets slower for no
  consent benefit. It is very likely a read; argue it and move on.
- The mixed sites are where a reviewer will assume safety that isn't
  there. Fix the assumption, not just the code.
- Non-zero exit is not failure of the *operation* — the operation
  succeeded in running something that returned non-zero. Receipt the
  distinction; it matters when the owner reads it back.
