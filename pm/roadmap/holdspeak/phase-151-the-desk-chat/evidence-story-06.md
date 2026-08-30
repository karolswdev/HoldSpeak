# Evidence - HS-151-06

- **Story:** HS-151-06 - The composer (mic, @-refs, send/stop, / verbs)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T00:00:45Z

- **Command:** `npx --prefix web vitest run --root web src/desk/__tests__/ThreadComposer.test.tsx src/desk/__tests__/ThreadPullout.test.tsx src/desk/__tests__/threads.test.ts`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1350df8cfbfb24cf9cafe827d85bc7f377de06a0

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/web


 Test Files  3 passed (3)
      Tests  49 passed (49)
   Start at  18:00:45
   Duration  715ms (transform 318ms, setup 110ms, import 525ms, tests 127ms, environment 653ms)
```

## Orchestrator triage (2026-08-30)

Read: 49 passed across ThreadComposer.test.tsx (27: keys, chips
add/remove, `/` verb filter, Send↔Stop, mic never sends, InlineEditor),
ThreadPullout.test.tsx and threads.test.ts. The composer is the
pullout's foot (Art. IV mic arms never sends; Enter/Shift+Enter/Esc;
`@` extends InletAutocomplete from zones to kind-tagged primitives —
people titles come from the same relationships endpoint PeopleCore
uses, display names only; `/` filters the registry, never a second
command system); the `window.prompt` fork became an inline editor
(Art. VII); edit-and-resend branches in place. Real-Chromium truth:
the e2e probe `test_hs151_thread_glass.py` (3 passed: progressive
deltas, receipt on the done row, Stop→Send after abort) and the rig's
composer legs at 1440 + 393 (overflow fixed in-round). The e2e abort
leg exposed a server defect (per-request service instances lost the
cancel event) — fixed in `81fe5780`.
