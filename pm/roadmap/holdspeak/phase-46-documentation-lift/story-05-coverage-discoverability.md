# HS-46-05 — Coverage & discoverability (feature → doc matrix)

- **Project:** holdspeak
- **Phase:** 46
- **Status:** done
- **Evidence:** [evidence-story-05.md](./evidence-story-05.md)
- **Depends on:** HS-46-01, HS-46-02, HS-46-03
- **Unblocks:** HS-46-06
- **Owner:** unassigned

## Problem
After thirteen phases, some shipped capabilities are under-sold or hard to find:
the dictation **journal + replay**, **actuators** (I/II), **desktop presence**,
the **first-run wizard**, **persistent correction memory**, the **config
cockpit**. A reader shouldn't have to know a feature exists to discover it. This
story guarantees coverage: every shipped capability is documented, discoverable,
and given a true, compelling hook.

## Scope
- **In:**
  - A **feature → doc matrix** (in the audit doc or `docs/README.md`): each
    shipped, user-facing capability → where it's documented → where it's linked
    from (README / index / guide). Gaps become fixes.
  - **Close the gaps:** ensure journal/replay, actuators, presence, the wizard,
    persistent memory, and the cockpit each have (a) a crisp hook in the
    README/highlights, (b) a home in a guide, and (c) a link from the index map.
  - A **discoverability pass:** the README "where to go next" + the `docs/README.md`
    map cover every journey; no orphan docs (a doc nothing links to) and no
    orphan features (a feature no doc covers).
  - Trim genuinely **stale/empty** content surfaced by the audit (dead "coming
    soon", retired-surface residue), keeping the set lean.
- **Out:** the deep prose/voice work (HS-46-03); visuals (HS-46-04). Coverage +
  discoverability + the honest hook for each capability.

## Acceptance criteria
- [ ] A feature → doc matrix exists and shows **no** shipped user-facing
      capability without documentation + a link.
- [ ] Journal/replay, actuators, presence, the wizard, persistent memory, and the
      cockpit each have a hook + a guide home + an index link.
- [ ] No orphan docs (unlinked) and no orphan features (undocumented); stale
      content trimmed.
- [ ] Every "cool fact" surfaced is true (cross-checked vs HS-46-01) — coverage
      didn't reintroduce overstatement.

## Test plan
- Manual: walk the matrix top-to-bottom; for each capability, click from the
  README/index to the doc and confirm it's real + current.
- Unit: `uv run pytest -q -k "doc_drift or link"` (no new dangling links).

## Notes / open questions
- This is the safety net that makes "sells the product" and "honest" both true at
  once — it's where bold framing (HS-46-02) gets reconciled with truth (HS-46-01).
- If a capability is genuinely not ready to advertise, say so honestly (or omit) —
  don't invent a hook for vapor.
