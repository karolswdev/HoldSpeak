# Mission control on the Desk: the design (HS-82-01)

**Scope:** the HoldSpeak-side design for Phase 82 — how the Desk
consumes Delivery Workbench's mission-control substrate and steers
it. The counterpart contract is that repo's `docs/mission-control.md`;
its §5 pins what any client may consume: exactly three documents,
via the dw CLI, no scraping of `pm/roadmap`, no reading dw
internals. Claim marks as in the counterpart doc: **verified-live**
(run on this desk, date recorded), **cited** (file pinned),
**decided** (a choice this document makes and owns).

Verification date: 2026-07-04, against dw 1.9.0 on this desk.

## What this client declares (§5 compliance)

- **`feed_schema` 1** — verified-live: `dw state --json` emits
  `feed_schema: 1` in the delivery-workbench checkout.
- **`sessions_schema` 1** — verified-live: `dw sessions --json`
  emits `sessions_schema: 1`, registry `ok`.
- **Correlation fields the Desk renders** (everything else is
  opaque and passed over in silence): `key`, `agent`,
  `correlation`, `stories` (`story_id`, `title`, `project`),
  `awaiting_response`, `stale`, `tmux.session`.
- Any other schema version is a **typed compatibility error**
  rendered honestly — the pack-MANIFEST precedent, now in a second
  client. Drift is a compatibility note on this client, never a
  silent break.

## 1. The bridge (implemented by HS-82-02)

**Decided:** the Desk island reads only same-origin `/api/*`
routes (the Desk's standing architectural rule), so the three
documents enter through a FastAPI bridge, not the browser:

- `GET /api/missioncontrol/state` — one entry per configured rails
  repo: `{"repos": [{"name", "path", "status": "live", "feed":
  <the dw state document, untouched>}]}`; on failure the entry
  carries `"status": "compatibility" | "unavailable"` and a
  `"detail"` string instead of `"feed"`.
- `GET /api/missioncontrol/sessions` — the correlation document,
  relayed once (it is desk-global, not per-repo), same status
  envelope.
- `GET /api/missioncontrol/events?tail=N` — per-repo event lists,
  `tail` clamped to 1..100, default 20.

**Decided: the repo set is the existing project map** —
`~/.holdspeak/delivery_workbench.json` (`{"projects": {name:
path}, "default": path}`), the same operator file the Phase-12
actuator pack reads (cited: the pack's `_load_project_map`). A new
reader lands in `holdspeak/delivery_workbench_map.py` following
the `Config.load` defensive-JSON style; no new config surface.

**Decided: the CLI resolution order is the pack's recorded
decision, unchanged** — the repo's own `.githooks/dw` first, the
installed `dw --root <repo>` second. Subprocess conventions per
the codebase: argv lists, never `shell=True`, explicit timeout
(30 s), `capture_output`, decode with `errors="replace"`, and the
runner injectable so tests fake it (cited:
`holdspeak/connector_runtime.py` runner seam).

**Ingress checks are the bridge's whole intelligence:** schema
versions verified at the door, JSON parse failures and non-zero
exits become `unavailable` with a trimmed stderr tail, and the
documents are otherwise relayed **byte-honest** — the bridge never
reshapes, merges, or annotates what the rails said.

## 2. The conveyor (implemented by HS-82-03)

**Decided:** a desk fixture, not a new app — a named-export React
component (`MissionControlConveyor`) mounted as a sibling in the
`.desk-next` composition, styled with global `desk-*` classes on
the Signal tokens (`--surface-*`, `--accent` reserved for the
next-actionable highlight, `--ok`/`--warn`/`--danger` always
paired with a glyph, never color alone).

Per project (one belt each): phases render as belt segments
(number, title, open/closed, `stories_done/stories_total`);
stories as items with status and the evidence mark; the feed's
`next_story` visually distinct (the one `--accent` use);
`warnings` visible but quiet. A `compatibility`/`unavailable`
repo renders its honest state — never an empty belt pretending
the rails are idle.

**Decided: polling is a 15-second `setInterval`** owned by the
conveyor slice, single-flight (a fetch in progress skips the
tick), started on mount. The store today refreshes only on demand;
the conveyor is the desk's first standing observer and owns its
own cadence rather than changing the global refresh model.

Wire→view normalizers are pure functions in `api.ts`
(`fromWireMissionControl*`), unit-tested in the established
pure-logic vitest style — no rendering harness exists and this
phase does not introduce one.

## 3. Sessions and events on the belt (implemented by HS-82-04)

Sessions render pinned to their story items (`on_story`) or in the
honest buckets the correlation names — `ambiguous` (candidates
listed), `idle_on_rails`, `off_rails`, `unreadable` —
`awaiting_response` is the loudest signal on the desk,
`stale` is visible and never dropped. Events render as a ticker
(last N, newest first): `gate_refusal` first-class with its rule
id verbatim; `story_status` and `gate_pass` are the belt's motion.
No transcript content exists in the documents and the Desk adds
none back.

## 4. The approval leg (implemented by HS-82-05)

**Decided: the native lifecycle, not a new one.** The Desk's story
verbs ride the same propose → approve → execute machinery every
desk actuator uses (cited: `holdspeak/web/routes/actuator_shared.py
decide_proposal`, the Phase 61/72 lineage):

- A belt action builds a **fields payload** (`dw_action` shape:
  verb/project/phase/story/status or title) — the UI never builds
  argv.
- `POST /api/missioncontrol/story/propose` records a proposal
  (`db.actuators.record_proposal`, target `delivery-workbench`)
  with a preview naming repo, story, from→to, and the standing
  sentence: *the dw gate still applies — a done-flip without
  evidence will be refused.*
- `POST /api/missioncontrol/story/{id}/decision` runs
  `decide_proposal` with an executor that builds a gated connector
  (cited: `holdspeak/plugins/gated_connector.py`,
  `WriteConnectorManifest` with exactly the two argv prefixes
  `… story status` / `… story create`) and executes. argv is built
  from the **stored** payload at egress; a payload naming a repo
  outside the project map is refused before planning.
- A dw refusal is the stack working: the banner rides back
  verbatim in the proposal's error field and renders first-class
  on the belt, pinned to the story that refused.

Certification stays human, always: nothing in this phase can flip
a contract box; the two argv shapes cannot commit at all.

## 5. The joint proof (HS-82-05, cited by their WLA-13-05)

Evidence-captured on this desk against the real delivery-workbench
checkout: (a) live phase state on the belt; (b) a real agent
session correlated to its story with its blocked state; (c) an
approved flip moving the conveyor; (d) the crown case — an
approved, evidence-less done-flip refused by the dw gate, refusal
rendered first-class. Screenshots under the phase's
`screenshots/`; the counterpart's WLA-13-05 cites this story's
evidence for its exit exam.

## Compatibility notes

- The registry's `SUPPORTED_AGENTS` is `{claude, codex}` today —
  pi sessions join the belt when the registry learns them; the
  conveyor is agent-name-agnostic.
- The iOS leg is out of phase scope (documented in the
  counterpart's WLA-13-05: the web Desk carries the joint proof);
  holdspeak-mobile picks the conveyor up in its own phase.
