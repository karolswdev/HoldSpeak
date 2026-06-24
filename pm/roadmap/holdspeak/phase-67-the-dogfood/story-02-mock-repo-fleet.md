# HS-67-02 — The mock repo fleet

- **Project:** holdspeak
- **Phase:** 67
- **Status:** built (awaiting commit)
- **Depends on:** HS-67-01
- **Owner:** unassigned

## Problem

Dictation grounding and meeting intel need believable projects to work against —
with `.hs/` context, a KB, and a history of completed work that gives the model
real material. The repo ships one small `tests/fixtures/dictation_demo_project`;
the dogfood needs a fleet covering the different MIR profiles.

## Scope

- **In:** `dogfood/repos/{ledgerline,questline,pylon-infra}`, each with: `.hs/`
  (context, memory, terms, instructions, workflows, issues), a
  `.holdspeak/project.yaml` KB map (string→string, identifier keys), a real-ish
  source tree, and completed-stage evidence (`STAGES.md`, `CHANGELOG.md`, ADRs,
  a postmortem) seeding the meeting scenarios. Internally consistent (issue IDs
  and file paths cross-link).
- **Out:** the scenarios that reference them (HS-67-03). Making them git repos
  (anchors are `.hs/` + `.holdspeak/`).

## Acceptance criteria

- [ ] Each repo's `project.yaml` loads via `read_project_kb` with all string
      values and identifier keys.
- [ ] Each repo's `.hs/` loads via `load_hs_project_context` with `exists=True`
      and all six canonical files present.
- [ ] Each repo names a believable open decision/incident that a meeting scenario
      can dramatize (ledgerline write-path scaling + LL-118 double-post;
      questline guilds-vs-activation + Q3 scope; pylon PI-204 cert outage +
      PI-215 autoscaler).
- [ ] Paths referenced in each `.hs/context.md` exist in the repo.

      See `evidence-story-02.md`.

## Test plan

- Unit: the HS-67-03 plumbing pytest parametrizes over the three repos
  (`test_repo_kb_and_context_load`).
- Manual: from inside a repo dir, `dogfood/hs dictation blocks validate` and a
  `dry-run` show project detection firing.

## Notes / open questions

- Three domains were chosen over one-deep or five-per-profile to cover all five
  MIR profiles without bloat (owner decision at scaffold).
