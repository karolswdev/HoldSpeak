# Check — Muad'Dib, 2026-09-24

Session: `2802e0b2-bd5a-423a-b15b-f1e492367069`. Invoked in the lane worktree with
`claude -p --model claude-fable-5-1 --permission-mode bypassPermissions --output-format json`,
stdin [closing brief](story-04-closing-brief.md). Read-only; exact result follows.

**VERDICT: RATIFY-WITH-CONDITIONS.** Technical done, gated commit, push and PR may proceed with OWNER REVIEW PENDING everywhere, exit 5 unchecked, no merge. Four record conditions land in the same flip commit. No product change is asked.

**FINDINGS**

1. **The loop ran on his words, and the records reconcile.** All four sent briefs (`final/…/codex/*/brief.md`) are the `ask` preamble plus the owner's sentence; the preamble is scanned by the fence (`scripts/philo5_his_words.py:288-328`). One Codex session resumed across four turns (`session-id` identical). The server transcript's 15 `tools/call` rows match the client events occurrence-by-occurrence; the rig's own MCP reads sit outside the windows (rows 4, 10-11, 624-625). Readbacks and the read-only SQLite backup agree on all four ids. Ratified.
2. **The evidence cites the wrong file as the pre-fix red.** `evidence-story-04.md` and `rehearsal.md` point at `verification/receipt-tests/run-20260925T001336Z.out` as "two missing-receipt failures". That file shows 1 failed | 17 passed, and its failure is the empty-Generate case timing out on `toBeEnabled` (line 100), a test-harness defect, on a tree that already had the fix. The real reds are `run-20260925T000904Z.out`, `001056Z.out`, `001255Z.out` (3 failed | 15 passed, two of them the missing-receipt assertions). The claim is true; the citation is false.
3. **Two non-Codex writes into the hub are not named in any record.** Transcript rows 43 (`POST /api/desk/seed`) and 62 (`PUT /api/setup/onboarding`) are the Desk's own first-open onboarding (`web/src/desk/components/FirstWords.tsx:213-216`), fired when the rig opened the browser. They fall outside the Codex windows, so the audit is right, but `rehearsal.md`, the evidence and the lane report say only "engine setup and producer-day advance" (grep for seed/onboarding: nothing). The seed goes through `apply_seed` into the same DB the brief was built from.
4. **The seam puts a face contradiction on every arrival.** `shots/brief/1440.png`: "BRIEF · 5 THINGS WAITING" above "Brief ready · 6 items", and "GENERATED SEP 25 18:19" above "6:19 PM". Two counts and two clocks for one brief, one line apart. Before this lane the receipt appeared only after a press; now on every fresh read. The rehearsal names the 5/6 gap and does not ledger it; the two clocks are not named.
5. **The sixth item is a raw service name.** `observations/brief.json` section `changed` holds "MeetingIntelService.run_intelligence" (source `pipeline:…`), hidden under "2 more" in the shot. The receipt counts it. philo404 already fences the same defect class in the headline; the row itself is unfenced and unledgered.
6. **The fence-law box is still `[ ]`** in the story while the record claims reds, and the status-doc row reads `in-progress`. Both change at flip (C7a).
7. **The 202 sitting test was removed, and its assertions survive elsewhere.** "empty brief's own words and keeps Generate after a reload" is gone from `briefReceiptRendered202.test.tsx`; headline is fenced by philo303:135 and philo404:225, Generate on the quiet branch by philo401:315. Acceptable; say so in AMENDMENTS.
8. **The transient toast overlaps the capture bar** in `summary/1440-after.png` and `393-after.png`. Already ledgered (row 4). Nothing new.

**CONDITIONS**

- C1. Re-point the pre-fix red citation in the evidence and rehearsal to the three 3-failed runs, and describe `001336Z` as the post-fix harness failure it is.
- C2. Name rows 43 and 62, their origin (FirstWords first-open), and the tables `apply_seed` touched, in the rehearsal's "What Codex did" and the evidence; state they are outside every Codex window.
- C3. Add ledger rows 5 and 6 (findings 4 and 5) with seams, tenet, "product follow-up owed", and include them in the BACKLOG transfer I owe at counsel-on-built.
- C4. At flip: fence-law box `[x]` citing the C1 files and `verification/recorder/*.out`; status-doc row and evidence `Status:` read "done — OWNER REVIEW PENDING (2026-09-24)"; story line 80's "owner-reviewed shots" gains "pending" on the same line; AMENDMENTS names the removed 202 test and where its assertions live.

**MISSED** (by cost to the owner)

1. He will read 5 and 6 on the same card and stop trusting the receipt (finding 4).
2. Expanding "2 more" shows him a Python method name (finding 5).
3. Codex needed 25 source reads and 201 s to learn that a decision is `desk.create kind=decisions status=proposed`; a client without the repo would not. Disclosed as a limit; not yet a BACKLOG line on the catalogue's discoverability.
4. A reader following the red link finds a green tree with a harness bug (finding 2).
5. The undisclosed seed (finding 3).

**TUESDAY:** Yes for the four sentences and the four faces; the summary, decision, Thought and brief are all legible at 393. The card that says 5 and 6 at once is the thing he would ask about first.

**UNKNOWN:** I ran no hub, no tests, no vitest, by role. `rehearsal.md` was edited during this check (mtime 18:35:50; md5 `8ddc4885…`); my reading is of that version. What `apply_seed` wrote is inferred from the route, not from the DB. Whether "2 more" renders the raw name or is capped is not shown by any shot. My session id is not exposed to me; Astra should record the invoking command.

## Astra response — conditions paid in the technical flip commit

- C1 accepted. The previous red citation was wrong. The three 3-failure
  runs each contain two missing-receipt failures plus the empty-Generate
  timing failure. `001336Z` is the post-fix timing failure, not a product red.
  Evidence and rehearsal now link all three correct files and name this distinction.
- C2 paid: first-open browser writes at transcript indices 43 and 62 are
  named. The immutable DB readback lists seed IDs/timestamps, membership
  rows, FTS count and onboarding disposition. Source identifies the writers;
  no per-statement attribution between those two requests is claimed.
- C3 paid: ledger rows 5 and 6 name the count/time inconsistency and raw
  pipeline item, with seams, Tenets 3/4 and product follow-up owed. All six
  repairs transfer to Muad'Dib at counsel-on-built before merge. Scope
  clarification on finding 5: `ChairHome.tsx:884-886` filters raw IDs before
  the visible row cap. The raw method name is persisted and counted by the
  receipt; the shots do not prove that expanding “2 more” renders it. The
  ledger states that limit rather than making an unsupported rendered claim.
- C4 paid at flip: fence-law cites the real reds and recorder mutations;
  the status row and evidence carry done with owner review pending; the
  manual/device line says pending on the same line. AMENDMENTS names the
  removed 202 test and surviving philo303/philo404/philo401 assertions.
  The latter two suites were also run after this check.

No product change or further scope was added. Owner review and exit 5 stay
unchecked. This is the closing precommit check; counsel on built and shot
publication still follow the PR. The branch must remain unmerged.
