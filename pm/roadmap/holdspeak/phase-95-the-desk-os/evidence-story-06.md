# Evidence - HS-95-06

- **Story:** HS-95-06 - Meetings and recording through the desk
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T03:40:23Z

- **Command:** `bash -c npm --prefix web run test:web 2>&1 | tail -3 && uv run python scripts/desk_gl_walk.py meetings && HS_WALK_BASE=http://localhost:8789 uv run python scripts/desk_gl_walk.py meetings --intel`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7947cb93427de18cc23ce038915bd70dff0a355f

```text
   Start at  21:40:23
   Duration  9.29s (transform 700ms, setup 1.28s, import 3.03s, tests 2.56s, environment 8.20s)

meetings walk: record→live window in place, one recorder truth, saved→pull-out, review scoped in-world, flat routes live
intel leg: .43 titled it 'Reviewing Desk Rundown Updates'; summary 'Meeting concluded with a discussion about the meaning of views into the desk run'; 'Intelligence ready' shown in-world
meetings walk: record→live window in place, one recorder truth, saved→pull-out, review scoped in-world, flat routes live
```
