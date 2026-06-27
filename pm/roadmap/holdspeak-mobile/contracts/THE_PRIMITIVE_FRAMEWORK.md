# The Primitive Framework — the canonical contract

> The spine. Three surfaces are being ported in parallel (desktop hub, iPad, web). They MUST converge
> on the shapes below. This doc is the source of truth; when a surface disagrees with it, the surface
> is wrong. Authored 2026-06-26 on the owner's directive: *"nearly full parity… the iPad things become
> first-class ports into the desktop… including agents… we are building a HUGE framework."*

## Thesis

One framework. **Every primitive is first-class on every surface — desktop, iPad, web — authored
anywhere, synced everywhere.** The iPad and web are first-class *authoring ports*, not viewers. A Note,
a KB, an **Agent (persona)**, a Workflow created on the iPad or the web is a real object that **ports
into the desktop** (the canonical store) and flows back out to the other surfaces.

Priority (owner): **web is king, iPad is king×2, the desktop hub is the happy backbone.**

## The hub + ports model

- **Desktop (the Mac) = the canonical store.** Every syncable primitive's truth lives here (SQLite +
  the HTTP API). The iPad and web are authoring ports + caches that sync to it.
- **Conflict policy:** last-write-wins by `last_modified` (ISO-8601 UTC `Z`). Deletes are **tombstones**
  (`deleted: true`), never hard removals on the wire.
- **Wire:** snake_case JSON ⇄ camelCase native (Swift) ⇄ camelCase TS. Mirror the existing Phase-0
  contract coder (`apple/Sources/Contracts/Coding.swift`).

## Sync classes (decided per primitive)

- **content** — durable, canonical, bidirectional sync (meetings, artifacts, notes).
- **organization** — durable, canonical, bidirectional (KBs, membership/classification).
- **capability** — durable, canonical, bidirectional (agents, chains, workflows; models sync a
  *manifest* only, binaries stay device-local).
- **presence** — ephemeral live state, an append/tail **event stream** + server-persisted replay; NOT
  the durable `ChangeSet` (coder sessions).
- **layout** — where a card sits on a given surface. **Per-device, never canonical.** At most a soft
  last-write hint.

## The canonical primitives

| Primitive | Kind | Sync class | Canonical wire shape (snake_case) |
|-----------|------|-----------|-----------------------------------|
| **Meeting** | `meeting` | content | exists — `meetings` / `Contracts.Meeting` |
| **Artifact** | `artifact` | content | `id, meeting_id?, artifact_type, title, body_markdown, structured_json?, status, sources[], egress?, created_at, updated_at, last_modified, deleted` — **the iPad `OutputRecord` IS this** |
| **Note** | `note` | content | `id, title, body_markdown, tags[], created_at, updated_at, last_modified, deleted` |
| **Directory** | `directory` | organization (identity+membership) · layout (geometry) | `id, name, parent_id?, created_at, last_modified, deleted` — **the iPad "zone" is this** (its name/nesting/membership sync; its geometry does NOT) |
| **KB** | `kb` | organization | `id, name, member_ids[], created_at, last_modified, deleted` |
| **Agent (persona)** | `agent` | capability | `id, name, avatar, role, system_prompt, user_template, tools[], kb_id?, created_at, last_modified, deleted` |
| **Chain (crew)** | `chain` | capability | `id, name, steps[] (agent_ids), last_modified, deleted` |
| **Workflow** | `workflow` | capability | `id, name, prompt? , graph_json?, last_modified, deleted` |
| **Coder session** | `coder` | presence | `agent ("claude"\|"codex"), session_id, project?, model?, tokens_used?, state (working\|waiting\|idle\|ended), events[]` — `CoderEvent` kinds: `user_prompt, assistant, tool(tool,target,detail), result(ok,summary,added,removed), command(cmd,exit,output), approval(question,command), notification, usage(tokens), ended` |
| **Model** | `model` | capability (manifest) | `id, name, capabilities[]` — manifest syncs, binary device-local |
| **Connector** | `connector` | config | integration target |
| **Membership** | — | organization | which primitive is filed in which KB/zone |
| **Game** | `game` | **local-only** | never syncs (the one honest exception) |

### Two distinct first-class "agents" — do NOT merge them
- **Agent (`agent`)** = a *user-authored persona* (system prompt + avatar + tools). The iPad
  Tailored-Agents object, **promoted** to a canonical synced server domain object. First-class everywhere.
- **Coder (`coder`)** = a *live Claude/Codex coding session* (Phase 17), captured by the desktop hooks
  (`holdspeak/agent_context` + `agent_hook.py`). Presence-class.
- They are different concepts. The desktop's existing `AgentSession` (agent_context) backs **Coder**, not
  **Agent**.

### Zones ARE Directories (the iPad's spatial skin of a shared primitive)
- A desk **zone** = a **Directory** rendered spatially. Split it cleanly:
  - **Syncs (organization):** the directory's `id, name, parent_id` (nesting) and its **membership** — which
    primitives are filed in it. A directory + its contents are the same on every surface.
  - **Per-device (layout, never canonical):** the zone's geometry + paint — `cx, cy, w, h, color,
    border, fill, glow` (the zone studio's styling). Your iPad arrangement is yours; web/desktop arrange
    their own directory view.
- The desktop already has this (the classic home's directories + the shared `filed` membership map); the
  port unifies it under the `directory` kind. Nested zones (dive-into) = `parent_id` chains.
- The iPad `ZoneRec` keeps its geometry/paint locally; only `{id (path), name, parent_id}` + membership
  ride the wire.

### KB vs project-KB vs `.hs` context — do NOT conflate
- **KB (`kb`)** here = the desk's knowledge *container* (named, holds member primitives).
- The desktop's existing **project-KB** (`project.yaml` `kb:` map) and **`.hs/` context files** are a
  *separate* knowledge surface. Relate them later; for the port, the desk `kb` is its own object.

## The port matrix (primitive × surface)

Legend: ● first-class+wired · ◐ partial/stubbed · ○ absent · — n/a

Legend update: ✅ = wave-1 landed (built/verified on that surface).

| Primitive | Desktop hub | iPad | Web |
|-----------|:---:|:---:|:---:|
| Meeting | ● | ● | ◐ (cockpit) |
| Artifact | ● | ✅ (`OutputRecord.toContract()→Artifact`) | ◐ |
| Note | ✅ (DB+repo+CRUD+sync) | ✅ (contract + `synced()`) | ✅ (render+author) |
| **Directory** (iPad "zone") | ◐ (classic dirs + `filed` map)→(wave 4 `directory` kind) | ◐ (`ZoneRec`, local)→(wave 4 identity+membership sync) | ○→(wave 4) |
| KB | ✅ (DB+repo+sync; CRUD now landing) | ✅ (contract + `synced()`) | ◐→live (wave 3) |
| Agent (persona) | ✅ (DB+repo+CRUD+sync+`/run`) | ✅ (contract + `synced()`) | ✅ (render+author) |
| Chain | ✅ (DB+repo+sync; **no CRUD route yet**) | ✅ (contract + `synced()`) | ◐ |
| Workflow | ✅ (DB+repo+sync; **no CRUD route yet**) | ✅ (`WorkflowDefinition` + `synced()`) | ◐ |
| Coder | ◐ (agent_context + companion) | ● (Phase 17 feed) | ✅ (read-only feed) |
| Game | — | ● | — |

**Wave 1 — LANDED (3 parallel agents, all verified):** Note + Agent(persona) fully through all three
surfaces (hub DB+repo+CRUD+sync; iPad canonical contract + `synced()` bridges; web render+author), KB/
Chain/Workflow given hub DB+sync + iPad bridges, `OutputRecord→Artifact` bridged on iPad, Coder read-only
on web. Hub: `2858 passed`. iPad: BUILD SUCCEEDED. Web: `npm run build` green. **But nothing SYNCS yet —
the bridges + routes exist; no code moves a `ChangeSet` between surfaces.** That's wave 2.

### Reconciliation tabs (settle in wave 2, fixes toward THIS doc)
1. **`Workflow` name** — iPad named the contract type `WorkflowDefinition` to avoid colliding with
   RuntimeCore's Blueprints `Workflow`. Wire `kind` stays `workflow`. Merge the two concepts (saved-Ask
   vs graph) later; keep `WorkflowDefinition` as the synced contract type for now.
2. **LWW instant** — iPad uses `updatedAt`; hub uses `last_modified`. The **`Synced<>` envelope
   `meta.last_modified` is the one truth**; each surface maps its field to/from it. Note/Agent VALUE
   field sets must converge to this doc's shapes.
3. **Missing hub CRUD** — KB/Chain/Workflow have DB+sync but no REST CRUD; web authors them local-mock
   until those routes land (wave 2, mechanical — same router pattern as notes/agents).

**Wave 2 (firing now):** (a) the **API stitch** — iPad actually pushes/pulls the `ChangeSet` through
`/api/sync/pull|push` so a Note/Agent authored on one surface appears on the other via the hub; (b) the
remaining hub CRUD routes (KB/Chain/Workflow) + web going live off them; (c) the field/name reconciliation
above. THE proof: a note made on the iPad shows up on the web.

**Wave 3 (in flight):** the live integration proof (real hub round-trip + cabled-iPad runbook), web close
tabs + polish to "wonderful" (KB/Chain/Workflow author, Agent Run, sync/connection status), iPad sync UX
(status indicator, per-primitive synced cue, pull-arrival delight) + the `WorkflowDefinition` naming.

**Wave 4 (queued — fires after wave 3 frees the surface dirs):** **Directory (= the iPad zone).** Promote
the zone's identity + nesting (`parent_id`) + membership to the canonical `directory` kind that syncs
desktop↔iPad↔web (hub DB+repo+CRUD+sync; iPad `ZoneRec` → split identity/membership onto the wire, keep
geometry/paint local; web renders directories + filing). Reconcile with the desktop classic-home dirs +
`filed` membership map. Geometry/paint stays per-device layout, never canonical.

**Wave 3:** the coder event-stream transport + persisted replay (Phase 17 17-01/02); membership sync;
the full capability layer (declare-once primitives); web layout/desk polish to iPad parity.

## Reconciliation rules (when the three ports land)

1. **One name per concept**, matching the Kind column above. `OutputRecord`→`Artifact`. The persona stays
   `agent`; the coding session stays `coder`. No surface invents a fourth word.
2. **The hub's API routes are canonical.** The desktop agent reports the exact route paths + shapes; the
   iPad and web ports must call those. Where the hub route doesn't exist yet, the surface stubs a typed
   client + a TODO naming the exact route needed — I stitch them in wave 2.
3. **Shapes match this doc byte-for-byte on the wire** (snake_case keys, the field lists above). Any
   surface that drifted gets corrected to this doc, not vice-versa.
4. **Layout never syncs.** If any port tries to sync positions, cut it.
