# The Protocol Notion — how a HoldSpeak UAT sitting is shaped

**Derived 2026-07-08** from the proof artifacts this repo already accumulated:
the Phase-67 dogfood `PROTOCOL.md`, the live phase-closing walks
(`scripts/walk_*.py`, `scripts/rails_walk_*.py`), the spoken-meeting e2e, and
the couch-walk runbooks (`HSM-16-06-WALK.md`). Those walks are the closest thing
the project has to UAT that *worked*; this doc distills why, and hands the shape
to the Phase-1 harness and the Phase-3 packs.

## The sitting shape (nine patterns that already worked)

1. **A beat-structured spine, not a checklist.** Every walk that closed a phase
   was a short ordered march of 6–8 numbered beats, each one
   *instruction → expectation → verdict*, printed as it ran (walk_hs85 = 6,
   Phase-87/90 = 8). The dogfood `PROTOCOL.md`'s flat ~58-check list is the
   anti-pattern — it "sat on the shelf." The guided site enforces the march.

2. **Stage, then walk.** Each walk opened by inducing the world (start a worker,
   import a fresh transcript, arm a grant, spawn a pane) and *asserting it live*
   before the first human beat. That preamble is exactly the UAT
   recipe-plus-verify-probe, lifted out of each hand-rolled script's top.

3. **Control-vs-treatment for every LLM feature.** Run the same prompt with
   grounding OFF then ON and assert the treatment output names a repo-specific
   token the control cannot know (hs87: "BLUEBIRD" / "Friday the 13th, 3:47pm"
   vs "I don't have access"; hs88: a filename present in treatment, absent in
   control). A no-LLM pass alone is declared insufficient — it hides broken
   features. **Every LLM capability in a pack gets a control beat.**

4. **An honest-failure beat closes the sitting.** Deliberately break the world
   mid-run (kill the worker, recycle the pane, dead endpoint) and assert the
   product degrades *correctly and fast*: the offline door reads offline, a
   forced run refuses in under five seconds naming the node, no hang. "Refuse
   fast, by name" is the pass bar — not "it worked."

5. **Structural verdicts for non-deterministic output.** Assert an artifact of
   the right *type* rendered (a `<svg>` mermaid, an action-item checklist, a
   decision *or* an open question) and judge it on substance — did it surface
   the decision / owner / risk — never on literal wording. The spoken-meeting
   e2e's whole philosophy.

6. **Every beat is a capture.** A screenshot into the run's shots dir *and* a
   printed provenance line (badge text, refs resolved, worker completions
   before→after) so the beat proves *where* it executed, not just a green tick.
   The badge ("mesh · walk-edge", "On-device", the egress scope) is asserted
   content, not decoration.

7. **Freshness discipline.** Never replay against a fixed fixture — reroute/intel
   dedup off the transcript hash, so a stale input silently no-ops ("deduped").
   Recipes must produce novel state per application, or idempotently re-verify —
   never falsely pass on a stale cache.

8. **Isolation preamble + teardown finally-block.** Run under an isolated HOME
   (the dogfood `_home` pattern), capture prior state, and in a `finally`:
   restore it, delete the walk's recipe/profile/meeting, kill the worker's
   process *group* (so `uv run` children don't orphan). A sitting leaves zero
   residue and never touches the real `~/.config`.

9. **The press-play device runbook (HSM-16-06).** For the device surfaces: a
   pre-flight block (hub LAN-bound, device paired with host+port+token, build
   installed on an *unlocked* device via the headless-signing recipe), then N
   labelled checks each with an EXPECT and an explicit CONTROL, and a fill-in
   trace table. Time-boxed (~15 min) and explicitly a bug-hunt. This is the
   shape the phone/iPad legs of every three-surface scenario inherit.

## What the old artifacts could NOT do (the gaps the harness closes)

Every one of these is a Phase-1 capability, named here so the sitting shape and
the rig stay in step:

- **Repeatability.** Each walk hand-rolled its staging inline with no named
  recipe and no idempotency contract — two runs a month apart were not
  guaranteed comparable. → the recipe layer with a verify probe (HSU-1-02).
- **Per-surface verdicts.** Every existing artifact proved *one* surface
  (walk_hs85 and the spoken e2e are web-only Playwright; HSM-16-06 is the lone
  cross-surface runbook, a hand-filled markdown with no shared record). Nothing
  cast a verdict *per surface* so a web-pass/iPhone-fail split became one finding
  wearing both verdicts. → the surface axis (HSU-1-03/04).
- **A human in the loop with structured capture.** The dogfood protocol was a
  fillable markdown nobody filled; the walks were agent self-proofs with no
  note/screenshot-per-step landing in a queryable DB. → the guided site
  (HSU-1-04).
- **The harness standing outside the product.** The spoken e2e imports HoldSpeak
  in-process — it cannot boot the product broken, kill it, reboot it differently.
  walk_hs85 got closer (a real subprocess worker) but drove the owner's *live*
  hub, not an isolated bootable run. → the conductor's subprocess-only boundary
  (HSU-1-01).
- **Coverage accounting.** No artifact could state what fraction of the surface a
  run touched or what was never sat through. → the feature ledger + coverage math
  (HSU-1-03), which this whole directory seeds.
- **Log-slice correlation for triage.** Walks printed ad-hoc lines; none windowed
  the product's own log around a failing step and handed it to triage. → the
  debrief packet (HSU-1-05).
- **Device-local state.** The walks induced *hub* state; device-local state (an
  installed GGUF, airplane mode) was hand-staged in HSM-16-06. Inducing hub state
  induces synced device state, but the truly device-local recipes stay partly
  manual — flagged in the worklist.
- **A findings lifecycle.** Walks passed or failed loudly; there was no triage
  vocabulary, no finding IDs, no backlog-block generation. → TRIAGE.md
  (HSU-1-05).

## The one rule that ties it together

**No pack is all-green-happy-path.** Every closed-phase walk both proved the
happy path *and* broke the world. A UAT pack opens with a staging-verify beat
(the recipe's probe, shown honestly with the log tail on failure) and closes
with at least one honest-failure or control beat. If a pack has no beat that
could fail loudly, it is not testing — it is a demo.
