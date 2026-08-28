# HS-146-07 design-beat plan — the Calendar Snapshot adapter (opus, 2026-08-28)

Read-only plan; all [ORCH-CALL]s ruled same day (dispositions in the
phase decision log). Anchors verified at plan time; story-02 lines
were in flux and excluded from anchoring.

## Ruled design

1. **Hosting.** Entry A (primary): the desk glass drop —
   `web/src/desk/glassDrop.ts:21` gains `GlassFileKind "screenshot"`
   (.png/.jpg/.jpeg/.webp); `GlassDropLayer.tsx:49-73` branches it to
   `POST /api/calendar/snapshot` then opens the review surface.
   Entry B (secondary): an IMPORT SCREENSHOT verb beside the story-03
   calendar list editor. Review = a NEW dedicated SurfaceWindow
   (`review-calendar-snapshot`, SURFACES array
   `SurfaceWindows.tsx:41+`), Core built from GadgetTable
   (`gadgets.tsx:498-578`) + StringGadget-with-mic (:217-283) +
   ConfirmVerb (`Surface.tsx:1107-1147`) + SurfaceFooter
   CONFIRM/CANCEL. No existing review surface honestly fits.
2. **Vision seam (three additive pieces).** (a) capability
   `calendar.snapshot_extract` in the background group
   (`inference_capabilities.py:1031+`): operation
   `calendar.snapshot.extract`, input text+image, `vision=True`
   (compat check `inference_assignment_service.py:1876` already
   refuses profiles without the vision claim), structured_output,
   4096 min context. (b) NEW `holdspeak/kernel/vision_prompt_adapter.py`
   building the OpenAI-style multi-part content array
   (text + data-URL image); requires widening
   `engine.py:265` `_chat_completion_text` messages to
   `list[dict[str, Any]]` (both llama.cpp and the OpenAI client
   accept multi-part natively; `_chat_completion_stream` widened for
   consistency). (c) payload carries
   `{system_prompt, user_prompt, image_base64, image_media_type}` —
   JSON path already handles it. **Hash ruling (orchestrator
   override of risk note 1): the canonical payload hash stays WHOLE —
   no image-exclusion special case; sha256 over a few MB is
   milliseconds and kernel hash semantics do not fork for an
   unmeasured optimization.**
3. **Extraction contract:** `{anchor_date: ISO|null,
   anchor_confidence: visible_header|inferred|absent, events:
   [{title, weekday, start_time, end_time, location}]}`; unreadable
   → `{error: "unreadable_screenshot", events: []}` = a NAMED
   in-flow refusal on the review surface; never empty success.
4. **Week anchoring:** the review surface always shows an editable
   "Week of" StringGadget (mic); prefilled when confidence
   visible_header/inferred; CONFIRM disabled until a parseable
   anchor exists. weekday→absolute timestamps resolved SERVER-side
   at confirm.
5. **.ics lifecycle:**
   `~/.local/share/holdspeak/calendar-snapshots/<source_id>.ics`
   (data-dir convention `db/core.py:41`), atomic temp+rename, one
   file per snapshot source regenerated per confirm; the
   CalendarSource ("O365 SNAPSHOT") registered/updated through the
   settings service's validated write path ONLY (no side door);
   NEW `trigger_calendar_refresh()` in the conductor module pokes
   `_conductor.refresh()` so the rail updates immediately;
   re-import replaces via the story-01 scoped
   `DELETE WHERE source_id`.
6. **Multi-screenshot:** up to 3 per import, each extracted
   separately, merged (exact-match dedupe within the import only)
   into ONE review list; >3 refused by name.
7. **Guards:** NEW route `POST /api/calendar/snapshot` →
   `scripts/gen_api_surface.py` regen + manifest guard moves
   (route count +1); NO new MCP tool (an interactive UI act).

## Slice order

A vision seam → B snapshot service (extraction orchestration, ICS
gen, anchor resolution, registration, lifecycle, trigger) → C HTTP
route + api-surface regen → D glass drop + review Core + SURFACES →
E e2e glass leg (fixture PNG + deterministic fake vision engine →
confirm → rail).

## Test plan

`tests/unit/test_calendar_snapshot_service.py` (schema validation /
ICS round-trip through the REAL `parse_calendar_bytes` / anchor
resolution / registration / refusals / file lifecycle);
review-Core vitest; `tests/e2e/test_hs146_calendar_snapshot_glass.py`;
fake-model idiom = engine-factory injection
(`test_one_path_spine.py:208-227` pattern) returning deterministic
extraction JSON. Route unit + api-surface snapshot guard.

## Risks (as planned, with rulings)

- 10 MB upload cap on the route; base64 inflation ~33% accepted.
- Egress truth: the review Core shows the assigned profile's
  boundary (the work calendar is exactly where egress matters most).
- Mic-on-inputs automatic via StringGadget defaults.
- .43 may lack a local vision model — cloud path with badge is
  lawful; one control-vs-treatment probe only if local vision
  exists (story scope).
- Engine type widening is backward-compatible (str ⊂ Any).
