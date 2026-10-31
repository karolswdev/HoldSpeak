# Workspace flow follow-up

2026-10-30. Lane `feat/workspace-flow`, from `47db71d54`.
The owner authorized the job-focused workspace and its UX implementation.
Canvas: [workspace-flow-canvas.html](workspace-flow-canvas.html).

## Built

The selected job leads Sessions: its brief, Project, available agent state
and question, with a useful next action. The selected session uses the shared
list selection. Detailed provenance remains in Context.

Supported Project resources use the existing Ask and Hand sheet. A file can
prepare an editable task with its source, worktree, path and captured read
revision. The read hash is paired with the inspected content. The source copy
is bounded and marked when shortened. Source context is disclosed before Start.
Preparing work does not dispatch it.

Cancel returns to the same inspected file. The form owns one scrolling body
and retains per-file task words in existing Desk drafts. A refused hand keeps
its acknowledged Note for an unchanged retry. Captured Project validation,
keyboard submission and late-response guards preserve the destination and
newer words. Read failures offer retry without replacing the draft.

## Verification

Required quick check GREEN on the final product source:

- Build, 1,667 related UI tests in 110 files and 192 web guards.
- Four private real-shell browser cases at 1440 and 393, with a narrow desktop frame.
- 129 Desk sweeps, 27 canon guards and 1,194 repository guards.
- Final TypeScript, Python lint and changed documentation navigation passed.

Logs: `.tmp/workspace-flow/quick-ship3/`. Root inspected desktop, phone and
narrow desktop captures. The initial runs caught an overlapping redundant
empty-state action, unclear failure/action wording and stale test selectors.
The final implementation keeps one creation action and names each resource
destination. No guard ceiling or allowlist was changed.
Evidence lives in `.tmp/workspace-flow/` and
`.tmp/evidence-shots/connected-workspace/`.
The browser rig uses private real tmux, Git and an isolated hub. Launch facts
are seeded; the agent hand refusal is intercepted using its recorded envelope.
Engine mode is `none`. Note creation and Project filing use the real hub.

## Limits

The file copy is reference material. The existing Project repository resolver
chooses the new agent worktree; this flow does not resume the selected shell,
copy its uncommitted files or add a multi-repository launch chooser.
Bounded terminal snapshots, host PTY resize, remote output, restart recovery
and GitHub synchronization remain separate work.
No live provider, physical device, deployment, postmerge full tape or owner
appearance acceptance is established by the isolated runs.
