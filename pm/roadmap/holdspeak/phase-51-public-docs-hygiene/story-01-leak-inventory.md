# HS-51-01 — Leak inventory + vocabulary policy

- **Project:** holdspeak
- **Phase:** 51
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-51-02, HS-51-03, HS-51-04, HS-51-05
- **Owner:** unassigned

## Problem
The public-facing docs leak internal roadmap vocabulary, but there is no agreed line
between "a phase tag a user should never see" and "a legitimate product noun that
happens to look internal". Without that line written down, the scrub (HS-51-02)
over-reaches or under-reaches and the guard (HS-51-03) has no spec. The inventory is
the map both follow.

## Scope
- **In:**
  - A complete inventory of offending lines in **user/operator-facing docs** (the
    root `README.md` + `docs/*.md`, excluding `docs/internal/**` and
    `docs/evidence/**`), produced with the grep in the AGENT-BRIEF (`HS-[0-9]{2}`,
    `Phase[ -][0-9]+`, `PMO`, `closeout`, `the current roadmap`).
  - A classification of each hit: **banned** (phase tag, story id, process word,
    phase-relative tense) or **keep** (product noun such as `actuator`/`connector`;
    named architecture spec `MIR-01`/`DIR-01`; a deliberate contributor pointer).
  - The **fixed scope** decision written down: exactly which files are user-facing
    (in), which are internal/evidence/PMO corpus (out and never touched).
  - The chosen **banned pattern + word list** that HS-51-03 will encode, and the
    **allowlist** of legitimate terms.
- **Out:** the edits themselves (HS-51-02); the guard (HS-51-03); any code change.

## Acceptance criteria
- [x] A written inventory (a section in `current-phase-status.md` or a scratch file
      in this phase folder) lists every offending line with `path:line` and a
      banned/keep verdict. (`leak-inventory.md` — 20 banned hits across 6 in-scope
      guides + 1 optional out-of-scope hit + the KEEP MIR/DIR lines, each with a
      product-tense rewrite)
- [x] The user-facing-vs-internal scope is stated explicitly, including that
      `pm/roadmap/**`, `docs/internal/**`, `docs/evidence/**` are out.
      (`leak-inventory.md` §"Scope decision", which also rules `docs/assets/**` out
      of the guard scan)
- [x] The banned pattern/word list and the keep-allowlist (`actuator`, `MIR-01`,
      `DIR-01`, ...) are written down for HS-51-03 to encode.
      (`leak-inventory.md` §"Banned pattern + allowlist", with the honest
      bare-`phase` regex limitation noted)
- [x] `npm run build` n/a (no UI bundle touched); 0 `_built/` tracked.

## Test plan
- No code; this story is the map. Sanity-run the AGENT-BRIEF grep and confirm the
  inventory matches its output (no missed file, no internal-corpus file included).

## Notes / open questions
- The root `README.md` is expected to be already clean (only `actuator`). Confirm.
- `MIR-01`/`DIR-01` do not match the banned patterns; that is intentional. Keep the
  patterns narrow enough that they never will.
