# Architecture lane accuracy report

Date: 2026-10-29  
Base: `4dce2796d`  
Scope: the seven architecture-owned guides and the architecture audit artifacts.

## Result

The lane corrected the concrete architecture seams found in source review:

- `docs/ARCHITECTURE.md` now scopes the `InferenceRunner` contract to core
  inference. The Line's direct Parakeet ASR and Pocket TTS calls are named as a
  separate path. Evidence: `holdspeak/kernel/inference_runner.py:82-127`,
  `holdspeak/line/speech.py:123-185`, `holdspeak/line/node.py:674-690`.
- `docs/ARCHITECTURE.md`, `docs/KERNEL.md`, and `docs/SYSTEM_ARCHITECTURE.md`
  no longer imply that every kernel or model record is content-free. Parent
  input snapshots can retain caller prompt text. Evidence:
  `holdspeak/kernel/parent_run.py:105-107`,
  `holdspeak/db/schema.py:3480-3496`,
  `holdspeak/kernel/model.py:9-12,83-91`.
- Saved Agent or persona wording was corrected to Mode while wire names such as
  `recipe:<id>` and `kind='mode'` remain unchanged. Evidence:
  `holdspeak/db/schema.py:1435-1439`,
  `holdspeak/services/thread_service.py:499-513`.
- The Thread pullout is documented as parked, with Ask as the active browser
  conversation surface. Interview remains a Thread-backed service and API
  contract. Evidence:
  `web/src/desk/store/compositorSlice.ts:300-304`,
  `web/src/desk/store/types.ts:433-435`,
  `web/src/desk/components/AskPanel.tsx:11-17,26-28`,
  `holdspeak/services/interview_service.py:67-73`.
- Sync now says five classes. `SYNC_REGISTRY` and the separate window registry
  support the distinction. Evidence:
  `holdspeak/services/sync_service.py:32-80`,
  `holdspeak/services/desk_window_service.py:93-113`.
- Memory documentation now states the active desk page set of three and
  separates `memory.embed` assignment requirements from the local or owner-made
  defaults for semantic background jobs. Evidence:
  `holdspeak/memory/pages.py:101-134`,
  `holdspeak/memory/engine.py:155-205`,
  `holdspeak/memory/consolidate.py:23-32`.

`docs/KERNEL.md`, `docs/DATA_MODEL.md`, and `docs/SYSTEM_INTEGRATION_MAP.md`
were source-checked without unrelated prose changes. Their state enums,
provenance, recovery, storage, and integration claims remain supported by the
source anchors in `architecture-audit.json`.

## Verification

- `python3 scripts/check_docs.py docs/ARCHITECTURE.md docs/KERNEL.md docs/DATA_MODEL.md docs/DOMAIN_MODEL.md docs/RELATIONSHIP_AWARE_MEMORY.md docs/SYSTEM_ARCHITECTURE.md docs/SYSTEM_INTEGRATION_MAP.md`
  passed: 7 files checked, local targets and Markdown headings resolve.
- `git diff --check` passed.
- No product tests, live Desk/provider/Line actions, browser walk, hardware,
  network call, install, staging, or commit was performed.

## Unknowns

No live provider, Desk, browser, microphone, Line node, paired device, external
destination, scheduled run, memory rebuild, or database backup/restore was run.
The active `PAGE_SET` has three desk pages, while the module docstring at
`holdspeak/memory/pages.py:8-11` still describes two. Product code was out of
scope, so the guide follows the active implementation and records the source
inconsistency in the JSON audit.

Status: **DRAFT — hold for SHIP**.
