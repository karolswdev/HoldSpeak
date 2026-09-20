# Check — Muad’Dib, round 2

Session: `cd3607f4-e784-45c3-9b0e-06be3fe8c66e`.
Scope: draft proposal publication only.

```
VERDICT: RATIFY-WITH-CONDITIONS
```
Scope: publish this plan only, as a labelled draft PR. This is not a merge verdict. It ratifies no audit, registry, SRS, artboard or skill, and it accepts no claim about the product.

**FINDINGS:**

1. **Condition 1 is met: the briefs are preserved.** `briefs/` holds the owner's request and both extracts. I recomputed the SHA-256 of all three files. Each matches `snapshot.json` (`owner_request_sources`, `b98e2d36…`, `f3226d25…`, `ae5606ee…`), and the byte counts match. `README.md:7-10` links them and states that the imported citations are not verified.

2. **Condition 2 is met for publication: charter before deliverables.** The plan puts a checked roadmap charter before any deliverable work. It records a lane table (`README.md:93-99`). `PMO-CONTRACT.md:130,180` allows an "atomic chunk" outside the roadmap framework, so the non-story framing is lawful. Git status shows only `docs/internal/philo/` as untracked. No roadmap file is touched.

3. **Condition 3 is met: a first useful slice comes first.** Part 0a traces Meet → Understand read-only and writes the first guide before the census widens (`README.md:80,87-88`). `README.md:48-55` forbids edits to Phase 201's status document and the shared roadmap README. It also forbids taking the Current phase pointer.

4. **Condition 4 is met as a plan rule: reconcile existing homes first.** `README.md:229-238` names the existing homes. It requires a keep, consolidate, park or historical disposition for each. It approves no new authored root (`:163`) and asks for one entry point. Astra's caveat is that a smaller file count is not itself the outcome. I accept that. The measure is the navigation the owner sees.

5. **Condition 5 is met: status axes are split.** The axes are separated. `internal` moves to exposure. `stable` requires a recorded owner observation plus test evidence (`README.md:166-171`).

6. **I concede Astra's dispute in response item 6.** Unchecked Phase 201 criteria do not prove that no owner observation exists anywhere. The rule does not need that claim.

7. **Conditions 6 to 8 are met.**
   - `README.md:158-164` extends the doc_claims registry and keeps domain-owned sources.
   - `README.md:144-145` uses the canvas workflow with the label "proposal, not ratified, not buildable".
   - `README.md:89-91` sets one check per part.
   - `README.md:89-91,180` makes each evidence anchor name the snapshot commit, path, symbol and line.
   - `README.md:82` names DOCS_STYLE in the Part 2 close.

8. **`initial-findings.md` makes honest claims.** It records `check_docs.py` and `test_docs_navigation` runs. It states that no pytest, hub, database or model was used. I did not run those commands again. They are Astra's claims with command output.

9. **`source-checklist.md` is a heading index, not requirement coverage, and it says so (`:3-5`).** It lists Mermaid diagram edges as sections, for example `capability-audit.txt:403` "HOTKEY --> API". Many of its roughly 250 rows are noise. This does no harm while every row is "Pending reconciliation". It would be misleading if Part 0 later counted those rows as coverage.

10. **`owner-request.txt` appears to contain both briefs.** It is 198 KB. The two extracts together are 97 KB plus 100 KB. About 400 KB is therefore committed to preserve about 200 KB of input. This does not block publication.

11. **The repository is PUBLIC, per `gh repo view`.** The PR will publish the owner's conversational request verbatim. It will also publish the local path `~/dev/tools/HoldSpeak-Philo` (`README.md:14`). I scanned all three briefs for keys, tokens, email addresses and home paths. The scan matched only design-token prose in `workbench-design-srs.txt`. It matched no credential, email address or home path. I did not read 395 KB line by line.

**CONDITIONS** (for publication time; all small):

1. Update `README.md:4`. The line "response pending second check" is stale once this record lands. Link round 2 there.

2. Make the draft PR title and the first body line say: plan only, no audit delivered, no product change. Keep the PR in draft. The body must state that charter and requirement-level coverage are next work.

3. Put the open owner question at the top of the PR body: which outcome leads (`README.md:31`). Put this one-line notice beside it: "your verbatim request is published in a public repository under `briefs/`". He asked for the PR, so this is a notice and not a block.

4. When Part 0 starts, regenerate the checklist without the diagram-edge rows, or mark those rows as diagram edges. Do not report the row count as coverage.

5. Make no later commit under this PR before the charter is checked (`README.md:97`).

**MISSED** (ranked by cost to the owner):

1. The briefs will be publicly visible. Neither the plan nor the response names this.

2. The checklist contains noise rows (finding 9).

3. The input is stored twice (finding 10). Keep the full request and drop the extracts, or state why the repository needs both.

4. The `dw doctor` stale-block finding is still not classified against the commit gate (`README.md:242-245`). The gate result of this first commit will settle it. If the gate blocks, record the banner. Never use `--no-verify`.

**TUESDAY:** For this publication, yes. The owner opens one draft PR, reads "plan only" and sees one question to answer. The five-minute understanding itself is still not delivered, and the plan says so.

**UNKNOWN:**

- **The briefs.** I did not read them in full. I cannot verify that the extracts are faithful to `owner-request.txt` beyond their size and heading structure. The keyword scan is not a privacy review.
- **The checks.** I did not run `check_docs.py`, the drift guard or the DW gate again. Whether the commit passes the gate is unknown until someone tries.
- **The canvas.** I did not confirm that the "ratified canvas workflow" exists as a channel.
- **Not executed.** I did not run the caller's wrapper, edit any file or contact anyone.
