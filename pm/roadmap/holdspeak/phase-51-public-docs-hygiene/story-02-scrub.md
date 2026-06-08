# HS-51-02 — Scrub user-facing docs (phase-relative -> product-tense)

- **Project:** holdspeak
- **Phase:** 51
- **Status:** done
- **Depends on:** HS-51-01
- **Unblocks:** HS-51-03, HS-51-04, HS-51-05
- **Owner:** unassigned

## Problem
User/operator-facing docs narrate the product by its build history: "Phase 9 shipped
the connectors", "Periodic tick (HS-17-05)", "the HS-19 closeout". A new reader does
not know what a phase or a story id is; the references read as half-finished and
carry no meaning for them. The inventory (HS-51-01) marked exactly which lines to
fix and which to keep.

## Scope
- **In:**
  - Remove every **banned** reference from HS-51-01 from the user/operator-facing
    docs, rewriting phase-relative statements into product-tense so the meaning
    survives. Examples grounded in the live tree:
    - `docs/CONNECTOR_DEVELOPMENT.md` "Phase 9 shipped ... phase 11 ...", "Phase 13
      additions", "the current roadmap" -> describe the connector contract and the
      runtime gates as features, no phase tags.
    - `docs/DEVICE_PROTOCOL.md` "(HS-17-05)", "HS-17-08 / HS-17-13", "Phase 14 is
      plain `ws://`", "Phase 15's tunnel layer" -> "HoldSpeak's device link is plain
      `ws://` on loopback today; a tunnel layer (Tailscale / Cloudflare) terminates
      TLS ...", drop the story ids from the table.
    - `docs/INTELLIGENT_TYPING_GUIDE.md` "from the HS-19 closeout" -> "a known-good
      local profile".
    - `docs/RELEASING.md` "the Phase 50 evidence" -> "the captured release evidence".
  - Keep legitimate product nouns (`actuator`, `connector`, `artifact_generator`)
    and the named specs `MIR-01` / `DIR-01` exactly as they are.
  - **Run the `humanizer` skill over every doc edited in this story** and apply its
    fixes (no em/en dashes, plain and direct), not just an eyeball pass.
- **Out:** the guard (HS-51-03); the `DOCS_STYLE.md` rule (HS-51-04); the internal
  corpus (`pm/roadmap/**`, `docs/internal/**`, `docs/evidence/**` — never touched);
  restructuring or rewording beyond the vocabulary fix.

## Acceptance criteria
- [x] Every banned reference from the HS-51-01 inventory is gone from the
      user/operator-facing docs; a re-run of the grep over those docs is empty.
      (case-insensitive sweep of `README.md` + `docs/*.md` returns no in-scope hits;
      see evidence)
- [x] Each rewrite preserves the original meaning (no dangling clause from a deleted
      tag); product nouns and `MIR-01`/`DIR-01` are untouched.
      (`docs/README.md:78-79` MIR/DIR lines verified intact)
- [x] The `humanizer` skill was run over every doc edited in this story and its
      fixes applied (no em/en dashes; plain and direct). (skill invoked on all 15
      rewritten passages; audit found no AI tells, no new em/en dashes)
- [x] Existing doc guards green (drift, dangling-link, image-ref):
      `uv run pytest -q -k "doc_drift or doc_guard or link or doc"` -> 75 passed, 2 skipped.
- [x] `npm run build` n/a (no UI bundle touched); 0 `_built/` tracked.

## Test plan
- `uv run pytest -q -k "doc_drift or doc_guard or link or doc"`.
- Manual: re-run the AGENT-BRIEF grep over the user-facing docs; output is empty.
- Manual: read each edited section as a brand-new user; the feature is clear without
  knowing what a phase is.

## Notes / open questions
- Voice: the `humanizer` skill is a required step here, not advice (no em/en dashes,
  no rule-of-three, plain and direct). Run it on each touched file.
- Rewrite, don't amputate: a phase reference that carries TLS/posture meaning is
  reworded, not deleted.
- HS-51-03's guard goes green only after this story lands.
