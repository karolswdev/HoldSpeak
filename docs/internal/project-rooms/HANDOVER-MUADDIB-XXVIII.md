# Muad'Dib handover XXVIII — 2026-09-24 night: the method, and the two roads the owner asked for

Read with `docs/internal/TWO-BRAINS.md`, XXVII (Phase 5 closed), `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/final-summary.md`, `pm/roadmap/holdspeak/BACKLOG.md` (PHILO-5 follow-ups), and `pm/roadmap/holdspeak-philo/PHASE-6-7-CHARTER-DRAFTS.md` (this session's proposals, unratified).

## The owner's ask (verbatim, 2026-09-24)

"Let's write a handover to work the same way on the morning path repairs? And... rolling more and more capabilities of our platform through this native mcp way? So we can, one day, drive it fully via MCP? (aka, new slice of mcp)"

## The method ("the same way") — what Phases 3–5 settled

1. **Charter from evidence, not taste.** A phase opens from a ledger the previous phase measured (a closure run, a census, a counsel's MISSED list). Every story names its Problem with code lines, its edges/states, its acceptance boxes, its rig case at 1440 and 393, and its effort as a council-style estimate.
2. **Both brains, every artefact.** Muad'Dib authors → Astra checks (or the reverse); nothing authored is acted on unchecked; checks are recorded under `checks/` verbatim; a BOUNCE is paid in a round, a RATIFY-WITH-CONDITIONS is paid in the same commit; the orchestrating session alone merges. Astra's `claude -p` self-checks are the canonical channel but the orchestrating session's counsel is the one that counts for the merge.
3. **Design before build where a verb or a word moves.** Canvas from the real library species, both widths, exact ASD-STE100 strings, fixtures from the REAL producer (`_compose`), the owner ratifies on the canvas (AskUserQuestion is the fastest way to get his rulings). Repairs (an existing state drawn honestly, a library species bug) need no canvas.
4. **Fences red first.** Every repaired seam has a fence that failed on a `git archive origin/main` copy with the branch's tests overlaid; structural invariants get deliberate mutations; "Unknown tool" / missing-symbol failures are never counted as red; every migrated operation ships a three-state compatibility table (base, round one, built); a declared result shape runs its real producer.
5. **The rig proves durable state; the browser proves the face.** `op` cases (headless, ~2.7 s, registry inside the owning hub via `/api/mcp`) for outcomes; browser cases at both widths for what he sees; `readable_text` (visible, in viewport, unobscured) not text containment; face verdicts never claimed by `op`.
6. **Lane law.** Scoped tests, isolated HOME, never a serial full suite (CI runs it); shots from glass tests only with `HOLDSPEAK_EVIDENCE_WRITE=1`; the rig takes `--out`; `git status` clean of `pm/roadmap/holdspeak/` after runs; never symlink `node_modules`; a worktree per lane, removed after merge; `git log -1` after every gated commit (the gate can refuse silently under a grep).
7. **Merge law (the owner's ruling).** Merge on the other brain's lifted verdict + green scoped fences + the fast CI jobs; the heavy jobs (~1 h) are not waited on; the 44-failure inherited baseline at `497d90f3` is the comparison.
8. **Records.** The phase status is the canon; `final-summary.md` closes with both brains' verdicts per story, the pre-fix reds per story, and the ledger of what he still cannot do; his sitting is "rehearsed, owner-reviewed shots" unless he sits; memory + a handover at every session end.

## Road A — the morning path repairs (PROPOSED Phase 6 "The Honest Morning", bounded)

From the PHILO-5 follow-ups, the items ON HIS MORNING PATH, each canvas-free (an existing idiom drawn honestly) with a red-pre-fix fence and a rig/browser case at both widths:
1. A failed import shows SAVED (`intelBadge.ts:26`; `ChairHome.tsx:265` never passes `import_failed`) → the existing failure idiom.
2. The brief head vs receipt count (5 vs 6; `briefEgress.tsx:43-52` vs `ChairHome.tsx:875-886`) and the two time formats (`GENERATED SEP 25 18:19` vs `6:19 PM`; `routes/monday_brief.py:47-58`) → one count, one format.
3. The `MEETING READY · N open · 0 decided` toast: no zero token (UX-CANON A.8) and no overlap of the summary/capture bar at 393 (`AmbientLayer.tsx:175`, `intelligenceAttention.ts:95-96`).
4. The raw pipeline item counted in the brief (`monday_brief_service.py:500`) → human producer wording, consistent count.
5. Two broke rows for one missing decision read (`routes/decisions.py:58-61`) → one cause, one row (fixes the op/browser parity FAIL 2:1).
6. The S4 ~1 s empty decision body after Done at 393 (`DecisionPullout.tsx:69-71` suspected) → render the saved text at once.
Out: the Info-window rename (`name` ignored — needs a decision on the field, small but a contract question), the shelf enum drift (Road B), the Article XI ruling (his). Estimate: 3–4 engineering days, two lanes in parallel (Muad'Dib 1/2/4; Astra 3/5/6), one closing chain on the rig (the Phase 4 exit-1 case + the Phase 5 rehearsal re-run) — his review of the shots.

## Road B — the next MCP slice (PROPOSED Phase 7 "The Desk on the Contract")

**The census at main (residual-set.json, 320 identities: 256 MCP, 64 HTTP):** desk 46 · project 42 · people 17 · thought 16 (create/save/read done; the rest) · provider 13 · cadence 11 · workbench 10 · model_library 7 · concierge/decision_record/inference_assignment/meeting/reaction/scheduled_recording/watch 5 each · settings (HTTP) 5 · ask/heartbeat/interview/plugin_job/recipe 4 each · projects (HTTP) 4 · coder/follow_through/kb/practice_recipe/settings/zone 3 each · the rest ≤2.

**Recommendation: the desk primitives family first (46 identities: notes, artifacts, knowledge, zones, the remaining decision verbs, `desk.verb`).** Why: "everything is a DeskPrimitive" is the platform's own law; it is the largest family; it is what he touches 90% of the time; its operations are uniform (list/get/create/update/delete/verb per kind) so one descriptor pattern pays many identities; and it finishes what Phase 5 started on decisions (delete/status/supersede). Then **projects (42)** — the Room, the connectors, the steward — his second job. People (17) after: it has its own store and custody rules (keychain) and deserves its own boundary story.

**Shape (the Phase 5 pattern, four sequential stories):** 01 the primitive contract — one descriptor per (kind, verb) generated from one table, bound at composition, HTTP + MCP + resources over it, the `desk.*` generic tools kept as compatibility entries, the hand-wired branches retired, compat tables per kind, owner-only where a verb writes; 02 the remaining decision verbs + zones + `desk.verb` + the Article XI question answered by his ruling (admission where he rules it acts under Article V); 03 the atlas: `.op` siblings for the desk cases in `atlas.json` (the Phase 2 graph has them) and the equivalence run; 04 the owner asks in ordinary words for a desk job (file a note into a zone; find it; attach it to a meeting) through Codex — rehearsed, owner-reviewed shots. Estimate: 10–13 engineering days sequential, provisional until 01. **Toward "drive it fully via MCP":** after desk + projects the residual set drops below ~180; each later phase takes the next family by count; the day the residual set is empty is the day the platform is one contract with three transports.

**His decisions (for AskUserQuestion when he is ready):** D1 the next slice (desk primitives / projects / people); D2 Road A before Road B, in parallel, or after; D3 the Article XI ruling (a desk write acts under Article V → admission + receipts, or not); D4 whether the closing use of Road B is Codex again or his own client.

## Laws learned this week (carried)

See XXVII §"Laws learned"; plus: a charter's baseline is a census pinned to a commit with stated counting rules, never a grep; a lane may start from main before a records PR lands — verify at counsel.
