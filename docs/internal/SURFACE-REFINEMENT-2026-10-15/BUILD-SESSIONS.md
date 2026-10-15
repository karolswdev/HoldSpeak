# Plain session terminal — build record

Status: source frozen — HOLD FOR SHIP. Built against base `a81364a0d` in
`wt-surface-refinement-20261015`; root owns production checks and release.

Root confirmed the 393 baseline: terminal top 1136.7, bottom 1232.2, below
the visible body while the footer already said Back. The inspected 1440
case stayed visible; this record claims no desktop baseline failure.

## Change

`web/src/desk/components/SessionPullout.tsx:819` now gives the terminal the
body. The report, question, application head and Details unmount; the
window header and footer remain. Back restores the work. Existing
unavailable Retry/Back and live-pane rendering use the same data and gates.

The existing durable answer/direct text drafts restore on Back. Direct's
send choice, grounding and rails now live in the same session parent so
the view switch also retains those choices (`SessionPullout.tsx:443`,
`:720`). They reset on compound session identity change as before. A late
delivery only clears options for its own still-open identity (`:472`).

Terminal entry records only the current Speak request (`:878`); Back
cannot restart that request when its mic remounts (`:776`). A later Speak
press reveals the composer and starts capture, including while terminal
is active (`:740`). Root approved the local footer seam: Direct
returns to the session and reveals its composer, including when Direct
was active before terminal entry (`:881`). No steering store, polling,
WebSocket, authority, launched lane or shared-kit code changed. No CSS
change was needed.

The new fixture is
`web/src/desk/components/__tests__/fixtures/session-terminal.recorded.json`.
It copies root's actual `before-final-393/sessions-wire.json` and
`peek-wire.json`; only scratch HOME paths become `/isolated`. The report,
session identity and no-pane envelope come from real isolated hook
ingestion with `env={}`. The UI test separately supplies a footer refusal
receipt to check custody; that receipt is not producer evidence.

## Focused proof

All runs used the provided helper, which creates an isolated HOME and
takes the machine test lock. Collection command:

```sh
.venv/bin/python .tmp/surface-refinement/locked.py sessions-speak-collect --web ./node_modules/.bin/vitest list src/desk/components/__tests__/sessionWork.surface.test.tsx src/desk/components/__tests__/sessionAnswer.f2.test.tsx src/desk/components/__tests__/sessionSpeakAnswer.f2.test.tsx src/desk/components/__tests__/sessionFooter.f2.test.tsx src/desk/components/__tests__/sessionArmVerb.r6.test.tsx
```

`.tmp/surface-refinement/sessions-speak-collect.log` contains all 27 named
cases. The test run uses the same exact five files:

```sh
.venv/bin/python .tmp/surface-refinement/locked.py sessions-speak-green --web ./node_modules/.bin/vitest run src/desk/components/__tests__/sessionWork.surface.test.tsx src/desk/components/__tests__/sessionAnswer.f2.test.tsx src/desk/components/__tests__/sessionSpeakAnswer.f2.test.tsx src/desk/components/__tests__/sessionFooter.f2.test.tsx src/desk/components/__tests__/sessionArmVerb.r6.test.tsx
```

The red commands used that same `run` argument vector with labels
`sessions-red-final`, `sessions-direct-red` and `sessions-speak-red`.
Actual tails:

```text
sessions-red-final.log — before product changes
Test Files  3 failed | 2 passed (5)
     Tests  5 failed | 20 passed (25)

sessions-direct-red.log — tightened already-active Direct case
Test Files  1 failed | 4 passed (5)
     Tests  1 failed | 24 passed (25)

sessions-green-final.log — original build
Test Files  5 passed (5)
     Tests  25 passed (25)
  Duration  1.91s

sessions-speak-red.log — root's P2, new Speak while terminal active
Test Files  1 failed | 4 passed (5)
     Tests  2 failed | 25 passed (27)

sessions-speak-green.log — final corrected source
Test Files  5 passed (5)
     Tests  27 passed (27)
  Duration  1.98s
```

The regressions cover the real long report becoming unmounted, the sole
terminal body child, unavailable Retry, Back and footer receipt custody,
same-id/different-agent reset, unsent question/direct drafts, the send
choice, Direct's terminal handoff, and capture cancellation without replay
in both question and direct composers. The two added P2 cases press Speak
while terminal is active, require the composer and one new capture without
an extra Back, then re-enter terminal and prove Back does not replay that
capture. Root's compiler correction removing the unsupported `exact`
ByRole option in `sessionAnswer.f2.test.tsx` was preserved. Existing send,
mic, arm and policy
checks stay green. Only three approved test files changed; the approved
footer and arm files were run unchanged.

Unknown: final production fit, focus/hit ownership and ANSI terminal
geometry. Worker ran no browser, production build, install, full suite or
hardware/terminal dispatch. Root owns the final 1440/393 walk and quick
check. No staging or commit; no sibling, canon or status edits.
