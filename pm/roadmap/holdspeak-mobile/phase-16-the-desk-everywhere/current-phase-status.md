# Phase 16 — The Desk, Everywhere (web parity + mesh sync)

**Status:** in-progress (opened 2026-06-24, on the owner's direct instruction after the iPad DeskOS
landed: *"take a fucking five steps back… create a phase that will look at everything we've just
delivered and look for parity with the web client in Astro… and design for synchronization with the
desktop. This is all a mesh system, so everything has to flow back and forth. Knowledge bases, stuff
like that."*)

**Last updated:** 2026-07-05 (**HSM-16-04 DONE — the desk runs on the web too (7/9).**
The survey-corrected remaining slice shipped: the recipe layer RESURRECTED (the Phase-17
rename had left it dead on web — loader keys, world/lineage/editor/pull-out kind checks,
a crashing "+ Agent" chip, a red vitest suite nobody saw) with in-world authoring at
parity, and the Ask AI atom's full web arc (lasso/shift-click → bundle bar → atelier
composer with the iPad's five lenses + mic + RUNS-ON → new hub `/api/ask` grounding from
the canonical store → the printed card wearing the RUN's honest egress → Keep mints the
byte-identical iPad artifact shape / Bin stores nothing). Two latent bugs found and fixed:
the hub NEVER emitted its live `desktop:intel` manifest row (16-08's `_hub_model_name`
read the wrong Config level; every test had monkeypatched the helper), and `theater.js`
popped the meeting theater on every desk run (no `scope:"run"` filter). Hub 2482 green,
web vitest 39/39, validator ALL PASS, 6 live Playwright shots. Next: 16-06 (the walk
riders + web cross-surface beat), then 16-07 docs. Earlier:
**HSM-16-08 DONE — the mesh knows its models (6/9).** The `model`
manifest is the sync wire's eleventh kind (contract + schema + hub table/repo/route + iPad
publish/consume); the run-target sheet names the hub's real model; the no-binary invariant is
asserted on three layers; pre-pays and the P24 supersession recorded in the story. Swift
467/9/0, hub 2474 green, validator ALL PASS. Next: 16-04's web slice. Earlier:
**HSM-16-09 DONE — the Ask AI atom, honest to the bone (5/9).** The
kept Ask now carries its full lineage (every card read + the prompt) onto the synced Artifact;
two egress lies fixed (card + theater now state the RUN's profile, not the app default); both Ask
surfaces left the scrim — the composer is an atelier panel and the card prints from the core.
Suite 467/9/0, sim shots committed, the device beat rides 16-06. The build also TRUTHED-UP the
morning's survey: the atom's skeleton already existed — the "zero code" claim was wrong. Next:
16-08. Earlier: **RESUMED, SURVEY-CORRECTED — more than half the phase was pre-paid
while it slept.** The phase was authored 2026-06-24 and then the Primitive Framework
([`THE_PRIMITIVE_FRAMEWORK.md`](../contracts/THE_PRIMITIVE_FRAMEWORK.md), waves 1–4, PRs #140–142),
Phase 17 (recipes atomic across hub/wire/Swift/web), Phase 22 (workflows travel + run on the hub),
Phase 23 (the 10-kind round-trip matrix), and the HS-73-02 owner call ("the desk IS the front door" —
`web/src/pages/index.astro` mounts `DeskApp`) delivered its parity + sync spine without ever touching
this doc. The survey records **16-01/02/03/05 done pre-paid** (evidence in the table; fresh targeted
run `uv run pytest tests/unit/test_web_routes_primitives.py test_web_routes_sync*.py
test_db_primitives.py test_primitive_contract.py` → **66 passed**, on top of today's `swift test`
437/8/0 from the Phase-23 closeout) and re-scopes 16-04/08 to their genuinely-open slices. What
remains is the phase's whole point made sharp: **the capability layer's felt value.**
**HSM-16-09 — the Ask AI atom — now LEADS**: it exists nowhere in the code (grep-verified), its
every dependency has since shipped (lasso HSM-14-19, `routableText` drop grammar 17-04, the
fresh-provider draft seam 17-05, runtime profiles Phase 24, the `EgressScope` grammar 21-01, the
materialize treatment 14-03, the speak-to-fill mic), and it composes them into the desk's signature
moment with almost no new construction. Sequence: 16-09 → 16-08 (the atom generalized) → 16-04's
web slice → 16-06 proof → 16-07 docs.)

## Why this phase exists

We just built a rich DeskOS on **one** surface (the iPad): objects with physics, the spill of a
meeting into its parts, lasso → bundle → file, floating app windows, and **knowledge bases** — all
governed by one documented convention (the DeskObject). But HoldSpeak is **a mesh, not an iPad app**.
Two things are missing and they are the whole point:

1. **Parity.** The web client (Astro, `web/src`) has none of the DeskOS. The Desk was declared canon
   for **both** surfaces ([[story-19-the-desk]]); right now only one exists. A mesh with one good
   surface is a demo, not a product.
2. **Flow.** Nothing we built **moves between devices.** A knowledge base created on the iPad lives in
   that iPad's `@AppStorage` and dies there. The desktop — the hub that owns the big models, the
   canonical store, the pipeline — has no idea it exists. For a *personal intelligence mesh*, the
   organization layer (KBs, directories, classifications) **must** flow desktop ↔ iPad ↔ web.

This phase makes the Desk a mesh citizen: one convention, three surfaces, one canonical organization
that syncs.

## The load-bearing design call (decided here, refined in 16-01/16-02)

Not everything on the desk is the same *kind* of data, and conflating them would make sync wrong:

- **Content** — Meetings, Artifacts. The canonical record. **Already syncs** (Phase 10). We extend, not
  redo.
- **Organization** — Directories, Knowledge Bases, and **membership/classification** (which object
  belongs to which container). This is **shared, canonical, must-sync** data. A KB and its contents are
  the same on every surface. *(New: HSM-16-02 adds it to the sync model; the desktop is the hub.)*
- **Capability** — the **executable, combinable** layer. Two members, treated differently on the wire:
  - **Workflows** — the Workbench's visual-programming AI programs (the node graph / blueprint). The
    **definition is portable canonical data → it syncs** (author on the iPad, run on the Mac). A
    workflow is a first-class object you **combine**: drop it onto a meeting / KB / selection and it
    **runs immediately**, producing Content (artifacts).
  - **Models** — the GGUF cartridges. A model **binary is device-local** (you do not sling gigabytes
    across the mesh; the iPad can't hold the Mac's big model). What **syncs is the model *manifest***:
    "this node has this model, with these capabilities." That lets a workflow say *run on a reasoning
    model* and the mesh **resolve the target per node** — exactly Phase-15 fluid compute (RUNS-ON:
    on-device / your Mac / endpoint). Manifest syncs; binary stays put.
- **Layout** — where a card physically sits, its presentation mode, whether it's spilled. This is
  **per-device ergonomics**, not shared truth. It does **not** sync as canon (a desk you arranged on
  the iPad is yours; the web arranges its own). At most a soft, last-write hint — never a conflict
  source.

**The cross-cutting behavior — combination/execution.** The classes are not islands: a **Workflow**
(capability) runs against an **input** (content or organization) on a **target Model** (capability,
resolved per node) and emits **Content** (artifacts). "Run a workflow immediately against something" is
the desk made productive — a drag-drop on the canvas, the same gesture as play. The Workbench already
does the non-spatial version (detail → "Run a workflow" → `generate(workflowTypes:)`); this phase makes
workflows and models first-class **DeskObjects** you combine, and makes their definitions/manifests flow
so a workflow authored on one surface runs on any node of the mesh.

**The atom under all of it — Ask AI (HSM-16-09).** The simplest, highest-value form of combine needs no
authored graph at all: **lasso context → pull "Ask AI" from a drawer → speak a prompt → a card prints
out of the shelf → keep it or bin it.** This is the gamified core of the whole DeskOS — context +
spoken intent + a physical result you judge. A workflow is just this atom *saved and chained*. It runs
**on-device today** and needs none of the mesh, which makes it the natural **lead** for the capability
work — the fastest path to felt value while 16-02..05 build the sync underneath.

Getting this taxonomy right is the difference between a mesh that feels coherent and one that fights
the user. It is the spine of the whole phase.

## Stories

| ID | Title | Status | Thrust |
|---|---|---|---|
| HSM-16-01 | The DeskObject parity & sync contract (inventory + spec) | **done** (pre-paid: [`THE_PRIMITIVE_FRAMEWORK.md`](../contracts/THE_PRIMITIVE_FRAMEWORK.md) IS this spec — the canonical primitive table, sync classes, wire shapes, per-surface parity inventory; authored 2026-06-26 on the owner's directive, kept current through wave 4 + the Phase-17 recipe rename) | the baseline both thrusts measure against |
| HSM-16-02 | The organization sync model (design + contract additions) | **done** (pre-paid: `SyncKind.kb`/`.directory`/`.membership` live in `apple/Sources/Contracts/Sync.swift` with identity+membership syncing and geometry/paint per-device, exactly this story's design call; locked by the Phase-23-04 round-trip matrix) | sync (design-first) |
| HSM-16-03 | The desktop hub surface for organization | **done** (pre-paid: `holdspeak/web/routes/primitives/` serves directories/kbs/notes/recipes/chains/workflows/profiles CRUD + `routes/sync.py`; fresh 66-test green run 2026-07-04) | sync (hub) |
| HSM-16-04 | The web Astro Desk (parity build) | **done** (2026-07-05 — the remaining slice: the recipe layer resurrected (the rename had left it DEAD on web — truth-up in the story) + in-world authoring, and the Ask atom's full web arc via new hub `/api/ask` + `/api/ask/keep` (keep mints the byte-identical iPad artifact shape, locked in tests); 6 live Playwright shots; 2 latent bugs fixed on the way (the hub's own manifest row never emitted; the meeting theater popped on desk runs)) | parity (the big build) |
| HSM-16-05 | Wire the mesh — organization flows back and forth | **done** (pre-paid: the Phase-23-04 10-kind per-primitive push→pull round-trip matrix covers kb/directory/membership byte-faithful, golden-pinned on both sides of the wire; live merges proven in the 22-01/22-04 DeskSync passes) | sync (wire) |
| HSM-16-09 | **The Ask AI atom** — lasso → ask → speak → print → keep/bin (on-device, no mesh needed) | **done** (2026-07-04, sim-proven; device beat rides 16-06. TRUTH-UP: the survey's "zero code exists" was wrong — the skeleton had shipped; this story built the missing substance: full Ask lineage on the wire, two egress-honesty fixes, composer + printed card off the scrim) | capability (the atom) |
| HSM-16-08 | Capability objects — the model manifest | **done** (2026-07-04: the `model` manifest is the sync wire's ELEVENTH kind — devices advertise installed models, the hub stores + advertises its own live row, and the run-target sheet NAMES what "your desktop" would run; no-binary invariant asserted on schema/Swift/hub layers. Truth-ups: combine-to-run + cross-node runs were pre-paid (desk era + P22); drop-model-sets-RUNS-ON superseded by P24 profiles; manifest informs the user's pick, never silent auto-routing (the approval+egress contract)) | capability (combine/execute) |
| HSM-16-06 | The cross-surface proof (author on one surface → felt on the other two, real metal) | todo (rescoped to ride the atom: an Ask kept on the iPad appears file-able on the web desk + the hub; org edits round-trip live) | proof (real metal) |
| HSM-16-07 | Docs catch-up (mesh + DeskObject across surfaces) | todo | docs |

*(The build order after the survey: **16-09 → 16-08 → 16-04's remaining slice → 16-06 → 16-07.**
09 is the atom 08 generalizes; 09 needs no sync and leads.)*

## Where we are

**16-04 DONE (7/9) — the desk runs on the web too.** The story opened with its own
truth-up: the "substantially pre-paid" recipe layer was dead on the web (the Phase-17
rename half-landed — the loader read the pre-rename wire key into a nonexistent items
lane, four components still checked a kind that no longer exists, the create chip was a
live crash, and the desk's OWN vitest suite was already red on a renamed import with no
gate watching). All of it fixed and regression-locked, and the in-world recipe editor
reached authoring parity (avatar/role/prompt/template/tools/KB/profile, autosaving).
Then the atom crossed surfaces: rope context with a real lasso (or shift-click), the
bundle bar rises, the composer docks in the atelier posture with the iPad's five lenses
and the speak-to-fill mic, a RUNS-ON pick whose egress chip is honest for the pick, and
the new `/api/ask` grounds the run IN THE CANONICAL STORE (asserted in tests — the
Phase-53 lesson) without persisting anything. The printed card wears where THIS run went
(model · host, from the response); Keep calls `/api/ask/keep`, which mints an artifact
byte-shaped like the iPad's kept Ask (`via_kind: "ask"`, every card + the exact prompt,
ask keys only when present) — so 16-06's cross-surface proof has ONE shape to trust —
and the card materializes on the desk wearing the NEW beat. Two latent bugs died on the
way: a real hub never emitted its live `desktop:intel` manifest row (16-08's helper read
the intel knobs off the wrong Config level; every test monkeypatched the helper — a new
test now runs the real body), and the full-screen meeting theater popped on every desk
capability run (`theater.js` lacked the `scope:"run"` filter the dashboard has). Suites:
hub 2482, web 39/39 (was red), validator ALL PASS, api-surface at 240 routes, six live
Playwright shots committed. **Next: 16-06** (the runbook now also carries the web Ask
beat), then 16-07 docs.

Earlier — **16-08 DONE the same evening (6/9) — the mesh knows its models.** The survey-corrected
remaining half of the capability layer shipped: a synced `model` MANIFEST ("this node has this
model") joins the wire as its eleventh kind — iPad pushes its installed GGUFs, the hub stores
them and advertises its own model as a live `desktop:intel` row, and the iPad's "where should
it run?" sheet now **names the actual model** your desktop would run (was "big model", a vague
promise). The binary never syncs: the schema's `additionalProperties:false`, a Swift wire
test, and a hub route test each assert it independently. Truth-ups recorded in the story:
combine-to-run and cross-node runs were pre-paid (desk era + Phase 22), drop-model-sets-RUNS-ON
was superseded by Phase-24 profiles, and manifest-driven "resolution" ships as informing the
user's pick — silent egress auto-routing would violate the approval contract. Suites: Swift
467/9/0, hub 2474 unit green + doc guard 18/18, validator ALL PASS (with a new no-binary
negative), sim shot committed. **Next: 16-04's remaining web slice** (recipe/atelier authoring
on the web + the Ask atom's web parity), then the 16-06 cross-surface proof (which now also
carries the manifest round-trip + the Ask device beat), then 16-07 docs.

Earlier — **16-09 DONE the day the phase resumed (5/9).** The build immediately truthed-up the resume
survey: the atom's skeleton (`askBundle` → `DioRouteSheet` → theater → `DioPrintedCard`) had
ALREADY shipped under other names — the survey's "zero Ask-AI code exists" was wrong, and the
story's real substance was what the skeleton faked. Shipped: **the full Ask lineage** (a kept Ask
persists as an `Artifact` naming every lasso'd card + the exact prompt, wire-tolerant and
golden-pin-safe — recipe/chain shapes byte-stable, test-locked), **two egress-honesty fixes**
(the printed card and the theater read the app-wide default, not the run's resolved profile — a
per-run cloud ask printed a card claiming local; both now resolve per-run and name the real
host), **both Ask surfaces off the scrim** (the composer joins the atelier posture; the card
PRINTS from the AI core), and the ask lineage glyph. Suite 467/9/0; sim build green; three
committed screenshots (selected / compose / printed) via new `HS_DESK_ASK` affordances. The
on-device walk beat rides 16-06. **Next: 16-08 — generalize the atom** (save an Ask as a
recipe/workflow by drop; model manifests; combine-by-drop), then 16-04's web slice.

Earlier — **resumed 2026-07-04, survey-corrected.** The parity + sync spine this phase was opened to design got
built underneath it by the Primitive Framework and Equilibrium (see the table's evidence pointers) —
the survey records 16-01/02/03/05 done pre-paid on a fresh 66-test green run and re-scopes the rest.
What was never built anywhere is the phase's own headline: **the Ask AI atom** (16-09), the desk's
gamified core — lasso a pile of context, speak your instruction on top of it, watch the answer print
out of the shelf, keep it (a real synced `Artifact` with provenance) or bin it. Every dependency has
shipped since the story was written: the lasso (HSM-14-19), the `routableText` drop/grounding grammar
(17-04), the fresh-resolved-provider one-call draft pattern (17-05's `CoderAnswer.draft`, Mode-A KV
rule included), per-agent runtime profiles with honest key custody (Phase 24), the one `EgressScope`
grammar (21-01), the materialize treatment (14-03), and the speak-to-fill mic
([[feedback_voice_mic_every_input]]). It runs on-device with no mesh — air-gap honest — and it is
in-world, no modals ([[feedback_no_modals_in_world]]). Next action: **build HSM-16-09 on the iPad**,
then generalize it (16-08), then carry it to the web (16-04's slice), then the cross-surface proof.

## Relationship to the rest of the roadmap

- **Phase 10 (sync)** — we extend `SyncKind`/`ChangeSet`, mirroring HSM-10-01's principle (sync the
  real entities in a thin envelope, never a parallel schema). We do not re-found sync.
- **Phase 15 (the mesh)** — we reuse the hub framing, `HTTPDesktopClient`, and the one
  approval+egress contract. The organization layer becomes another thing the mesh carries.
- **holdspeak Phase 68 (web convergence)** — its design-pattern catalog + shared Signal tokens are the
  raw material for HSM-16-04; this phase is the DeskOS-specific port the catalog was preparing for.
