# Evidence — HSM-17-02: hooks inject into the live Claude/Codex instances

**Date:** 2026-07-04. **Proof style:** real metal — the hooks were installed on the
owner's actual Mac by the new one-command installer, and real Claude Code + Codex
CLI sessions were driven in tmux while the live set was observed over the new
endpoint on a running `holdspeak web`.

## What shipped

- **The lifecycle** (`agent_context/models.py`, `sessions.py`): `AgentSession`
  gains `lifecycle` (raw, from the last hook event: working | waiting | ended)
  and `question` (secret-filtered at ingest via the dictation journal's
  whole-field redaction). `effective_state()` adds read-time decay:
  no heartbeat for 30 min → `idle`, 4 h → `ended`; `ended` is sticky. The
  registry is never rewritten by staleness.
- **Event mapping**: SessionStart/CwdChanged/UserPromptSubmit/PreToolUse/
  PostToolUse/PreCompact/SubagentStop → working (question cleared — the coder
  resumed); Notification → waiting + the payload `message` as the question;
  Stop → waiting (+ the captured assistant text as the question when it is
  question-shaped); SessionEnd → ended. Unknown events keep the prior state.
- **Templates** (`agent_context/hooks.py`): Claude gains `Notification`,
  `PostToolUse` (matcher `Bash|Edit|Write|Task` — a spawn per meaningful tool,
  not per read) and `SessionEnd`; Codex gains `Notification` + `SessionEnd`.
- **One-command install** (`holdspeak agent-hook install|uninstall`):
  idempotent (re-running converges, capture-flag changes replace instead of
  stack), reversible (uninstall restores the pre-install JSON exactly,
  test-pinned), foreign hooks and unrelated settings preserved, unreadable
  JSON refused rather than rewritten.
- **The live set** (`GET /api/coders/sessions`): every known session — not just
  the awaiting ones — newest first, each with `state` (decayed), `lifecycle`,
  `question`, and the identity payload; sessions past the dead window fall out;
  `include_ended=false` drops fresh tombstones. API surface manifest
  regenerated (233 routes).

## The recorded live arc (Claude Code, session `d19676dc`)

Observed over `GET /api/coders/sessions` on a live server, driving a real
`claude` in tmux in a scratch repo:

| Beat | Endpoint read |
|---|---|
| Session launched (SessionStart) | `state: working`, events 1 |
| Prompt + `git status` (UserPromptSubmit, PostToolUse Bash) | `working`, `last_tool: Bash` |
| Turn finished (Stop + Notification) | `state: waiting`, `question: "Claude is waiting for your input"`, events 5 |
| `git commit` **permission ask** (the story's crux) | `state: waiting`, `question: "Claude needs your permission"`, events 7 |
| Approved → committed → resumed | `waiting`, `question: None` (cleared on resume), events 9 |
| Second permission ask (`git push`) | `waiting`, `"Claude needs your permission"`, events 11 |
| `/exit` (SessionEnd) | `state: ended`, events 12; absent under `include_ended=false` |

## The Codex arc (session `019f2e2e`)

Our installer merged into the real `~/.codex/hooks.json`; codex 0.142.4 raised
its own "Hooks need review" consent gate (trusted), then a driven prompt ran
`rg --files` and answered — the registry read `lifecycle: waiting, events: 5`.
Codex did **not** emit `SessionEnd` on `/quit`; its row tombstones via the
bounded staleness decay instead (the unit-tested path) — recorded honestly.

## The self-capture

While the proof ran, the registry showed `claude:96df20ed…` at 35+ events,
`working` — **the very Claude Code session that built this story, reporting
through the hooks it had just installed**, alongside a second live session of
the owner's in another worktree. The capture loop is live on this machine for
both agents from here on (uninstall: `holdspeak agent-hook uninstall`).

## Tests

- `tests/unit/test_agent_session_lifecycle.py` (9): event→state mapping, question
  capture + clear, Stop question-shape, tombstone stickiness, idle/dead decay +
  custom windows, secret redaction, registry round-trip.
- `tests/unit/test_agent_hook_install.py` (10): create/merge/idempotent/converge,
  foreign-hook + settings preservation, exact uninstall reversal, empty-object
  cleanup, missing-file no-op, unreadable-JSON refusal, CLI round-trip.
- `tests/integration/test_web_server.py` (+4): the live set includes working
  sessions the status board hides, agent filter, tombstone include/exclude,
  dead-window cutoff.
- Batteries: the 4 touched files 117 passed; `-k "agent or hook or coders or
  companion"` 219 passed, 2 skipped. API-surface lock green after regen.
