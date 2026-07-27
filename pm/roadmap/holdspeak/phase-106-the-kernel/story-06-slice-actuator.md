# HS-106-06 - Thin slice II — actuator egress

- **Project:** holdspeak
- **Phase:** 106
- **Status:** done
- **Depends on:** HS-106-05
- **Unblocks:** HS-106-07
- **Owner:** unassigned

## The thesis (the bar)

The first genuinely heterogeneous driver, and therefore the first
real test of the spine. Actuators differ from terminal input on
every axis that matters: the decision is **durable** rather than
immediate (a proposal can sit for a day), the effect is **outward**
(egress, Article III), and the authority question involves material
the owner must actually read before approving.

If the broker needs one `if` to serve both, the kernel claim is
already dead and HS-106-07 will only confirm it. This is the story
where the design is falsified or earns its name.

## Problem

`ActuatorExecutor` (`holdspeak/plugins/actuator_executor.py:56`) and
the proposal state machine implement propose/approve/execute in
their own vocabulary, with their own audit rows. The Phase-104 gate
implements the same shape again for tool calls. Two consent spines
for one constitutional article (Article V) means neither can be
strengthened without the other silently drifting.

## Recipe

1. **A kernel operation creates and links the EXISTING proposal.**
   There is no rival proposal system — that would be the double
   truth the migration rules forbid. `submit` admits the operation
   and links it to the proposal the actuator machinery already
   creates.
2. **`decide` advances the EXISTING state machine.** The kernel call
   is the entrance; the domain machine remains the authority on
   actuator states. Domain states stay domain data; only the small
   universal states project up.
3. **`ActuatorExecutor` stays the driver.** It is adapted, not
   replaced, exactly as `coder_steering` was in slice I.
4. **Existing audit rows project as receipts.** Historic actuator
   audit history becomes readable through `read` as receipt
   projections without being copied into the journal.
5. **Egress is honest at admission.** The operation's derived effect
   class names the destination and the data classes crossing the
   boundary, so the desk's egress badge is fed from the journal
   rather than from a per-surface guess. One badge, never prose.
6. **Durable decision semantics land here, not in the broker.** A
   proposal that waits a day, an owner who approves from a different
   session, a warrant minted at decision time rather than submission
   time — all of it must be expressible in the envelope and warrant
   the broker already has. Where it is not, the field is added
   **because a second real driver needs it**, which is the RFC's
   stated bar for generalization.

## Out of scope

- New actuators or new connectors.
- Changing what any existing actuator does.
- The connector `PermissionGate` sandboxing question — `PermissionGate`
  is not a security boundary and this story does not pretend
  otherwise; confinement is RFC §5b, deliberately later.
- Migrating the 13 census egress sites broadly. This slice proves
  the shape on the actuator path.

## Acceptance

- A real actuator proposal is created through `submit`, sits
  durably, is approved through `decide`, executes through
  `ActuatorExecutor`, and produces a receipt — end to end on real
  metal.
- A proposal REJECTED through `decide` produces a refusal receipt
  and never executes.
- A proposal approved after the target has moved on (stale expected
  revision) is refused by name — the immutable target binding
  holding under a durable decision, which is where it is hardest.
- Historic actuator audit rows are readable as receipt projections
  without duplication.
- **The heterogeneity check, stated as an acceptance criterion:**
  the broker modules gained ZERO driver-specific conditionals across
  slices I and II. Any envelope field added for actuators is used by
  a second driver or justified in writing in the evidence.
- The egress badge on the desk is fed from the journal for this
  path, and a screenshot shows it honest.
- The Article V shape is preserved exactly: propose, approve,
  execute — nothing became implicit.

## Test plan

- **Unit:** the actuator operation codec; durable warrant minting at
  decision time; stale-revision refusal.
- **Integration:** propose → wait → approve → execute → receipt, and
  the reject path, over real HTTP against a real spawned hub.
- **Live (evidence):** a real actuator firing at a real destination
  with the receipt read, plus one honest refusal.
- **Guards:** zero-conditional and line-budget census green after
  two heterogeneous drivers — this is the story where that guard
  first means something.
- **Full suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Chef's notes

- When the durable-decision requirement pushes back on the warrant
  model, that pushback is the point. Resolve it in the envelope and
  the warrant, not with a branch in the broker. If it cannot be
  resolved that way, write that down honestly — HS-106-07's kill
  criterion wants to hear it.
- The Phase-104 gate and the actuator proposal machine are two
  implementations of Article V. This story is the opportunity to
  make them one. Take it, but do not let "unify consent" grow into
  a rewrite of either — link and adapt.
