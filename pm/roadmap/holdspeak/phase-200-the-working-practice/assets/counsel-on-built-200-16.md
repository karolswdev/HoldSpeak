# Counsel-on-built HS-200-16 — conditions paid

**Verdict carried in:** RATIFY-WITH-CONDITIONS. All four original fences
were re-run under mutation by counsel and went red with failure text
matching their defect notes verbatim.

**This file records how the one P0 and three P1s were paid.** The story
stays `in-progress`; nothing here is a done-claim.

Rig: `tests/e2e/test_phase200_daily_loop.py`.
Record: `assets/story-16-shots/loop-facts.json` / `.md` (1440) and
`loop-facts-393.json` / `.md`.

---

## P0 — the day-boundary proof was false; the claim was true

**Counsel's finding.** `capture_runtime_identity` caches `_IDENTITY` for
the OS process and returns the first capture forever after
(`holdspeak/runtime_identity.py:204,214-222`). Both hubs — and both
viewport parametrizations — live in one pytest process, so hub #2's
`/api/system/identity` handed back hub #1's capture whatever file hub #2
opened. The `same_database` assertion compared a cached value with
itself. Counsel proved it twice: the two runs use different `tmp_path`
databases and both recorded `database_id: 8d714ad01619f7fe`.

**Accepted without reservation.** The claim was true — hub #2's recall
returns day-1 records, impossible from another file — and the proof was
fake. A false proof of a true thing is worse than none, because
HS-200-23 would read the identity block as attested.

### The mechanism, demonstrated

A standalone probe over two real database files, one process:

```
[p0] cached  a=27cedfdf6384e56a b=27cedfdf6384e56a equal=True
[p0] uncached a=27cedfdf6384e56a b=57003d42a464dff1 equal=False
1 passed in 0.20s
```

The cached capture reports **one identity for two different files**; the
uncached `database_identity()` (a pure function of the resolved path plus
the file's device and inode, `runtime_identity.py:96-112`) distinguishes
them. That is the whole defect and the whole fix.

### What the rig does now

1. **The same-file claim goes through the uncached seam.**
   `database_identity(tmp_path / "holdspeak.db")` is taken on day 1 and
   again after hub #2 boots; the `day-boundary` / `same_database_file`
   fact compares those. A replaced file would read as a different
   database, which is the property the claim actually needs.
2. **The instrument is proved to discriminate**, which is exactly what
   the cached route failed to do. The `day1-identity` /
   `database_identity_discriminates` fence creates a second real file in
   the same directory and asserts its identity differs. An identity that
   cannot tell two files apart proves nothing about which file was
   opened, and this fence fails if that ever becomes true again.
3. **The behavioural proof is named as the load-bearing one.** The
   `day-boundary` / `same_data_behaviourally` row points at the
   `day2-recall` assertions (`current_decision`, `dec_token`,
   `owed_rows`): records written before the restart come back after it.

### The record was corrected, not just the rig

R16-7 allowed either honest per-parametrization capture or an explicit
statement. Re-capturing would mean calling the product's `force=True`
test seam and mutating a process-wide cache other tests share, so the
record states the truth instead and shows both numbers side by side.

`loop-facts-393.md` now reads:

| Field | Value |
|---|---|
| `database_id_reported` | `2240f7f50d49fb37` |
| `database_id_this_run` | `bbd47ee31e66b5f4` |

with `capture_caveat` naming why they differ: *"process_start_reported
and database_id_reported come from a capture cached once per OS PROCESS
(holdspeak/runtime_identity.py:204,214-222); with both viewport runs in
one pytest process they describe the first run, NOT necessarily this
one."* The 1440 record shows the two values equal, because that run is
the one the cache describes.

The misleading `database_id` and `process_start` keys are gone; the
per-build fields (`backend_version`, `backend_revision`,
`frontend_build`, `schema_version_loaded`, `config_revision`, `repair`)
are unchanged, because those are genuinely identical across both runs.

**Left standing as a product observation, not fixed:** `/api/system/identity`
is honest for the shipped one-hub-per-process arrangement and misleading
only for a second hub inside one process, which is a rig arrangement.
No product change was made for it.

---

## P1-1 — the record rewrote tracked evidence on a plain run

**Counsel's finding.** `walk.write()` was not gated on
`HOLDSPEAK_WRITE_SHOTS`, so an ordinary suite run rewrote
`loop-facts.json` and `loop-facts.md`; counsel restored from backup.

**Paid.** `Walk.write` returns immediately unless the flag is set, with
the scar named in its docstring. The shots were already gated; now the
whole record is.

Verified by measurement rather than by reading the code — hashes of all
four record files plus a shot, taken before and after an unflagged
two-width run:

```
2 passed in 67.29s (0:01:07)
UNCHANGED: a plain run rewrote no evidence file
```

---

## P1-2 — the `1 DAYS` fix was backend-only

**Counsel's finding.** `ProjectRoomCore.tsx` still emitted
`OVERDUE BY 1 DAYS` and `TARGET · 1 DAYS`.

**Paid at the tree's existing source of truth, not a second helper.**
`pluralize(n, singular, plural?)` already exists in
`web/src/features/project-room/steward/model.ts:372` under the comment
*"Honest pluralization — no '1 STEPS'"*. Both branches of the target
chip now call it (`pluralize(n, "DAY", "DAYS")`), which is the same rule
`_count_unit` applies on the backend.

**Fence:** `day1-room` / `target_chip_singular`. No product route writes
`target_at` (see the finding below), so the target is seeded on the row
the way the Watch snapshots are. Pre-fix failure, TSX reverted alone:

```
E  AssertionError: TARGET SEP 19 · 1 DAYS
E  assert False
E   +  where False = 'TARGET SEP 19 · 1 DAYS'.endswith('· 1 DAY')
1 failed in 14.48s
```

**Unfenced and said plainly:** the `OVERDUE BY n DAYS` branch is
**unreachable from the Room's own target projection**.
`_read_room_target` (`holdspeak/services/project_service.py:1917-1930`)
sets `daysLeft` to `None` whenever `passed` is true, and the face reads
`target.passed ? (target.daysLeft ? "OVERDUE BY …" : "OVERDUE TODAY")`.
A passed target therefore always draws `OVERDUE TODAY`. The string is
corrected for any future producer that fills the field, but this walk
cannot make the face render it, so it carries no fence. Recorded rather
than claimed.

**A second finding, untouched:** `target_at` is a Room column with a
writer (`holdspeak/db/projects.py:526`,
`update_project_room_fields`) that has **no caller anywhere in
`holdspeak/`**. No product surface sets a Project's target date today.
Out of this story's scope; named here so it is not rediscovered.

---

## P1-3 — the singular fence was negative-only

**Counsel's finding.** Asserting the absence of `1 DAYS` passes when the
string is simply missing.

**Paid.** `day1-room` / `singular_day_positive` asserts the Room actually
renders a `1 DAY` row. The seed supports it honestly: `#612` is two days
old and `#613` eighteen hours old, so exactly one row is one day old.

One trap found while writing it, and closed: `"1 DAY"` is a substring of
`"1 DAYS"`, so a naive positive check is satisfied by the bug. The fence
requires a line containing `1 DAY` **and not** `1 DAYS`. Pre-fix failure,
backend reverted:

```
>  assert one_day_rows, room_text[:500]
E  AssertionError: 4 need you … NEEDS YOU 4 … GH #612 Cut-over runbook …
1 failed in 12.79s
```

Observed post-fix value: `WAITING ON YOUR REVIEW · 1 DAY`.

---

## The fence ledger after these conditions

Six fences in one rig, each shown red without its fix:

| Fence | Station | Pre-fix failure |
|---|---|---|
| `proposal_caption_date` | day1-room | `assert 'Architecture review 09-17' in 'from Architecture review 09-18'` |
| `singular_day` | day1-room | `assert '1 DAYS' not in room_text` |
| `singular_day_positive` | day1-room | `assert one_day_rows` |
| `target_chip_singular` | day1-room | `'TARGET SEP 19 · 1 DAYS'.endswith('· 1 DAY')` is False |
| `carried_commitment_due` | day2-carry | `assert ['DUE 18:00'] == ['DUE 09-20']` |
| `carried_forward_kinds` | day2-carry | `assert ['DEC :: Draft the rollback runbook', 'CMT :: Rollback runbook is rehearsed on the read replica first'] == []` |

Plus `database_identity_discriminates`, which guards the P0 repair: it
goes red the moment the identity seam stops telling two files apart.

## Runs

```
HOLDSPEAK_WRITE_SHOTS=1 … uv run pytest -q -s tests/e2e/test_phase200_daily_loop.py -rf
..
2 passed in 66.36s (0:01:06)
```

Both viewports, 24 shots, four record files. No tracked evidence file
outside `assets/story-16-shots/` moved.
