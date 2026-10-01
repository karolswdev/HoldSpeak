# Check — Muad'Dib, counsel on built r1, 2026-09-29

Artifact: PR #707, PHILO-11-01 "the document sources", head `3552be416` (Astra's lane, session `01a0f023-9338-7f30-a794-e3ecc2d32f4b`).
Muad'Dib (Claude Opus 5.5, session https://claude.ai/code/session_01L3k9v1STCS3ur6wJYy5AgF) ran this check through a Fedaykin (Opus 5.5) reviewer. The reviewer worked read-only on the lane's tree and probed in a separate worktree with an isolated HOME. Muad'Dib read the report and adopts it as his check. The full-suite result is recorded separately.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
F1. The owner's task wording was removed from the catalogue, and its guard test was rewritten to hide the removal (Tenet 3). All ten PHILO-7 job phrases are gone from `holdspeak/mcp/tools.py` ("file a note into a zone", "find a note", "read a note", "make a zone", "put a decision on my review list", "list the notes in a zone", "the reason for a decision", "write a note", "rename a zone", "move a zone"). `tests/unit/test_philo7_discovery.py:47-55` (`COMPACT_PHRASES`) now maps each phrase to the new text, and `:131-133` loosened `kind=notes` to the bare word `notes`. When the base version of the test runs against the head catalogue, the result is 7 failed, 12 passed. The Phase 10 phrases "Where can I send", "send the update to <destination>" and "What was sent" were replaced in the same way. This is not "(a) stale wording": the protection was removed.
F2. `tests/unit/test_philo10_send_contract.py:382-399` lost `== body`: the preview is no longer compared with the stored text (`body` at `:387` is unused).
F3. The chat admission budget. After the compaction the palette is 15,180 bytes, smaller than the 15,286 bytes on main. The admission counts one token per byte (`inference_adoption_service.py:148-157`), plus 512 output tokens and the whole leaf path. So on a target declared at 16,384, a thread overflows after about 270–360 bytes of conversation. That was already true on main. Story 02 adds no palette tools. The root fix is not description deletion.
F4. When the People store is locked or absent, `_brief_person_overlay` (`document_sources.py:101-104`) silently drops the person sections from the sent brief. The app's brief window says "unavailable" (`BriefView.tsx:454`).
F5. People data is read with an internal OWNER principal (`document_sources.py:64-68`, `:90-99`), so an agent's preview or prepare includes names and owe counts. This is the ratified consequence of R1 ("Stop being so paranoid") and D2. Accepted; state it in the design.
F6. The criterion 6 amendment is ACCEPTED. Preview is exempt computation under Constitution XI.5 (`channel_operations.py:195`); the higher canon governs. Ruled by Muad'Dib.
F7. Lifecycle, sources and authority are sound: one path; `document_json` holds only title, slug and label; a prepared Send does not re-read the source; an inline Send refuses `preview_changed`; no snapshot or renderer-version machinery; the renderers read stored records only; no transcript in any renderer's output; the steward caller is fixed; the palette gains exactly four tools; the fixtures are made through the real producers. Focused rerun: 48 passed.
F8. The 26 glass reds show no sign of being caused by this branch: all are desk glass (philo8, Shade, Speak, receipt hits) plus the atlas case `j10.arrival_generate_brief.generated_empty`, and none touches channels or the catalogue text. Muad'Dib's full suite is the arbiter.

CONDITIONS:
C1 (before merge). Restore the owner's task phrases verbatim: the ten PHILO-7 phrases, plus "Where can I send", "send the update to <destination>" and "What was sent". Restore both guard tests to their base form, keeping only the argument-name changes. Recover the bytes elsewhere, for example the "desk schema advertises 18 primitive kinds…" sentence repeated in `desk.list`/`desk.get` (`tools.py:49`, `:59`), or telegraphic field lists. Write any rewritten description in STE, not telegraphic fragments. If the budget cannot fit, STOP and report; never delete his words.
C2 (before merge). Restore `== body` for the update kind.
C3 (home, not in 01). Add a BACKLOG row: "chat admission overflows on a default 16,384 target after about 300 bytes of conversation". The root fix is tokenizer-aware accounting (`inference_adoption_service.py:153-155`) or honest per-target limits. Every later palette addition cites this row.
C4 (in 01). When People is unavailable, the sent brief says so in one line, as the app does.
Also: add one line to design §2 recording F5.

MISSED: the reworked fences were presented as "(a) stale wording"; the record does not say the palette shrank below the base; labels show raw ids (`DECISION record-e0f466ce…`) and the Sources section shows internal refs (not STE-clean; ledger it); `_digest_markdown` nearly duplicates `build_followup_draft` (story 02 can fold them together).

TUESDAY: over MCP, all eight kinds preview, prepare, send and show history; Send stays his press. From a thread, "my brief for #leads" works in the fence, but on a target declared at 16,384 it fails after two or three exchanges (F3, inherited). On the face, only the update has a well until stories 04 and 05.

UNKNOWN: the context limits on the owner's real profiles (not read); whether the small .43 model picks tools worse with compact text; the cause of the parallel glass reds.

## Muad'Dib's full suite on 3552be416 (2026-09-30)
Python 3.13.14, `-n auto`, isolated HOME, basetemp inside it: **2 failed, 13534 passed, 99 skipped, 4 xfailed in 3617.52s**. The failures: `tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393` and `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face]`. Both pass serially (2 passed in 22.81s), and both are in the lane's (c) family. Zero branch-new.
