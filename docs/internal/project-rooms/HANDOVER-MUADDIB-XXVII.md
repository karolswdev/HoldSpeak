# Muad'Dib handover XXVII — 2026-09-24 night, Phase 5 built 4/4; the owner's review of the rehearsal is the last open item

Read with `docs/internal/TWO-BRAINS.md`, `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/final-summary.md`, `current-phase-status.md`, `pm/roadmap/holdspeak/BACKLOG.md` (the PHILO-5 follow-up sections). XXVI holds the day's first half (Phases 3–4 closed).

## Where the tree is

- **Phase 5 The One Service Layer: 4/4 merged** (01 `6e707ff3`, 02 `c4d46498`, 03 `9c653937`+`29380711`, 04 `6162239f`), exits 1–4 flipped, `final-summary.md` written. **Exit 5 open:** the owner reviews the rehearsal shots (https://claude.ai/artifact/Q6AqpXtUmtTQgrrR9WhzKM); on his word the phase closes as "rehearsed, owner-reviewed shots" (never a sitting). Both brains on every story; every bounce paid; the Astra→Muad'Dib and Muad'Dib→Astra checks recorded under `checks/`.
- **The contract:** `holdspeak/operations.py` (17 descriptors, `bind` at `runtime/composition.py`, `invoke`, `authorize` with `owner_only`), `docs/generated/operations.json`, `scripts/residual_census.py` + `docs/internal/philo/phase-5/residual-set.json` (334 → 320), the MCP roster 225 → 228 (`meeting.import` Owner only; `monday_brief.shelf`, `shelf_read`), the proxy proxy-only. The rig: `op` step kind, headless mode, `scripts/philo5_pairs.py` (18 pairs), `philo5_his_words.py` (the rehearsal driver), the Codex seams (port published, token persisted, `scripts/astra -c`).
- **Open by design:** the Article XI admission debt (his ruling); already-open Desk refresh after an agent write (he accepted a reopened read); usefulness (partial as measured).
- **BACKLOG (real, owner-visible, not fixed):** a failed import shows SAVED; the zero-decided toast (and it covers the summary at 393); the brief count/time conflict (5 vs 6; 18:19 vs 6:19 PM) now visible on every fresh read; a raw pipeline item counted; the S4 ~1 s empty decision body at 393; the rename sends `name`; two broke rows for one missing read; the shelf enum drift; MCP discoverability (25 reads to file a review decision).
- **Main CI:** the heavy jobs (~1 h+) were never waited on today, per the owner's ruling; the 44-failure inherited baseline at `497d90f3` is on file; main's own `api-reference.json` drift was regenerated in #638.

## Next session, in order

1. His word on the rehearsal → flip exit 5 as "rehearsed, owner-reviewed" → close Phase 5 (a one-line commit on the status + README).
2. Then, before any Phase 6: the BACKLOG's PHILO-5 follow-ups that lie on his morning path (SAVED on a failed import; the brief count/time conflict; the zero toast covering the summary at 393) — small, canvas-free repairs with red-pre-fix fences; a bounded tree pass, not a phase, unless he charters one.
3. His ruling on the Article XI question (does a desk decision write act under Article V?) — it decides whether decisions get kernel admission + receipts.
4. The four Constitution amendments (Phase 201) still unruled.

## Laws learned today (add to briefs)

- Every migrated operation ships a three-state compatibility table; never narrow accepted inputs; never slice an already-limited list.
- A boundary lives in the operation, before any side effect, fenced with a genuinely issued credential from the wrong side; the tool description says "Owner only."
- Every braced result shape runs its real producer in a fence.
- The gate refuses amending a done story's evidence file (corrections → `checks/`); read `git log -1` after every gated commit (a refusal was missed once when piped through grep).
- An Astra lane may start from main before a records PR lands: verify at counsel what the lane's story file carried.
- Never symlink `node_modules` into a worktree/archive and then run `uv` (the build hook follows the link; four incidents in two days).
