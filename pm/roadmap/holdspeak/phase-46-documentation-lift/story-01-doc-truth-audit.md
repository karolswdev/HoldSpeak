# HS-46-01 — Doc truth audit & drift fix

- **Project:** holdspeak
- **Phase:** 46
- **Status:** done
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)
- **Depends on:** none
- **Unblocks:** HS-46-02, HS-46-03, HS-46-05
- **Owner:** unassigned

## Problem
Thirteen phases shipped since the last documentation pass (Phase 33). The docs
have accreted, and claims drift from the code (feature names, config keys, flags,
CLI commands, route names, counts like "14 plugins", model suggestions). You
can't reimagine the README or unify voice on top of statements that are wrong —
truth is the foundation. (Repo standing rule: docs must be grounded in live code;
canon wins over a drifted doc.)

## Scope
- **In:**
  - A short **audit doc** (`docs/internal/DOC_AUDIT_2026-06.md` or under the phase
    folder) inventorying every live doc (README + `docs/*.md`) with, per doc: its
    purpose, a freshness/accuracy verdict, and a list of concrete drift findings
    (each: the claim, the live-code reality, the fix).
  - **Fix the factual drift** found: counts (plugin count, supported types),
    config keys (e.g. journal/presence/pipeline knobs), flags + their current
    status (e.g. presence is now a config toggle, not env-var-only), CLI commands,
    route/anchor names, model suggestions, and any "coming soon"/"stub" language
    that's now false.
  - Verify cross-links + anchors resolve (the existing dangling-link guard) and
    extend the **doc-drift guard** if a cheap new check earns its keep (e.g. the
    advertised plugin count vs the registry).
- **Out:** voice/structure (HS-46-03); the README rewrite (HS-46-02); visuals
  (HS-46-04). This is *accuracy*, not prose polish.

## Acceptance criteria
- [ ] An audit doc lists every live doc with a verdict + concrete drift findings.
- [ ] Every factual error found is fixed (or filed as a real code bug, not
      silently "fixed" in prose) — claims match live code: counts, keys, flags,
      commands, routes, model names.
- [ ] Doc-drift guard + dangling-link/anchor check green; any new guard added is
      green and justified.
- [ ] No live doc claims a capability that doesn't exist, or omits a default that
      changed (e.g. presence config toggle, journal default-on).

## Test plan
- Unit: `uv run pytest -q -k "doc_drift or link or doc_guard"` (existing guards +
  any added).
- Manual: spot-check each high-traffic doc's claims against the code paths it
  names (config dataclasses, CLI, routes, plugin registry).

## Notes / open questions
- Keep the audit doc itself honest and durable — it's the map HS-46-02/03/05 work
  from, and a template for the next doc pass.
- Likely drift hotspots: the plugin count + table; presence enablement wording;
  the dictation pipeline/journal config keys; model suggestions in `MODELS.md`;
  any "TUI/menubar" residue (retired in Phase 32).
