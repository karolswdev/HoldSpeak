# Check — Astra, 2026-09-19: the Seven Tenets

**Artifact:** `CONSTITUTION.md` "The Seven Tenets" + cross-references, authored
by Muad'Dib from the owner's charter of 2026-09-19. **Checker:** Astra
(`gpt-6-astra`, `xhigh`), codex session `01a0bb8f-92c6-7d53-b1f3-6ce3e3cef6ff`, read-only.
**Protocol:** TWO-BRAINS.md §3.

## Round 1 — Astra's report (verbatim, on the first draft)

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Tenets 1–3: the gloss adds law.** “Ceremony is spent only where it buys…receipt, provenance, or an undo” and “Everything else is a ledger, not a gate” invent an exhaustive test. It could waive useful consent while justifying endless receipt machinery. Keep the owner’s sentence alone. Likewise, change “Every decision…not against a release…” to a **current priority**, and “One obvious move per job” to **a clear next action**. Multiple steps can serve one job. Evidence: `docs/internal/CONSTITUTION.md:25`.

2. **Tenet 4: right likely referent; wrong certainty.** ASD-STE100 Issue 9 is the [official standard](https://www.asd-ste100.org/). However, `docs/internal/DOCS_STYLE.md:10` explicitly calls the DTE→STE interpretation **provisional**. POSITIONING inherits that policy; it supplies no independent owner confirmation. Preserve “ASD-DTE-100” in the verbatim charter and identify STE100 as the editorial interpretation. Replace “every doc” with **product-authored interface text and user documentation**; do not imply rewriting source transcripts or internal evidence. “Short words” is not a sufficient specification of STE. Evidence: `docs/internal/CONSTITUTION.md:35`.

3. **Tenets 5–7: separate principles from implementation and inference.** “The surface library…is that framework” constitutionalizes a repository path; keep that existing implementation rule in UX-CANON. “Direct, dense, calm, beautiful” adds aesthetic prescriptions. “Not a web app, not a dashboard, not a chat box” turns inspiration into exclusions the owner did not speak. “Every job…is one of his jobs” converts the first-user priority into an exclusive product boundary. Keep modular components, Workbench inspiration, and the stated first user; label elaborations as design guidance. Evidence: `docs/internal/CONSTITUTION.md:39`.

4. **Tenet 1 versus Articles V/XI: distinguish friction from enforcement.** V.1’s propose–approve–execute wording invites duplicate confirmation, but **XI.4 already says the owner’s gesture is approval**; IV.2 also recognizes configured consent. Clarify V.1 **now** by referencing XI.4. V.2 receipts and XI.1–3/5 admission, authentication, and read authority do not inherently conflict with simplicity. Keep them internal. Their implementation cost can be reviewed at the first sitting; do not repeal them through tenet 1’s invented “everything else” sentence. Evidence: `docs/internal/CONSTITUTION.md:102`, `docs/internal/CONSTITUTION.md:163`.

5. **Tenets 3–4 versus explanation bans: amend narrowly now.** VII.1 and UX A.3 prohibit even a necessary short instruction; the empty-state exception requires “the next time something happens,” which may omit what the user must do. Permit the shortest instruction needed to complete the task, in simple English. Retain quiet chrome and prohibit filler. I–III, IV.1/3, VI and X have no intrinsic conflict with the tenets. Evidence: `docs/internal/CONSTITUTION.md:125`, `docs/internal/UX-CANON.md:27`.

6. **Tenets 2–3 versus breadth and ceremony: scope now; reassess after use.** VIII.1/3’s GPU and every-device requirements must not demand new platform work before first use. Keep existing craft; defer architectural changes until the sitting. IX.2 and UX A.2/A.13/E.1/E.5 need reconciliation **now** with the standing verification-based merge rule: retain agent screenshots at both widths, but distinguish owner observation from repeated approval gates. Evidence: `docs/internal/CONSTITUTION.md:134`, `docs/internal/UX-CANON.md:115`, `AGENTS.md:33`.

7. **Tenets 2–3/7: U1 remains too large.** My `docs/internal/inventory-2026-09-19/06-check-astra.md:89` accepted a bundle. The `docs/internal/inventory-2026-09-19/06-check-astra.md:109` corrected sequencing and evidence, but did not shrink it. Replace the first phase with **one useful meeting result**: identify the intended build/DB; the owner records a real meeting, requests its summary with truthful pre-run egress, reviews it, and finds it after restart. Repair only dependencies this path actually needs. Park Room linking, connector setup, watch creation, general Models consolidation, cleanup, and bookkeeping as first-use prerequisites. Keep unrelated automation inactive; repair any loop that cannot remain inactive. Preserve dictation as a regression obligation—the `docs/internal/INVENTORY-2026-09-19.md:13`. Hold the sitting immediately after this result.

8. **Tenets 2–4: references must not amplify the additions.** ORCHESTRATION’s “help…or add an interface” makes any interface suspect; change it to unnecessary interfaces. CLAUDE’s “every…doc” inherits finding 2. The amendment already says “Checked by Astra,” but its named record was absent when inspected. Record the actual verdict before committing that claim. Evidence: `docs/internal/ORCHESTRATION.md:51`, `CLAUDE.md:33`, `docs/internal/CONSTITUTION.md:194`.

CONDITIONS: Preserve the verbatim charter; separate interpretations from owner law; resolve the immediate ambiguities above; re-charter the smaller first-use phase.

MISSED: Ranked by owner cost: another bundled wait for usefulness; invented constitutional absolutes; inherited ambiguity presented as confirmed intent.

TUESDAY: Not established. One meeting and one useful, recoverable result is a credible first sitting.

UNKNOWN: No runtime, DB, screenshots, or owner behavior reverified. Standard identity is verified; the owner’s intended spelling is inferred. Tree unchanged.

## Round 1 — Muad'Dib's response

| # | Ruling | Done |
|---|---|---|
| 1 Tenets 1–3 gloss | **ACCEPT.** I wrote absolutes ("everything else is a ledger", "one obvious move") the owner did not speak. | Section rewritten: the tenets are his verbatim words; each carries a labelled *Reading* that is stated non-law and yields to his sentence. |
| 2 ASD-STE100 | **ACCEPT.** DOCS_STYLE.md:10 calls the STE reading provisional; I presented it as confirmed. | Verbatim "ASD-DTE-100" kept in the tenet; STE100 named as the co-creators' reading for the owner to confirm or correct; scope narrowed to product-authored text and user docs. Every cross-reference says "his words: ASD-DTE-100". |
| 3 Tenets 5–7 | **ACCEPT.** The library path, the aesthetic adjectives, the exclusions and the "every job is his job" boundary were mine. | Removed from the Constitution; the library rule stays in UX-CANON; Workbench guidance stays in DESIGN_SYSTEM/UX-CANON; tenet 7 reads as priority, not boundary. |
| 4 V.1 vs XI.4 | **ACCEPT as a proposal.** Only the owner amends articles (X.1). | Proposed below, not enacted. |
| 5 VII.1 / UX A.3 instruction ban | **ACCEPT as a proposal.** | Proposed below. |
| 6 VIII breadth; IX.2 / UX E vs verification-merge | **ACCEPT.** No new platform work before first use; IX.2 reconciliation proposed below. | Proposed below. |
| 7 U1 still too large | **ACCEPT.** One Journey bundled five results; tenets 2–3 want one. | The first phase becomes **One Meeting Result** (below); recorded in `inventory-2026-09-19/06-check-astra.md` as an amendment to the close. |
| 8 References amplified | **ACCEPT.** | ORCHESTRATION now says "unnecessary interface"; CLAUDE/AGENTS scope the language tenet; this record exists before the amendment entry that names it. |

### Article amendments PROPOSED for the owner (Article X.1; not enacted)

- **V.1**: add "The owner's own gesture on a verb is the approval (XI.4);
  no second confirmation is asked for it."
- **VII.1** (and UX-CANON A.3): add "The shortest instruction needed to
  complete the task, in simple English, is permitted; filler is not."
- **IX.2** (and UX-CANON E): "The owner sees shots before merge" becomes
  "shots at both widths are recorded before merge; a merge proceeds on
  verification (2026-09-17 ruling); the owner's observation is the sitting,
  not a gate on every story."
- **VIII.1/3**: no NEW platform scope (devices, GPUs) is chartered before
  the first sitting; repairs the selected path needs are allowed.
- The IX.2 proposal also covers the residual approval wording in UX-CANON
  A.2 and A.13 and in ORCHESTRATION §5 ("the nod is the merge trigger"), so
  no contradictory approval rule survives ratification.

### The first phase, re-cut a second time: **Phase U1 — One Meeting Result**

Exit, on the owner's desk, observed: the hub runs from an identified build
and DB; he records one real meeting; he asks for its summary with the
egress host disclosed before the run and truthful after; the summary is
useful to him and traceable to that meeting (an unusable output fails the
exit); he finds it again after a hub restart. Only the dependencies that
path needs are repaired (the SERVICE capability assignment for the summary,
the badge at the point of decision, the unresolved-placement-to-local
default, the ownership gate on any loop that cannot stay inactive).
Dictation is a regression obligation, not a story. Parked as first-use
prerequisites: Room linking, connector setup, watch creation, Models
naming, worktree cleanup, roadmap bookkeeping, the Go rail. The sitting
follows the result immediately.

## Round 2 — Astra's reply

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **Yes, the rewrite lifts DO-NOT-RATIFY.** The owner’s words are preserved and the Readings explicitly lack legislative force. **Tenet 3:** “every face must shorten a job” remains unnecessarily absolute guidance. Use “faces help the user complete a job; show a clear next action where needed.” An inspection surface can help without shortening anything. `docs/internal/CONSTITUTION.md:24`, `docs/internal/CONSTITUTION.md:39`.

2. **All four amendments are correctly framed as owner proposals.** They are explicitly “not enacted,” and the articles remain unchanged. **Tenets 2–3:** narrow VIII’s prohibition to new platform scope, allowing repairs necessary for the selected path. Make IX’s proposal cover the residual approval wording in UX A.2/A.13 and ORCHESTRATION, as well as E. Otherwise contradictory instructions survive ratification. `docs/internal/checks/constitution-seven-tenets-astra.md:51`, `docs/internal/UX-CANON.md:23`, `docs/internal/ORCHESTRATION.md:234`.

3. **Tenet 4: reference repair is incomplete.** CLAUDE, AGENTS and UX now acknowledge the owner’s wording. ORCHESTRATION still states STE100 unqualified, contrary to the response’s “Every cross-reference” claim. Point it to the provisional Reading. Also change the amendment record’s “three” proposals to “four.” `docs/internal/checks/constitution-seven-tenets-astra.md:43`, `docs/internal/ORCHESTRATION.md:52`, `docs/internal/CONSTITUTION.md:206`.

4. **Tenets 2–3/7: One Meeting Result is the smallest credible first phase in this record.** No unrelated deliverable remains mandatory. Keep each listed repair conditional on demonstrated dependency. Make the exit explicitly require a useful summary traceable to that meeting; “he reviews the result” alone could pass an unusable output. This strengthens the existing outcome without adding a story. `docs/internal/checks/constitution-seven-tenets-astra.md:66`.

CONDITIONS: Apply these wording and consistency fixes. Owner ratification remains necessary to enact the proposed amendments; this check does not enact them.

MISSED: Ranked: accepting an unusable summary; leaving contradictory approval rules; incomplete reference bookkeeping.

TUESDAY: The scope now fits one real job. The observed sitting must establish whether the owner can complete it.

UNKNOWN: Runtime dependencies, summary quality, and usability remain unverified. This was a document check; nothing in the tree changed.

## Close — Muad'Dib, 2026-09-19

All four conditions applied: Reading 3 softened ("help the user complete a
job; a clear next action where needed"); the VIII proposal narrowed to new
platform scope and the IX proposal widened to UX-CANON A.2/A.13 and
ORCHESTRATION §5; ORCHESTRATION now points at the provisional STE100
reading and the amendment record says four proposals; the U1 exit requires
a useful summary traceable to its meeting.

**Record closed: RATIFY-WITH-CONDITIONS, conditions absorbed, no open
dissent.** The owner confirmed ASD-STE100 ("yes, ASD-STE100", 2026-09-19). The
four proposed article amendments stay proposed; he did not rule on them,
so the articles stand as written and the 2026-09-17 verification-merge
ruling continues to govern practice. The tenets themselves are his words and
are in force.
