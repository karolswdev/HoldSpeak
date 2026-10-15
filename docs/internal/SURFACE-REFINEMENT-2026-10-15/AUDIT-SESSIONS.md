# Plain session terminal — source audit

Status: DRAFT — HOLD for root's live inspection and settled canvas/design.
Base: `a81364a0d`; anchors re-read in `wt-surface-refinement-20261015` on
2026-10-15. No product edits, tests, browser, build or install ran.

**Candidate confirmed in source; scroll failure still needs glass.**
`web/src/desk/components/SessionPullout.tsx:802` always mounts the head,
question and complete Latest report before the terminal at `:817`. The
footer at `:859` only toggles `terminal`; it immediately says Back to
session without a scroll or focus handoff. The body scrolls and each child
keeps its height (`session-pullout.css:387`, `:395`). A long report can
therefore leave the terminal below the visible body. If reproduced, this
fails Tenets 3/5/7 and UX-CANON D's body-ownership rule. Tuesday: the owner
must reach the terminal with the press, then return to the report.

## Safe real producer and opening path

There is no session-create/report HTTP route. The actual producer is
`ingest_agent_hook_event` (`holdspeak/agent_context/sessions.py:204`). The
existing isolated glass setup already uses it for an unlaunched working
session (`tests/e2e/test_conductor_glass.py:238`–`:267`):

1. Boot root's isolated hub, with its registry and launch ledger inside
   its scratch HOME. Point `holdspeak.agent_context.AGENT_CONTEXT_FILE`
   at that registry; point `event_log.default_spool_dir` at its spool.
   `glass_infra.py:235`–`:261` lists the existing isolation switches and
   isolated configuration/database boundaries.
2. Write one JSONL assistant record (`role: assistant`, `content: report`)
   inside that scratch directory. Use about 3,800 characters of ordinary
   sentences ending with a period. The producer normalizes whitespace and
   keeps at most 4,096 characters (`sessions.py:1017`; `models.py:56`), so
   typed multiline or unlimited report fixtures would misrepresent it.
3. Ingest a Stop with `agent="codex"`, a fresh unique `session_id`, the
   scratch repository's `cwd`, `transcript_path`, `last_assistant_message`,
   `capture_messages=True`, explicit `state_path` and `events_spool_dir`.
   **Pass `env={}` and omit every tmux field.** Otherwise the hook reads
   inherited `TMUX_PANE` and can inspect owner tmux (`hooks.py:101`–`:106`).
4. Ingest PreToolUse with `tool_name="Bash"` for that same identity and
   explicit paths/environment. It retains the report and makes the
   session working, clearing the Stop's pending question (`sessions.py:327`).
   Do not create a launch or flight for this identity.
5. Read `/api/coders/sessions?include_ended=false` and verify the exact
   `session.agent`, `session.session_id`, stored report, working state and
   absence of a flight. Its real producer is `CoderService.list_sessions`
   (`holdspeak/services/coder_service.py:35`); the route is `coders.py:299`.
6. Open `/conductor`, then
   `.conductor-window [data-object-id='coder:codex:<session_id>']`
   → `[data-testid='conductor-open']`. The existing rig uses this exact
   route/selector at `test_conductor_glass.py:290`, `:304`. Verify
   `.is-session` and `[data-testid='session-head']`; a `.is-lane` is the
   wrong case. Press `session-open-terminal`; inspect `session-terminal`
   against the body bounds at 1440 and 393 without an extra scroll.

The plain ref becomes `coder:<agent>:<session_id>` only without a flight
(`web/src/desk/conductor/members.ts:215`, `:225`). It reaches
`openCoderSession` through `openObject.ts:159`; the shell checks again for
a launch (`shell.ts:169`). The session automatically polls
`/api/coders/codex%3A<session_id>/peek?lines=200&raw=1`
(`steering.ts:321`, `:746`). With no pane in the fresh registry, the real
peek answers `no_pane` before any tmux transport call
(`coder_steering_routes.py:151`–`:167`; `coder_steering.py:79`). Retry repeats
that read. This safely proves the long-report handoff and unavailable/Back
path. It does not prove a live terminal.

## Cheap fixture boundary and scoped tests

Record the isolated hub's actual sessions GET and exact peek GET answers,
then replay those two answers through `apiFetch`/`apiRequest` in the
existing session surface test. Use the existing recorded-wire pattern
(`web/src/desk/__tests__/conductor.app.test.tsx:1`; `:12`) and
`recordedHub.ts:12`; current C4 fixtures have launches and no long plain
report/peek pair. Do not type an invented live-peek envelope. If root needs
live-pane geometry, it needs a recorded response from a dedicated isolated
transport; owner tmux is outside this lane. A no-pane pair is enough for
the body ownership regression at the cheapest tier.

Existing files proposed for root's approval, not run:

- `web/src/desk/components/__tests__/sessionWork.surface.test.tsx` — compound
  identity, report, unavailable Retry/Back, unavailable answer gate; add the
  settled terminal-body transition and long report regression here.
- `web/src/desk/components/__tests__/sessionAnswer.f2.test.tsx` — question,
  one answer input, existing send and footer receipt.
- `web/src/desk/components/__tests__/sessionSpeakAnswer.f2.test.tsx` — one
  capture per press and cancellation when session identity changes.
- `web/src/desk/components/__tests__/sessionFooter.f2.test.tsx` — policy
  tokens and pane identity stay out of the footer.
- `web/src/desk/components/__tests__/sessionArmVerb.r6.test.tsx` — library
  Arm verb, unresolved-pane gate, unchanged arm call and rename/kill branch.

Root owns actual geometry, canvas, quick check and release. Preserve
compound identity (`SessionPullout.tsx:711`), coder-frame refresh (`:722`),
pane/raw/hash/grant polling in `steering.ts`, terminal reset on identity
(`:724`), answer/direct drafts and signals, availability gates (`:754`),
Details controls, and footer receipt precedence (`:857`). Do not change
launched LaneWindow, shared kit, canon, status or sibling files. Unknown:
live fit, scroll position, hit ownership, terminal ANSI geometry and
owner verdict. Source pass complete; HOLD for settled design.
