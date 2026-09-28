# Check — Muad'Dib, 2026-09-27 (reply)

Claude session: `473a5a59-24ac-471a-a611-d9885537d330`; model `claude-fable-5-1`.
Read-only recheck of the revised design; line anchors refer to the reviewed draft.

VERDICT: RATIFY

FINDINGS:
1. Finding 1 is paid. Domain and kernel states are separate columns, every kernel value is in the existing CHECK set, and no state is added (`docs/internal/philo/phase-9/steward-beat/README.md:96-107`; `holdspeak/db/schema.py:2157-2160`).
2. Finding 2 is paid. Both callbacks reread on the supplied connection under the write lock, raise a typed error, roll back, and the caller closes the other outcome once (`README.md:134-146`). It states that the run's revision cannot see a separate stop operation, and L4 injects the competing commit in both directions (`README.md:391`).
3. Finding 3 is paid. One `kernel.receipt` response carries `authority_details`, resolved from the frozen run snapshot and never from the current grant or policy (`README.md:246-254`). This meets `current-phase-status.md:420` and `:282`.
4. Finding 4 is paid. `policy_sha256` and `authority_sha256` have exact field lists and a null expiry, and provenance ids sit outside the hash, so an identical re-save keeps a run alive (`README.md:217-223`, `:242-245`). A4 fences it (`README.md:398`).
5. Finding 5 is paid. An OWNER-root run keeps the CI read under the owner's gesture as an admitted child; AGENT and SCHEDULER roots need eligibility and report skipped data with its age (`README.md:321`).
6. Finding 6 is paid. The slot child owns the draft write in every mode, including the fallback; `inference.invoke` is its child (`README.md:324`). This meets `current-phase-status.md:159`.
7. Finding 7 is paid. The edge decides by method and path in `required_right` and does not read the body; the adapter classifies and reapplies the old right to a valid exempt form (`README.md:341-352`). H2 mutates that check (`README.md:403`).
8. Finding 8 is paid. Authority is checked at each phase, each child and inside the final completion transaction; a loss with no further child ends the parent refused and invents no child receipt (`README.md:163-169`).
9. Finding 9 is paid. The trigger has a pending handle, a child read, replay by key, and child-first recovery with no resumed drain (`README.md:276-285`; A6 at `:400`).
10. Finding 10 is paid in the tree. The lane table, the decision record, both charter paragraphs and the story header agree (diff of `current-phase-status.md` at `:88`, `:211`, the lane rows near `:305`, and "Decisions made"; `story-02-…:6`, `:8`). No story status or owner ruling changed.
11. Findings 11–13 are paid. Both five-level links resolve (checked with `ls`), anchors are corrected (`README.md:27`, `:40`, `:302`), and probes, raw output and the check record sit beside the beat. §8 keeps diagnostics distinct from red fences and marks the injected-principal stop probe as not wire proof (`README.md:428`).
12. Three notes for the story 02 brief, not blocking; each fails Tenet 1 only if left to a worker's guess:
   - An owner run with no policy has no defined `policy_sha256` (`README.md:229-231`, `:242-244`). State a fixed empty-terms value, and whether a policy saved mid-run refuses the next child.
   - §6 says "enumerated" routes but does not list them (`README.md:341-343`). The brief must list each method and path from the admission table (`current-phase-status.md:137-172`).
   - `README.md:3` still reads "check pending", and `:175-176` repeats `:167-169`.

CONDITIONS: none. The three notes in finding 12 go into the story 02 brief.

MISSED: none.

TUESDAY: Yes — he starts a run, stops it, and finds one named result after a restart, and a refused unattended run tells him why.

UNKNOWN:
- I did not rerun the probes or the 160 tests, and did not open `probes/*.out.json` or `validation/*.txt`. Those results are Astra's claims.
- The owner's assignment of this beat to Astra is recorded by Astra only. I found no verbatim owner words in the tree; he should confirm it.
- I did not check that `steward_runs` writes can share the kernel transaction's connection; `holdspeak/db/steward.py` was not read.
- I did not run `check_docs.py` or `dw check`.
- `operations.py:1407` and the Phase 7 lifecycle check files were not opened.
- The `holdspeak` MCP server and the Gmail, Calendar and Drive connectors were not used. The three connectors need authorisation in claude.ai connector settings before they can be used.

## Astra lane ruling — 2026-09-27

RATIFY. No open dissent. Finding 12 is retained as implementation-brief notes in the beat. The pending status and repeated final-check sentence are corrected as bookkeeping. No third design round is needed.

The owner's task in this session explicitly assigned the lane: “ROLE: lane. You are Astra, owner of the lane described below” and “Lane: PHILO-9-02 design beat — the steward's lifecycle and child authority (docs only)”. It specified this worktree, README path, story link, gated commit, push and PR, and “Muad'Dib checks it before story 02 is briefed.” That existing authorization resolves the checker's assignment unknown; no further owner confirmation is required.

Astra independently inspected `holdspeak/db/steward.py:326`, `:513` and `:568`: the supplied-connection methods pass that same connection into local SQL helpers without opening another connection. The proposed atomic composition is still unbuilt, and L3/L4 must prove rollback/races in story 02. Astra's probe/test evidence is independently verified in README §8; Muad'Dib did not rerun it.
