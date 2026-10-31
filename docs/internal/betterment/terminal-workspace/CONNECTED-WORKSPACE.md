# Connected workspace

Status: implementation brief, 2026-10-30. Owner clarified “Both—the full
connected workspace”: use nodeterm workflow ideas and HoldSpeak’s own Desk
capabilities. The earlier terminal-only interpretation was incomplete.
This lane is `feat/connected-workspace`, based on main `c7be6ee7c`.

## One complete job

Choose the Project and brief. Start an agent with HoldSpeak tools in its
worktree. Its own terminal opens when it is ready. Keep notes and source
context beside the work. Read and edit the correct worktree’s files, inspect
its changes, and stage/commit locally. Answer or review the matching agent,
open its Program step and inspect the result. Close/reload without losing
work or changing the action’s target.

The Desk remains the spatial surface. No nested window manager, graph runtime,
new agent launcher, second project store or duplicate permission UI. Compose
shared kit and the existing repository browser/editor, launch/hand, Project,
Program, Note, agent lane and source/reference mechanisms. This applies all
Seven Tenets: accelerate the real job, use simple words, reuse the framework,
make native interactions first class, and keep the architect’s context intact.

## Product composition

Terminals becomes a connected workspace rather than an inventory alone.
Project and session selection retain real identity. A selected session has
Files, Changes and Context views using the window’s shared wings/interior.
The dark terminal remains its independent native Desk window. Each terminal
has a Workspace door into its own selected context, plus bound Agent/Project/
Program/review actions where those real records exist. Context shows the
brief/origin, project notes/resources and HoldSpeak tools’ configuration fact.
Configured is not a successful MCP handshake. Arbitrary shells do not claim
agent credentials or a launch association.

Starting from this workspace keeps the captured Project and opens the exact
new launch’s terminal when it appears. A queued hand remains visibly queued;
a failed or slow launch has a named recovery path and never opens another
agent’s pane. Opening the related agent uses its launch ID and retains the
return path. Notes/sources and re-brief use existing persisted domain records,
not text inferred from terminal output. Existing voice gadgets prepare text;
only the explicit input/Send act executes it.

A Start agent retry with the same words and Project reuses its created brief
Note and resumes the failed filing or hand step. A refusal does not create a
second copy of the same brief. A new set of words or Project is a new intent.
The queue does not retain a queue ID on the launched flight. Keep the
acknowledged brief Note ref on each pending handoff and join a queued arrival
only to one verified launch with that exact origin and Project. Refuse an
ambiguous association; a queue ID is not a launch or attempt ID.

A local repository can be filed in a Project through the existing Project
resource operation. The owner explicitly chooses the Project and registered
source; agents cannot use this binding to attach another repository. A filed
repository is sufficient for the existing agent handoff to resolve the local
source, without a remote clone or a label-based guess. Project filtering may
include shells in a filed repository; this is not a launch or MCP claim.
An unbound shell's Context offers a Repository folder field and Register folder
through the existing repository API. It starts from that captured session's
folder, keeps input on refusal, then refreshes the source/worktree facts.
The subsequent Project binding is explicit. No API console or unrelated
Automation window is needed for this local first-use path.

Files and Changes use the source AND worktree ID. Opening the source’s primary
checkout instead is wrong. File edits retain input on failure and use the
read revision to reject overwriting agent changes. Changing selection cannot
redirect an outstanding read, edit or Git action. Shells in a registered
worktree may browse that worktree, but folder membership does not confer
launch/project/Program ownership. Equal folder names must remain distinguishable.
After a real file-version conflict, Read latest shows the current disk text
beside the kept edit. The owner reviews the text and uses Save reviewed edit
against that fetched revision. Another disk change still refuses the save.
A retry must not require discarding the owner's words or bypassing the hash.

## Additive terminal wire

Each descriptor gains `context` (old fields/identity stay):

```text
context: {
 status: "bound" | "worktree" | "unbound" | "unavailable",
 project: {id,name} | null,
 source: {id,name} | null,
 worktree: {id,branch} | null,
 launch: {id,profile_id,state,role,origin_ref,attempt_id} | null,
 program: {id,title,step_id,step_ordinal} | null,
 mcp: {status:"configured"|"unknown",server,palette,pre_approved,read_only} | null
}
```

A launch binding must match its stored immutable target ID/generation to the
currently verified pane. Session name, hook label and cwd alone are not a
launch identity. Read the launch ledger once per inventory, use composed
services and the same target registry, and keep DB/filesystem work off-loop.
A context lookup failure does not hide a live terminal. The wire contains no
credentials or config contents. The existing launch credential and MCP
injection remain the source of authority.

Repository HTTP keeps its existing source ID routes and gains optional
`worktree_id` on relevant reads/writes. An unknown worktree fails explicitly;
it never falls back to primary. Read file answers include a content SHA-256;
workspace writes echo it as `expected_sha256` and receive 409 on changed text.
A bounded `GET /api/repositories/{id}/diff` accepts the same worktree scope and
optional contained `path`/`staged` selection. Status adds changed-file records
without changing existing counts. Legacy callers keep their current shape.
Use the existing operation path; do not invent shell-command construction in
the browser or imply stronger legacy repository authority than actually exists.

## Verification and limits

T1 exact/recycled launch identity, Project/Program/MCP projection, registered
worktree resolution, traversal/symlink refusal, file conflict, exact-worktree
file/Git reads and local effects. T2 recorded producer fixtures: Project/session
selection, correct context actions, launch-to-terminal/queued recovery, stale
response guards, retained edit/input, failures, real file/diff result rendering.
T4 isolated hub, private tmux and private Git worktrees: terminal A/B, correct
worktree contents/diff/edit/stage/commit, context/launch doors, desktop/phone
reflow, reload and close. Root runs the required quick check with shots.
Every test uses the machine lock and isolated HOME/DB/Keychain; no real agent,
provider, microphone, calendar, phone, external Git destination or owner tmux.

This is workflow inspiration, not a claim of nodeterm feature parity. SSH
projects/remote screen transport, reboot restoration, native phone relay,
two-way GitHub Kanban, additional CLI providers and PTY streaming/host resize
are distinct capabilities. Do not expose dead verbs or describe them as built.
The lane must distinguish connected existing capabilities from genuinely absent
ones in the public guide and open-work ledger. Canvas: connected-canvas.html.
