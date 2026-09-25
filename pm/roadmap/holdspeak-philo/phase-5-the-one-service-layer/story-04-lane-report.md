# PHILO-5-04 — The owner asks in his own words

**OWNER REVIEW PENDING (2026-09-24).** Target proof mode:
**REHEARSED, OWNER-REVIEWED SHOTS — PENDING**. No live sitting is claimed.

## LANE

PHILO-5-04, technically done; Astra owns; Muad'Dib checks. Worktree `../wt-philo-5-04`,
branch `feat/philo-5-04-his-words`, from main `9c653937`.
PR: [#638](https://github.com/karolswdev/HoldSpeak/pull/638), OPEN and unmerged. Build commit `4c56fa94`
passed the stamped gate (7/7, one story with evidence). Muad'Dib counsels
on built and publishes the shots next; owner review remains pending.

## OUTCOME

The real-engine Codex rehearsal completed in 326.090 seconds. Four ordinary
prompts produced a meeting summary, a proposed review decision, a saved
Thought edit, and a next-day brief with that decision visible at both
1440 and 393. The fresh Desk now shows the existing brief receipt for the
latest durable brief. This narrow product seam was checked before build.
Muad'Dib ratified technical completion with four record conditions, paid
in this commit. Owner review remains pending, separately from technical
completion. [Closing check](checks/story-04-closing-muaddib.md).

## PROOF

[Rehearsal record](../../../../docs/internal/philo/phase-5/his-words/rehearsal.md)
contains all four prompts verbatim, the 15-call sequence, per-turn durations,
shot IDs at both widths, registry readbacks and limits.
[Complete final run](assets/story-04-shots/final/20260925T001407Z-his-words-real/observations.json),
[full server transcript](assets/story-04-shots/final/20260925T001407Z-his-words-real/rehearsal-transcript.jsonl),
[effective config](assets/story-04-shots/final/20260925T001407Z-his-words-real/effective-codex-config.json),
[DB-path proof](assets/story-04-shots/final/20260925T001407Z-his-words-real/hub-proof.json).
The LAN engine answered HTTP 200 and actually made the summary.

Canonical readbacks: meeting `1a1f7ce7`; decision
`decision_96c04b1b7a13`; Thought `thought_2b4148a5b1f8` (revision 1 → 2);
brief `brief-de8a52459de14125bc7ed351be8451b9`. The brief's decision source
matches the decision ID. The summary arrived on the existing pages with no
manual refresh; the brief used the accepted fresh/reopened read.

The root inspected all final face views at both widths. The first browser
opening also issued `/api/desk/seed` and `/api/setup/onboarding` at transcript
indices 43 and 62, outside every Codex turn; see the [seed readback](assets/story-04-shots/verification/first-open-seed-readback.txt). The receipt says
`Brief ready · 6 items · 6:19 PM`; six raw items are not six visible rows.
The timestamp is the producer period end. Receipt before/after proof uses
the same earlier Codex-produced brief, with no second Generate:
[red](assets/story-04-shots/receipt-red/brief-read.json),
[green](assets/story-04-shots/receipt-green/brief-read.json).
[Four stopped attempts](assets/story-04-shots/attempts/README.md) remain
retained with their original prompts, outputs, errors and limits.

Scoped Python validation collected 240 tests; the final run had 239 pass
and one atlas-line-reference failure. The ten shifted references were
corrected with the product edit; the affected atlas/schema/reference suites
then passed **113 tests**. These are overlapping scopes, not 352 unique
tests. [Failed run](assets/story-04-shots/verification/final-python-tests.txt),
[corrected run](assets/story-04-shots/verification/anchor-fixed-python-tests.txt).
The rendered receipt/load/date suites pass **20 tests** (four files);
the C3 clear-on-failure mutation fails as required. These and the artifact mutation audit are
recorded in [evidence](evidence-story-04.md). No full suite was run.

Actual atlas cases paid the direct import hash citation, the missing-
decision refusal pair (with parity still failed), and S4 saved decision
content at 393 and 1440. The six carried boxes link those proofs and the
four carried repair dispositions; the closing check added two more ledger rows.

## LEDGER

These six items are **LEDGERED**, not repaired. Classification **b** means
an inherited product defect. The only ratified product change in this lane is the latest-brief receipt
seam; these six repairs remain outside that scope. Muad'Dib accepted the disposition and the ledger transfer in
[the scope check](checks/story-04-scope-muaddib.md) and
[closing check](checks/story-04-closing-muaddib.md).

| Item | Class and evidence | Owner cost and disposition |
| --- | --- | --- |
| Shelf invalid-state schema pre-empts the registry | **b**. `holdspeak/mcp/tools.py:459` against `holdspeak/operations.py:421-423`; [story 03 counsel](checks/story-03-shelf-refusal-muaddib.md). | The transport answers before the service's named refusal. Tenet 3 and the phase's contract-reach criterion. Preserve `refusal_origin: transport_schema` and `registry_reached: false`; accepted shelf paths have separate reach proof. **Product follow-up owed**: align transport and contract with real-producer red/green evidence in a product story. The refused branch does not count toward exit 1. |
| Missing-decision HTTP fallback records two failures | **b**. `holdspeak/web/routes/decisions.py:58-61`, `holdspeak/services/monday_brief_service.py:577-593`; [scope check finding 3](checks/story-04-scope-muaddib.md). | One missing object becomes two broken items in the brief. Tenet 3, Article VI and inherited Article XI compatibility debt. **Product follow-up owed**: settle legacy-ID dispatch/observer semantics without dropping legacy reads. The actual refusal pair must retain both row counts and a failed parity verdict. No normalization is an equivalence claim. |
| Failed import shown as SAVED | **b**. `web/src/desk/chair/intelBadge.ts:26`, `web/src/desk/chair/ChairHome.tsx:265`, `holdspeak/services/meeting_service.py:315`; [story 03 glass reading](assets/story-03-shots/glass-review.md). | A failed transcript appears saved. Tenets 3/4 and Article VI. **Product follow-up owed**: map the real import failure on the Arrival row and fence the rendered state. This badge repair is outside the narrow receipt amendment. |
| Transient zero-decided toast | **b**. `web/src/components/AmbientLayer.tsx:175`, `web/src/desk/intelligenceAttention.ts:95-96`; `docs/internal/UX-CANON.md:43`. | A zero count adds a false signal during meeting completion. Tenets 3/4 and UX-CANON A.8. **Product follow-up owed**: omit zero tokens and prove the rendered transition. The inherited toast remains visible if the rehearsal catches it. |
| Conflicting brief counts and time formats on arrival | **b**, exposed on every fresh read by the checked receipt seam. `web/src/desk/chair/briefEgress.tsx:43-52` counts all raw sections and formats local time; `web/src/desk/chair/ChairHome.tsx:875-886` filters raw IDs for the human count; `holdspeak/web/routes/monday_brief.py:47-58` supplies a 24-hour label. [1440 shot](assets/story-04-shots/final/20260925T001407Z-his-words-real/shots/brief/1440.png). | Five things waiting versus six items, and 18:19 versus 6:19 PM, undermine the saved-result receipt. Tenets 3/4, Article III. **Product follow-up owed**: settle one understandable count and time presentation, then real-producer rendered red/green proof. No repair is claimed here. |
| Raw pipeline service name retained and counted | **b**. `holdspeak/services/monday_brief_service.py:500` stores `MeetingIntelService.run_intelligence`; `web/src/desk/chair/briefEgress.tsx:43-46` counts it; `web/src/desk/chair/ChairHome.tsx:884-886` filters it from Arrival. [Readback](assets/story-04-shots/final/20260925T001407Z-his-words-real/observations/brief.json). | An internal method becomes a durable brief item and inflates the receipt. Tenets 3/4 and product-language canon. **Product follow-up owed**: human-readable producer wording and a consistent count/rendering fence. The raw name is not proven visible by expanding “2 more”; that interaction was not walked. |

BACKLOG rows for all six to be filed by **Muad'Dib at counsel-on-built,
before merge**. This is an owed transfer to the product's parking lot, not
an assertion that the rows are already there.

The inherited decision.create/update kernel-admission question remains
unruled and separately assigned by story 02. No admission is added or
silently certified by this rehearsal.

The initial Homebrew Node could not start (`libllhttp.9.3.dylib` missing).
The lane uses the already installed Node 22.21.0 for its local build; no
machine installation or shared runtime was changed. The worktree venv and
production web bundle built successfully with that runtime.

## AMENDMENTS

The owner's direct brief orders technical done, gated commit and PR before
Muad'Dib publishes the shots for owner review. The story's owner-review
line and phase exit 5 stay unchecked. Pending-review labels remain in the
story row, evidence, phase status, README and PR.
[Scope check](checks/story-04-scope-muaddib.md).

The unit plan's “none new” was amended for recorder, transcript and prompt
fences. Complete client/server records must reconcile; deliberate mutations
must reject changed prompts, results and write paths.

The phase's no-face-change scope has one checked exception: the existing
Article III receipt now also identifies the latest durable brief on a
fresh Desk read. A later Generate must replace its count and time. The
real missing-receipt shots and rendered pre-fix failures precede the fix.
[Receipt design and check](../../../../docs/internal/philo/phase-5/his-words/receipt-seam.md).
No new layout, wording or already-open brief refresh was introduced.

The final decision prompt specifies the review list after a stopped run
chose an accepted decision and a separate decision record. The existing
collector includes proposed decisions. The prior prompt is retained;
no collector change or hidden status instruction was made.

The former 202 test “empty brief's own words and keeps Generate after a
reload” was replaced during the receipt-fence rewrite. Its empty-headline
assertions remain in `briefLoadAndDate.philo303.test.tsx:135` and
`triagedHeadline.philo404.test.tsx:225`; quiet-branch Generate remains in
`generateAlwaysReachable.philo401.test.tsx:315`. The latter two suites were
run for this closing check: **18 passed**, two files. Together with the
20 receipt/load/date tests, **38 web tests** passed across six files; the
scopes are distinct. Exact collection/run output is retained.

## UNKNOWN

The phase is **technically done and open — OWNER REVIEW PENDING**.
`dw check` reports one expected phase-close receipt lint:
`ERROR pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer: all stories are done but final-summary.md is missing`.
`dw_pmo/validate.py:189-194` emits it. A summary file would mark this phase
CLOSED by existence alone (`statefeed.py:111-118`; `api.py:30-34`), so it
must not be created now. The stamped commit gate does not consume this
phase lint and remains unchanged. `.githooks/dw phase close`
(`mutations.py:400-415`) is deferred until the owner's review closes exit 5
and the phase close is verified. [Both brains' receipt disposition](checks/story-04-phase-receipt-muaddib.md).

Owner review, a live sitting, already-open brief refresh and usefulness
are not proven. Usefulness retains Phase 3's measurement. Discovery without
repository access is not claimed: Codex read source while finding review
fields. A scheduled reminder is not claimed; the review date is context
text. The six product repairs and decision kernel admission remain owed.
The failed missing-decision parity is not counted as equal by normalization.
No final-run restart or full-suite claim is made. Muad'Dib's counsel on
built and publication remain downstream; the branch must stay unmerged.
