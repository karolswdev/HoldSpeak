# Evidence — HS-46-01: Doc truth audit & drift fix

**Date:** 2026-06-06. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-46-documentation-lift`.

## What shipped

The accuracy foundation the rest of Phase 46 builds on: every user-facing doc
inventoried against live code, the factual drift fixed, and the headline
"cool fact" (the plugin count) pinned by a new guard so it can't silently rot.

### The audit doc

`docs/internal/DOC_AUDIT_2026-06.md` — a durable, reusable map:

- A **canonical-facts table** (the yardstick) verified against code: 14 built-in
  plugins (all real, zero stubs); 5 intent types / 5 routing profiles; journal
  on-by-default; presence config-backed; actuators off + default-safe; the fixed
  180 s cloud-intel timeout (not a config key); 9 CLI subcommands; 10 page routes;
  retired TUI/menubar; version 0.2.1 pre-release.
- A **per-doc verdict table** for all 18 live user-facing/root docs (Fresh / Minor
  drift / Stale) with the findings keyed.
- The drift findings (fixed), a **verified-correct** section (so a future pass
  doesn't "fix" things that are already right — see the anchors note below), a
  noted-not-fixed item, the provenance-doc list, and the guard description.

### Drift fixed (4 findings across 6 docs)

- **F1 — presence sold as env-var-only.** `README.md:26`,
  `docs/INTELLIGENT_TYPING_GUIDE.md` §11 "Turn it on", `docs/GETTING_STARTED.md`
  Tip all presented `HOLDSPEAK_DESKTOP_PRESENCE=1` as the enable path. Since
  HS-43-04 presence is **config-backed** (`presence.enabled`, flipped from
  Settings / the welcome wizard; `desktop_presence.py:228`, `web_runtime.py:644`);
  the env var is a retained force-on override. All three now lead with the toggle
  and label the env var as the headless/power-user override.
- **F2 — phantom config key.** `docs/MEETING_MODE_GUIDE.md:399` listed
  `intel_cloud_timeout_seconds` in the MeetingConfig reference. No such field
  exists — it's the fixed constant `DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS = 180.0`
  (`holdspeak/intel/models.py:23`), never read from config (setting it is silently
  dropped). Row removed. *Not a code bug* — the engine works; the doc over-claimed
  configurability. (Follow-up idea recorded in the audit: wire it as a real field
  if user-tuning is wanted.)
- **F3 — incomplete enum.** `docs/CONNECTOR_DEVELOPMENT.md:67` listed 4 of the 5
  `KNOWN_KINDS`; added the missing `pipeline` (`holdspeak/connector_sdk.py:31`).
- **F4 — example contradicted its own spec.** `docs/DEVICE_PROTOCOL.md` worked
  example pushed `Listening...`/`Thinking...` status frames that AIPI-4-13 removed
  (stated correctly in the same doc's §6.1 and matched by
  `web_runtime.py:2013,2043`). The two stale push lines were removed from the
  example and the schema example text swapped off the removed phrase.

### Verified-correct (NOT changed — recorded to prevent a wrong "fix")

The README + docs-index deep links
(`#11-desktop-presence-ambient-on-desktop-status`,
`#12-dictation-journal-corrections--replay`) are **correct**: GitHub's slugger
keeps the parenthetical words and only strips punctuation, so the headings
slugify exactly to those anchors (including the intentional `--` from the removed
` & `). An automated pass flagged these as broken — that was wrong; verified by
hand against the headings.

### New guard

`tests/unit/test_doc_drift_guard.py::test_readme_plugin_count_matches_registry`
— imports `_BUILTIN_PLUGIN_DEFS` and asserts every "N built-in plugins" claim in
the README equals the registry count (14). Cheap (one import + one regex); pins
the most prominent "cool fact" against drift. Justified: the count is exactly the
kind of headline number HS-46-02 will lead with.

## Tests run

- Story test plan: `uv run pytest -q -k "doc_drift or link or doc_guard"`
  → **7 passed, 1 skipped** (the new guard included).
- Full-suite gate: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → **2364 passed, 17 skipped** (exit 0). The existing dangling-link guard scans
  the new audit doc clean (it uses code spans, not links, for doc paths).

## Acceptance criteria

- [x] An audit doc lists every live doc with a verdict + concrete drift findings.
- [x] Every factual error fixed (or recorded, not silently prose-patched): F1–F4
      fixed against code; F2 noted as a non-bug with a follow-up idea, not hidden.
- [x] Doc-drift + dangling-link guard green; the added count guard is green +
      justified.
- [x] No live doc claims a non-existent capability or omits a changed default
      (presence config toggle, journal default-on now stated correctly).
