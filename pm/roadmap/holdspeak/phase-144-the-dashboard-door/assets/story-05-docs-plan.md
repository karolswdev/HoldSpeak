# HS-144-05 — Docs: implementation plan

**Planning ground truth:** `feat/hs144-04-upcoming-rail` at committed
`851178de` (HS-144-03 done), inspected 2026-08-27. Story 04 is actively
editing Chair/settings files in this checkout, so this plan does **not** treat
its dirty work as source fact. Its accepted plan and 2026-08-28 dispositions
are the post-04 composition contract: the Chair is `Door → Meetings → Agents`,
with the upcoming rail inside `DoorBoardLane`; it is the sole Chair home for
future scheduled-recording rows; and its schedule affordance reuses the
existing in-world `openScheduleCreate()` path.

This is a documentation and documentation-guard story only. It changes no
product route, service, schema, generated web bundle, or roadmap file.

## 0. The shipped truth the docs must say

- The Chair is the post-first-value front door. Its Door board is a server
  projection with five columns: **Overdue, Now, Waiting, Unassigned, Active**.
  A card action is only rendered when the aggregate names a lawful existing
  verb. The action calls that verb and shows the resulting Receipt in flow;
  moving/completing a card is not a cosmetic board-position edit.
- The board's old Chair furniture is gone: Brief and Follow-Through remain
  reachable Intelligence views, but not Chair lanes. `FinishThoughtsLane` is
  unmounted. Meetings remains for live/recent meetings and Agents remains.
- The Door's one server-owned upcoming timeline merges `calendar_event` and
  `scheduled_recording` rows in chronological order. The rail labels the two
  kinds honestly; a calendar event is not a recording and a schedule is not an
  invitation. It can be empty or schedule-only without inventing calendar
  chrome.
- A scheduled recording can be created from the Chair's upcoming rail through
  the existing in-world schedule window and existing
  `POST /api/scheduled-recordings` verb. The pre-reforge `CaptureHero` is no
  longer mounted in the Chair; the docs must not preserve it as an alternate
  create path.
- One calendar subscription accepts either a local ICS file path or an HTTPS
  URL. The projection includes occurrences in the next **14 days** and the
  conductor refreshes at boot and every **15 minutes**. A local file is local.
  An HTTPS subscription renders the Settings Calendar egress chip and makes a
  bounded fetch:
  no credentials, caller-supplied headers, cookies, proxy configuration, or
  redirect follow-up are sent; redirects refuse. The owner configures the
  source under **Settings → Meetings → Calendar**.
- `door.get` is the one closed, read-only MCP Door aggregate (not a resource).
  It returns board, active Thoughts, the mixed upcoming timeline, and
  server-derived counts through the same composition as HTTP.

Source anchors: `holdspeak/services/door_service.py:29-53,152-214`,
`holdspeak/calendar_ingest.py:18-23,71-95`,
`holdspeak/calendar_ingest_conductor.py:62-128,131-223`,
`holdspeak/mcp/families/door.py:15-25,28-57`, and the accepted Story-04 plan
§§1-3 and dispositions.

## 1. Falsified-statements inventory

The inventory separates a literal stale claim from a required entry-point gap.
A gap is still work: the docs story's acceptance criterion is that a cold
reader can discover the Door, rail, and subscription without phase lore.
`docs/internal/**`, evidence, and `pm/roadmap/**` are historical/internal
material, not rewritten as user-facing product truth.

| Entry point | File:line | Finding | Correction direction |
| --- | --- | --- | --- |
| Public README | `README.md:81-87` | **Hard false (4):** “four fixed lanes (Brief, Follow-Through, Meetings, Agents)” describes retired Chair furniture, and its capture-hero-at-centre / hero-record / hero-voice-start / hero-Ask claims describe an unmounted component. | Replace the complete Chair paragraph with the Door as the after-first-value front door: board first, upcoming rail, live/recent Meetings, Agents, and a compact Brief entry point. State that board actions are real verbs with Receipts; do not teach old lane headers or the unmounted hero as the navigation model. |
| Public README | `README.md:79` | Adjacent front-door caption still describes the pre-Door visual grammar (“the rail asks”). | Reword only if the surrounding Chair paragraph changes; do not claim the pictured spatial Floor is the Door. No asset replacement belongs in this story. |
| Owner guide | `docs/USER_GUIDE.md:478-515` | **Hard false (2):** `:488-490` tells the reader to use the unmounted Capture Hero's Schedule control; `:513-515` says future schedules appear in Meetings with a `SCHEDULED` badge. It also omits the Door board, receipts, mixed rail, and ICS subscription. | Add a concise Door section before schedule instructions: five meaning-based columns; a card change invokes its named verb and returns a Receipt; rail kinds and source truth. Make the Door rail's one-click in-world schedule control the sole documented Chair create path. Replace the old location claim with “future schedules appear once in the Door upcoming rail; Meetings keeps live/recent meetings.” Add ICS file/HTTPS setup, 14-day projection, and 15-minute/boot refresh facts. |
| Security/effect entry point | `docs/SECURITY.md:344-369` | **Coverage false (1):** the table promises “everywhere data can leave” but has no ICS HTTPS fetch row. | Add one terse **Calendar ICS subscription** row after other configured URL fetches. Name the configured HTTPS source and boot/15-minute fetch trigger; say the request is the configured URL's ICS fetch and excludes credentials, caller headers/cookies, proxies, and redirects. State file subscriptions cause no egress. Do not duplicate a privacy essay elsewhere. |
| MCP reference | `docs/MCP_SIDECAR.md:82-88` | **Hard incomplete claim (1):** `door.get` is described as returning “upcoming scheduled recordings,” which excludes shipped calendar events. | Say one read-only aggregate returns the board, active Thoughts, mixed calendar-event/scheduled-recording upcoming timeline, and matching counts; preserve “no MCP resource” and People-overlay qualification. |
| Count anchors | `README.md:446-448`; `docs/MCP_SIDECAR.md:3-5,58-60,299`; `docs/API_SURFACE.md:12` | **Verified clean (0 stale numbers), but ambiguous:** 135 tools and 30 families are correct. The 29-resource prose is the non-owner listing (15 static + 14 templates); the sidecar's owner view is 32 (16 static + 16 templates). API surface is 538 routes, 89 iOS-consumed, 416 web-consumed. Story 01 changed 134 → 135; Story 03's People transition manifest regeneration changed 537 → 538. | Do not change 29 to 32. Add one concise qualification in `MCP_SIDECAR.md` that access-filtering explains the non-owner/owner resource totals; make the short README anchor say it is the default/non-owner count or link to that qualification. Recheck tool count against the MCP walk and API count against committed `docs/api-surface.json`; if concurrent work changes routes, regenerate API surface rather than hand-editing it. |
| Models guide | `docs/MODELS.md:8-10` | **Hard false (1):** “Nothing leaves your machine except the model endpoint you choose” is no longer true when the owner configures an ICS HTTPS subscription. It does not mention Chair, but it makes an absolute egress claim. | Narrow only the Model-specific sentence: model material goes only to the chosen model endpoint. Point all complete egress truth to Security; do not add a second privacy explanation. |
| Phase-140 onboarding | `docs/GETTING_STARTED.md:88-93,97-125` | **Hard false (3):** a developing Thought is opened from **Finish thoughts**, a retired Chair mounting; `:97` says a returning user lands on the Desk/Floor; `:120` defines `/` as the spatial Desk. | Replace the retired link with the Door's **Active** column / the existing Thought entry point, without changing the Thought Workbench mechanics. State that the Chair Door follows the first sentence and revise the `/` table row to name it; preserve the Floor as a reachable spatial world and leave unrelated legacy deep links alone. |
| Documentation index | `docs/README.md:6-8,15-19` | **Entry-point drift (2 related claims):** the index calls the spatial Desk / `WEB_DESK.md` “the front door itself,” with no Chair Door route. | Narrowly make the index distinguish the post-first-value Chair Door from the Floor's spatial world, and point the reader to the appropriate guide. Do not re-catalogue all rooms. |
| Linked Desk guide | `docs/WEB_DESK.md:2-7,13-15` | **Hard false (2 related claims):** its opening defines `/` as the spatial Desk and says every non-setup user arrives at the Floor. | Amend only the opening/arrival paragraphs: `/` reaches the Chair Door after first value; the Floor remains the spatial object world reached through its existing control. Keep the remainder as a Floor/window reference rather than rewriting it as a second Door guide. |

No scanned user-facing entry point claims “no calendar” or advertises
`BriefLane`, `FollowThroughLane`, or `FinishThoughtsLane` by identifier. The
absence does not eliminate the retirement guard: the old words need a
regression fence once the prose has been reconciled.

## 2. Retired-vocabulary guard

The Phase-143 precedent is
`tests/unit/test_doc_drift_guard.py:54-105`:

1. a compiled pattern is narrowly named for the retired contract;
2. `test_docs_do_not_restore_…` scans `_all_docs_and_readme()` and reports
   `path:line` offenders;
3. a paired non-vacuity test proves both forbidden examples and kept current
   wording. It intentionally scans the full `docs/**` corpus plus root README,
   while the PMO roadmap remains outside the scan.

Add a sibling **Chair-retirement** pattern and its two tests in that same file,
not a new test module. It should reject only terms that are unequivocally stale
as Chair furniture:

- `BriefLane`, `FollowThroughLane`, and `FinishThoughtsLane`;
- the exact old “four fixed lanes” / four-item Chair roster;
- the plural navigation phrase “Finish thoughts”; and
- “Scheduled recordings show in the Meetings lane.”

The guard must **not** ban plain “Brief,” “Follow-Through,” “Meetings,”
“Thought,” or “Finish Thought”: Brief/Follow-Through remain valid Intelligence
views and Finish Thought remains a valid verb. Its keep vectors should prove
that those current meanings stay legal, while violation vectors prove each
retired spelling/context fails. This is a doc guard only; it must not inspect
or rename surviving component source files.

## 3. Documentation proof inventory

| Proof | What it covers | DB-opening / required environment | Exact focused command |
| --- | --- | --- | --- |
| `tests/unit/test_doc_drift_guard.py` | Existing live-doc links/images/voice/roadmap guards plus the new retired-Chair pattern and non-vacuity vectors. | No database authority, but use an isolated HOME for a uniform docs capture. | `HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/unit/test_doc_drift_guard.py` |
| `tests/unit/test_product_copy.py` | Product-language inventory over `README.md`, `docs/USER_GUIDE.md`, `docs/SECURITY.md`, `docs/MODELS.md`, and `docs/WEB_DESK.md`; protects prose classification/drift for changed primary guides. | No DB. | `HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/unit/test_product_copy.py` |
| `tests/e2e/test_mermaid_renders.py` | Renders every fenced Mermaid block in root README, top-level docs, and internal docs. None is planned here, but this is the repository's documentation-render proof and must remain green. | No DB. Use the warm npm cache while HOME is isolated so `npx`/Chromium is judged rather than re-downloaded. | `HOME_REAL="$HOME"; HOME="$(mktemp -d)" npm_config_cache="$HOME_REAL/.npm" uv run --python 3.13.11 pytest -q tests/e2e/test_mermaid_renders.py` |
| `tests/unit/test_api_surface.py` | `docs/api-surface.json` matches the live assembled app and `docs/API_SURFACE.md` is its exact renderer output. | **Opens the assembled app / DB path. Isolated HOME is mandatory.** | `HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/unit/test_api_surface.py` |
| `scripts/gen_api_surface.py` | The only lawful generator for `docs/api-surface.json` and `docs/API_SURFACE.md`. It is a regeneration check, not a hand-edit path. | **Builds the assembled app / can open a DB. Isolated HOME is mandatory.** Run only if the final tree has a route/call-site change or the API guard reports drift. | `HOME="$(mktemp -d)" uv run --python 3.13.11 python scripts/gen_api_surface.py` |
| `scripts/mcp_walk.py` | Real stdio MCP `tools/list`: exact `tool_count_135`, closed `door.get@1` schema, and the transport catalogue. This is the authoritative MCP inventory proof; no existing test parses the prose count in `MCP_SIDECAR.md`. | **Boots a real sidecar / DB. Isolated HOME is mandatory** (the script also creates a child isolated HOME). | `HOME="$(mktemp -d)" uv run --python 3.13.11 python scripts/mcp_walk.py` |
| `tests/unit/test_door_mcp.py` | The direct closed `door.get` MCP contract used to support the corrected family prose. | Calls `reset_database()` before creating its temporary database, so isolated HOME is mandatory. | `HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/unit/test_door_mcp.py` |

There is deliberately no full-suite command in this plan. The API generator is
not run merely to touch docs: Story 05 makes no route change, so generated
artifacts stay unmodified unless the final concurrent product tree proves them
stale. Do not substitute the charter's `-k "doc or mcp_inventory"` selector:
`mcp_inventory` matches no test and `doc` pulls broad doctor coverage. The
named focused commands above are the honest documentation net.

**Known planning-head baseline:**
`tests/unit/test_product_language.py::test_primary_ui_has_no_new_unqualified_ambiguous_terms`
is red at committed `851178de` on
`web/src/desk/pullouts/editors/RecipeEditor.tsx:91` (`label="Context"`). It is
pre-existing, product-source work outside this docs story. Do not hide it by
calling a broad selector green; if it recurs in a chosen aggregate capture,
record it as inherited rather than editing product code here.

## 4. Delivery slices

### S1 — Reframe the public and owner front doors

**Files**

- Modify `README.md`.
- Modify `docs/USER_GUIDE.md`.
- Modify `docs/GETTING_STARTED.md`.
- Modify `docs/MODELS.md` only for its false absolute model-egress sentence.
- Subject to the scoped call below, modify `docs/README.md` and `docs/WEB_DESK.md`
  only in their arrival/front-door paragraphs.

**Work**

1. Replace the old four-lane/capture-hero Chair explanation with the Door board
   and upcoming rail. Preserve the First Sentence distinction: this is what
   follows first value, not a competing welcome flow.
2. In the User Guide, give a reader the columns' practical meaning, lawful
   card-action/Receipt rule, upcoming kind truth, the rail's sole Chair
   schedule-create affordance, and the non-duplicating live/recent Meetings
   boundary.
3. Give ICS one concise discovery path: **Settings → Meetings → Calendar**;
   accept local file or HTTPS URL; name the 14-day horizon and boot/15-minute
   cadence. Cross-link the Security row rather than repeating egress mechanics.
4. Replace phase-140's retired **Finish thoughts** navigation with the Door's
   Active path, then update both the returning-user sentence and the `/` deep
   link row to name the Chair Door rather than the Floor.
5. Narrow `MODELS.md`'s model-egress sentence so it describes model material
   only and routes all complete boundary truth to Security.

**Named proofs**

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_doc_drift_guard.py \
  tests/unit/test_product_copy.py
```

### S2 — Put the ICS crossing in the one egress ledger

**Files**

- Modify `docs/SECURITY.md`.

**Work**

1. Add exactly one Calendar ICS HTTPS fetch row to the existing egress table.
2. Make its boundary legible without a privacy novel: HTTPS source fetch only,
   source configured by owner, boot plus 15-minute cadence, bounded ICS bytes;
   no credential/header/cookie/proxy/redirect follow-up, and local files never
   cross the network.
3. Keep Schedule/recording semantics out of this table. This row describes the
   source I/O boundary, not an invitation or capture trigger.

**Named proof**

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_doc_drift_guard.py \
  tests/unit/test_product_copy.py
```

### S3 — Reconcile the programmable and generated inventories

**Files**

- Modify `docs/MCP_SIDECAR.md`.
- Verify only (do not edit unless drift is real): `README.md`,
  `docs/api-surface.json`, and `docs/API_SURFACE.md`.

**Work**

1. Correct the `door.get` family paragraph to include the mixed upcoming
   timeline and preserve closed/read-only/no-resource semantics.
2. Recount rather than copy historical numbers: MCP is **135 tools / 30
   families**. Its resources are principal-filtered: the existing 29 is the
   non-owner/default listing; owner discovery has 32. Reconcile that explanation
   between the sidecar's summary and owner resource section, and make the README
   anchor unambiguous without replacing 29 with a false universal total. API
   manifest is **538 routes**.
3. If a real post-Story-04 route/call-site change makes API output drift, run the
   documented generator under isolated HOME, inspect the generated diff, and
   then include the generated pair. Do not hand-edit either API artifact.

**Named proofs**

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/unit/test_api_surface.py
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/unit/test_door_mcp.py
HOME="$(mktemp -d)" uv run --python 3.13.11 python scripts/mcp_walk.py
```

### S4 — Lock the retired Chair vocabulary and render the corpus

**Files**

- Modify `tests/unit/test_doc_drift_guard.py`.

**Work**

1. Add the narrow retirement regex, live-doc scan test, and non-vacuity/keep
   vectors described in §2.
2. Do not add a broad ban on product nouns that are still meaningful outside the
   Chair. The guard is a fence against a specific removed composition, not a
   vocabulary purge.
3. Run the current documentation checks as separate focused legs and read their
   output before evidence capture. No product test needs to be changed.

**Named proofs**

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/unit/test_doc_drift_guard.py

HOME_REAL="$HOME"; HOME="$(mktemp -d)" npm_config_cache="$HOME_REAL/.npm" \
  uv run --python 3.13.11 pytest -q tests/e2e/test_mermaid_renders.py
```

## 5. [ORCH-CALL]

| Open boundary | Recommendation | Consequence |
| --- | --- | --- |
| The public documentation index and linked `WEB_DESK.md` call the spatial Floor “the front door,” but HS-144-05's charter explicitly names README/User Guide/Security/MCP and does not name a broad Desk-guide rewrite. | **Accept a two-paragraph-only reconciliation in S1.** Update `docs/README.md:6-8,15-19` and `docs/WEB_DESK.md:2-7,13-15` to say the post-first-value `/` arrival is the Chair Door and the Floor remains the spatial object world. Do not audit or rewrite the rest of `WEB_DESK.md`. | Leaves no README-linked owner entry point telling a returning reader that the Floor is the default arrival, while keeping this a narrow docs story rather than a retroactive Desk manual rewrite. |
| `docs/trust-destinations.json`, the machine-readable egress registry, currently has no calendar source even though the Security table must document its HTTPS fetch. A documentation edit cannot make the global trust badge discover it. | **Do not add or fake a registry row in this docs-only story.** Add the truthful Security row and Settings-level egress explanation; record central trust-registry/badge coverage as a product-gap disposition for the orchestrator/Story 04 owner. | Prevents the docs from promising that the global badge names an unregistered calendar destination, while preserving a visible, truthful local Settings egress fact. |

## 6. Stop signals and evidence checklist

| Stop signal | Required correction |
| --- | --- |
| New prose calls a calendar event a recording, or a scheduled recording an invitation. | Restore source-kind language and one mixed chronological rail. |
| Docs say a card drag/reorder is its own state change or omit the verb/Receipt consequence. | State server-derived lanes and named existing verbs; remove cosmetic-board language. |
| An HTTPS fetch row implies a token/header/cookie or hides the file-vs-URL egress distinction. | Return to the conductor's actual boundary: bare bounded HTTPS request; file is local; redirects refuse. |
| README/MCP count anchor changes without a live recount or presents 29 as a universal resource total. | Keep 135 tools / 30 families, qualify 29 as the non-owner resource listing and 32 as owner discovery, and retain 538 routes unless the real walk/generator proves a concurrent change. |
| `Brief`, `Follow-Through`, or `Finish Thought` is banned wholesale. | Narrow the guard to retired component/context phrases; those current terms remain valid elsewhere. |
| The API surface is hand-edited. | Regenerate it under isolated HOME, inspect the output, then run `test_api_surface.py`. |

- [ ] Read all focused test output before capturing evidence.
- [ ] Record the MCP walk's exact 135-tool result and `door.get` closed-schema
  assertion.
- [ ] Record the API test's 538-route generated-doc parity result under isolated
  HOME.
- [ ] Record the doc drift/product-copy and Mermaid renderer outputs separately.
- [ ] Verify `git diff --name-only` contains documentation and its documentation
  guard only: no product source, generated web bundle, or roadmap status file.

## Orchestrator dispositions (ruled 2026-08-28)

1. **The falsified-statements inventory is ACCEPTED as the work list**,
   including the narrow MODELS egress correction and the narrow
   onboarding/WEB_DESK arrival-language updates. The 29-vs-32
   resource-count split is respected — no universal replace.
2. **trust-destinations.json: ACCEPTED as recommended.** The ICS
   crossing is documented truthfully in the docs; NO fake registry
   entry (a data-only entry would claim enforcement that does not
   exist). The missing central badge/registry coverage for the
   calendar fetch is a PRODUCT GAP → phase close ledger, owner
   visible.
3. **The charter's `-k "doc or mcp_inventory"` selector is amended by
   this plan's named focused commands** (the story file's Test plan
   noted the selector was to be confirmed by the plan — it now is).
4. The inherited `test_product_language` planning-head failure stays
   what it is: baseline debt, out of this story's scope.

Build order: after HS-144-04 closes (single-writer tree).
