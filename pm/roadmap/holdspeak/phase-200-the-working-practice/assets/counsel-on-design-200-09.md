# Counsel on the design — 200-09 The daily Project workflow

Counsel read `assets/settled-design-daily-workflow.md` (SETTLED against
`feat/phase-200-g0`, baseline `bea4176c`) in full; all twenty-one
artboards under `assets/mockups/` (rendered headless at their
`canvas.json` sizes, at DPR 2, and read one by one); `README.md`,
`CONTRACTS.md` (C1–C12), `ACCEPTANCE.md`, `BASELINE.md`, and stories
09–15; `docs/internal/CONSTITUTION.md` and `docs/internal/UX-CANON.md`;
the 176 precedent; and the code every D3 and D2.0 claim points at.
Read-only throughout: no git verb touched the tree or the index, no
file outside this one was written, `~/.local/share/holdspeak` was never
opened, and no test was run.

Canon measured against: Constitution III (local first, honest egress),
IV (voice first-class), V (consent, refusal by name), VI (honest by
construction; copy never promises what the code does not do), VII (no
prose, no modals), IX (proof over claim), XI (receipts); UX-CANON A.1,
A.2, A.3, A.7, A.8, A.9, A.10, A.11, B, C, D, E; Phase 200 C2, C3, C4,
C5, C6, C11; `README.md` §"Returning priorities"; the 175 law "a
replacing face keeps its verbs".

**What stands.** The six postures are the right decomposition of his
Tuesday. D1's law table is the best piece of design writing in this
phase — nineteen laws, each with a source and a binding, and most of
them are obeyed by most of the boards. D3's wire map is largely
accurate and is the reason this read could be specific. D4's twelve
hunts anticipate seven of the defects below before counsel found them.
The bounce is not about the design's spine; it is about four things the
boards say that the canon, the contracts and the wire contradict.

---

## VERDICT: BOUNCE — four reasons (P0-1 … P0-4). Conditions C5–C21 hold either way.

**P0-1 — the six 393 boards are not the same faces.** C11 makes both
widths acceptance ("Desktop and compact layouts are verified at 1440
and 393 pixels"); D5 beat 8 says "every verb reachable"; canon D says
one row grammar per species *at both widths*. Nine measured breaks:

| Board | What 1440 has that 393 does not |
|---|---|
| `P3BriefPhone` | The `NO SOURCE` claim's verb becomes `Open source` (`aria-label="Open source &mdash; NO SOURCE"`). At 1440 it is correctly `Find support`. This inverts the design's **own** D1 law (line 105: "It never shows an empty chip and never an `Open source` that opens nothing") and A.11 |
| `P3BriefPhone` | The `EgressChip` and the model receipt are gone (`grep -c 192.168.1.43`: `P3Brief` 1, `P3BriefPhone` 0) on a face a model produced. Article III.2, A.9 |
| `P3BriefPhone` | `CLAIMS 4` over three drawn claims (`KAN-7 slipped past the freeze window` dropped); the `NUMBER · 95%` unknown dropped (C2) |
| `P5RecallPhone` | `3 remembered` over two drawn results — the whole `OWED 1` section is gone; `SEARCHED 09:20 · 2 PROJECTS` gone; the `Meetings` filter gone; `SUPERSEDED BY DEC 09-07` and its `Open` gone; no footer, so no `THIS DEVICE` |
| `P1Phone` | Every `SOURCES` row loses its emblem, its facts line and its **verb** — including `Connect calendar`, the only repair path for the one gap on that face |
| `P2ArrivalPhone` | `COVERAGE 6 OF 8` over one gap row; the `confluence PLATFORM · CHECKING` row is gone |
| `P4ReviewPhone` | `Open transcript` gone; `31 TURNS READ` gone |
| `P6Phone` | `Open` gone from both `STILL TRUE` rows |

These are the boards his walk beat 8 uses. Redraw the six.

**P0-2 — `5 need you across 3 projects` is the cap, not the total.**
`README.md:60-62` is explicit: "The existing arrival presents up to five
initial priorities. The rest remain accessible, **with an honest
total**." `P2Arrival` puts the capped number in the one display element
— which D1 line 113 itself calls "the one big honest fact" — and states
the true 17 only as `12 MORE`, two sections below, at caption step.
`NEEDS YOU 5` repeats the cap as a section count. On a desk with 17
items the biggest word on his screen is wrong. Also: the head says
"across 3 projects" while the five drawn rows span two
(`Q4 PLATFORM`, `GOVERNANCE`) — the third project's only evidence is
inside the hidden twelve. Fix: the display line carries the true total
(`17 need you across 3 projects`), the section caption carries the cap
(`NEEDS YOU 5 OF 17`), and the remainder row keeps `12 MORE · Show all`.

**P0-3 — posture 4 draws a claim vocabulary the meeting store does not
have, and D3 does not say so.** The design's banner (line 32) promises
"Where something is NOT built, this document says MISSING rather than
describing it as though it exists." D3's meeting seam lists two MISSING
items; neither is this. `follow_through_proposals`
(`holdspeak/db/schema.py:4061-4089`) stores `kind ∈ {decision, action}`
and `state ∈ {proposed, confirmed, dismissed}` — **no support, no
acceptance, no unknowns, no `refs[]`** — and `segment_timestamp`
(`:4071`) is a single REAL, a point, so "the `EVIDENCE` disclosure
holding the transcript span" has no end to draw.
`proposal_bridge_service.py` records no `job_id` and no `attempt`, so
`JOB K-8C21`, `RESUMED · SAME JOB`, `ATTEMPT 2` and
`ALREADY KEPT 2 · FROM ATTEMPT 1` have nothing to read; nothing anywhere
counts turns read, so `31 OF 47 TURNS READ` has no numerator
(`segments`, `schema.py:76-86`, gives only the 47). Three boards
(`P4Processing`, `P4Review`, `P4ReviewPhone`) and D2(d)'s five-state
table rest on this. Posture 4, not the manifest, is the biggest unknown
in the phase.

**P0-4 — the coverage law is not universal on the boards, and `N` in
`N OF M` is undefined.** D1's first law: coverage "sits between the head
and the first result on every posture that reads sources." Four boards
break it, and one board's arithmetic breaks the law itself:

- `P1RouteUnset`: no coverage token; `SOURCES 4` drawn over **two**
  rows; head reads `4 SOURCES READABLE` while the same Project's
  calendar is `UNAVAILABLE` on `P1Ask` and its coverage is `3 OF 4` on
  `P1Running`. Three boards, one Project, three different source truths.
- `P3PrepareNoModel`: no coverage token, and the `FORBIDDEN` confluence
  source that `P3Prepare` names simply disappears — the failed face
  clears a known gap by omission, which is the exact thing D1 line 100
  forbids.
- `P4Review` / `P4Processing`: no coverage anywhere; `31 TURNS READ`
  carries no denominator (D2(d)'s Partial state says `31 OF 47`).
- **The definition.** `P3Prepare` counts a `STALE` source inside
  `SOURCES 3 OF 4 READ`, while `P2Arrival` counts a `CHECKING` source
  outside `6 OF 8`. D3 line 660 says `complete` is
  `all(state == "available")`. With `N` = "sources we have data for",
  four stale sources render `COVERAGE · 4 OF 4` on a read that is not
  complete — and the fraction is only shown *because* it is incomplete.
  Define `N` as the count in state `available` (making `N == M`
  unreachable while incomplete), or rename the token.

---

## The conditions

| # | Condition | Sev |
|---|---|---|
| C1 | Redraw the six 393 boards: no verb, egress chip, coverage row, unknown token, filter or section may exist at 1440 and vanish at 393; `Find support` stays `Find support`; every section count equals its drawn rows. | **P0** |
| C2 | The display line carries the true total, the section caption carries the cap (`NEEDS YOU 5 OF 17`). `README.md:60-62`. | **P0** |
| C3 | D3's meeting seam gains four MISSING rows (claim axes on proposals; the transcript **span**; proposal→job/attempt provenance; the turns-read numerator), and story 12's size is re-judged against them. | **P0** |
| C4 | Coverage rides above the answer on `P1RouteUnset`, `P3PrepareNoModel`, `P4Review`, `P4Processing`; `P1RouteUnset`'s `SOURCES 4` draws four rows; `N` is defined as the `available` count. | **P0** |
| C5 | `Keep` has **no route and no service write.** `monday_brief.py:100-140` exposes latest/generate/shelf only; `monday_briefs.disposition` (`schema.py:2281`) is never written by `monday_brief_service.py`; `monday_briefs` has no `project_id`, so 11 AC4's "the kept brief remains attached to the originating Project" has nothing to attach to. D3's preparation seam must mark it MISSING. | P1 |
| C6 | **"C3's versioned manifest has no record" (D3 line 695) is too absolute.** Two frozen source manifests exist: `project_updates.source_manifest_json` (`schema.py:3941`, built `project_update_service.py:565-580`) and `project_reviews.source_manifest_json` (`schema.py:3916`, built `project_delta_service.py:1454-1475`, whose docstring reads "Build the frozen source manifest from coverage results"). The true statement is "no manifest is bound to a brief". This shrinks story 11's stated biggest unknown; say so. | P1 |
| C7 | **"MISSING: accept / reject" (D3 line 707) is false.** `POST /api/decisions/{id}/accept` and `/reject` exist at `holdspeak/web/routes/decisions.py:57,61`, mounted `web_server.py:1064`, backed by `decision_lifecycle_service.py:40-41`. The design cites `primitives/decisions.py`, a different router. `BASELINE.md:69` carries the same error and should be corrected with it. | P1 |
| C8 | **Continuity back to the originating Project is drawn on 6 of 21 boards.** `Q4 PLATFORM` appears on `P2Arrival`, `P2ArrivalPhone`, `P4Processing`, `P5Recall`, `P6Repair`, `P6Resume` — and on none of the posture-1 or posture-3 boards, none of `P4Review`/`P4ReviewPhone`, and not on `P5RecallPhone`. Story 09 AC2 requires it per posture. Worse, D2(g)'s "way back" column names `Confirm` (a write) for posture 4 and `Carry into brief` (a write) for posture 5 — neither returns him anywhere. Make the Project token a library `Button` with a region (canon D) on every posture, and correct D2(g). | P1 |
| C9 | `P1RouteUnset`'s `Prepare` is drawn **byte-identical** to the enabled primary (`background:#a86e4a; border:1px solid #a86e4a; cursor:pointer`) while its accessible name reads "unavailable until a route is ready". No board in the set uses `disabled` or `aria-disabled` (0/21). Either withhold the verb (A.11) or draw and mark the unavailable state; and reconcile with `P3PrepareNoModel`, which withholds it — one refusal, two grammars. | P1 |
| C10 | `OWNER · PRIYA?` (`P4Review`, `P4ReviewPhone`) asserts a name it cannot support and hedges with punctuation. C2: "Missing values remain typed unknowns." The design's own text (line 72) says `OWNER · UNKNOWN`. Same class: `DEADLINE · 2026-12-31` and `NUMBER · 95%` on `P3Brief` print the values as facts in a warning chip; per C2 they are unsupported values and must say so (`DEADLINE 2026-12-31 · NO SOURCE`). | P1 |
| C11 | **The stated ranking cannot produce the drawn order.** `RANKED BY DUE THEN AGE` on `P2Arrival` orders: `3 DAYS` · `OVERDUE · 2 DAYS` · `40 MIN AGO` · `DUE TODAY` · `1 DAY`. Overdue and due-today sit below a three-day item; `CI failing on main` has no due date and the rule does not say where such items sort. D2(b).2 also drops severity, which C4 keeps as a concept ("cannot lower a known unresolved item's severity"). State the full key including the no-due case, and draw a board whose order obeys it. Note for story 15: the dedup key is not a blank sheet — `needs_you_aggregate.py:135-143 _item_id` exists with the docstring "A stable id for one attention row, for dedup and reconciliation" and **zero callers**. | P1 |
| C12 | **Eleven of sixteen named gaps have no acceptance criterion.** Covered by an AC: the five-cap (15 AC1), the changed-set edge (15 AC4), dedup (15 AC3), ranking (15 AC2), and the manifest in weakened wording (11 AC2 names decisions and omissions, not observed revisions, observation times, coverage or the data boundary that `CONTRACTS.md:53` requires). **No AC covers:** `ClaimAxes` promotion, `CoverageLedger` promotion, `RepairRow` promotion, `TaskResume`, the ThreadComposer raw buttons, draft custody, search-side coverage, the recipe `CycleGadget`, the job identity on the face, focus return, and accept/reject over the acceptance axis. **Posture 6 has no story at all** — the Sizes table lists 09/10/11/12/13/15, and `P6Repair`, `P6Resume`, `P6Phone`, the six work states and `THE RUNTIME` are in none of them. Story 14 is absent from the Sizes table entirely. Either the ACs gain the text or the Sizes table stops claiming the coverage. | P1 |
| C13 | Verbs that lead where the face already is: `P5Recall`/`P5RecallQuiet` show the `SEARCH` wing active **and** a footer `Search`; `P6Resume` shows `UNFINISHED` active **and** a footer `Unfinished`. A.11. Also on `P5Recall`, `Open` is a verb on two rows and `OPEN` is a state chip on the third — one word, two meanings, one face (canon D). | P1 |
| C14 | The name is said twice on three faces. `P4Review`: title bar `Architecture review — Sep 7`, head token line `ARCHITECTURE REVIEW · SEP 07`. `P4Processing`: same, plus the `MEETING` row repeating it a third time. `P5RecallQuiet`: head `Nothing matches` over a `NOTHING MATCHES` empty token. A.7, and D1 line 112 forbids it — but D2(d) line 442 **asks** for it ("Head `5 to review` + the meeting + date"). The text contradicts the law; fix the text, then the boards. | P1 |
| C15 | Row-verb grammar is not one grammar. `P2Arrival`/`P6Repair`/`P5Recall` draw row verbs ghost or outlined; `P4Review` draws `Confirm` as a filled primary on all five rows **plus** a sixth primary `Accept reviewed` in the footer; `P6Resume` draws two primaries (`Resume`, `Answer`). Story 09 AC2 asks for "a clear primary action" per posture. Pick one grammar: row verbs dense/ghost, one primary per face. | P1 |
| C16 | Accessible names are specified in D2 but delivered on 144 of 211 board buttons. Concretely: every `SOURCES` row verb on `P1Ask` and `P3Prepare` is unlabelled, and the `MicButton` is labelled `aria-label="Purpose"` on five boards — the same name as the field it sits in, so a reader hears two controls called "Purpose". D2(a) line 250 specifies `Dictate purpose`; `Library.dc.html` uses a third spelling, `Dictate`. C11 makes accessible names acceptance. | P1 |
| C17 | Two facts on the boards are wrong at the source. `P3Prepare` gives the **confluence** PLATFORM row the reason `JIRA CREDENTIAL EXPIRED` (only board with that string; `P3Brief` and `P6Repair` correctly say `CREDENTIAL EXPIRED`). And an expired credential draws `Open source` as its owning verb on `P3Prepare`, `P3Brief` and `P6Repair`, while an expired jira query draws `Reconnect` — one failure class, two owning verbs (A.10, canon D). | P1 |
| C18 | `P2ArrivalQuiet`'s one prose exception is `Next — Architecture review at 11:00`. He has **zero calendar sources** (`BASELINE.md:32`), so the only line on the only all-clear face cannot render on his desk. State the no-calendar all-clear line. Related: `P3Prepare`'s head reads `Prepare the 11:00 review` beside its own `NO CALENDAR` token, with no 11:00 in the typed purpose — the head invents the fact the token denies. | P1 |
| C19 | Two library species the boards use are declared nowhere: `Material` (D2(c) names `Material.tsx:82`) and `SurfaceIdentity` (D2(a) element 2) are in neither the D2.0 reuse table nor the `Library` board. Four that **are** in the table are not specimened on the board (`PadGadget`, `CheckGadget` token, `count.ts`, `CitationChips`) — the design's parenthetical at line 159 admits the count but not which four. Separately, `ConfirmVerb` and `EditInPlace` are in the library but **absent from `contract.md`**; canon B's documentation is owed for two of the twenty-two "reused exactly as they are". | P1 |
| C20 | The two ThreadComposer residues are miscounted as one and mislocated. `:970` is `className="thread-composer-input"`; the self-flagging comment is `:966` and it flags the **raw `<textarea>` at `:968`**, not the buttons. So there are two residues — raw Stop/Send (A.1) and a raw textarea, which is a mic-law site the scanner cannot see (`ux_canon_scan.py` does not match `<textarea>`, the 176 C9 finding). The ceiling carries them under `B: 2` for that face, not `A1`. | P2 |
| C21 | Twelve `file:line` citations are off by 2–13 lines and one is materially wrong: D3's "Face" row cites `ChairHome.tsx:616-796` for `Arrival`, which is declared at `:345` (`:616` is its `return`, and the range overruns into `NeedsYouSection`). Also `UpdatePosture`'s `hasAxes` gate is `:141`, not `:136`. Everything points at the right file and the right symbol; the design's line-31 claim "Every `file:line` below was read on this branch" should be softened or the numbers corrected. Non-blocking, but the 175 law on line-anchored fences is why it is here. | P2 |

---

## Per hunt

### H1 — one primary verb; the name once; no prose; no zero; the emblem; egress where it happens

**Read:** all 21 boards rendered and read; `aria-label` and `<button>`
censuses over the raw HTML; type-step census (26/15/13/12/11 px);
UX-CANON A.1, A.3, A.7, A.8, A.9, A.11, C, D; C11.

**Passes.** Every board carries exactly **one** 26px display element
(21/21) and at least three type steps — the geometry probe is clean.
Every verb is drawn as a Button-shaped control; no modal appears
anywhere; `SurfaceLedger` rows use the 52px lead slot at 1440
consistently. `THIS DEVICE` is drawn on the five faces where nothing
left (`P1RouteUnset`, `P3PrepareNoModel`, `P5Recall`, `P5RecallQuiet`,
`P6Resume`) and the host chip sits beside the sending verb on
`P1Ask`/`P1Running`/`P3Prepare`. Zero counters are avoided honestly
(`NO DECISIONS`, `NOTHING KEPT YET`, `NOTHING ACCEPTED YET`).

**Fails.** The primary-verb grammar is not one grammar (C15). The name
is said twice on three faces, and D2(d)'s text asks for it (C14). The
refusal board's `Prepare` looks enabled (C9). One egress chip is
decorative and one is missing: `P1Ask` and `P3Prepare` carry
`192.168.1.43 · LAN` in the footer beside `NOTHING KEPT YET` — a host
chip on a face where nothing has left — while `P3BriefPhone` drops the
chip from a face a model produced (C1). `P6Repair` carries no egress
disclosure at all while its sibling `P6Resume` carries `THIS DEVICE`.

**Sev: C9, C14, C15 (P1); the `P1Ask`/`P3Prepare` footer chip is folded
into C1's rule.** **Change:** the footer egress slot renders only after
a send, and `P6Repair` gains `THIS DEVICE`.

---

### H2 — the five-item cap, the honest remainder, the ranking, the dedup

**Read:** `README.md:56-62`; C4 (`CONTRACTS.md:68-84`); story 15's five
ACs; `P2Arrival`, `P2ArrivalPhone`, `P2ArrivalQuiet`;
`ChairHome.tsx:436-447` and `:812`; `needs_you_aggregate.py:135-143`.

**Found.**

1. **The cap is drawn; the honest total is not** (P0-2). The wire
   confirms the gap is real: `merged.sort((a,b) => (SEV[a.severity] ??
   2) - (SEV[b.severity] ?? 2))` (`ChairHome.tsx:439`) is a single key
   with no tie-break, and `NeedsYouSection` renders `{items.map(...)}`
   at `:812` with no `.slice` — uncapped, unranked, exactly as D3 says.
2. **The ranking rule as stated cannot produce the drawn order**, and
   it does not say where an item with no due date sorts (C11).
3. **Is `12 MORE` reachable by a verb?** Yes — `Show all` is a real
   ghost Button with `aria-label="Show all -- the remaining 12"` at
   1440. At 393 the label degrades to `Show all` (minor; folded into
   C16).
4. **Can the same item appear twice across the projections?** Not on
   the boards — the five drawn rows are five distinct objects. But
   story 15 AC3 requires "traceable sources" on a deduplicated row and
   **no board draws that disclosure**, so the promise is textual only.
   The design also treats the dedup key as unwritten; a helper computing
   exactly it already exists and is dead code (C11).

**Sev: P0-2 and C11.** **Change:** as stated in the verdict, plus one
board (or one row on `P2Arrival`) showing a deduplicated item with its
sources traceable.

---

### H3 — the evidence manifest, and what posture 3/4/5 draw that the wire cannot produce

**Read:** C3 (`CONTRACTS.md:50-61`); `holdspeak/db/schema.py`
(`monday_briefs` `:2274-2304`, `refinement_attachment_*` `:959-999`,
`project_sources`/`project_observations` `:3829-3866`,
`project_reviews` `:3910-3923`, `project_updates` `:3932-3949`,
`follow_through_proposals` `:4061-4089`, `intel_jobs` `:137-176`);
`monday_brief_service.py:296-306,451,499,539,569`;
`project_update_service.py:89-240,565-580`;
`project_delta_service.py:1454-1475`;
`refinement_context_service.py:18-43,1105-1138`;
`needs_you_aggregate.py:65-113`; `holdspeak/db/memory.py:67-97`.

**Found — the design's claim is directionally right and factually too
strong.** No manifest is bound to a kept brief. But two frozen source
manifests already exist on the update/review path (C6), and the
`refinement_attachment_*` triple is a better pattern than BASELINE
credits: integer revision, `attachment_sha256` recomputed and compared
on every read (`refinement_context_service.py:1105-1111`), a
`frozen=True` self-validating snapshot the browser cannot substitute
(`:25-43`), per-row `source_last_modified`, declared byte bounds, and a
**named** stale repair (`{"repair": "update_context"}`, `:1113-1119`)
rather than silence.

**What a kept brief stores today**, against C3's seven elements:
`monday_briefs(id, period_start, period_end, headline, generated_at,
spoken, disposition)` and `monday_brief_items(id, brief_id, section,
text, detail, source_ref, priority)`. Project — **absent** (the brief is
window-keyed). Observed revisions, observation times, claims, coverage,
resolved data boundary — **all absent**. Qualified refs — one free-text
`source_ref` per item, never run through `qualified_ref()`. And there is
no keep route at all (C5).

**The minimal honest manifest** — the fields the boards actually need:

*Header (for `MANIFEST M-118 · REV 1`, `COVERAGE · 3 OF 4`,
`PREPARED 09:12`, `KEPT`, and `P6Resume`'s `INCOMPLETE · 3 OF 4
SOURCES`):* `manifest_id`, `revision` (int, monotonic, one row per bind
— copy `refinement_attachment_revisions.attachment_revision`),
`manifest_sha256` (copy `attachment_sha256`), `project_id`,
`target_ref` (the brief id, exists), `prepared_at` (exists as
`generated_at`), a written lifecycle (the `disposition` column exists
but is dead; `project_updates.lifecycle` is the working pattern), and
the resolved data boundary (copy `project_updates.generator,
generator_host, generator_model`, `schema.py:3945-3947`).

*Per-source coverage row (for `COVERAGE`, `NOT READ 1`, `CREDENTIAL
EXPIRED · OMITTED FROM THIS BRIEF`):* the eight fields
`_coverage_row` already returns at runtime
(`needs_you_aggregate.py:91-113`) — `source_id · kind · state ·
observed_at · label · project_id · reason · repair` — **persisted**.
Six of the eight already have durable homes
(`project_sources.freshness_state/.last_observed_at/.revision`,
`project_observations.coverage_state/.source_version/.content_hash`);
only `reason` + `repair` are new to persist.

*Per-claim row (for `CLAIMS 4` with its refs and `Open source`):* reuse
`Claim` and `SupportRecord` unchanged
(`project_update_service.py:144-240`). Nothing new but the binding — a
brief has no claims today.

*Continuity (for `Carry into brief`, `CARRIED FORWARD 2`):*
`decisions.lifecycle` and `decisions.superseded_by`
(`holdspeak/db/decisions.py:19,62,112`) exist; `carried_refs[]` on the
manifest, by reference, is new.

**Genuinely new and minimal: seven fields/bindings.** Brief↔Project;
revision + freeze hash; persisted coverage rows; claims bound to a
brief; the data boundary; carried refs; a written lifecycle. Everything
else is reuse. **Story 11's "biggest unknown" is smaller than the
design says** — and posture 4's is bigger (P0-3).

**Five board elements no manifest can rescue**, because they are
meeting-side and search-side records that no service writes:
`31 OF 47 TURNS READ`; `ALREADY KEPT 2 · FROM ATTEMPT 1`;
`SEARCHED 2 OF 4 PROJECTS` (`MemorySearchResult.to_dict()`,
`db/memory.py:67-97`, returns hits + page + ranking and no per-Project
readability); `PROPOSAL · support · UNREVIEWED` with its unknowns and
its `EVIDENCE` **span**; and the brief footer's model + elapsed receipt.

**Sev: P0-3, C5, C6.**

---

### H4 — continuity back to the originating Project

**Read:** D2(g) (lines 632-645); story 09 AC2; the Project-token census
across all 21 boards.

**Found.** `Q4 PLATFORM` is drawn on six boards and absent from
fifteen. The Room's title bar (posture 1) carries the Project's outcome,
which counsel accepts as the name. But **the kept brief names no
Project on its face** — the title bar reads `Architecture review —
brief`, the manifest token is `MANIFEST M-118 · REV 1` with no Project
in it, and `Open sources` opens sources. **The meeting review names no
Project** (`P4Processing` does; `P4Review` drops it when the wing
flips). **Recall at 393 drops it.** And D2(g)'s "way back" column names
two writes as ways back: `Confirm` writes into the Project's decisions,
`Carry into brief` returns a record to a preparation — neither
navigates. Only posture 6's `Resume` is a genuine return, and it is the
one the design models everything else on.

**Sev: C8 (P1).** **Change:** the Project token becomes a library
`Button` with a region on every posture; D2(g)'s column names a verb
that navigates, or says "none" honestly.

---

### H5 — voice, keyboard, accessible names, focus return, disclosure

**Read:** D2(a)–(f)'s per-posture Voice / Keyboard / Accessible names /
Focus return / Disclosure blocks; C11 (`CONTRACTS.md:225-241`); the
`aria-label`, `aria-pressed`, `disabled` censuses; `MicButton.tsx:42,
135-147, 159-177, 362-370, 399, 419-428`; `Disclosure.tsx:13, 66-79,
93, 105`; `roving.ts:34`.

**The text passes, and passes well.** D2 specifies per control: mic on
every text input with click-to-toggle and append-never-submit
(Article IV.2), one mic authority (`Talk` owns the floor, field mics own
fields), tab order, Enter/Escape semantics, the explicit "no hidden
keys" ruling, accessible names verb-by-verb, focus return on eleven
named verbs, and Escape-closes-and-returns for `Disclosure`. Counsel
verified every library line it rests on: `MicButton`'s toggle at
`:362-370`, `aria-pressed` at `:399`, the NAMED unavailable state at
`:159-177`; `Disclosure`'s `aria-expanded` `:93`, `role="region"`
`:105`, Escape `:74-79`, focus-to-trigger `:66-72`; `useRovingRows` at
`roving.ts:34`. The canon ceiling confirms `"mic": 0`.

**The boards under-deliver it.** Mic present on every drawn text input
(6/6) ✓. But 67 of 211 buttons carry no accessible name, the mic is
labelled with its field's name on five boards, and no board draws a
disabled or `aria-disabled` state (C9, C16). The `ACTIONS` disclosure is
correctly closed by default on `P1Running` and `P4Processing` and holds
only latency/per-source reads/the model call — **no failure is reachable
only inside it** on any board (D4 hunt 11 passes). It does, however, sit
on the same row as the primary `Stop`; if "never on the primary line" is
meant literally, move it.

**Sev: C16 (P1).**

---

### H6 — his desk on day one

**Read:** `BASELINE.md:28,32,33,148-155`; D4 hunts 1-5; every board.

**Found.** The design's D4 is honest about all five facts and its
structural answers are right — the purpose is typed, so posture 1 and 3
work with no calendar; `P1RouteUnset` is correctly called the first face
he will meet. Two things it does not carry through:

1. **The one-Project rule is stated and drawn nowhere.** D4 hunt 2 rules
   that the Project token is withheld when there is one Project, and
   unresolved concern 8 admits no board shows it. Every arrival board
   therefore draws a face he cannot see, and the face he *will* see is
   undrawn. This is one board, and it is beat 1 of his own walk.
2. **The all-clear cannot render on his desk** (C18): its one prose line
   is a calendar fact he has none of.

Also false on his desk on day one: `5 need you across 3 projects`
(one active Project); posture 5 entirely (zero decisions, zero
commitments — the design's hunt 4 says so and orders the walk
accordingly, which is the right answer); `THE RUNTIME` until HS-200-02
lands (the design says so).

**Sev: C18 (P1); the one-Project board is folded into C8's redraw and
into H8's ruling on concern 8.**

---

### H7 — are the gaps sized honestly?

**Read:** stories 10-15 in full; `EXECUTION.md`, `DELIVERY.md`,
`ACCEPTANCE.md`; the Sizes table (lines 912-937).

**Found — eleven of sixteen gaps have no acceptance criterion, and one
posture has no story** (C12). The pattern is asymmetric: story **15** is
sized M and four of its five ACs map one-to-one onto D3's MISSING list —
that row is honest. Story **11** is sized L and must absorb the recipe
picker, the manifest record, `ClaimAxes` promotion, `CoverageLedger`
consumption, `NOT READ`, `Write it myself`, `Keep`, and
reopen-after-restart — of which **six of eight have no acceptance text**
to gate them, and one (`Keep`) has no route to build on. L is not
obviously wrong; ungated is.

Specifically unowned: `ClaimAxes` (S2), `CoverageLedger` (S1),
`RepairRow` (S3), `TaskResume` (S5), the ThreadComposer raw buttons,
draft custody (the design assigns it to 10; story 10's five ACs are
promotion, reference, correction, revocation and People — no draft),
search-side coverage, the recipe `CycleGadget`, the job identity on the
face, focus return, accept/reject over the acceptance axis,
`Carry into brief`, `Keep`, `ALREADY KEPT`, `31 OF 47 TURNS READ`, and
all of posture 6.

**Sev: C12 (P1).**

---

### H8 — the nine unresolved concerns: his, or the orchestrator's

| # | Concern | Whose | Counsel's proposed ruling |
|---|---|---|---|
| 1 | The pilot stream is not chosen | **OWNER** | `BASELINE.md:166` writes it as his blocking question. Beats 3-6 cannot run until he answers. Nothing to rule. |
| 2 | The model route | **OWNER** | Article III.2: it decides whether his transcripts leave the machine, and `BASELINE.md:150` calls it his call. The design correctly puts the choice beside the verb without making it. |
| 3 | Five is asserted, not measured | **OWNER** (the cap) / **orchestrator** (the total) | C4 fixes five; changing it is his. But P0-2 is not about the number — the honest total is a `README` requirement and can be fixed now, before he sees it. Rule the total; carry the cap to him. |
| 4 | `Coverage incomplete` may read as an error | **OWNER's ear** | Already shipped by HS-200-07; his walk decides. Do not spread it to three more faces before he has read it once. |
| 5 | Two shipped faces edited to promote S3 | **ORCHESTRATOR** | Rule: promote the species, leave both call sites behaviourally identical (175: a replacing face keeps its verbs), retire the duplicate in a later story — the design's own fallback. One thing rides free: `ChairHome.tsx:923-929` draws the coverage token as a raw `<span className="arrival-why-token">` while `ConciergeCore.tsx:275-278` uses `StateChip` for the same fact. Converging on `StateChip` is species canon, not a behaviour change; do it inside the promotion. |
| 6 | Thread draft custody is in-memory | **ORCHESTRATOR** | Rule: state the limitation on the face (`DRAFT NOT SAVED`) rather than persist, unless persistence proves trivial — but note the ruling has nowhere to land: story 10 has no draft AC and the only draft AC in the phase is 28 AC1, at G3. The ruling must add the AC, not just choose. |
| 7 | The evidence manifest does not exist | **ORCHESTRATOR** | Rule: bind the manifest to the **kept** brief only (the design's own fallback), reuse `refinement_attachment_revisions`' revision + sha256 mechanics and `_coverage_row`'s eight fields, and correct the "no such record exists" claim (C6). The seven new bindings in H3 are the scope. |
| 8 | The one-Project face is not drawn | **ORCHESTRATOR** | Rule: draw it. It is the only arrival on his desk and it is beat 1 of his walk. One board is cheaper than discovering the withholding rule in front of him. |
| 9 | `Edit` has no route | **ORCHESTRATOR** | Rule: edit-then-confirm is lawful and the routes are verified (`proposals.py:66,86`; no PUT/PATCH exists). But C2 requires the edit to drop support to `LINKED · EDITED` — and the confirm route does no such thing today, so the ruling must name where the invalidation happens or the face lies about it. |

---

### H9 — what a board draws that the text does not say, and the reverse

**The 176 lesson, applied.** Fourteen divergences found; the load-bearing
ones are already conditions (C9 `Prepare`, C10 `PRIYA?` and the unknown
values, C14 the doubled name, C15 the primary grammar, C17 the wrong
reason and the wrong repair verb, C18 the invented 11:00). The rest:

- **Board says, text does not:** `NO DECISIONS` in `P1Ask`'s token line
  (D2(a) element 2 specifies source count, `CHECKED n MIN AGO`, and the
  coverage fraction — not this); `KEPT` on `P1Running`'s purpose row
  (the text puts `PURPOSE KEPT` only on the failed state);
  `NO DUPLICATE PROPOSALS` in `P4Processing`'s footer (an unverifiable
  negative, borderline against Article VII.1's "no reassurance");
  `3 TODAY` in `P5Recall`'s footer beside a head that says
  `3 remembered` — two counts, one referent, unexplained;
  `2 PROJECTS` in the same head, where D2(e) specifies coverage
  (`SEARCHED n OF m`) and the wire can produce neither (H3).
- **Text says, board does not:** the coverage fraction in posture 1's
  head "when it is not complete" — `P1Ask` has an `UNAVAILABLE` calendar
  and no fraction, while `P1Running` shows `3 OF 4` for the same
  Project; `31 OF 47 TURNS READ` (board: `31 TURNS READ`); `Dictate
  purpose` (board: `Purpose`); the `Q4 PLATFORM` withholding rule
  (drawn nowhere); the dedup disclosure (drawn nowhere); `BRIEF ·
  Generate` on the quiet arrival (`P2Arrival` has it, `P2ArrivalQuiet`
  drops it though nothing is prepared there either).
- **Composition unexplained:** `P6Repair` is described as living on the
  arrival but draws no `NEEDS YOU` and no `BRIEF` section. Say whether
  it is the arrival re-composed or a separate face.
- Narrative drift: D0 says "ninety seconds later the brief is a
  document"; `P3Brief`'s receipt says `11.4 S` and `P1Running` shows
  `00:38` at step 3 of 5.
- Vocabulary drift inside the phase: `ACCEPTANCE.md:209` lists coverage
  as "available, stale, failed, **excluded**, and **missing**"; C4 and
  the code say `forbidden` and `unavailable`. The design follows the
  code, correctly; `ACCEPTANCE.md` should follow it too.

**Sev: P2 for the residue above; the named conditions carry the rest.**

---

## Not paid, carried to the build lane

- Whether the Room ask well's free text is persisted anywhere durable —
  counsel did not trace `RoomAskWell` submission to a durable row, so
  `RESUMED AFTER RESTART · SAVED 09:04` and the whole `UNFINISHED`
  ledger rest on an **unknown**, not a verified seam.
- D3's "MISSING: the changed-set notification" and "Residue: MCP
  steering read-only" cite `BASELINE.md` only; counsel did not trace
  either in code. **Unknown**, not verified.
- No test was run and no live face was opened. Every board judgment
  above is against the rendered artboard, not against a built face.

---

## Counsel's re-read (2026-09-07)

Counsel re-read the rewritten `assets/settled-design-daily-workflow.md`
(1206 lines, with the addendum "counsel's read: BOUNCE, the rulings"
and R1–R5), re-rendered all **22** boards headless at their
`canvas.json` sizes and read every one, and re-ran the mechanical
censuses (buttons, accessible names, `aria-disabled`, egress chips,
display elements, every `N OF M` fraction, and a 1440↔393 accessible-name
diff per width pair). Read-only; no git verb touched the tree; only this
file was written.

### VERDICT: RATIFY-WITH-CONDITIONS — the bounce is lifted. All four P0s are paid; two new conditions (N1, N2), both P1, neither blocking the canvas.

### The bounce

| # | Verdict | Evidence |
|---|---|---|
| **P0-1** the 393 boards are not the same faces | **PAID-WITH-NOTE** | `P3BriefPhone` now draws four claims for `CLAIMS 4`, `NO SOURCE · UNSUPPORTED · UNREVIEWED` with **`Find support`**, both `· NO SOURCE` unknown tokens, the coverage row, the `Q4 PLATFORM` button, and the footer's `192.168.1.43 · LAN` + `QWEN3 35B · 11.4 S`. `P5RecallPhone` draws all three sections, all five filters, `SUPERSEDED BY DEC 09-07` with its `Open`, and `THIS DEVICE`. `P1Phone` draws all four source rows with their verbs; `P6Phone` both `STILL TRUE` rows with `Open`; `P4ReviewPhone` the receipt and `Open transcript`. An accessible-name diff per pair returns **empty for `P3Brief`↔`P3BriefPhone` and `P5Recall`↔`P5RecallPhone`**. Note: three verbs still drop at 393 — `Ask` (`P1Phone` footer), `Search` (`P6Phone` footer), and the coverage row's `Open transcript` (`P4ReviewPhone`, though the footer keeps a same-named verb). Secondary, not load-bearing |
| **P0-2** the display line is the cap, not the total | **PAID** | `P2Arrival`: display `17 need you across 3 projects`; caption `NEEDS YOU 5 OF 17`; remainder `12 MORE · Show all` (5 + 12 = 17). The five drawn rows now span three Projects (`Q4 PLATFORM`, `GOVERNANCE`, `PAYMENTS`), so "across 3 projects" is evidenced on the face. Same at 393. D1 carries it as a law |
| **P0-3** posture 4 draws a vocabulary the store lacks, unmarked | **PAID** | D3's meeting seam now carries five numbered MISSING rows — claim axes on a proposal, the transcript SPAN, the proposal→job/attempt link, the turns-read numerator, and R5's confirm-does-not-invalidate. Story 12 re-judged **M → L**. The boards keep drawing it, which is now lawful because the document says what is not built |
| **P0-4** coverage is not universal; `N` is undefined | **PAID-WITH-NOTE** | A `COVERAGE` section is present on all 15 posture-1/2/3/4 boards (0 on posture 5/6, which D1 now explicitly scopes out). D1 states `N` = the count in state `available`. **Verified arithmetically on all 17 fractions**: `P3Prepare` moved `3 OF 4` → **`2 OF 4`** because `KAN` is `STALE` — the rule bit, and bit correctly. `P1RouteUnset` draws `SOURCES 4` as four rows. `47 OF 47 TURNS` is complete and lawful. New defect at N1 below |

### The conditions

| # | Verdict | Board or line |
|---|---|---|
| C1 | **PAID-WITH-NOTE** | as P0-1. Two of six pairs are byte-identical in verb set; the three residues are named above |
| C2 | **PAID** | `P2Arrival`, `P2ArrivalPhone`; D1 law 3 |
| C3 | **PAID** | D3 meeting seam, five MISSING rows; Sizes story 12 = L |
| C4 | **PAID-WITH-NOTE** | as P0-4; see N1 |
| C5 | **PAID** | D3 preparation seam: `MISSING: `Keep` has no route and no service write` and `MISSING: monday_briefs has no project_id`, both owned by story 11 |
| C6 | **PAID** | D3 now names `schema.py:3941` and `:3916` and states the true claim ("no manifest is bound to a brief"); the unknown is restated as seven bindings over existing mechanics |
| C7 | **PAID** | D3 corrected; `BASELINE.md:69` flagged, not edited — the orchestrator holds it (confirmed in flight) |
| C8 | **PAID** | `ProjectButton` added as owed species **S6**; `Q4 PLATFORM` verified on `P1RouteUnset`, `P3Prepare`, `P3BriefPhone`, `P4Review`, `P5Recall`, `P5RecallPhone`, `P6Repair`, `P6Phone` — and correctly **withheld** on `P2ArrivalOne`. D2(g) rewritten so a write is never named a way back |
| C9 | **PAID** | `aria-disabled` present on `P1RouteUnset`, `P3PrepareNoModel` and the `Library` specimen (3 boards, 0 before). The refused `Prepare` renders flat, dashed, muted. Both refusal boards now share one grammar |
| C10 | **PAID** | `OWNER · UNKNOWN` on `P4Review`/`P4ReviewPhone`; `DEADLINE 2026-12-31 · NO SOURCE` and `NUMBER 95% · NO SOURCE` on `P3Brief`/`P3BriefPhone`. `PRIYA?` is gone |
| C11 | **PAID** | D2(b).2 states the four-class key with in-class ordering and the stable-id tie-break, and keeps severity as the reason token's ink. `P2Arrival`'s rows are drawn in exactly that order: `OVERDUE · 2 DAYS` → `DUE TODAY` → `NO DUE DATE · CHANGED 40 MIN AGO` → `WAITING · 3 DAYS` → `WAITING · 1 DAY`. `_item_id` (`:135-143`) named as the dedup key. (The new board disobeys — N1 below) |
| C12 | **PAID** | Sizes now carries 10–15 including **13** and **14**; posture 6 lands on story 15, re-judged **M → L**; each row names the ACs it owes |
| C13 | **PAID** | Wings are `SEARCH \| UNFINISHED \| REPAIRS`; each footer names only the inactive wings. The `OPEN` state chip is gone from `P5Recall`'s `OWED` row |
| C14 | **PAID** | D2(d) no longer asks for the meeting name in the head. `P4Review`'s head reads `Q4 PLATFORM · NOTHING ACCEPTED YET · EXTRACTED 12:04`; the name is in the title bar alone. `P5RecallQuiet` no longer repeats its display line as a token |
| C15 | **PAID** | Exactly one filled primary per board: `Open` (top-ranked row) on `P2Arrival`/`P2ArrivalOne`, `Accept reviewed` on `P4Review`, `Carry into brief` on `P5Recall`, `Resume` on `P6Repair`, `Keep` on `P3Brief`. Row secondaries moved into `▸ MORE` |
| C16 | **PAID** | Verified mechanically: **279 buttons, 322 accessible names, 0 unlabelled across all 22 boards**. The mic is `Dictate into <field>` everywhere including the `Library` specimen |
| C17 | **PAID-WITH-NOTE** | `CREDENTIAL EXPIRED · CONFLUENCE` replaces the jira-on-confluence error (0 hits for the old string); both credential failures take `Reconnect`, the engine takes `Check`. See N2 |
| C18 | **PAID** | `P2ArrivalQuiet` drops the prose line and carries `COVERAGE COMPLETE · 8 OF 8 AVAILABLE`, `NO CALENDAR · Connect calendar` and the `BRIEF · Generate` row. `P3Prepare`'s head reads `Prepare a brief` |
| C19 | **PAID** | `Library` headline `24 reused · 6 to add`; `Material`, `SurfaceIdentity`, `PadGadget`, `CheckGadget`, `countToken` and `CitationChips` all specimened; two rows flagged `NOT IN CONTRACT.MD` |
| C20 | **PAID** | Two residues at their true lines: the raw `<textarea>` at `:968` (comment `:966`, carried under rule `B`) and the two raw `<button>`s at `:985-1004` (rule A.1) |
| C21 | **PAID** | `ChairHome.tsx:345`, `UpdatePosture.tsx:141`, `:436-447`/`:812`, `decisions.py:57,61`. The banner no longer claims more than was checked |

### New findings the redraw introduced

**N1 — `P2ArrivalOne` disobeys the ranking key that `P2Arrival` obeys, and adds a fifth class. P1.**
The key is `1 Overdue · 2 Due today · 3 No due date · 4 Waiting`. `P2ArrivalOne` draws `#612 · WAITING · 3 DAYS` (class 4) **above** `CI failing on main · NO DUE DATE · CHANGED 40 MIN AGO` (class 3), and its third row carries `NOT RUN · 2 DAYS` — a class the head token does not name and the key does not rank. This is the one-Project board: his desk, beat 1 of his walk, and the arrival he will actually read. **Change:** reorder to `NO DUE DATE` → `WAITING`, and either fold `NOT RUN` into an existing class or add it to the key and the head token.

**N2 — the `COVERAGE` section duplicates rows the source ledger already carries, on seven boards. P1.**
C4's fix added a coverage section above the answer; on faces that already carry a full `SOURCES` (or `NOT READ`) ledger, the gap source is now drawn **twice on one face** with the same emblem, state, observation time and verb. `P3Prepare` is the clearest: `KAN · STALE · Retry` and `confluence PLATFORM · CANT CHECK · Reconnect` each appear in `COVERAGE 2 OF 4` **and** in `SOURCES 4` — six rows for four sources. Same on `P1Ask`, `P1Phone`, `P1RouteUnset` (`Calendar` twice), `P3PrepareNoModel`, `P3Brief` and `P3BriefPhone` (`confluence PLATFORM` in `COVERAGE` and again in `NOT READ 1`). Canon D: *the same object never drawn two ways; compose repeated things as one object.* **Change:** where a face already lists every source, the coverage line is the **token** (`COVERAGE 2 OF 4`) and the gap is marked in that one ledger; the standalone coverage section stays on the faces that have no source ledger (`P2*`, `P1Running`, `P4*`).

**Three notes, P2, no change required before his sitting.**
1. C17's fix collapsed three distinct failures onto one chip: `P6Repair` shows `CANT CHECK` for a rejected query, an unreachable engine **and** an expired credential, where `needs_you_aggregate.py:65-88` distinguishes seven tokens (an expired credential is `FORBIDDEN` there). One verb per failure class is right; one chip for every failure is not. Also `CANT CHECK` sits beside a verb named `Check`.
2. `WAITING ON THE ENGINE DRAFT NOT SAVED` renders as one run-on phrase on `P6Repair` and `P6Phone` — two tokens, no separator.
3. Unit drift in one token: `COVERAGE 47 OF 47 TURNS` (posture 4) counts turns while every other board counts sources; and it is a complete read stated as a fraction where the row beside it already says `READ IN FULL`. Posture 5 now carries no coverage at all — D1 scopes the law to postures 1–4 and D3 marks search-side coverage MISSING, so this is honest, but D2(e)'s `SEARCHED n OF m PROJECTS` partial state is now a state with no law and no board.

### Still carried, unchanged

`RoomAskWell`'s durable persistence remains **UNKNOWN** and the whole
`UNFINISHED` ledger rests on it; the changed-set notification and the
MCP steering residue remain BASELINE claims, not verified seams;
`ACCEPTANCE.md:209`'s coverage vocabulary still disagrees with C4 and
the code. No test was run and no live face was opened.
