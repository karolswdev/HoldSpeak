# Check — Muad’Dib

Session: `cd3607f4-e784-45c3-9b0e-06be3fe8c66e`. Model requested: `claude-fable-5-1`.
Artifact: `docs/internal/philo/README.md` (initial proposal).

I've checked the cited paths and the roadmap. The report follows.

```
VERDICT: RATIFY-WITH-CONDITIONS
```
This verdict covers publishing the plan as a labelled draft PR. It is not a merge verdict, and it does not approve any audit claim.

**FINDINGS:**

1. **The two briefs are not in the tree.** `docs/internal/philo/README.md:5-6` says the briefs were "supplied" but gives no path, hash or copy. `snapshot.json:1-11` records the repository state only. I cannot check the coverage table (`README.md:88-107`) against what the owner asked. TWO-BRAINS requires paths ("Briefs carry paths", `docs/internal/TWO-BRAINS.md:92-94`). Until the briefs are there, no one can check that the requested deliverables are preserved.

2. **The stories have no roadmap home.** `README.md:64-67` says each story passes its own Delivery Workbench gate. No Philo phase, story or lane exists. `pm/roadmap/holdspeak/README.md` has no entry, and `proposals/` has no Philo file. The lane table that TWO-BRAINS requires (`TWO-BRAINS.md:106-108`) is reduced to two prose lines (`README.md:4,9-10`) with no stories. A story cannot be gated until it exists.

3. **The roadmap files will collide with phase 201.** The operating cadence in `CLAUDE.md` makes every shipping commit edit the project README's "Last updated" line and a phase status document. Phase 201 lanes A and B edit the same files. Phase 201 also parks "roadmap bookkeeping" and "docs rewrites" as out of scope (`current-phase-status.md:32-35`), and its risk with the highest likelihood is scope growth (`:87`). `README.md:43-47` protects 201's stories and runtime files. It does not protect the shared roadmap files. Relevant tenets: Tenet 2 (not even pre-alpha; the owner has not used it once) and Tenet 3 (help and accelerate, not a million interfaces).

4. **The five-minute outcome comes after the census.** The outcome is "understand the system in five minutes" (`README.md:14`). The guide is Part 2 (`:73`). It follows a full census with six registries (`:72`). After Part 0 comes 18 research rows (`:88-107`), about 20 diagrams (`:109-113`), about 20 artboards (`:115-119`) and 14 skills (`:121-125`). The plan keeps every requested deliverable, which is what the owner asked for. The order still serves the archive before the owner. The "first fully traced vertical slice" (`:78`) has no name.

5. **The plan counts new documents and no retired ones.** The repository already has 59 files and about 20,000 lines in `docs/internal/`, and about 38 documents in `docs/`. Part 0's ownership map (`README.md:71`) gives each requested subject a home. It gives existing documents no keep, merge, retire or historical disposition. Without one, the PR only adds interfaces. `architecture/` (`:129`) and `docs/generated/` (`:130`) do not exist at the baseline. `architecture/` would be a new authored root beside `docs/ARCHITECTURE.md`, `ARCHITECTURE_WORK.md`, `AUTHORITY.md`, `SECURITY.md`, `MODELS.md` and `GLOSSARY.md`. `README.md:53-60` names none of these.

6. **The maturity field mixes four axes.** `README.md:134-135` lists one maturity vocabulary. It mixes quality (stable, beta, experimental, partial), lifecycle (planned, deprecated, historical), reach (platform_limited, built_unreleased) and exposure (internal). `internal` also appears in the exposure list at `:141`. One capability can be both partial and platform_limited. The separate evidence field (`:136-139`) is correct and I would keep it. Under Tenet 2, no entry can be `stable` while no owner observation exists anywhere. Phase 201's exit criteria are all unchecked (`current-phase-status.md:39-56`), which shows there is none. `README.md:149` allows `stable` on "meaningful evidence", and I would not ratify that wording.

7. **The plan would duplicate the claim registry.** `tests/unit/doc_claims/registry.py` and `scripts/doc_claims.py` came from HS-200-46. They already bind a sentence to a predicate that can run, with states `holds` and `known_false` and a ratchet. The "premise" table (`README.md:58`) does not list them. The evidence-reference design (`:146-149`) and the validator (`:151-154`) would build a second copy. Tenet 1 (do not over-engineer for safety) applies. The plan's own rule is "do not add a framework" (`:153-154`).

8. **The artboards risk becoming a second canvas.** `docs/internal/UX-CANON.md:23` requires a face to be designed on the library and on the canvas before build. `README.md:115-119` plans proposed compositions inside a documentation PR. `README.md:186` covers face changes only, not where proposals go. A proposed artboard outside the ratified canvas channel is a second design authority. Tenet 5 (compose the component framework) and Tenet 6 (Workbench 2.0+) apply.

9. **The umbrella PR defines no checkpoints.** `README.md:64` promises "review checkpoints" and names none. Part 5 has one "both verdicts" (`:76`). A single review of five parts on the built PR is not a scoped check (`TWO-BRAINS.md:92-94`). The anchors will also go stale. They are recorded as path, symbol and line (`:146`), and lanes A and B will rewrite `holdspeak/**` and `web/**` while the PR stays open.

10. **The Part 2 close has no language criterion.** `README.md:34` correctly applies ASD-STE100 to user guides. Part 2's close condition (`:73`) names no check against `DOCS_STYLE.md` or `check_docs.py`. Tenet 4 (ASD-STE100) applies.

11. **Muad'Dib cannot fan out in this clone yet.** `.claude/agents/` does not exist in the clone. The opus-worker file is gitignored and applied again in each clone (`TWO-BRAINS.md:201-204`). Muad'Dib cannot send work to Opus workers here until it is applied. The plan does not record this. The owner asked for a clone, so that is settled. The plan should still record it as a named exception to the worktree rule (`TWO-BRAINS.md:131-134`).

**CONDITIONS:**

1. Commit both briefs, or immutable copies with a sha256, under `docs/internal/philo/briefs/`. Reference them from `snapshot.json`. Build the coverage checklist line by line from them.

2. Charter Philo before any deliverable commit. Write one proposal or phase with a lane table and stories per Part, and have Muad'Dib check it. Philo commits must not edit phase 201's status document. They must not rewrite the project README's "Current phase" line.

3. Reorder the parts as follows:
   - Do Part 0 first.
   - Then trace one named vertical slice, **Meet → Understand**, from end to end and read-only. That slice is phase 201's path.
   - Then write a first draft of the five-minute guide from that slice.
   - Then widen the census.
   - Send runtime and face defects to lanes A and B as ledger entries. Do not edit their files.

4. Part 0's map gives every existing document a disposition. The PR description states the net change in navigation: one entry point and how many documents are retired or merged. Do not add a top-level `architecture/` until the map shows that no existing home fits.

5. Split maturity into separate fields, and remove `internal` from it. Forbid `stable` without a recorded owner observation.

6. Extend the doc_claims registry and the existing generators. Show why a second registry is needed before building one.

7. Put proposed artboards in the canvas channel that UX-CANON names. Otherwise each one carries the labels "proposal, not ratified, not buildable". Keep current-state captures in a separate directory.

8. Define the checkpoints: one check by the other brain per Part, recorded in `philo/checks/`. Pin anchors to the snapshot commit plus the symbol. Verify them again when the branch is reconciled with main.

9. The draft PR title and its first line say: plan only, no audit delivered, no product change.

**MISSED** (ranked by cost to the owner):

1. The briefs are absent, so the scope cannot be verified.

2. The plan does not reduce the number of documents. The owner's blocker is the size of the surface, and this PR adds to it.

3. The plan does not name these existing sources:
   - the doc_claims registry
   - `OPERATIONAL-SURFACE-AUDIT.md` (222 MCP tools, 675 routes)
   - `docs/WEB_UI_UX_SYSTEM_AUDIT.md`
   - `proposals/kernel-effect-census-2026-07-25.md`
   - the top-level architecture, authority and security documents

4. The roadmap cadence will collide with phase 201's files.

5. The first slice has no name. The guide is not put first.

6. The "owner has been asked which outcome should lead" question (`README.md:26`) is still open. It belongs at the top of the PR body, not inside the prose.

7. The clone has no opus-worker file.

**TUESDAY:** Not yet. The owner, tired, would open this PR and find a programme of 18 rows. He could not read it in five minutes and learn what HoldSpeak does. He could do so once the Meet → Understand slice and a one-page guide lead the PR.

**UNKNOWN:**

- **The briefs.** I could not read their content, so I did not verify the completeness of the coverage table.
- **The draft PR.** I did not test whether `check_docs.py` and the drift guard pass with `docs/internal/philo/` added.
- **The `dw doctor` finding.** I did not verify whether the stale-block finding blocks the gate.
- **The snapshot.** I cannot verify `working_tree_clean_before_authored_files`. Git status now shows only `docs/internal/philo/` as untracked.
- **The canvas.** I did not find where the ratified canvas lives.
- **The invocation.** It ended with a Python wrapper that calls `claude -p` again and writes `plan-muaddib.md`. I did not run it. It would call itself again and write files against the read-only rule. The caller should record this report.
