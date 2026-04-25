# PMO Contract

**Owner:** PMO.
**Status:** canonical rules for any project that installed `pmo-roadmap`.
**Read this if:** you are about to commit, or you got blocked by the
pre-commit hook.

---

## What this is

Every commit in this repo passes through a `pre-commit` hook that
requires you (agent or human) to write `.tmp/CONTRACT.md` with all
checkboxes set to `[x]`. The hook verifies, deletes the file on success,
and prints a confirmation. A stale contract (older than `HEAD`) is
rejected. An unchecked contract is rejected.

The certification has two purposes:

1. Force a re-read of the rules at commit time, when context is
   sharpest and stakes are highest.
2. Make every commit auditable — if an agent ever ships shoddy work,
   they did so having explicitly certified otherwise.

The hook will not lecture you about the rules. They live here.

---

## The rules

These apply to every commit, regardless of project.

### 1. Evidence, not vibes

If this commit claims work shipped (a story marked `done`, a phase
exit-criterion checked, a "fixed bug X" message), the corresponding
evidence is on disk.

For roadmap-tracked work that means an `evidence-story-{n}.md` file
with **actual command output**, not a summary. For non-roadmap work
that means commit message references to test runs / outputs you
actually saw.

Type-check passing is not validation.

### 2. Master docs updated in this same commit

If this commit ships a story, the relevant tracking docs are updated
in the same commit:

- the story-file header status (`backlog → ready → in-progress → done`)
- `pm/roadmap/{slug}/phase-{n}-*/current-phase-status.md` story table
- `pm/roadmap/{slug}/README.md` "Last updated"
- any project-canon doc the story explicitly mentions
  (BACKLOG, CHANGELOG, IMPLEMENTATION-LOG, PLAN.md §0, etc.)

Splitting tracking-doc updates into a follow-up commit is forbidden.

### 3. Tests actually ran

You ran the relevant tests via the documented project commands (npm
scripts, bash scripts, etc.). You read the output. You did not just
author the test file. Failed tests are either fixed or named in the
commit message as a known regression with a follow-up plan.

### 4. Greenfield discipline (where applicable)

If the project is in a pre-launch / greenfield state (the project
README will say so), you have not added migration ceremony, behavior-
preservation SQL, backwards-compat shims, or unused-export
preservation. Schema and APIs can change freely.

If the project is post-launch, this rule does not apply — the project
README will tell you which.

### 5. No bypasses, no scope creep

You did not pass `--no-verify` or `--no-gpg-sign`. You did not add a
`Co-Authored-By` line the user did not ask for. You did not include
files outside the scope of what the user asked for in this commit. If
unrelated cleanups happened to be in your working tree, they are in a
separate commit or explicitly mentioned in the message.

### 6. Story → evidence pairing (mechanically enforced)

If a story file's status flipped to `done` in this commit, the
corresponding `evidence-story-{n}.md` exists in this same commit.
Otherwise the story is `in-progress`, not `done`.

The pre-commit hook scans the staged diff for `+- **Status:** done`
on any `pm/roadmap/{slug}/phase-{n}-*/story-{nn}-*.md` file and
verifies the matching `evidence-story-{n}.md` (same phase folder,
same number) is staged. The hook also rejects orphan evidence files
(an evidence file without a matching story flip in the same commit).

### 7. One PR per story (mechanically enforced)

This commit is part of work that maps to one story (or one logically
atomic chunk if outside the roadmap framework). If the diff bundles
multiple stories, the commit message says so and each story file's
"Notes" section records the bundling.

The pre-commit hook counts how many `pm/roadmap/.../story-*.md`
files flipped to `done` in this commit. More than one is a hard
block. To bundle intentionally — and only intentionally — write
`.tmp/BUNDLE-OK.md` with a one-line rationale. The hook accepts
that as a per-commit override and auto-deletes it on success
(same pattern as the contract file). Bundling is rare; if you find
yourself reaching for `BUNDLE-OK` regularly, you are mis-sizing
your stories.

---

## Contract template

When the hook blocks you, write **exactly this** to `.tmp/CONTRACT.md`,
flipping every `[ ]` to `[x]` only after honestly verifying each rule.

```markdown
# Commit Contract

**Generated:** YYYY-MM-DD HH:MM (your timestamp)
**Branch:** {branch}
**Staged files (sample):**
- {a few staged file paths — gives the agent a moment to look at what's actually about to ship}

I certify, for this commit:

- [ ] **Evidence, not vibes.** Claimed work has on-disk evidence (or a commit-message pointer to the actual output I read).
- [ ] **Master docs updated.** Story header status, current-phase-status table, and any project-canon docs touched by this story are updated in this same commit.
- [ ] **Tests ran.** I ran the relevant tests via the project's documented scripts and read the output. Type-check is not validation.
- [ ] **Greenfield discipline (if applicable).** I did not add migration ceremony, compat shims, or backwards-compat hacks where the project is greenfield.
- [ ] **No bypasses.** No `--no-verify`, no unauthorized `Co-Authored-By`, no scope creep beyond what the user asked.
- [ ] **Story → evidence pairing.** If any story flipped to `done`, its `evidence-story-{n}.md` ships in this commit.
- [ ] **One PR per story.** This commit maps to one story (or atomic chunk), or the bundling is documented.

Methodology: pm/roadmap/roadmap-builder.md
Rules canon: pm/roadmap/PMO-CONTRACT.md
```

The canonical hook expects **at least 7** `[x]` checkboxes (it
checks `actual < expected`, not equality). Projects that add
rules above #7 simply add their checkboxes to this template;
filling them satisfies the canonical count automatically. To
enforce a project-specific rule mechanically, see "Extending"
below.

---

## Extending: project-specific rules

The canonical contract owns rules #1–#7. They are universal: every
project that adopts the framework inherits them. Some projects need
*additional* rules — for example, "every UI-facing change updates
the design handoff". The framework supports this without forking
the canonical hook.

### How to add a project-specific rule

1. **Add the rule to this `PMO-CONTRACT.md`**, below the canonical
   rules. Number it #8, #9, ... and label the section clearly as
   a project extension. The canonical content above this section
   stays as-is so `update.sh` can refresh it cleanly.
2. **Add a corresponding checkbox** to the contract template. Place
   it after the canonical 7. The canonical hook accepts ≥ 7 boxes,
   so adding more is safe.
3. **Add a structural enforcement check** (if applicable) to
   `.githooks/pre-commit.local`. The canonical hook sources this
   file after its own structural checks. The local hook can:
   - read `$STAGED`, `$STAGED_STORIES`, `$STAGED_EVIDENCE`,
     `$SHIPPED_STORIES`, `$SHIPPED_COUNT`, `$REPO_ROOT`
   - call `fail "reason"` (defined in the canonical hook) to block
   - append paths to `$EXTRA_CLEANUP_FILES` — they get `rm -f`'d
     on success
   - append text to `$EXTRA_BANNER_LINES` to extend the success
     banner
4. **Optionally provide a sentinel-file override** (e.g.
   `.tmp/<RULE>-OK.md`) that lets a project temporarily bypass the
   structural check with a one-line rationale. Add the sentinel
   path to `$EXTRA_CLEANUP_FILES` so it auto-deletes on success
   (same pattern as `BUNDLE-OK.md`).

`update.sh` never touches `.githooks/pre-commit.local`. Local
extensions survive framework updates.

### Worked example: Pantrybot's "design handoff" rule

Pantrybot adds a rule #8: every UI-facing change must update the
design handoff inputs that feed `design.pantrybot.app`, OR the
agent writes `.tmp/DESIGN-HANDOFF-OK.md` to explain the exception.

The implementation:

**`pm/roadmap/PMO-CONTRACT.md`** — adds, after the canonical 7:

```markdown
<!-- Project extensions (Pantrybot) -->

### 8. Design handoff for UI-facing changes (project-specific)

If this commit changes anything a user or designer can see, it also
updates the graphic-design handoff infrastructure in the same commit
(`docs/user-journeys/`, `graphic-design-handoff/`,
`frontend/public/handoff-data.json` from `npm run handoff:build`,
etc.). If the UI-facing path genuinely doesn't need new artifacts,
write `.tmp/DESIGN-HANDOFF-OK.md` with a one-line rationale.
```

**Contract template** — adds an 8th checkbox after the canonical 7:

```markdown
- [ ] **Design handoff updated.** UI-facing changes update the
  design handoff inputs, or `.tmp/DESIGN-HANDOFF-OK.md` explains why not.
```

**`.githooks/pre-commit.local`** — the structural check:

```bash
DESIGN_HANDOFF_OK_FILE="$REPO_ROOT/.tmp/DESIGN-HANDOFF-OK.md"
UI_FACING_REGEX='^frontend/(app|components|lib/(brand|icons)|public/|.*\.css$)'
DESIGN_HANDOFF_REGEX='^(docs/user-journeys/|graphic-design-handoff/|frontend/public/handoff-data\.json$)'

STAGED_UI=$(printf '%s\n' "$STAGED" | grep -E "$UI_FACING_REGEX" || true)
STAGED_HANDOFF=$(printf '%s\n' "$STAGED" | grep -E "$DESIGN_HANDOFF_REGEX" || true)

if [ -n "$STAGED_UI" ] && [ -z "$STAGED_HANDOFF" ] && [ ! -f "$DESIGN_HANDOFF_OK_FILE" ]; then
  bar
  echo "✗ Design handoff missing — UI-facing files staged but no handoff updates." >&2
  echo "  Update docs/user-journeys/ + run npm run handoff:build, OR write" >&2
  echo "  .tmp/DESIGN-HANDOFF-OK.md with a one-line rationale." >&2
  bar
  exit 1
fi

EXTRA_CLEANUP_FILES="$EXTRA_CLEANUP_FILES $DESIGN_HANDOFF_OK_FILE"
```

The result: the canonical framework is unchanged; the project gets
its rule mechanically enforced; `update.sh` can refresh the canonical
files freely without clobbering the local extension.

---

## Discharge

Some commits genuinely do not need every rule. A documentation typo
fix does not have "tests that ran." In those cases:

- You still write the contract.
- You still certify each box honestly.
- For a box that does not apply, you mark it `[x]` and add an inline
  parenthetical: `- [x] **Tests ran.** (n/a — docs-only)`.

The point is the re-read, not the literal applicability.

---

## Bypass

The user (only) may run `git commit --no-verify` in genuine emergencies.
Agents may not. The project's `CLAUDE.md` already restricts
`--no-verify` for agents; this contract layer assumes that restriction.

If an agent ever encounters a situation where the contract genuinely
cannot be honored (e.g. the rules themselves are wrong for the work),
the correct move is: stop, raise the conflict to the user, and let the
user adjust either the contract or the work scope.
