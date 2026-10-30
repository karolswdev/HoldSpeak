# Terminals: remove the control-panel tax

Owner rejection, 2026-10-30: the merged interface fails the product’s smooth,
native UI/UX direction. This is a fix-forward lane from main after #1652.

## Diagnosis

The real 1440 shot has a padded pullout body plus a padded terminal wrapper.
The black working surface floats inside a pale page. An always-visible message
field competes with the actual terminal. Enable typing requires another screen
click. Inventory rows reimplement ListRow and repeat their group’s folder.
Empty inventory says “0 terminals”. Technical success was not appearance acceptance.
These fail Tenets 2, 3, 5 and 6 and UX canon’s single window grammar.

## Settled correction

- Use the existing Desk frame, Toolbar and StatusBar. Zero the terminal body’s
  outer padding and gap. The dark terminal surface joins the strips directly;
  one small inner screen padding protects text. No new theme or shell.
- Primary Type press focuses the mounted xterm synchronously, then requests its
  existing scoped typing grant. The receipt only changes permission; it never
  steals focus on arrival. Show pending, refusal and View only truthfully.
  No automatic arming on mount, restore, selection or ordinary screen click.
- Message is a toolbar disclosure for voice/buffered input. Keep it closed by
  default; an existing draft reopens it. Keep its mic, retained draft and send
  receipt. Hiding it never discards text. Find and Keys remain real kit actions.
- Use shared ListView/ListDay/ListRow for the inventory; opening a session is
  the row’s library Button. Group by folder once; do not repeat the full path
  in each row. Keep search over the full underlying metadata. Use short folder
  names with the full path available at the group. Forms replace the list while
  open, have Cancel, and are mutually exclusive. Shell name/folder drafts survive
  a form switch. Secondary actions fold through
  the shared menu, preserving their actual actions and 44px compact targets.
- Empty inventory says No terminal sessions with useful creation verbs; omit
  zero-count status. No state-token leakage or prose added to the face.

## Verification and bounds

Existing terminal app Vitest, controller tests and real private-tmux browser
case cover the fix. Add the missing outcome checks: Type press focuses before
its delayed acknowledgement; moving focus elsewhere while waiting keeps that
focus; default screen has no composer; draft survives hide/reopen and failed
send; inventory uses kit rows and one creation flow at a time. Real browser
checks flush geometry at 1440, 393 and a narrow desktop frame, ordinary typing,
message disclosure, Keys/Find, close-without-kill and restore. Use required quick
check with shots and inspect them. No owner provider, mic or real tmux touched.

This lane does not claim byte-stream transport, PTY resize or aesthetic owner
acceptance. Polling and host geometry remain the documented transport limits.
Canvas: flow-canvas.html, shared production material, fixture content only.

## Built and checked

The correction uses the existing interior hook on inventory and
`data-interior="editor"` on terminal frames, rather than adding another skin.
Find and Message return focus on their close press. Unavailable Type is
disabled; a delayed grant changes permission only. The controller requests one
coalesced read after the final acknowledged input batch, without local echo or
changing the periodic cadence. A pending read gets at most one follow-up.

Focused app/controller/input checks: 30 passed. Controller evidence:
`.tmp/terminal-flow-verification/feedback/terminalSession.{collection,run}.log`.
UI evidence: `.tmp/terminal-flow-verification/ui/terminals.app.test.log`.
Standalone browser: 2 cases collected and 2 passed, 1440 and 393, against a
private tmux server and isolated hub. The walk also resizes a desktop frame to
480 × 360. It proves Type focus with no extra test focus call, a real grant
reply arriving after Find takes focus, draft disclosure, actual shell execution
of a Message, compact hit ownership, flush screen geometry, independent input,
reload placement and close without kill. No page errors. Output contrast: 17.9:1.

Browser logs: `.tmp/terminal-flow-verification/browser-{collection,run}.log`.
Shots and private-rig provenance: `.tmp/evidence-shots/terminal-flow/`:
`inventory-{1440,393}.png`, `workspace-{1440,393}.png`,
`workspace-narrow-desktop.png`, `message-{1440,393}.png`,
`observation-{1440,393}.json`. Root inspected these shots.
The first expanded walk exposed its own Escape-prefix state in bash: the later
printf became Meta-p history search. The rig now sends a real Ctrl-C after its
Escape assertion. It does not alter product delivery to make that case pass.
The failure shots remain beside the final shots.

Required quick check and ship result are recorded in `pm/STATUS.md`.
The output remains a bounded recent-screen snapshot; host PTY resize is still
open. Live providers, deployment, the postmerge full tape and owner appearance
acceptance are separate and are not established by these runs.

The read-only visual check found one more status defect: every error was called
“Not sent”. The final source uses Not connected for connection failures,
View only for grant/refusal/disarm state, and Not sent while typing is allowed.
Five app assertions cover these cases. It also uses the shared `countWords`
formatter for the inventory’s empty count. The initial required run found a
missing `.venv/bin/python` in the new worktree’s real-producer test environment;
a local ignored link reuses the existing dev interpreter, with isolated HOME
still managed by the rig. No test guard, ceiling or allowlist was changed.

Low-priority follow-up: full folder paths in inventory are hover titles. A
keyboard/touch inspection affordance and disambiguation for equal folder names
remain open. This does not affect full-path search or the target identity.

Final required check GREEN: build, 4,752 related web tests (including the new
status cases), 192 web guards, 2 real-shell browser cases, 128 Desk sweep cases,
27 canon checks and 1,185 repository guards. Logs:
`.tmp/terminal-flow-verification/quick-final/`. The first red run is retained at
`quick-first/`. Final screenshots are newer than the final product source and
were inspected again. TypeScript, Ruff, documentation navigation and diff checks
also passed. No optional full-suite or live-provider claim is made.
