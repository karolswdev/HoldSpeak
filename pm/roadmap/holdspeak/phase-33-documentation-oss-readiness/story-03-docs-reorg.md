# HS-33-03 — `docs/` reorganization + index

**Status:** not-started.

## Goal

A newcomer opening `docs/` today sees 23 files where user guides sit next to
internal phase plans — they can't tell what's for them. Separate the two and add
an index that surfaces the user journey.

## Scope

- **Classify the 23 `docs/*.md`:**
  - *User-facing* (keep at `docs/`): `GETTING_STARTED`, `USER_GUIDE`,
    `MEETING_MODE_GUIDE`, `INTELLIGENT_TYPING_GUIDE`, `AGENT_HOOK_INSTALL`,
    `FIREFOX_EXTENSION_GUIDE`, `CONNECTOR_DEVELOPMENT`, `DEVICE_PROTOCOL`,
    `AIPI_LITE_DEV_WORKFLOW`, `SECURITY`, plus the new `MODELS.md` (HS-33-01).
  - *Internal / historical* (move to `docs/internal/`): the `PLAN_*` set,
    `CROSS_PLATFORM_ROADMAP`, `CROSS_PLATFORM_TASK_BOARD`, `LINUX_PORT_PLAN`,
    `LINUX_PORT_EXECUTION`, `RELEASE_HARDENING_CHECKLIST`.
- **Move** the internal docs to `docs/internal/` via `git mv` (preserve history).
- **`docs/README.md`** — an index: a "Start here" user path
  (Getting Started → User Guide → Meeting Mode → Models → …) and a short
  "Internal / historical plans" pointer to `docs/internal/`.
- **Fix links** the move breaks: grep every moved file's basename across the repo
  (README, code comments, other docs, **CLAUDE.md source-canon list**, the
  `pm/` source-canon references) and update the paths. Note: CLAUDE.md and the
  roadmap reference some `docs/PLAN_*.md` as "source canon" — those references
  must be repointed to `docs/internal/PLAN_*.md`.

## Test plan

- A repo-wide grep shows no dangling `docs/<moved-file>.md` reference.
- Add/extend a lightweight link-check (the HS-32-06 drift guard can grow a
  "no doc links a non-existent path" assertion, or a dedicated test).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.

## Done when

- [ ] User-facing vs internal/historical docs are separated; `docs/internal/`
      holds the plans (history preserved via `git mv`).
- [ ] `docs/README.md` index surfaces the user journey.
- [ ] No broken inbound links (incl. CLAUDE.md / roadmap source-canon refs);
      full suite green.
