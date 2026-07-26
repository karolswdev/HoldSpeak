# HS-106-01 - Article XI ratified, with the migration provision

- **Project:** holdspeak
- **Phase:** 106
- **Status:** ready
- **Depends on:** none
- **Unblocks:** HS-106-04
- **Owner:** unassigned

## The thesis (the bar)

Every article in the Constitution earned its place by being the
thing the codebase is measured against when a shortcut looks
attractive. Article XI is the first article about *mechanism* rather
than *posture*, and that makes it the easiest one to write badly:
too loose and it blesses whatever exists; too tight and it becomes a
law the repo cannot honestly satisfy, which is worse than no law.

The council said exactly that. Sol's second pass
([archived verbatim](../proposals/kernel-council-sol-article-xi.md))
returned **do not ratify yet**: the drafted clauses turn the RFC's
destination into present-tense constitutional fact, and clauses 2
and 6 would be false on the day of signing and still false at the
end of this phase, because the RFC deliberately postpones broad
migration to rung 5. Two of its findings were re-verified directly
before this story was written and both hold:

- `holdspeak/web/routes/system/gate_routes.py:152` —
  `decided_by=str(body.get("actor") or "owner")`. The caller asserts
  who decided, defaulting to the owner, at the very route Phase 104
  shipped as the `decide` prototype. Clause 3 is false there today.
- `holdspeak/coder_steering.py:649-658` — the transport fires and
  the audit wrap follows, so an effect can succeed while its receipt
  fails to be written. Clause 2's receipt promise is not currently
  guaranteed even at the audited chokepoint.

**The owner ruled** (Article X — the owner alone amends): ratify
now, **with an explicit temporary migration provision** naming the
unmigrated cooperating paths as declared debt and forbidding agent
access to them. Sol's stated preference was to wait until clause 2
is materially true; that dissent is on the record and is not
overturned by being overruled.

The bar: after this story, a reviewer can point at any consequential
line of code and ask "which admission path, which principal, which
receipt?" and the answer is either a citation, a defect, or **a
named entry in the debt register** — never a shrug.

## Problem

The kernel design has been through four council passes and sits as a
DRAFT RFC. Its §10 Article XI is proposed but unratified, so every
story below it would be built against a document with no standing.
And the clauses as drafted cannot be signed honestly: they claim
present-tense properties the code does not have.

## Recipe

1. **Adopt Sol's amendments.** Clauses 1 through 5 are replaced with
   the council's rewritten text (paste-ready in the archived
   opinion). The substantive corrections carried:
   - Clause 1 stops using **process topology** as the definition of
     consequence — a browser-to-server hop is not a constitutional
     event, and a same-process authority mutation is. Consequence is
     defined by Article V, authority, process/machine control, model
     invocation, egress, and irreversibility. Model invocation and
     egress are named **separately**; the `model/egress` slash goes.
   - Clause 2 scopes the claim to what HoldSpeak **performs,
     brokers, or authorizes**, and requires a **terminal** receipt
     naming refusal, failure, and indeterminate outcome — because
     Phase 104 proved an admission row and an execution receipt are
     not interchangeable.
   - Clause 3 separates immutable binding from revocability:
     payload, target, and authority basis are immutable; the right
     to execute may still expire or be revoked.
   - Clause 4 replaces the aphorism with a rule — rights derive from
     authenticated principal and bounded delegation; only the owner
     approves, rejects, or delegates — and explicitly allows **the
     owner's direct gesture to supply approval without a redundant
     hold**, which is what keeps dictation fast.
   - Clause 5 keeps reads cheap but drops "owe the kernel nothing":
     authentication and read authority still apply, or a delegated
     agent could read outside its scope while remaining compliant.
2. **Delete the old clause 6.** Its first half restates
   constitutional supremacy, which `CONSTITUTION.md` already
   establishes; its second half ("regardless of how local or
   reversible") collides head-on with RFC §12, which says ordinary
   reversible local edits never pay remote-command ceremony. The
   nested-effects loophole stays closed by clauses 1, 2, and 5.
3. **Write the migration provision as the new clause 6** — the
   owner's ruling, and the price of ratifying early. It must do four
   things or it is a loophole with a nice name:
   - **Enumerate.** The debt is a checked-in register, not a mood.
     HS-106-03's effect ledger IS that register — the two are the
     same artifact, so the law and the test cannot drift apart.
   - **Fence.** No path silently joins the register; adding one is a
     deliberate, reviewed edit that the HS-106-03 test enforces.
   - **Forbid agent access.** No agent principal may reach a
     registered unmigrated path. This is the clause that makes early
     ratification survivable: the debt is the owner's to carry by
     hand, never a surface delegated to an agent.
   - **Expire.** The provision and the register die together, on the
     day the register is empty. A transitional clause with no
     sunset is permanent law wearing a disguise.
4. **The owner ratifies.** The owner reads the final clause text —
   the five amended clauses plus the provision — and says the word.
   Nothing lands in `CONSTITUTION.md` before that.
5. **Land the article.** Article XI enters
   `docs/internal/CONSTITUTION.md` in the voice and shape of
   Articles I through X: same heading form, same density, no RFC
   jargon leaking into constitutional language. Article X's
   amendment record notes the addition, the migration provision, and
   its sunset condition.
6. **Reconcile Article V explicitly.** The two articles
   cross-reference each other, so a future reader cannot find one
   without the other, and Article XI can never be read as a
   narrowing of consent.
7. **Flip the RFC.** `PLAN_KERNEL_OPERATION_BROKER.md` moves from
   DRAFT to RATIFIED, §10 carries the ratified text, and §11 gains
   the fourth council pass including **Sol's dissent recorded as
   dissent**. The RFC stops being the home of the law and becomes
   its rationale.

## Out of scope

- Any kernel code. This story is law and record only.
- Amending Articles I through X beyond Article X's amendment record.
- Re-litigating the six amendments adopted from Sol's first pass;
  they are settled unless new evidence lands against them.
- Building the register. HS-106-03 builds it; this story binds the
  law to it.

## Acceptance

- Sol's opinion archived verbatim (done — see the proposals file),
  and every finding answered in the evidence file with adopted /
  adapted / **rejected with a reason**. The rejected ones matter
  most: the owner overruled the do-not-ratify verdict, and the
  evidence must say so plainly rather than eliding it.
- The owner's ratification recorded verbatim in the evidence file
  (Article IX.4 — the owner's words, not a paraphrase).
- Article XI present in `CONSTITUTION.md`, matching the surrounding
  articles' voice; the doc voice guard green.
- The migration provision satisfies all four requirements above,
  and its sunset condition is stated as a testable fact (the
  register is empty), not a sentiment.
- Article V and Article XI cross-reference each other.
- The RFC reads RATIFIED with the council record extended and the
  dissent preserved.
- **The honesty audit ships with it:** a table in the evidence
  stating, per clause, whether it is satisfied today, at the end of
  Phase 106, or later — carried from Sol's audit and re-checked, not
  copied on faith.

## Test plan

- **Guards:** the docs voice/vocabulary guard over
  `docs/internal/CONSTITUTION.md`.
- **Link check:** `.githooks/dw check holdspeak` clean.
- **Re-verification:** the two Sol findings cited in the thesis
  re-run against the tree at ship time; if either has been fixed
  meanwhile, the evidence says so.
- **Evidence:** the council opinion, the answer table, the honesty
  audit, and the owner's verbatim ratification.

## Chef's notes

- The migration provision is the whole risk of this story. Written
  loosely it becomes the exception that swallows the Article;
  written with the register, the agent prohibition, and the sunset,
  it is a debt ledger with constitutional force. Do not soften any
  of the four.
- The clause most likely to be quietly dropped while drafting is the
  agent prohibition, because it is the one that costs something.
  Keep it. It is the reason early ratification is defensible at all.
- Record the dissent properly. A council whose refusals are absorbed
  into agreement stops being worth convening.
