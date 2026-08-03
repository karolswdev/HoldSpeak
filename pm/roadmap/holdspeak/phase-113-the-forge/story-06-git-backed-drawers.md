# HS-113-06 - Git-backed drawers

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** HS-113-01, HS-113-02
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

A drawer on the Desk can be backed by a git repository. Opening it
shows the repo's file tree, its PRs, its issues, its branches, and
its commit history — all as wings of the same drawer window. Files
open in the Desk editor. The user can browse, edit, stage, commit,
switch branches, view PR status with CI rollup, browse issues, and
see the full git lifecycle — all from the DeskOS experience, without
leaving the Desk world. The Delivery system's existing git
infrastructure (`registry.py`, worktree management, PR receipts)
becomes the backend; the drawer/zone primitive model becomes the
frontend. GitHub-hosted metadata flows through an expanded `gh` CLI
policy that remains read-heavy and approval-gated for writes.

**Articles served:** I (the Desk is the front door — code too),
II (capabilities are primitives), III (no feature-owned pages),
V (local-first truth), VI (propose-approve-execute with receipt).

## Ground (from the pre-charter survey)

- `web/src/lib/primitives.ts` — `PrimitiveKind` is a union type.
  Adding `"repository"` extends the Desk grammar with a new kind.
  `Directory` has `memberIds: string[]` pointing at qualified refs;
  a repo drawer's "members" are file paths, not existing primitives.
- `web/src/desk/components/ZoneWindow.tsx` — the drawer window
  supports Icons and List views with sort by Name/Kind/Modified. For
  a repo drawer, Kind becomes file type, Modified comes from git, and
  a new Status column shows git status (M/A/?/D).
- `holdspeak/delivery/registry.py` — `DeliveryRegistry` already
  manages registered git sources with `source_id`, normalized origin,
  root-commit fingerprint, branch metadata, and multiple worktrees.
  This becomes the repo drawer's backend.
- `holdspeak/delivery/pr_receipts.py` — PR receipt system already
  runs `gh pr list --state all --limit 50` per source, caches rows,
  tracks freshness, attributes PRs to worktrees, and provides local
  diff. This is the foundation for the PR wing.
- `holdspeak/connector_packs/github_cli.py` — the connector
  allowlist is currently `{("pr","view"), ("issue","view")}` only.
  `gh pr list` is used by PR receipts but not covered by this
  allowlist — a policy gap that must be unified. The drawer needs
  an expanded but still deliberate command policy.
- `holdspeak/delivery/factory_launch.py` — has `git worktree add`
  and `git status --porcelain` implementations.
- `holdspeak/web/routes/delivery_prs.py` — existing PR routes:
  list, refresh, diff, fetch, send-agent, draft-review, propose,
  decide. These become the PR wing's backend with source-scoping.
- `web/src/desk/prReceipts.ts` + `PrReceiptsSection.tsx` — existing
  PR receipt frontend: source-grouped table, CI rollup badges,
  worktree attribution, diff view, agent/review workflows. This UI
  vocabulary migrates into the repo drawer's PR wing.
- `holdspeak/plugins/builtin/github_pr_actuator.py` — approved PR
  comment and commit status writes. Proposal-gated. Reusable as-is.
- `holdspeak/plugins/builtin/github_issue_actuator.py` — approved
  issue creation. No issue listing yet.
- `web/src/desk/store.ts` — `createPrimitive` dispatches by kind.
  A `"repository"` kind needs a creation flow: pick a registered
  source (or register a new local path), choose a branch, and the
  drawer materializes on the desk.
- `docs/internal/DESK_GRAMMAR.md` — Drawer Law says a zone is
  visually a drawer icon. A repo drawer is a drawer with a different
  sprite and a status badge (branch name + dirty count).

## Method

1. **Primitive extension:**
   - Add `"repository"` to `PrimitiveKind`.
   - Define `Repository` interface: `kind`, `id`, `name`,
     `sourceId`, `branch`, `workingDir`, `createdAt`.
   - Add a `PrimitiveDescriptor` entry with icon, label, syncClass.
   - New 64x64 pixel-art sprite: a drawer with a branch/tree motif.

2. **Backend routes (`routes/repositories.py`):**

   **Local git operations:**
   - `POST /api/repositories` — register a repo drawer (accepts a
     delivery source ID or a local path to register).
   - `GET /api/repositories/{id}/tree` — returns the file/directory
     listing for the current branch. Uses `git ls-tree -r --name-only`
     plus `git status --porcelain` for working-tree status.
   - `GET /api/repositories/{id}/file/{path}` — returns file content
     for editing.
   - `PUT /api/repositories/{id}/file/{path}` — writes file content
     back to the working tree.
   - `POST /api/repositories/{id}/stage` — stages files (accepts
     path list).
   - `POST /api/repositories/{id}/commit` — commits staged changes
     (accepts message). Propose-approve-execute.
   - `GET /api/repositories/{id}/branches` — lists local + remote
     branches via `git for-each-ref refs/heads refs/remotes`.
   - `POST /api/repositories/{id}/checkout` — switches branch.
   - `GET /api/repositories/{id}/status` — returns `git status`
     summary (branch, ahead/behind, dirty files).
   - `GET /api/repositories/{id}/log?limit=50` — bounded commit
     history via `git log --format` (SHA, author, date, subject).
   - `POST /api/repositories/{id}/pull` — `git pull` with receipt.
   - `POST /api/repositories/{id}/push` — `git push` with receipt.
     Approval-gated (egress).

   **GitHub-aware operations (via expanded `gh` policy):**
   - `GET /api/repositories/{id}/prs` — delegates to the existing
     PR receipts system (`pr_receipts.py`), scoped to this source.
     Returns cached rows; explicit refresh available.
   - `GET /api/repositories/{id}/prs/{number}/diff` — local diff
     via existing delivery PR diff route.
   - `GET /api/repositories/{id}/issues?state=open&limit=50` — new.
     Uses `gh issue list --repo <owner/repo> --json number,title,
     state,author,labels,assignees,milestone,url --limit 50`.
   - `GET /api/repositories/{id}/issues/{number}` — new. Uses
     `gh issue view --repo <owner/repo> --json` for full detail.
   - `GET /api/repositories/{id}/prs/{number}` — new. Uses
     `gh pr view --repo <owner/repo> --json` with expanded fields
     (files, reviews, comments, timeline).

3. **Expanded GitHub CLI policy:**
   - Add to `ALLOWED_SUBCOMMANDS` in `github_cli.py`:
     `("issue", "list")`, `("pr", "list")`, `("pr", "diff")`.
   - Reconcile the existing `gh pr list` usage in `pr_receipts.py`
     to flow through the connector pack policy, not bypass it.
   - All queries are scoped to registered sources' `owner/repo`
     derived from their normalized origin URL.
   - Write operations (`pr comment`, `issue create`, commit status)
     remain approval-gated through the existing actuator/proposal
     system.

4. **Repo drawer window (`RepoWindow.tsx`):**
   - Extends the zone window pattern: same `DeskWindowFrame`,
     same Icons/List toggle, same sort affordances.
   - **Window head wings** (per Application Layer Thesis — wings in
     the head, not tab walls):
     - **Files** (default): file tree browser.
     - **PRs**: PR receipt list migrated from `PrReceiptsSection`,
       scoped to this repo. CI rollup, attribution, diff, agent
       and review verbs.
     - **Issues**: issue list with state/label/assignee. Click to
       open issue detail in an Info-style card.
   - **Files wing:**
     - **Icons view:** file/folder sprites in a grid. Folders are
       navigable (click to descend, breadcrumb to ascend).
     - **List view:** Name, Type (extension), Modified, Status (git).
       Sortable by each column.
     - **File open:** clicking a file opens it in the CM6 editor
       (from HS-113-01) as an in-world editor anchored to the repo
       window. Save writes back via the PUT route.
     - **Stage/commit flow:** select files (checkbox column in list
       view), click Stage, write a commit message in a one-line
       input in the window footer, click Commit.
       Propose-approve-execute: the commit button shows the exact
       files and message before executing. Receipt appears as an
       inline confirmation with the commit SHA.
   - **PR wing:**
     - Reuses the `PrReceiptsSection` vocabulary: source-grouped
       table, state/CI badges, draft flag, author, head branch.
     - Clicking a PR opens a detail card: changed files, commit
       list, review state, check runs, comments.
     - Existing PR action verbs (send-agent, draft-review, propose
       comment/status) are available per PR.
     - Explicit refresh button. Freshness/stale indicators.
   - **Issues wing:**
     - Table: number, title, state, labels, assignee, milestone.
     - Sortable by number, state, updated.
     - Click to open issue detail in an Info-style card.
     - Explicit refresh. Freshness/stale indicators.
   - **Window header:** branch name as a dropdown (switch branch),
     dirty-file count badge, ahead/behind remote indicator.
   - **Window footer:** status bar showing branch, last fetch time,
     and a compact git status summary.

5. **Cache and freshness semantics:**
   - PR data uses the existing PR receipts cache (observed_at,
     stale last-known-good, explicit refresh).
   - Issue data follows the same pattern: cached rows, explicit
     refresh, observed timestamps, bounded output.
   - File tree and git status are always live (local reads, no
     cache needed).
   - Branch list is live (local git read).
   - All GitHub-sourced data shows a quiet egress badge per
     Article V.

6. **Desk integration:**
   - Repo drawers appear on the desk floor with the repository
     sprite. Badge shows branch name.
   - Context menu: Open, Info, Switch Branch, Pull, Push, Terminal.
   - Terminal verb opens an xterm.js pane (from HS-111-11) cd'd to
     the repo's working directory.
   - `DeskListView` / `DeskTable` (from HS-113-02) shows repo
     drawers in a REPOSITORIES kind band.

5. **Sprite and visual design:**
   - New 64x64 sprites: `repo.png`, `repo_sel.png`, `repo_stale.png`.
   - File-type sprites (8-12 variants): generic file, folder,
     markdown, code (js/ts/py), config (json/yaml), image, binary.
   - All sprites follow ICON-DISCIPLINE.md: 1:1 rendering, distinct
     silhouette, no fractional scaling.

## Test plan

**Primitive and registration:**
- Unit: `Repository` primitive registers in `PRIMITIVES` table,
  appears in `DESK_GROUPS`.
- Unit: `POST /api/repositories` registers a source and returns the
  primitive.

**Local git operations:**
- Unit: `GET /api/repositories/{id}/tree` returns correct file
  listing with git status markers.
- Unit: `PUT /api/repositories/{id}/file/{path}` writes content,
  `GET` reads it back.
- Unit: `POST /api/repositories/{id}/stage` + `commit` creates a
  real git commit.
- Unit: `GET /api/repositories/{id}/branches` returns local and
  remote refs.
- Unit: `GET /api/repositories/{id}/log` returns bounded commit
  history with correct fields.
- Unit: `POST /api/repositories/{id}/push` is approval-gated and
  shows egress badge.

**GitHub-aware operations:**
- Unit: `GET /api/repositories/{id}/prs` returns cached PR receipt
  rows scoped to this source.
- Unit: `GET /api/repositories/{id}/issues` runs `gh issue list`
  through the connector policy and returns structured rows.
- Unit: `GET /api/repositories/{id}/issues/{number}` returns full
  issue detail via `gh issue view`.
- Unit: expanded `ALLOWED_SUBCOMMANDS` includes `("issue","list")`,
  `("pr","list")`, `("pr","diff")`.
- Unit: `pr_receipts.py` `gh pr list` call now routes through the
  connector policy, not a separate runner.

**Frontend:**
- Unit: `RepoWindow` renders Files wing with file tree in list view,
  sorts by name.
- Unit: `RepoWindow` PR wing renders PR receipt rows with CI badges
  and state.
- Unit: `RepoWindow` Issues wing renders issue rows with state and
  labels.
- Unit: clicking a file opens CM6 editor with file content.
- Unit: stage + commit flow shows confirmation before executing.
- Unit: PR click opens detail card with files, reviews, comments.
- Unit: issue click opens detail card.

**Integration:**
- Create a repo drawer from a registered delivery source, browse
  files, edit one, stage, commit — `git log` shows the new commit.
- Switch to PR wing — see the repo's PRs with CI status.
- Switch to Issues wing — see open issues with labels.
- Refresh PRs — freshness timestamp updates.

**Screenshot walk:**
- 1440px — repo drawer open on the desk, Files wing, file tree
  visible, one file open in the editor beside the window.
- 1440px — repo drawer PR wing with 3+ PRs showing CI badges.
- 1440px — repo drawer Issues wing with 3+ issues.
- 393px mobile — all three wings, horizontal scroll in tables.
- Must feel like a Desk experience, not a web IDE or a GitHub clone.

**Error legs:**
- Repo path does not exist — creation fails with reason.
- Commit with no staged files — commit verb ghosted with
  "Nothing staged."
- No `gh` CLI installed — PR and Issues wings show ghosted refresh
  with "GitHub CLI not available." File browsing still works (local
  git only).
- Non-GitHub remote (e.g. GitLab) — PR and Issues wings are hidden
  entirely. Files and local git operations work normally.

**Security:**
- File read/write routes must validate paths are within the
  registered repo root. No path traversal (`../` rejected).
- All `gh` queries are scoped to the source's derived `owner/repo`.
  No arbitrary repo targeting.
