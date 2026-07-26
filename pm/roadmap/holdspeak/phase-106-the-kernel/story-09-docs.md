# HS-106-09 - Docs — the kernel at the entry points

- **Project:** holdspeak
- **Phase:** 106
- **Status:** ready
- **Depends on:** HS-106-08
- **Unblocks:** HS-106-10
- **Owner:** unassigned

## The thesis (the bar)

A kernel nobody can find is a private convention. This story puts it
at the doors people actually walk through, and — harder — makes the
docs tell the truth about **what the kernel does not yet cover**,
including the migration provision's debt register.

The bar: a reader arriving cold can answer three questions from the
entry points alone. What is admitted through the kernel? What is
not, and why? And when something goes wrong, where is the receipt?

## Problem

Phases repeatedly ship real capability whose only description lives
in a story file. Worse here: the kernel's security claim is
**narrowed to cooperating surfaces** until RFC §5b confinement
lands, and a doc that omits that narrowing is not a simplification,
it is a false claim about a security boundary.

## Recipe

1. **`docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md`** — the kernel
   as a named component: the four caller calls, the executor plane,
   the journal-as-truth and bus-as-projection rule, and a rendered
   mermaid of one operation's life from submit to receipt.
2. **`docs/internal/CONSTITUTION.md`** — already carries Article XI
   from HS-106-01; this story adds nothing to it and verifies the
   cross-references still resolve.
3. **`docs/internal/SECURITY.md`** (or the boundary doc it lives in)
   — the narrowing stated plainly and early: the kernel is an audit
   and consent boundary for **cooperating code**; it is not a
   sandbox; `PermissionGate` says so about itself and the raw
   transports are public functions. Name the threshold at which the
   claim strengthens (§5b confinement, before untrusted or
   agent-authored code executes). The debt register is linked here.
4. **`USER_GUIDE`** — beside the steering material, in the owner's
   terms rather than the RFC's: what gets held and asked about, what
   just happens, where receipts appear, and what the PR
   follow-through loop does. No syscall vocabulary on a user page.
5. **`README.md`** — one paragraph, leading with what the reader
   gets, not with the architecture.
6. **Truth-audit every claim on the shipped tree.** The HS-104-06
   method: each sentence checked against the code as merged, not
   against the story's intent. A doc claim that outran the
   implementation is a defect fixed here, in either direction.
7. **The debt register is documented as a register**, with its
   sunset condition, so a future reader understands why some paths
   are outside the kernel and that this is recorded rather than
   overlooked.

## Out of scope

- New capability of any kind.
- Rewriting the RFC. It is rationale; HS-106-01 already flipped it.
- Marketing language. Positioning canon governs voice, and the
  kernel is plumbing that earns its keep by being invisible.

## Acceptance

- All five entry points touched, each claim truth-audited against
  the shipped tree with the audit recorded in the evidence.
- The cooperating-surfaces narrowing appears at the security entry
  point **before** any strong statement about what the kernel
  prevents.
- The mermaid renders.
- The debt register is linked and its sunset stated.
- Doc voice and vocabulary guards green (they have refused this
  repo's prose before — expect it).
- No user-facing page uses `submit`, `decide`, `warrant`, or
  `principal` as user vocabulary.

## Test plan

- **Guards:** doc voice/vocabulary, link check, mermaid render.
- **Audit (evidence):** claim-by-claim table, each with the file and
  line that makes it true.
- **Full suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Chef's notes

- The security page is the one to write last and most carefully. It
  is the page where an enthusiastic sentence becomes a lie about a
  boundary.
- If a claim is awkward to write honestly, that awkwardness is
  usually a real gap in the implementation. Fix the gap or narrow
  the claim; never smooth the sentence.
