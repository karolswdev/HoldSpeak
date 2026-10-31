# Connected workspace result

2026-10-30. Lane `feat/connected-workspace`, from `c7be6ee7c`.

## Built

Terminals connects the local coding job through existing Desk objects:
Project and brief, agent handoff, exact terminal, worktree files and changes,
Project resources, agent lane and Program. Sessions, Files and Context use
the shared window wings. Each dark terminal remains an independent Desk
window with its own input authority.

An existing local shell can register its Git top folder in Context, then file
that repository in a Project. A refused registration does not write an
invalid registry entry. Project filing uses the existing resource command,
revision and event path, and requires the owner. A filed source resolves by
its identity rather than its label.

File and Git operations use source plus worktree identity. Edits retain their
text and original hash through a reload. A real version conflict keeps the
edit; Read latest shows current bytes, and Save reviewed edit uses that read's
hash. A further change still refuses the write. Stage and Commit keep their
selection or message on failure and retry the failed operation.

Launch context requires one matching immutable, currently verified terminal
target. Folder membership alone supplies worktree context. It supplies no
launch, Project, Program or MCP claim. MCP Configured describes the launch's
configuration, not a completed handshake. A context failure leaves the live
terminal visible.

Queued starts retain their actual brief Note and Project identity. Their
arrival must match one verified launch; the queue ID is not reused as a
launch or attempt ID. Each start captures its own view epoch so an older
reply cannot close a newer form or take focus. Retrying an unchanged brief
reuses its filed Note.

The repository service retains the existing local Git behavior. Its exact
effect-census selector moved with the code; this is not a claim that legacy
repository operations became kernel-admitted operations. Git paths use NUL
records, including renamed files and names with quotes or newlines.

## Verified

- Required quick check GREEN: build; 4,889 related web tests; 192 web guards;
  2,321 affected Python tests (two intentional skips, including the opt-in
  live-provider case); 128 Desk sweeps; 27 canon guards; 1,185 repository
  guards. The four real-shell browser cases are included in affected Python.
  Logs: `.tmp/connected-workspace/quick-ship/`.
- Focused MCP/factory checks: 62 passed. Claude and Codex configuration,
  credential admission, palette and Project/item boundaries were exercised.
  These tests do not prove a live provider or pi handshake.
- Real-browser cases use an isolated hub, private real tmux and private Git.
  They cover exact checkout contents, retained edit/hash across reload,
  actual 409, reviewed save, index-lock Stage refusal, hook-refused Commit,
  correct Retry, unchanged main/sibling checkouts, Program/Decision doors,
  local registration and Project filing. Desktop is 1440; phone is 393.
- Launch, Program and MCP facts in the browser cases are real producer seed
  records. No agent CLI or model runs. Engine mode: `none`.
- TypeScript, Python lint and documentation navigation are checked separately.

Current local shots and observations are in
`.tmp/evidence-shots/connected-workspace/`. The README includes an
[actual workspace capture](../../../assets/readme/workspace.png).
The [user guide](../../../TERMINALS.md) describes the implemented flow.

## Open work

This is an independent HoldSpeak composition, not nodeterm feature parity.
Output remains bounded snapshot polling; host PTY resize, SSH/remote output,
machine-reboot restoration and a two-way GitHub Issues board are not built
here. Existing Project Room watches remain distinct from that board.
The existing Project repository resolver remains the handoff authority;
this lane does not add a multi-repository launch chooser.

No live provider, physical microphone/device run, deployment, postmerge full
tape or owner appearance acceptance is claimed by this local verification.
