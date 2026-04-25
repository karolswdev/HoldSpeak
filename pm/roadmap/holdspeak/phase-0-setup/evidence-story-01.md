# Evidence — HS-0-01 (Install pmo-roadmap framework)

**Captured:** 2026-04-25.
**Commit:** (this commit, see `git log -1` after merge).

## Framework files installed

```
$ ls .githooks/ pm/roadmap/ pm/roadmap/holdspeak/
.githooks/:
pre-commit

pm/roadmap/:
PMO-CONTRACT.md  holdspeak  roadmap-builder.md

pm/roadmap/holdspeak/:
phase-0-setup  phase-1-dictation-intent-routing  README.md
```

## Hook is wired

```
$ git config --get core.hooksPath
.githooks
$ test -x .githooks/pre-commit && echo executable
executable
```

## .gitignore updated

```
$ grep -E '^\.tmp/?$' .gitignore
.tmp/
```

## CLAUDE.md present

```
$ test -f CLAUDE.md && grep -q 'PMO hygiene gate' CLAUDE.md && echo ok
ok
```

## Phase-1 skeleton scaffolded

```
$ ls pm/roadmap/holdspeak/phase-1-dictation-intent-routing/
current-phase-status.md  story-01-baseline-and-spike.md  story-02-contracts.md
```
