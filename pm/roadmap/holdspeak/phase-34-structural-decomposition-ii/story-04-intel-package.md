# HS-34-04 — Decompose `intel.py` → `intel/` package

- **Status:** done (2026-06-03). Evidence: [evidence-story-04.md](./evidence-story-04.md).

## Goal

`intel.py` is 1,066 lines mixing provider resolution + egress posture, JSON
coercion/parsing helpers, and the `MeetingIntel` engine. Decompose it into an
`intel/` package with a full re-export `__init__`, mirroring the Phase-31 db split —
so every `from holdspeak.intel import X` caller is unchanged.

## Scope

- Create `holdspeak/intel/` (replacing the single module) with:
  - `models.py` — `ActionItem`, `IntelResult`, `MeetingIntelError`, and the
    `DEFAULT_INTEL_*` / `VALID_INTEL_PROVIDERS` constants (the suggested-default
    model path landed here in HS-33-01).
  - `providers.py` — provider resolution + egress posture:
    `resolve_intel_provider`, `get_local_intel_runtime_status`,
    `get_cloud_intel_runtime_status`, `get_intel_runtime_status`,
    `resolve_llm_capability`, `build_configured_meeting_intel`,
    `intel_egress_posture`, and the cloud key / base-url helpers
    (`_resolve_cloud_api_key`, `_effective_cloud_api_key`, `_is_self_hosted_base_url`,
    `_validate_base_url`, `_normalize_provider`).
  - `parsing.py` — the response/JSON helpers: `_json_only_messages`,
    `_extract_json`, `_coerce_str_list`, `_coerce_action_items`,
    `_extract_openai_message_text`, `_extract_status_code`, `_describe_cloud_exception`,
    `_generate_action_item_id`.
  - `engine.py` — the `MeetingIntel` class (the big consumer of the above).
  - `__init__.py` — re-export the **full public surface**, so the import path is
    stable.
- Phase-31 lessons apply: per-module imports, relative-import depth, `ruff
  --select F821`, and **monkeypatch targets follow the symbol** — the intel test
  suite is large (`test_intel_*.py` ×5: cloud/coerce/command/egress_invariant/
  enhanced/extract/queue); grep their patch targets and re-export so each resolves.
  The **egress-invariant** test is the one to watch — keep the egress-posture seam
  exactly where it patches.

## Test plan

- `grep` the `test_intel_*.py` suite + other callers for `holdspeak.intel.<symbol>`
  patch/import targets; confirm each resolves post-split.
- `ruff --select F821` on each new module.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green (the intel
  egress-invariant + queue tests especially).
- `uv run ruff check holdspeak/intel/` — clean.

## Done when

- [x] `intel.py` → an `intel/` package (models / providers / parsing / engine).
- [x] `__init__` re-exports the full public surface; no caller or test import
      changed; egress-invariant + intel suite green.
- [x] Full suite green; package ruff-clean.
