# Evidence — HS-86-02 — The refreshed rails: stamped gate + embedded dw

- **Shipped:** 2026-07-07
- **Commit:** (this commit — the first through the stamped gate; its
  `PMO-Story: HS-86-02` + `PMO-Contract-Digest` trailers and the
  archived contract under `.git/pmo-contract-archive/` are verified
  post-commit by `.githooks/dw verify` in HS-86-03's evidence)
- **Owner:** agent (Claude), owner-directed

## What changed

`~/dev/reusable-processes/pmo-roadmap/update.sh .` (upstream main
with phase 16 merged, dw 1.12.0 + the flagship-tree reader):

- `.githooks/`: the stamped-fact `pre-commit` gate (replacing the
  April bash hook), `commit-msg` (PMO trailers), `post-commit`
  (contract archive), embedded `dw` + `dw_pmo/`, `dw-workbench` +
  workbench UI, `dw-mcp`, work-log helpers.
- `.claude/commands/dw-*.md` slash commands.
- `pm/roadmap/roadmap-builder.md` + `pm/roadmap/PMO-CONTRACT.md`
  refreshed to current canon (`--force` after verifying the local
  file was the unmodified April canon — no project extensions
  existed; diff reviewed before overwrite).
- `CLAUDE.md`: the managed Delivery Workbench block added by
  `dw agent-docs`; the old hand-written-contract walkthrough replaced
  with a pointer to the block (HoldSpeak-specific sections — roadmap,
  canon, test commands — kept outside the block).

## Verification artifacts

```text
$ .githooks/dw doctor
ok   python3: /opt/homebrew/bin/python3 (3.14.6)
ok   core.hooksPath: .githooks
ok   hook:pre-commit / commit-msg / post-commit
ok   dw-cli: .githooks/dw + .githooks/dw_pmo/
ok   agent-docs: CLAUDE.md block is current
ok   roadmap: pm/roadmap
ok   rider:claude: wired, matches canon
dw doctor: healthy. Canonical invocation: .githooks/dw <command>
```

The refusal proof — a deliberately hand-written (old-style, unstamped)
contract attempted against the new gate; the commit did NOT land:

```text
$ git commit -m "refusal probe (must not land)"
✗ .tmp/CONTRACT.md carries no stamped facts block (Branch / HEAD / Index-tree).
$ git log -1 --format=%s
HS-86-01: the clean tree — dw check reads zero errors across 86 phases
```

Full suite with the refreshed rails:

```text
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
3299 passed, 37 skipped, 1 warning in 255.30s (0:04:15)
```

## Acceptance criteria — re-checked

- [x] `dw doctor` healthy — output above.
- [x] This commit carries the trailers + archived contract —
      verified post-commit (see HS-86-03 evidence; a commit cannot
      quote its own sha).
- [x] CLAUDE.md holds the managed block (doctor: "block is current")
      plus the HoldSpeak sections; the contradicting walkthrough
      replaced.
- [x] hooksPath unchanged; hand-written contract refused (captured
      above); suite green (appended).

## Deviations from plan

`PMO-CONTRACT.md` was refreshed with `--force` — the story scoped it
as "no rules change", and none changed: the local file was verbatim
old canon (no extensions), and the new canon's rules 1–7 are the
same rules with the stamped-facts mechanics documented.

## Follow-ups

None.
