# Evidence - HS-106-01: Article XI ratified, with the migration provision

**Story:** [story-01-article-xi](./story-01-article-xi.md)
**Date:** 2026-07-26

## The owner's ratification (Article IX.4 / Article X.1)

Recorded as given. The first is the owner's own words; the second and
third are the options the owner selected from a written choice, quoted
exactly as they were put to him.

1. **Verbatim, on convening the council:** *"Ratify, but also ask Sol
   to chime in. Ask him to be grounded in the notion of - we do not
   invent and over-complicate, but we certainly build for the future
   of an agent-connected workflow into nearly anything - and anything
   - including just being an awesome power user."*
2. **On the council's refusal**, presented with three honesty options,
   the owner chose: **"Ratify now with a migration provision"** —
   *"Article XI lands immediately, plus a temporary clause naming
   unmigrated paths as declared debt and forbidding agent access to
   them. You get the law today; the cost is scaffolding written into
   permanent law."*
3. **On the final clause text**, presented in full as it now reads in
   the Constitution, the owner chose: **"Ratify as written."**

The owner was shown, before ratifying: that the council's verdict was
*do not ratify yet*; that the council's stated preference was to defer;
and that clause 6 costs him the 36 unmigrated effect sites by hand,
because no agent principal may reach them.

## The council's findings, answered

Fourth council pass archived verbatim at
[`kernel-council-sol-article-xi.md`](../proposals/kernel-council-sol-article-xi.md).
Every finding is answered below. Nothing was silently dropped.

| # | Finding | Disposition | Reason |
|---|---|---|---|
| 1 | Clause 1 uses **process topology** as the definition of consequence; a browser-to-server hop would be constitutional while an in-process authority mutation would not | **ADOPTED** | Sustained on the code. The Desk's React/Python split would have dragged reversible shell bookkeeping into the kernel, contradicting RFC §12 and Article VII.3 (the arrangement persists). Consequence is now defined by Article V, authority, process/machine control, model invocation, egress, and irreversibility |
| 2 | `model/egress` compresses two distinct events | **ADOPTED** | Model invocation and egress are named separately in the ratified clause 1 |
| 3 | Clause 2's universal claim is false today and at phase close | **ADAPTED** | Scope narrowed to what HoldSpeak "performs, brokers, or authorizes" (the council's wording). The remaining falsity is carried explicitly by clause 6 rather than pretended away |
| 4 | "Produces a receipt" does not distinguish admission from execution; Phase 104 proves they are not interchangeable | **ADOPTED** | Clause 2 now requires a **terminal** receipt and names refusal, failure, and the outcome that cannot be determined |
| 5 | Clause 3 conflates immutable binding with irrevocable authority | **ADOPTED** | Payload, target and authority basis are immutable; the right to execute may expire or be revoked |
| 6 | Clause 4 is an aphorism where a rule is needed | **ADOPTED** | Rights now derive from authenticated principal and bounded delegation; only the owner approves, rejects, or delegates |
| 7 | "Only the owner decides" plus clause 6 would impose a second confirmation on the owner's own direct gesture, taxing dictation | **ADOPTED** | Clause 4 closes with "the owner's own gesture is approval; consent is not a second confirmation of what the owner just did" |
| 8 | Clause 5's "owe the kernel nothing" would let a delegated agent read outside its scope while remaining compliant | **ADOPTED** | Reads owe no admission and no receipt, but still owe an authenticated principal and read authority |
| 9 | Clause 6 is redundant with constitutional supremacy and collides with RFC §12 on reversible local edits | **ADOPTED** | Drafted clause 6 deleted entirely. The nested-effects loophole remains closed by clauses 1, 2 and 5 |
| 10 | **Do not ratify at all** until clause 2 is materially true (after broad migration and §5b confinement) | **REJECTED — by the owner, under Article X.1** | The owner ruled to ratify early behind the migration provision, having been shown the council's preference and the cost. The dissent is preserved verbatim in the archive and named in the RFC §11 council record and in the Constitution's amendment record. It was overruled, not absorbed |

## Honest-satisfiability audit (re-run, not copied)

The council's audit was re-checked against the tree as shipped — which
now includes HS-106-02 and HS-106-03, both of which landed **after**
the council wrote its opinion and change three of its rows.

| Clause | Today (2026-07-26, post 02 + 03) | End of Phase 106 | Later | Standing |
|---|---|---|---|---|
| 1 | **Satisfiable.** The topology error is removed; the definition rests on Article V, authority, control, model invocation, egress and irreversibility — all properties of the act | same | same | **Law** |
| 2 | **False**, and openly so. The RFC postpones broad migration to rung 5 | **Still false** — three thin slices are not universal migration | True for cooperating surfaces after rung 5; enforceable against untrusted code only after §5b confinement | **Law, with the falsity carried by clause 6** |
| 3 | **Substantially true and newly so.** HS-106-02 closed the caller-asserted-authority holes: `gate_routes.py` now derives `decided_by` from the principal, and `required_right()` is deny-by-default | True for kernel operations | True system-wide once every authority-bearing entrance uses warrants | **Law** |
| 4 | **True at the edge.** HS-106-02 landed typed owner/agent/node principals with immutable right sets; agents are refused `decide` by name, proven against a real agent process | same | same | **Law** |
| 5 | **Satisfiable.** Read authority exists as of HS-106-02 | same | same | **Law** |
| 6 | **True, and executable.** The register is `holdspeak/kernel/effect_ledger.json` (40 sites, 4 covered, 36 not), fenced by `tests/unit/test_kernel_effect_fence.py` | Shrinks as slices land | Expires with the register | **Transitional, self-repealing** |

**The one clause that is knowingly false at ratification is clause 2**,
and that is the whole reason clause 6 exists. Clause 6 is not a
softening of clause 2 — it is the enumeration of exactly where clause 2
does not yet hold, plus the rule that the owner alone carries that
ground.

Correction to the council's audit, on the record: rows 3, 4 and 5 were
written when the loopback deputy was open. HS-106-02 shipped before
ratification, so those clauses are in materially better standing than
the opinion states.

## What landed

- `docs/internal/CONSTITUTION.md` — **Article XI (The Kernel)**, six
  clauses; **Article V clause 5** added, pointing to it and stating
  that Article XI never narrows Article V; an **Amendment record**
  section noting the addition, the transitional clause, its sunset
  condition, and the overruled dissent.
- `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md` — status DRAFT →
  **RATIFIED**, with the Constitution named as the authority; §10
  rewritten from "proposed amendment" into the ratification record
  (what was refused, what was adopted, what the owner ruled, and the
  two properties that make early ratification defensible); §11 extended
  with the fourth council pass and its dissent.

## Verification

### Captured run — 2026-07-27T01:15:38Z

- **Command:** `.githooks/dw check holdspeak`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 05c8a4f52b91fe70133736fffbdd7b95118482bf

```text
ERROR pm/roadmap/holdspeak/phase-101-the-native-innards/evidence-story-04.md: evidence exists but matching story is not done
ERROR pm/roadmap/holdspeak/phase-106-the-kernel/evidence-story-01.md: evidence exists but matching story is not done
```

### Captured run — 2026-07-27T01:15:48Z

- **Command:** `uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_kernel_effect_fence.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 05c8a4f52b91fe70133736fffbdd7b95118482bf

```text
.........................                                                [100%]
25 passed in 1.33s
```
