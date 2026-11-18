# The final handover of HoldSpeak: the extraction to Tenvil

Written 2026-11-14 by the orchestrator (Claude Fable 5.2), for a fresh session with no memory of this one.
HoldSpeak `main` is `081335d8d`. The owner's hub serves `baa85f08b` (the same code; the newer commits are documents).

This document is the whole brief. Read all of it before you start an agent.

---

## 1. The order, in the owner's words

2026-11-14, after a year of work on this repository:

> "It contains such an incredible mass of commits and literally a shit ton of documents… it's becoming really, really difficult to manage this repository and this project and its future."

> "What I want you now to focus on… is extraction… we grab only the core. So all of our web stuff, all of our Python backend stuff, none of the documentation, none. And we create a new repository, currently private, called Tenvil, T-E-N-V-I-L. Tenvil is going to be the new name of this program."

> "I expect the repository to be really, really slimmed down, really chiseled. We forget about the entirety of the history of this repository. We are building a new product from where we are today with HoldSpeak. So all of the history doesn't matter. Only the code matters, and only the code in its current state. All of the advancements we made, all of the refactorings that we've made, they are going over to Tenvil."

> "The org that will handle all of this is lopiksoft, and under it we will have tenvil." (This replaced his first idea of an organization named "Tenvil OS".)

> "Apple is legacy. AIPI-Lite - we drop it for now… apple and aipi-lite, are things we come back to later, from HoldSpeak. The extension almost doesn't matter at this point… not carried over either."

> "You actually become the orchestrator of Opus agents who then orchestrate within through Sonnet agents on a big, big move."

What this means, in one paragraph: a new private repository `lopiksoft/tenvil`, one first commit, no history, no documentation from HoldSpeak. It holds the Python hub and the web desk as they are today, their tests, and the smallest set of build files. The product is renamed Tenvil. HoldSpeak stays where it is, as the place to look things up.

Checked on 2026-11-14: the GitHub organization `lopiksoft` exists and the owner's account is an admin of it. `lopiksoft/tenvil` does not exist yet.

---

## 2. What the product is (the owner confirmed this the same day)

The owner's words:

> "Everything has to be funneled through a service so that we can basically express the entirety of our capabilities through essentially APIs, or at least, you know, ports."

> "This is meant to be a powerful system that allows people to work efficiently out of this desk interface. It's for professionals. It's for people who sit in meetings all day long, who have a bunch of priorities that are very difficult to keep track of. It's a system that allows you also to efficiently manage your AI agentic workflows… It allows you to develop products within this ecosystem, but also products that are completely disconnected from this ecosystem."

> "Let's say you are a senior architect and you work for a… medtech company delivering products. You are working out of this interface because you are able to extract all of the right context that's been… stored in directories in their own shapes and formats and sizes. You have access to decisions and so on. All those APIs are eventually exposed to agents through MCP servers."

The orchestrator's reading, which he said was right "on an architectural level":

- **Services are the backbone** (ports and adapters). The desk, MCP, Telegram and calls are clients of the same operations.
- **The desk is a desktop environment**, not a set of web pages: a window frame, a component kit, apps as clients of the kit. His phrase is "Workbench 2.0+ on steroids".
- **The loop the product serves:** capture (meetings, dictation, calls) → hold the context (projects, decisions, sources read where they live) → keep track (Needs you, commitments) → direct agents with that context → answer them from the desk or from a phone.
- **Agents get the same capabilities** through MCP, under rules about what they may see.

Rules of his that outlive the move (the full text is in HoldSpeak `CLAUDE.md` and `docs/internal/CONSTITUTION.md`; do not copy those files, carry the rules):

- One implementation of a thing. A change removes a seam or a second implementation; it never adds one.
- No over-engineering for safety. The product is "not even pre-alpha"; he is the only user.
- Product text in ASD-STE100 (Simplified Technical English).
- A face is judged live on his desk. A grey, flat face is a hold. No modals, no host chips, no counters of zero, every verb a kit Button.
- Tests never touch his real HOME, database or Keychain.
- Every merge can be reverted. Never push `main` directly; merge through a pull request.

---

## 3. Where HoldSpeak stands today

| | |
|---|---|
| `main` | `081335d8d` (documents only after `baa85f08b`) |
| The owner's hub | serves `baa85f08b` from `/Users/karol/dev/tools/wt-desk-main-20261025`, port 8765 |
| Checks on `baa85f08b` | whole browser suite 861 passed, 0 failed; whole non-browser suite 20,031 passed; quick check and repo guards green; web unit suite about 5,650 passed |
| Builders running | none |
| Open work | listed in `pm/STATUS.md`, top entry of 2026-11-14 ("LEFT, not started") |

Size, measured on `081335d8d`:

| | Files | Notes |
|---|---|---|
| Commits | 8,386 | none go over |
| Tracked files | 18,477 | |
| `docs/` | 4,636 (266 MB) | does not go |
| `pm/` | 4,794 (48 MB) | does not go |
| `holdspeak/` | 1,217 | 975 live `.py` files, 363,649 lines; 220 parked files |
| `web/` | 4,039 | 900 live source files, 204,217 lines; 574 live test files; 1,449 parked files |
| `tests/` | 2,433 | 1,390 live `.py` files, 13,638 tests; 869 parked files |
| `scripts/` | 234 | about 45 are used by the product, the tests or the checks |

The target: a repository of roughly 3,000 to 3,500 files where every file is live code, a live test, a fixture a test reads, or a build file.

---

## 4. The manifest: what goes and what stays

"Goes" means: copied into the new tree, then cut and renamed as sections 5 to 7 say. "Stays" means: it remains in HoldSpeak only.

| Path | Verdict | Why |
|---|---|---|
| `holdspeak/` | **Goes**, without any `_parked/` directory | the Python hub |
| `web/src/` | **Goes**, without any `_parked/` directory and without `*.txt` copies of code | the desk |
| `web/public/` | **Goes**, without `desk/sprites/_parked-*` | sprites, atmospheres, sounds |
| `web/` root files (`package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `briefing.html`, `atmospheres.html`, `design-tokens.json`, `token-allowlist.json`, `fence-baseline.json`) | **Goes** | the build |
| `web/scripts/` | **Goes**, only the scripts that `web/package.json` runs | `check` chain; drop the gallery and atmosphere shooters that read `docs/` or write `pm/` |
| `web/design/icons/` | **Goes**, only the 54 live files | 520 of 574 are parked |
| `web/uat/_runs/` | Stays | three stray screenshots |
| `web/README.md`, `web/AGENTS.md`, `web/ICON-DISCIPLINE.md`, `holdspeak/AGENTS.md` | Stays | documentation |
| `tests/unit`, `tests/integration`, `tests/e2e`, `tests/critical`, `tests/mcp`, `tests/web`, `tests/mocks`, `tests/fixtures`, `tests/memory_bench`, root helpers (`conftest.py`, `_evidence.py`, `room_bindings.py`, `watch_seed.py`, …) | **Goes**, minus the files section 6.2 lists | the safety net; the owner said "only the code": tests are code |
| `tests/_parked/`, `tests/e2e/_parked/`, `tests/fixtures/_parked/` | Stays | 869 files, not collected |
| `tests/uat/` and top-level `uat/` | **Decision D3** (section 11) | 17 test files import the `uat` package (124 tests) |
| `scripts/` | **Goes**, only the keep list of section 6.3 | about 45 of 234 |
| `pyproject.toml`, `uv.lock`, `hatch_build.py`, `.gitignore` | **Goes**, edited | the package and its build |
| `LICENSE`, `NOTICE` | **Goes** | Apache-2.0; `NOTICE` is required by the herdr-derived files in `holdspeak/agent_context/rules/*.toml` |
| `README.md` | Stays; a new one is written (section 8) | `pyproject.toml` needs a readme to build |
| `CLAUDE.md`, `AGENTS.md` | Stays; a new short one is written (section 8) | working agreements for the new repository, not the old ones |
| `docs/` | Stays, except two data files (section 5.1) | "none of the documentation, none" |
| `pm/` | Stays | status, roadmap, evidence |
| `apple/` | Stays | "Apple is legacy" |
| `aipi-lite/` | Stays | "we drop it for now" |
| `extensions/` | Stays | "not carried over either" |
| `.githooks/` | **Decision D2** (section 11) | a vendored copy of Delivery Workbench; product features and 7 test files run it |
| `.github/workflows/` | Stays; new workflows are written (section 8) | four of six serve docs, the Apple app or the gallery |
| `agent/`, `dogfood/`, `architecture/`, `gallery/`, `designer-handoff/`, `parked/`, `.holdspeak/`, `.mcp.json`, `demo.tape`, `.guru_meditation.md`, `.gitattributes`, `CHANGELOG.md`, `CONTRIBUTING.md`, `THIRD_PARTY_NOTICES.md`, `screen-*.log` | Stays | process, history, dogfood rigs, stray files |

---

## 5. What must be cut so the core stands alone

A plain copy of `holdspeak/`, `web/` and `tests/` does not build and does not pass its tests. These are the links to cut. File and line numbers are from `081335d8d`.

### 5.1 Two data files live in `docs/` and ship in the wheel

- `docs/product-language.json` and `docs/trust-destinations.json` are copied into the wheel by `pyproject.toml` (sdist include near lines 208–209, wheel force-include near 234–235) and read at runtime by `holdspeak/product_language.py:279` and `holdspeak/trust_destinations.py:10` (the second at import time).
- `web/src/lib/productLanguage.test.ts:33` reads `../docs/product-language.json`; it is in `npm run check`.
- **Do:** move both files into the package as `holdspeak/data/product-language.json` and `holdspeak/data/trust-destinations.json`; make the two modules read only that place; remove the force-include; point the web test at the package copy. `web/src/lib/productLanguage.ts` is a hand-kept copy of the same data: make one of them the source (D6 in section 11).

### 5.2 Product code that reads this repository's own documents

| Where | What it reads | Do |
|---|---|---|
| `holdspeak/mcp/resources.py:39, 477` | `docs/internal/CONSTITUTION.md` as MCP resource `holdspeak://desk/constitution` | remove the resource (it is already broken in an installed wheel) |
| `holdspeak/services/roadmap_service.py:323` (also 52, 72, 171, 259) | this checkout's `pm/roadmap/*`, `pm/archive-manifest.txt`, runs `.githooks/dw` | the default root becomes "none": the feature serves only a repository the person registers. See D2 |
| `holdspeak/delivery/pr_receipts.py:672` | `<source>/pm/roadmap/holdspeak/phase-*` | the slug `holdspeak` is hard-coded for a registered source; make it the source's own slug or remove with D2 |
| `holdspeak/line/install.py:39` | `scripts/line/build-baresip-linux.sh` | carry the script (it is on the keep list) |
| `holdspeak/services/program_canon.py:33`, `program_service.py:67`, `program_runner.py:1477` | `tests/e2e/test_desk_sweep.py`, `scripts/ux_canon_scan.py`, `scripts/quick_check.sh`, `scripts/test_lock.py` in the target repository | these assume the product works on its own repository; they hold after the move because those files go over. Leave them; note them for a later generalisation |
| `holdspeak/services/program_planner.py:54`, `holdspeak/program_templates.py:37` | lists of this repository's folders (`pm/`, `docs/`, `parked/`, `dogfood/`, `aipi-lite/`, …) | reduce to the folders that exist in Tenvil |
| Comments that cite `docs/…` or `pm/…` | — | delete the citation; keep the sentence that explains the code |

### 5.3 Tests that read outside the core

- `web/src/desk/components/delivery06.test.tsx:8-9` imports two JSON fixtures from `apple/Tests/ContractsTests/Fixtures/`. **Do:** copy the two files beside the test.
- `tests/unit/test_architecture_tools.py:88` reads `architecture/desk-workspace.schema.json`. It is a documentation-tool test: it goes with section 6.2.
- `tests/integration/program_plan_seed.py:60` reads `.holdspeak/program.json`. **Do:** move that one file into `tests/fixtures/` and read it there.
- `tests/unit/doc_claims/registry.py:260` reads `.mcp.json`; the registry is dead (its runner is parked). Keep only `raw_button_count`, which `tests/unit/test_ux_canon_scan_shapes.py:36` imports; move it beside its user.
- About ten product test files hold one test or fixture that reads `docs/` or `pm/` (for example `tests/unit/test_coder_gate.py:539`, `test_program_text.py:263`, `test_desk_seed.py:166`, `test_meeting_prepared_plan.py:14`, `tests/own_agents_rig.py:10`). **Do:** for each, copy the small fixture it needs into `tests/fixtures/` or drop the one test if it guards a document.
- Two live tests import parked code: `tests/unit/test_agent_hand_queue_outcome.py:75` and `tests/unit/test_schema_retirement.py:11`. **Do:** rewrite or drop them; no `_parked` goes over.

### 5.4 Clients that stay behind

`apple/`, `aipi-lite/` and `extensions/` stay. The hub still has code that only serves them (push to the iPhone app in `holdspeak/phone/push.py`, the device audio socket, the extension's intake route in `holdspeak/web/routes/activity/enrichment.py`, the mesh companion paths). **Do not cut that code during the extraction.** It is recorded as a later chisel (section 12), after Tenvil is green. Mixing a move with a removal of server code hides which one broke a test.

---

## 6. The chisel inside the core

### 6.1 Parked material: none of it goes

| Tree | Parked files | Lines |
|---|---|---|
| `holdspeak/**/_parked` | 220 | 38,289 |
| `web/src/**/_parked` | 731 | 202,386 |
| `web/public/desk/sprites/_parked-*` | 198 | images |
| `web/design/icons/_parked-*` | 520 | images |
| `tests/**/_parked` | 869 | 216,461 |
| `scripts/_parked` | 3 | 363 |

HoldSpeak's rule was "never delete, park instead". Tenvil starts with no parked directory at all, and HoldSpeak is the archive. Remove the `_parked` excludes from `web/tsconfig.json` and `web/vite.config.ts`, and `tests/_parked/conftest.py` does not exist. One live fixture directory is named `web/src/desk/__tests__/fixtures/parked-wire/`: it is live; keep it.

### 6.2 Tests that guard documents or process: they do not go

About 17 whole files (about 189 tests) exist to check documents, the canon, the atlas or PM files: `tests/unit/test_doc_drift_guard.py`, `test_docs_navigation.py`, `test_doc_generator_checkout.py`, `test_mcp_sidecar_doc_drift.py`, `test_engines_name_guard.py`, `test_product_language.py` (keep the parts that check the data file, drop the Swift scan), `test_primitive_contract.py`, `test_blueprint_graph_conformance.py`, `test_evidence_archive.py`, `test_evidence_scratch_guard.py`, `test_architecture_tools.py`, `tests/e2e/test_mermaid_renders.py`, `tests/e2e/test_roadmap_glass.py`, and the atlas family (`tests/unit/test_graph_atlas.py`, `tests/e2e/test_walk_rig.py`, `test_walk_rig_clearance.py`, `test_graph_walk_smoke.py`, `test_decisions_readable_rows.py`), which reads `docs/internal/philo/graph/atlas*.json`.

The atlas family is the one real loss of coverage: it walks the desk along a graph kept in `docs/`. It is **Decision D4**. The orchestrator's recommendation is to leave it behind: the desk sweep (`tests/e2e/test_desk_sweep.py`, every app at three sizes) and the per-app glass files stay and are the live guard.

Before you delete a guard, read it once: where it checks a product fact (not a document), keep that part.

### 6.3 `scripts/`: the keep list

Keep only what the product, a kept test or a check runs. Start from this list and let the test run correct it:

- **The checks:** `quick_check.sh`, `quick_check_affected.py`, `quick_check_memo.py`, `main_check.sh`, `test_lock.py`, `vitest_related.py`, `glass_for.py`, `check_web_baseline.py`, `ux_canon_scan.py`, `lane.sh`, `linux_smoke.sh`, `measure.py` with `measure_seams.json`.
- **Used by the product:** `line/build-baresip-linux.sh`.
- **Loaded by kept tests** (verify each by running the tests): `walk.py`, `reach_runner.py`, `operation_parity.py`, `gen_operations_json.py`, `residual_census.py`, `prune_empty_polls.py`, `program_import_history.py`, `record_room_wires.py`, `record_steward_fixture.py`, `record_connected_workspace_fixture.py`, `wire_metal_intel.py`, `philo5_pairs.py`, `philo13_needs_you_fixture.py`, `needs_you_faces_fixture.py`, `philo13_meetings_headline_fixture.py`, `philo13_b4_fixture.py`, `philo11_send_job.py` and what it imports (`philo9_room_job.py`, `philo7_file_and_find.py`, `philo5_his_words.py`), `phase200_eval.py`.
- **The fixture recorders** a kept fixture needs to be made again after the rename (the `record_*` family, 24 files): keep those whose output a kept test reads.
- **`install.sh`:** keep and rename (it is the end-user installer).

Everything else stays: about 95 screenshot and walk rigs, about 48 one-off phase scripts, about 20 document generators, `orchestrate/` (it drives Codex builders; the new orchestration is different, section 10), `astra`, the AIPI scripts.

Rename the survivors that carry a phase name (`philo13_b4_fixture.py` and the like) to say what they do. Do that after the suite is green, as its own commit.

### 6.4 Dead and superseded code still in the tree (candidates, not orders)

Imported only by parked code (safe to leave behind): `web/src/features/concierge/concierge.css`, `web/src/features/project-room/core/slots.tsx`, `web/src/desk/people/PeopleReadFailed.tsx`, `web/src/desk/components/inlet-autocomplete.css`, `web/src/pages/cores/dictation/index.ts`.

Used only by tests or document scripts: `holdspeak/product_copy.py` (564 lines), `holdspeak/realtime_frames.py` (240), `tests/unit/doc_claims/registry.py` (880).

Self-described as legacy or retired but still imported (each is a later chisel with its own test run, not part of the move): `holdspeak/missioncontrol_bridge.py` and the `/api/missioncontrol/*` surface, `holdspeak/kernel/inference.py`, `holdspeak/meeting_session/intel_plan.py`, `holdspeak/slack_export.py`, `holdspeak/workbench_templates.py`, the legacy alias in `holdspeak/web/routes/meeting_import.py`, `web/src/desk/store.ts` (a re-export shim with about 294 importers), `web/src/desk/surface/controls/MicButton.tsx`, `web/src/components/signal/Signal.tsx`, `web/src/pages/cores/design-reference/ControlsGallery.tsx`.

### 6.5 Fixtures

Recorded hub answers stay as test doubles (about 12.5 MB in `web/src`, 2.5 MB in `tests/fixtures`). After the rename they are recorded again, not text-replaced (section 7.4). Two WAV files in `tests/fixtures` (1.2 MB) and six desk textures in `web/src/desk/gl/textures/` (3.9 MB) are live.

---

## 7. The rename: HoldSpeak becomes Tenvil

The name appears about 26,000 times in about 3,040 files of the core. It is in code, in what is stored on a machine, in other tools' configuration, in wire protocols and in encryption domains.

### 7.1 The basis: a clean break (Decision D1)

The orchestrator recommended, and wrote this plan on the basis, that **Tenvil has no compatibility with HoldSpeak's stored state**: new folders, new Keychain names, new MCP server name, no migration code, no "read both names" shim. The owner is the only user. His HoldSpeak state is parked, as in the fresh starts of 2026-10-08 and 2026-11-02, and he sets Tenvil up as a new install.

**Ruled by the owner, 2026-11-14,** in answer to the four decisions the orchestrator put first (D1, D2, D4, D5): "Yes. That's fine. I'm okay with it. No compatibility." D1 is settled in his own words: no compatibility. The orchestrator reads "That's fine. I'm okay with it" as acceptance of the recommendations for D2, D4 and D5 as written; he named only compatibility, so confirm those three in one line at stage 0. If he later misses some data, write a one-time import tool; do not put compatibility code in the product.

### 7.2 The names

| Thing | HoldSpeak | Tenvil |
|---|---|---|
| Python package and distribution | `holdspeak` | `tenvil` |
| Commands | `holdspeak`, `holdspeak-mcp` | `tenvil`, `tenvil-mcp` |
| npm package | `holdspeak-web` | `tenvil-web` |
| Environment variables | `HOLDSPEAK_*` (133 names) | `TENVIL_*` |
| Data, config, state | `~/.local/share/holdspeak/`, `~/.config/holdspeak/`, `~/.holdspeak/` | `~/.local/share/tenvil/`, `~/.config/tenvil/`, `~/.tenvil/` |
| Database, log | `holdspeak.db`, `holdspeak.log` | `tenvil.db`, `tenvil.log` |
| Keychain services | `HoldSpeak`, `HoldSpeak People`, `… Line`, `… Phone`, `… Email`, `… Slack` | `Tenvil`, `Tenvil People`, … |
| Per-project folder | `<repo>/.holdspeak/` (and `.hs/`) | `<repo>/.tenvil/` (one name; see D5) |
| Git refs in project repositories | `refs/holdspeak/checkpoints`, author `HoldSpeak <holdspeak@localhost>` | `refs/tenvil/checkpoints`, `Tenvil <tenvil@localhost>` |
| MCP server, resource scheme | `holdspeak`, `holdspeak://` | `tenvil`, `tenvil://` |
| HTTP headers, socket subprotocols | `X-HoldSpeak-Token`, `X-HoldSpeak-Node-Token`, `holdspeak.v1`, `holdspeak.auth.v1.` | `X-Tenvil-Token`, `X-Tenvil-Node-Token`, `tenvil.v1`, `tenvil.auth.v1.` |
| mDNS service | `_holdspeak._tcp` | `_tenvil._tcp` |
| launchd, systemd | `com.holdspeak.line`, `holdspeak-line.service` | `com.tenvil.line`, `tenvil-line.service` |
| Browser storage | `holdspeak.*` keys, IndexedDB `holdspeak-voice-recovery`, events `holdspeak:*` | `tenvil.*`, `tenvil-voice-recovery`, `tenvil:*` |
| Product text | "HoldSpeak" (about 52 lines of UI text, about 325 Python string lines) | "Tenvil" |
| Sent-files folder | `~/Documents/HoldSpeak/Sent` | `~/Documents/Tenvil/Sent` |
| Repository URLs | `karolswdev/HoldSpeak` | `lopiksoft/tenvil` |
| Image | `web/public/holdspeak-mark.png` | a new mark from the owner; until then rename the file and keep the picture (D7) |

### 7.3 Traps a blind search-and-replace falls into

1. **`holdspeak.db` is both a Python module path and a file name.** Replace the module path by import rewriting, the file name by its constant in `holdspeak/db/core.py:48`.
2. **Strings that look like module paths but are stored or signed identifiers.** With the clean break they may all change, but change them on purpose, as a list, and run the tests that cover each:
   - encryption domain of People records: `holdspeak/people/crypto.py:55` (`b"holdspeak.people.v1\0…"`);
   - mesh signing domains: `holdspeak/mesh_authority/offer.py:61`, `report.py:41`, `holdspeak/kernel/mesh_local_authority.py:35`;
   - phone pairing: JWT issuer and `hub_id` hash in `holdspeak/phone/devices.py:41, 138`;
   - contract names in receipts: `holdspeak.ask`, `holdspeak.thread`, `holdspeak.whisper-*`, `holdspeak.dictation-*`, `holdspeak.meeting-*`, `holdspeak.refinement.*`;
   - hash inputs: `holdspeak/services/refinement_context_service.py:23, 133`, `holdspeak/services/launch_rebrief.py:114`;
   - values written to rows: `made_by="holdspeak_default"`, `BUILTIN_FOLDER_ID = "holdspeak-folder"`, speaker and `ended_by="holdspeak"`, calendar UIDs `@holdspeak-snapshot`.
3. **Tokens with the `HOLDSPEAK_` prefix that are not environment variables:** the error code `HOLDSPEAK_ERROR`, the push category `HOLDSPEAK_REPLY`, the stdout sentinel `HOLDSPEAK_SIGNIN_DONE`, the Vite define `__HOLDSPEAK_BUILD__`.
4. **Recognition of installed hooks by command name:** `holdspeak/agent_context/hooks.py:426` (`basename == "holdspeak"`), the pi hook file `holdspeak.json`, the extension `holdspeak-pi.ts`, the skill at `skills/holdspeak/SKILL.md`.
5. **A system prompt that names the product** (`holdspeak/calls/service.py:57`, "You are HoldSpeak…"): recorded answers that depend on it change.
6. **Seed data:** `holdspeak/seeds/fresh-desk.yaml` and `holdspeak/agent_skill/SKILL.md` carry the name and are written into a new desk.
7. **File and directory names:** the package directory itself, `holdspeak/agent_context/pi_extension/holdspeak-pi.ts`, `tests/uat/test_no_holdspeak_import.py`, `tests/fixtures/dictation_demo_project/.holdspeak/`, `web/public/holdspeak-mark.png`.
8. **The abbreviation `hs`** is a different thing (D5): `--hs-*` CSS tokens (291 uses), `.hs/` as a project folder, `hs.` and `hs:` storage keys (about 40), `hs-<slug>` tmux sessions, `HS-nnn` story ids in comments.

### 7.4 Order of the rename

Do the rename only after the extracted tree is green under the old name (stage 3 in section 9). Then, one commit per step, each verified:

1. The Python package: directory, imports, string module paths, patch targets in tests, entry points, logger names, `pyproject.toml`, `hatch_build.py`, `web/vite.config.ts` output path. Gate: the whole non-browser suite.
2. Environment variables, by an exact list of the 133 names (the list is produced by `git grep -oh "HOLDSPEAK_[A-Z0-9_]*" | sort -u`). Gate: the whole non-browser suite and the browser rigs' environment (the isolation switches in every rig hub).
3. Stored locations, Keychain names, launchd and systemd names, temp prefixes, tmux names. Gate: the hub tests and the doctor tests.
4. Wire and protocol names: MCP, headers, subprotocols, mDNS, resource URIs, browser storage keys, custom events. Gate: the web unit suite and the whole browser suite.
5. The stored and signed identifiers of trap 2, as one reviewed list. Gate: the People, mesh, phone and receipt tests.
6. Product text, seed data, prompts.
7. Record the fixtures again with the recorders (`TENVIL_WIRE_WRITE=1`, `TENVIL_WRITE_WIRE_FIXTURES=1`); do not text-replace recorded answers, some carry digests of their own content. Gate: every suite.
8. The `hs` abbreviation, if D5 says so.

End state: `git grep -i holdspeak` returns nothing in `lopiksoft/tenvil`. Add that as one test so the name cannot come back.

---

## 8. The new repository

- **Create:** `gh repo create lopiksoft/tenvil --private`. This is an outward act: do it when the owner says go, not before.
- **History:** the first commit is the green extracted tree. Do the work in a scratch directory with its own `git init`, commit stage by stage there for your own safety, then squash to one commit before the first push. No HoldSpeak commit, tag or author history goes over.
- **Layout:** the same as today (`tenvil/` after the rename, `web/`, `tests/`, `scripts/`, build files). Do not reorganise during the move.
- **Files written fresh, not copied:**
  - `README.md`: under 40 lines. What Tenvil is (two sentences from section 2), how to install for development (`uv sync --extra dev`, `cd web && npm ci`), how to run the hub, how to run the checks. No feature tour.
  - `CLAUDE.md`: under 60 lines: the rules of section 2, the three checks, the test commands with an isolated HOME, the test lock, "whole browser suite to a log after any kit or frame change", "no `_parked` directories; delete, HoldSpeak and git are the archive". Do not import HoldSpeak's history of rulings.
  - `.github/workflows/`: one `test.yml` (web check; unit; integration; scoped browser tests), one `nightly.yml` (whole suite). No docs job, no mobile job, no gallery, no release to PyPI until the owner asks (the PyPI name `tenvil` is not reserved; D8).
  - `.gitignore`: the Python, venv, `web/node_modules`, `web/dist`, built bundle and `.tmp/` lines only.
  - `.mcp.json`: the `tenvil` server for agents that work on the repository.
- **`pyproject.toml`:** name `tenvil`, version `0.1.0` (a new product), the two entry points, the URLs, the sdist include without `docs/` and with only the kept scripts, the wheel artifacts path, the coverage paths, the pytest markers.
- **`LICENSE`, `NOTICE`:** copied; update the product name where `NOTICE` names it.

---

## 9. The plan, in stages with gates

Each stage ends on a gate. Do not start the next stage on a red gate.

| Stage | Work | Gate |
|---|---|---|
| 0. Freeze | Ask the owner the open decisions of section 11. Tag HoldSpeak `main` as `tenvil-extraction-base`. No merge into HoldSpeak during the move. | The tag exists; the decisions are answered or defaulted in writing |
| 1. Copy by manifest | A script (kept in HoldSpeak, not in Tenvil) copies the "Goes" paths of section 4 from the tagged commit into a scratch tree, leaving out every `_parked` path, every `*.txt` copy of code and the "Stays" paths. `git init` there. | File count and a listing by top-level directory match the manifest; no path contains `_parked` |
| 2. Cut the links | Section 5: the data files, the document reads, the outside fixtures, the tests of section 6.2 removed, the scripts reduced to the keep list, `pyproject.toml` and build fixed. | `uv sync --extra dev` works; `uv build` makes a wheel that holds the web bundle; `cd web && npm ci && npm run check` passes |
| 3. Green under the old name | Run everything; fix what the cut broke; drop only tests that guard something that stayed behind, and write each drop in a list with its reason. | Whole non-browser suite green; web unit suite green; whole browser suite green, run to a log file. Compare the counts with section 3 and explain every difference |
| 4. Rename | Section 7.4, step by step. | After each step its gate; at the end `git grep -i holdspeak` is empty |
| 5. Green as Tenvil | Fixtures recorded again; every suite. | The same three suites green; the built wheel installs in a clean virtual environment and `tenvil web --no-open` serves the desk |
| 6. First push | Squash to one commit; create `lopiksoft/tenvil`; push; CI green on GitHub. | CI green on the first commit |
| 7. The owner's desk | Stop the HoldSpeak hub; park his HoldSpeak state (`~/.local/share/holdspeak`, `~/.config/holdspeak`, `~/.holdspeak`, the Keychain items stay untouched); install Tenvil; start its hub on 8765 with the Tailscale address; walk the first run with him. | He opens the desk and judges it live |
| 8. Close HoldSpeak | One last line in `pm/STATUS.md`; archive the GitHub repository read-only (not deleted). | He says so |

Stage 7 touches his machine and his running hub: confirm with him at that moment. Stages 1 to 5 touch nothing of his.

---

## 10. How to orchestrate the move

The owner's instruction: the orchestrator directs Opus agents, and each Opus agent directs Sonnet agents. (HoldSpeak's builders were Codex Sol sessions; that ruling of 2026-11-09 is not the instruction for this move. Model ids: Opus `claude-opus-5-5`, Sonnet `claude-sonnet-5-5`.)

### 10.1 Roles

- **The orchestrator (Fable):** holds this document, the manifest and the gates; talks to the owner; starts one Opus lead per workstream; reads their reports; runs the gates itself; decides. It writes no bulk edits.
- **An Opus lead:** owns one workstream end to end. It splits the work into pieces that share no files, gives each piece to a Sonnet worker with an exact brief, checks every result against the code (not against the worker's summary), integrates, runs the workstream's tests, and reports.
- **A Sonnet worker:** does one bounded, mechanical or well-specified piece (a directory, a list of files, one category of the rename) and reports what it changed and what it could not do.

### 10.2 Workstreams

Stages 1 to 3 (they can overlap only where the table says):

| Lead | Workstream | Sonnet pieces | Depends on |
|---|---|---|---|
| A | The copy script and the scratch tree; `pyproject.toml`, `hatch_build.py`, the build | manifest listing; build fix | — |
| B | Hub links: section 5.1 and 5.2 | one piece per row of the tables | A |
| C | Test triage: section 5.3 and 6.2; the list of dropped tests with reasons | by test directory | A |
| D | `scripts/` keep list and `uat/` (per D3); the checks run in the new tree | by script group | A |
| E | Web: remove parked excludes, the outside fixtures, `web/scripts`, `npm run check` | by `web/` area | A |
| F | Fresh files and CI: section 8 | — | A |

Stage 4 (strictly in the order of section 7.4, one lead at a time on the tree, because every step touches most files):

| Lead | Workstream | Sonnet pieces |
|---|---|---|
| G | Rename steps 1 to 3 (package, environment, stored locations) | by top-level package and by test directory, from an exact generated list |
| H | Rename steps 4 to 6 (wire names, stored identifiers, text) | by category |
| I | Rename step 7: record fixtures again; step 8 if D5 says so | by recorder |

### 10.3 Rules that this repository paid for (keep them)

- **A brief is exact.** It names the files, the rule, the test command and what "done" is. A worker that must guess will guess.
- **Two agents never edit the same file at the same time.** Split by directory. The rename is serial for that reason.
- **Decide one mechanism before two agents solve the same problem.** In wave 14 two builders built two "whole rows" mechanisms in one night.
- **A summary is not evidence.** A lead reads the diff; the orchestrator runs the gate. Reports of "passed" were wrong several times in this repository because a run's output was cut.
- **Run suites to a log file** (`pytest -rf … > file 2>&1`), never through `| tail`. Read the failing test ids from the file.
- **One CPU budget.** Every pytest and vitest run goes through `scripts/test_lock.py`. A browser run counts its workers twice. A load above the core count is a fault.
- **Tests use an isolated HOME** in the system temp directory (`H=$(mktemp -d); HOME=$H …`), with `PLAYWRIGHT_BROWSERS_PATH` and `npm_config_cache` pointed at the real caches. Never the owner's HOME, database or Keychain.
- **A new worktree is synced with `uv sync --extra dev` only.** Never symlink `node_modules` or `.venv` between trees and then reinstall through the link.
- **"Timed out under load, passes alone" three times is a finding.** In wave 14 it was a real stall (one browser layout per list cell).
- **After a change to the kit or the window frame, the whole browser suite runs before the next change lands.**
- **A security surface gets one review by a fresh agent after it lands** (the gate, tokens, egress, Telegram, credentials, any new write path), bounded to the diff, and its findings are fixed forward with a test per finding. The rename's step 5 (signed and encrypted identifiers) is such a surface.

### 10.4 What the orchestrator reports to the owner

Short, plain, and with the gate result first. What is green, what is red and why, what was dropped and why, what he must decide. Nothing is reported as approved by him unless he said it.

---

## 11. Decisions for the owner

Each has the orchestrator's recommendation. D1 is ruled. Ask the others together, once, at stage 0 (D2, D4 and D5 need only a one-line confirmation; see section 7.1).

| | Decision | Recommendation |
|---|---|---|
| D1 | Does Tenvil keep any compatibility with HoldSpeak's stored state (data folders, Keychain, pairings, MCP names)? | **RULED 2026-11-14: "No compatibility."** A clean break; his HoldSpeak state is parked |
| D2 | Delivery Workbench (`.githooks/dw`, 40 files): product features (roadmaps, Programs delivery) and 7 test files (about 98 tests) run the vendored copy | Do not carry `.githooks/`. The product already falls back to a `dw` on PATH. Carry the vendored copy only as test support under `tests/support/dw/`, and decide later whether the integration stays in the product at all |
| D3 | `uat/` (290 files): a UAT framework that runs the product as a subprocess; 17 test files (124 tests) import it | Carry `uat/conductor` and what those tests import; leave the guided site, decks and campaign documents behind |
| D4 | The atlas (a graph of the desk kept in `docs/`) and its walk tests (about 110 tests) | Leave behind; the desk sweep and the glass files remain |
| D5 | The abbreviation `hs` (`--hs-*` tokens, `.hs/`, `hs.` storage keys, `hs-` tmux names) | Rename in step 8 of the rename, to `tv`/`.tenvil/`, so no trace of the old name stays; it is mechanical once the suites are green |
| D6 | `product-language` exists as JSON and as a hand-kept TypeScript copy | One source: the JSON in the package; the web reads it at build time |
| D7 | The mark and icons that show the old name or wordmark | He supplies a Tenvil mark; until then the files are renamed and the pictures kept |
| D8 | A public package name and a release | Not now; the repository is private and nothing is published |
| D9 | Hub code that only serves the Apple app, the AIPI device or the Firefox extension | Keep during the move; remove as the first chisel after Tenvil is green |

---

## 12. After the move (not part of it)

In the order the orchestrator would take them:

1. The chisel of D9 and of section 6.4, one at a time, each with its tests.
2. The owner's direction of 2026-11-07: pick work by core workflow, not by app. The loop of section 2 has never been walked end to end on the desk as one path. The proposal he was shown on 2026-11-14 and did not yet answer: make the product good enough for him to run one real working day on it, and fix only what that day breaks.
3. What wave 14 left (HoldSpeak `pm/STATUS.md`, 2026-11-14): the Room review Text field (the kit's `PadGadget` must clip to whole lines); Needs you at 900 leaves 49 px under ten rows; the Ask scope pop-up over the heading at 393; the Engines `+` menu and the Agents queued menu over the next row; two intermittent browser tests with no cause found (the Room at 1440, the Terminal at 393); the last 132 tool descriptions; the Automation definition as a Program template.
4. He has not judged the 40 px title bar or any wave-14 face. His last verdicts on the look of the desk were "sterile, so vanilla" (2026-11-11) and a pick of material direction D "but not with that fugly green".

---

## 13. What is not known

- Whether the document and census tests fail, skip or pass empty when their trees are missing: none was run without them.
- Whether contract names and operation factory strings are written into database receipts (it matters only if D1 changes).
- Whether the favicon, the touch icon and the menu mark hold the old wordmark as pixels.
- The exact set of scripts that kept tests load at run time: the keep list of section 6.3 is from a static search; the test run corrects it.
- Whether `tests/uat` can run with a reduced `uat/` tree (D3).
- How many of the recorded fixtures carry digests over text that holds the name.

---

## 14. Facts a new session needs on the first day

- **HoldSpeak checkout:** `/Users/karol/dev/tools/HoldSpeak`. Never commit to its `main` directly.
- **The owner's hub:** served from `/Users/karol/dev/tools/wt-desk-main-20261025` (detached), started with `HOME=/Users/karol HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_UI_FEEDBACK=1 nohup .venv/bin/python -m holdspeak.cli_entry web --no-open`, log at `~/.local/state/holdspeak/hub-main-20261107.log`. Links, always both, Tailscale first: `https://karols-macbook-pro.tailad9943.ts.net` and `http://127.0.0.1:8765`. Leave it running until stage 7.
- **Node:** `export PATH=$HOME/.nvm/versions/node/v22.21.0/bin:$PATH`. Web build: `cd web && npm run build` (writes `holdspeak/static/_built`). Browser rigs serve the built bundle: build before a browser run.
- **The suites today:**
  - non-browser: `HOME_REAL=$HOME; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q -n auto --dist worksteal -m "not slow" tests/unit tests/integration tests/critical tests/web tests/mcp tests/uat`
  - browser: the same environment, `uv run python scripts/test_lock.py --cpus 8 -- uv run pytest -q -rf -n 4 --dist worksteal -p no:cacheprovider tests/e2e > log 2>&1` (about 20 minutes)
  - web unit: `cd web && ./node_modules/.bin/vitest run --maxWorkers=4`; type check: `./node_modules/.bin/tsc --noEmit -p .`; the whole web gate: `npm run check`.
- **The surveys behind this document** were three read-only searches of `081335d8d` on 2026-11-14 (the other top-level folders; coupling and parked material; the rename surface). Their numbers are in sections 3 to 7. Verify a number before you depend on it.
- **The owner's manner:** direct, fast, profane when a thing is wrong. He granted wide permission ("yolo… permissions are pretty much granted"): decide and do, do not park decisions on him, do not send lists of caveats. Keep only the engineering gates: a test that fails first, a backup before a destructive act, one review after a change of authority, a look at the live desk after a deploy. One sentence from him is a ruling; record it in his words.
