# The Steward's Hand and Voice -- the settled design (Phase 173, story 01)

> **DRAFT -- pending 172's merge and his word on 172's canvas.**

The owner's Tuesday moment (THE-TUESDAY-ARC.md section 2, "Phase 173"):
Monday 18:00, the steward drafted this week's update from the real
deltas -- prose a stakeholder can read, every claim with its ref,
unverified marked. He edits two sentences and publishes. Tuesday the
Room reads `Ania is the review bottleneck this week: 47 h median, 3 PRs
waiting` and the steward asks `Nudge her on #612?` -- one receipted
comment if he says yes. The face canon binds (docs/internal/UX-CANON.md);
the Door's, the Arrival's, the Heartbeat's, and the Loop Closes' grammar
(Phases 169--172) are the ratified precedent.


> **ON THE CANVAS (2026-09-05)** — nine boards published at
> https://claude.ai/code/artifact/9f1558b4-0867-4152-bc7e-1314dde5e82c ;
> counsel reading; faces build to the ratified boards under the standing
> goal; **his word gates the merge** (stacked on 172 #555).

## D0 -- the Tuesday moment

Monday 18:00. The steward's unattended run drafts this week's update.
The deterministic inventory (Claim schema, project_update_service.py:89)
collects every delta since the last published update; the model drafter
(_draft_with_model, project_update_service.py:679) rewrites the
inventory into stakeholder-readable prose. Every factual sentence
carries its Claim ref. Sentences the model added beyond the inventory
are marked `**[UNVERIFIED]**` (UNVERIFIED_MARKER,
project_update_service.py:79). The egress chip on the card names the
model's host. He opens the update, edits two sentences, presses
`Publish`. Done.

Tuesday 09:00. The Room's HEALTH section reads:

    REVIEW LATENCY  47 H MEDIAN  3 WAITING
    ISSUE AGING     4 > 14 D
    CI              2 FLAKY  QUEUE 3
    RELEASE         READY

Under NEEDS YOU a new row: `Ania -- review bottleneck -- 47 H MEDIAN --
3 PRS WAITING` with a `Nudge` verb. He presses `Nudge`. The nudge card
unfolds: the proposed comment text (editable in place), the PR
(`#612`), the host `GITHUB.COM`, and `Send` / `Dismiss`. He reads the
text, presses `Send`. The comment posts to #612. The receipt row
appears: `SENT -- #612 -- 18:02 -- GITHUB.COM`.

He never typed the comment. He never opened GitHub. The steward acted
within his word; he saw the exact text before it went; the receipt
names the host and the URL.


## D1 -- the laws

| Law | Source | How it binds |
|---|---|---|
| Acting is armed, opt-in per project | Constitution Article V:1 | The `github.comment` effect kind must be explicitly added to `eligible_effect_kinds_json` in the steward policy (project_steward_service.py:837); default is `[]` (project_steward_service.py:1530); no project fires a nudge until the owner enables it |
| Every external effect admitted and receipted | Constitution Article XI:2 | The nudge is admitted through the kernel before it acts; the terminal receipt records comment URL, PR number, reviewer name, timestamp, approval principal; refusal and failure also receipted |
| The nudge names its host and its exact text before it goes | Constitution Article III, V | The nudge card shows the proposed comment in full (editable); the host chip reads `GITHUB.COM`; `Send` is the chokepoint; the comment text the owner sees IS the text that posts |
| Never a nudge without his word on that project | Article V:1, the policy gate | The effect kind gate at project_steward_service.py:898 refuses any effect kind not in the project's eligible list; the Approve step is per-nudge (the owner presses `Send` on each one) |
| No counters of zero | UX-CANON.md rule A.8 | HEALTH rows absent when no data; REVIEW LATENCY absent when no pending reviews; RELEASE READINESS absent when no signals have data; the section label carries no `0` |
| Every verb the library Button | UX-CANON.md rule A.1 | `Send` (primary), `Dismiss` (ghost), `Nudge` (ghost dense), `Publish` / `Copy` / `Save` on the update, `Edit` (inline) -- all library Button |
| No prose | UX-CANON.md rule A.3 | Tokens, verbs, counts, names. The HEALTH rows are token strips. The nudge card is structured, not a paragraph |
| No modals | UX-CANON.md rule A.4 | The nudge card unfolds inline under the NEEDS YOU row; the update editor is the existing in-world posture |
| Egress where egress happens | UX-CANON.md rule A.9, Article III | EgressChip `GITHUB.COM` on the nudge card (where the write leaves); EgressChip on the model-drafted update card naming the model's host (where the draft was generated); the receipt's host |
| Design before build | UX-CANON.md rule A.2 | This document is the design; artboards at 1440 + 393 drawn from it; his word before any code |
| Ledger not gate | Owner ruling | Every steward run, every nudge send, every nudge refusal -- receipted via the service event ledger and kernel operation broker; no ceremony beyond the receipt |
| Unverified claims marked, never smoothed | Article VI:1 | The model drafter marks any claim not grounded in the deterministic inventory with UNVERIFIED_MARKER; the face renders the marker inline; the deterministic fallback has no markers |


## D2 -- the faces (element by element, species named)

### (a) The model-drafted update in the editor

**Position:** the UpdatePosture (web/src/features/project-room/update/
UpdatePosture.tsx). The existing update editor already handles the
deterministic draft with claims, the Save / Copy / Publish verbs, and
the EgressChip when the model drafter was used (UpdatePosture.tsx:428,
:472-474).

**What 173 adds to the existing face:**

- **Claims as chips with their refs.** Each Claim (project_update_
  service.py:89) renders as an inline chip in the prose body, styled
  with `surface-token[data-chip]` (secondary step, 12 mono). Clicking
  a chip opens its ref (the existing `openSourceRef` pattern from
  citations.ts). Unverified claims carry a warning StateChip
  `UNVERIFIED` (failure tone) beside the chip.
- **Model host chip.** When `generator` is not `deterministic`, the
  EgressChip at UpdatePosture.tsx:472-474 reads the model's host name
  (e.g. `192.168.1.43 -- LAN`, `openrouter.ai`). When the generator
  IS `deterministic`, no EgressChip (the fallback is local
  computation, not egress).
- **Verbs.** `Save` (Button ghost dense) persists the edit without
  publishing. `Copy` (Button ghost dense) copies the Markdown to
  clipboard. `Publish` (Button primary dense) publishes through the
  project revision law. All three exist today (UpdatePosture.tsx:
  494-521).

**Species used:** SurfaceLedger, SurfaceLedgerRow, surface-token
[data-chip], StateChip (failure for UNVERIFIED), EgressChip, Button
(primary dense, ghost dense), EditInPlace (the body is editable
inline).

**Widths:**

- 1440: the editor body takes the full column width; claims render
  inline in the prose; the model host chip sits in the footer beside
  the verbs.
- 393: the body stacks full-width; claims wrap naturally; the footer
  stacks verbs under the host chip.


### (b) The Room's HEALTH rows

**Position:** a new HEALTH section inside the Room, between the
headline chips (ProjectRoomCore.tsx:255-263, the existing AT RISK / ON
TRACK health assessment) and the NEEDS YOU section
(ProjectRoomCore.tsx:299). The HEALTH section is absent when no signals
have data (rule A.8).

**Section caption:** `HEALTH` (caption step, 11 mono uppercase 0.06em).
No count token (the signals ARE the content; a count of signals would
be a counter of implementation, not of reality).

**Rows** (SurfaceLedgerRow, 52px lead slot, one per signal with data):

1. **REVIEW LATENCY** (when at least one person has a computable
   median):
   - Lead: StateChip `*` (green <= 24 h, amber 24--48 h, red > 48 h;
     the worst person's median sets the tone).
   - Primary (15/600): `REVIEW LATENCY`.
   - Cells (secondary step, 12 mono): `47 H MEDIAN` (the overall
     median across all reviewers) -- `3 WAITING` (count of PRs with
     pending reviewRequests).
   - Trailing: no verb (the nudge lives on the per-person NEEDS YOU
     row, not here).

2. **ISSUE AGING** (when at least one issue exceeds the aging
   threshold):
   - Lead: StateChip `*` (green = 0 aged, amber = 1--2, red = 3+).
   - Primary: `ISSUE AGING`.
   - Cells: `4 > 14 D` (count of issues older than the threshold,
     default 14 days).

3. **CI** (when branch_ci entities exist):
   - Lead: StateChip `*` (green = last 3 pass, amber = 1 failure in
     last 3, red = 2+ failures).
   - Primary: `CI`.
   - Cells: `2 FLAKY` (count of branches with alternating pass/fail
     in history, when > 0) -- `QUEUE 3` (merge-queue depth: open PRs
     with passing CI not yet merged, when > 0). Absent tokens for
     zero values (rule A.8).

4. **RELEASE** (when at least one signal has data):
   - Lead: StateChip `*` (the scorecard's composite: green when all
     signals green, amber when any amber, red when any red).
   - Primary: `RELEASE`.
   - Cells: `READY` when all green, or a summary token naming the
     worst signal: `2 BLOCKERS` (count of red signals with their
     names).

**Empty state:** the entire HEALTH section is absent when no signal has
data (no pending reviews, no aged issues, no CI entities, no release
signals). This is NOT the same as "all green" -- all green shows the
section with green indicators.

**Species used:** SurfaceSection (caption), SurfaceLedgerRow, StateChip
(success/warning/failure), surface-token[data-chip].

**Widths:**

- 1440: each HEALTH row is one line (lead / primary / cells).
- 393: cells wrap under the primary; the lead stays left-aligned.


### (c) The NUDGE proposal card

**Position:** inline under a NEEDS YOU row, triggered by the `Nudge`
verb on a reviewer-bottleneck row. The card unfolds in place (rule A.4:
no modals). It replaces the row's trailing verb strip while open.

**Trigger:** a reviewer-latency-derived NEEDS YOU row (from HS-173-03)
carries a trailing `Nudge` verb (Button ghost dense) when the project
has `github.comment` in its eligible effect kinds. The verb is withheld
when the effect kind is not eligible (rule A.11: a verb that does
nothing is a lie).

**The card** (SurfaceWell, under the row):

- **Who:** the reviewer's name (primary step, 15/600). From the
  reviewRequests field (watch_sources.py:108) matched via the People
  resolver (172's face).
- **Which PR:** `#612 -- Title of the PR` (secondary step, 12 mono)
  with a link token to the PR URL.
- **The exact comment text** (body step, 13): the proposed comment,
  rendered in an EditInPlace so the owner can modify it before
  sending. Default template: `This PR has been waiting for review for
  N days. Flagged by HoldSpeak on behalf of [owner].` The template is
  factual, short, and respectful (counsel reviews the wording).
- **Host:** EgressChip `GITHUB.COM` (the write leaves HoldSpeak and
  lands on GitHub; Article III at the point of decision).
- **Verbs:** `Send` (Button primary dense) -- fires the nudge through
  the kernel. `Dismiss` (Button ghost dense) -- closes the card, no
  write.

**The receipt row** (replaces the card after `Send`):

- SurfaceLedgerRow: lead = StateChip `*` (success); primary =
  `SENT`; cells = `#612` (the PR number, linked) -- `18:02` (the
  timestamp) -- EgressChip `GITHUB.COM`; trailing = `Undo` is NOT
  offered (a posted comment cannot be retracted by HoldSpeak; honesty
  over convenience).
- The receipt persists in the service event ledger with the comment
  URL, the PR number, the reviewer name, the owner as approval
  principal, and the timestamp.

**Species used:** SurfaceWell, SurfaceLedgerRow, StateChip (success),
EgressChip, EditInPlace, Button (primary dense, ghost dense),
surface-token[data-chip].

**Widths:**

- 1440: the card is a well under the row, full width of the NEEDS YOU
  column. Who / PR on one line; the comment body on the next; host +
  verbs on the last.
- 393: the card stacks: who, then PR, then comment (full width), then
  host, then verbs.


### (d) The steward policy row -- EXTERNAL EFFECTS

**Position:** inside the StewardPosture's policy GadgetGroup
(StewardPosture.tsx:437), under the existing Effects CheckGadget rows
(StewardPosture.tsx:509-525). The new `github.comment` kind appears as
a sixth CheckGadget row in the same list.

**What 173 adds:**

- A new entry in EFFECT_KINDS (both backend
  project_steward_service.py:39 and frontend steward/model.ts:397):
  `"github_comment"` (the sixth kind).
- `effectKindLabel("github_comment")` returns `"Reviewer nudge"`
  (human label, never the raw snake_case kind on the face).
- `isModelTouchingKind("github_comment")` returns `false` (the nudge
  is a CLI call, not a model invocation).
- The CheckGadget row for `github_comment` carries an additional
  EgressChip `GITHUB.COM` (the egress badge at the point of policy,
  naming the host the effect writes to). No other effect kind carries
  an egress badge here (they are all internal).

**The policy flow:** unchecked (default) = the effect is not in
`eligible_effect_kinds_json` = nudges are never proposed. Checked = the
effect kind is added to the eligible list = the steward MAY propose a
nudge during its ACT phase, but the owner still approves each one via
the nudge card (double gate: policy eligibility + per-nudge approval).

**Species used:** GadgetGroup, GadgetRow, CheckGadget, EgressChip.

**Widths:**

- 1440: the CheckGadget row is inline with the label and the egress
  badge.
- 393: the egress badge wraps under the label.


### (e) The release-readiness row

**Position:** the fourth row in the Room's HEALTH section (D2b above),
when at least one signal has data.

**Composition:** a composite of four sub-signals, each independently
computed:

1. Review latency (from D2b row 1).
2. CI health (from D2b row 3).
3. Open blockers (from Watch entities where state=open AND labels
   contain "blocker" or priority is "blocker"/"critical").
4. Overdue commitments (from the People ledger / follow-through
   service -- commitments past their due date).

**Thresholds** (configurable per project via the steward policy):

| Signal | Green | Amber | Red |
|---|---|---|---|
| Review latency | all < 24 h | any 24--48 h | any > 48 h |
| CI health | last 3 pass | 1 failure in last 3 | 2+ failures |
| Open blockers | 0 | 1 | 2+ |
| Overdue commitments | 0 | 1 | 2+ |

**The composite:** green when all four are green; amber when any is
amber and none is red; red when any is red. The row's StateChip carries
the composite tone.

**The cells:** `READY` (all green) or a summary naming the blockers:
`2 BLOCKERS` with a tooltip listing the red/amber signals. At 393
the tooltip becomes a second line of tokens.

**Species used:** SurfaceLedgerRow, StateChip, surface-token[data-chip].

**Widths:** same as the other HEALTH rows (D2b).


## D3 -- the wire

### The model drafter behind the claim schema

**Seam:** `project_update_service.py:679` (`_draft_with_model`). Today
it resolves a deployment revision for `PROJECT_UPDATE_CAPABILITY`
("project.update_draft", project_update_service.py:77), builds a prompt
from the deterministic claims via `_build_model_prompt`, invokes the
inference runner, and parses the output via `_parse_model_output`
(:544). The output is structured JSON with sections and claims; each
claim is verified against the inventory refs (the frozenset of all refs
from deterministic claims). A claim whose `cited_refs` are not in the
inventory is marked `verified=False` (the UNVERIFIED_MARKER).

**What 173 changes:**

- The prompt gains an instruction to rewrite prose for stakeholder
  readability while preserving every Claim ref verbatim and marking
  any language not grounded in the inventory.
- `_parse_model_output` (:544) already handles the verified/unverified
  split. No change to the parser.
- The return triple `(body_md, claims_json, generator)` is unchanged;
  `generator` carries the deployment's human label (the egress fact).
- The face reads `generator` to decide the EgressChip (UpdatePosture.tsx
  :472-474 already does this).

**Fallback:** when `_draft_with_model` raises `_ModelDraftFailed` (no
broker, no assignment, model error, timeout, unparseable output), the
caller (`_deterministic_or_model_draft`) falls back to the
deterministic body. No unverified markers on deterministic output.

### The health derivations from snapshots

**The entity shape (the persisted snapshot):**

The Watch snapshot is `{"schema":1, "entities": {"526": {...snake_case}}}`.
`ProjectService._entities` (project_service.py:505) unwraps it to a
flat list of dicts. Each PR entity carries:

- `reviewRequests`: `list[str]` -- reviewer login names (watch_sources.
  py:108, via `_reviewer_names`).
- `reviewDecision`: `str | None` -- `"APPROVED"`, `"CHANGES_REQUESTED"`,
  `"REVIEW_REQUIRED"`, or `None` (watch_sources.py:109).
- `updatedAt`: `str` -- ISO timestamp of the PR's last update
  (watch_sources.py:111).
- `state`: `str` -- `"OPEN"`, `"CLOSED"`, `"MERGED"`.
- `checks`: `str | None` -- rollup conclusion (watch_sources.py:107).
- `url`: `str` -- the PR URL.
- `number`: `int` -- the PR number.
- `title`: `str`.

Each branch_ci entity carries:

- `conclusion`: `str | None` -- `"success"`, `"failure"`, `"timed_out"`,
  `"cancelled"` (watch_sources.py:55, GH_BRANCH_CI_FIELDS).
- `status`: `str` -- `"completed"`, `"in_progress"`, `"queued"`.
- `name`: `str` -- workflow name.
- `url`: `str` -- run URL.
- `updatedAt`: `str` -- ISO timestamp.
- `headBranch`: `str` -- the branch name.

Each Jira entity carries:

- `updated_at`: `str` (watch_sources.py:373).
- `created_at`: `str` (watch_sources.py:374).
- `status`: `str`.
- `assignee`: `str`.
- `due_at` / `dueDate`: `str | None`.

**CRITICAL GAP: review request timestamps.**

The persisted PR entities do NOT carry a `reviewRequestedAt` or
`createdAt` field. `GH_WATCH_FIELDS` (watch_sources.py:35) is:
`"number,title,url,state,isDraft,reviewRequests,reviewDecision,
statusCheckRollup,headRefOid,updatedAt"`. The `reviewRequests` field
gives reviewer NAMES only (login strings via `_reviewer_names`), not
timestamps. The `reviewDecision` field is a status enum, not a
timestamp. The `updatedAt` is the PR's general last-update time.

**Consequence for reviewer-latency computation:** true latency
(request-to-decision time) cannot be computed from the current snapshot
fields. Two practical approaches:

1. **Approximation from `updatedAt` and current time.** For open PRs
   with `reviewDecision` still null/REVIEW_REQUIRED, the age since
   `updatedAt` (or since `createdAt` if added to GH_WATCH_FIELDS) is a
   proxy for how long the PR has been waiting. This is an approximation:
   `updatedAt` resets on any PR event (push, comment, label), not only
   on the review request.

2. **Add `createdAt` to GH_WATCH_FIELDS.** Extend the field list at
   watch_sources.py:35 to include `createdAt`. This gives the PR
   creation timestamp, which is a reasonable lower bound for review-wait
   time (the request usually happens at or shortly after creation). The
   entity shape at watch_sources.py:108-111 gains `"createdAt":
   row.get("createdAt")`. The derivation then computes wait time as
   `now - createdAt` for open PRs with pending reviewRequests.

**Recommended:** option 2 (add `createdAt`). It is a read-only field
addition to the `gh pr list --json` call; no new CLI subcommand needed;
no write; the allowlist at github_cli.py:78 is unaffected (the
allowlist gates subcommand/verb pairs, not field names). The
approximation is honest: the face says `WAITING N DAYS` (from
createdAt), not `REVIEW LATENCY N H` (from a timestamp the system does
not have). For closed/merged PRs where `reviewDecision` is APPROVED, the
decision-time approximation (updatedAt) is acceptable for the median.

**Reviewer-latency derivation (the function):**

1. Collect all PR entities from active Watch snapshots for the project
   (via `ProjectService._entities`, project_service.py:505).
2. For each open PR where `reviewRequests` is non-empty and
   `reviewDecision` is null or `REVIEW_REQUIRED`: compute wait =
   `now - createdAt` (in hours).
3. Group by reviewer name. Per reviewer: median wait hours, count of
   waiting PRs.
4. Overall: median across all waiting PRs, total count.
5. Per-person rows feed NEEDS YOU (when median > threshold).
6. Overall median and count feed the HEALTH row.

**Issue-aging derivation:**

1. Collect Jira entities from Watch snapshots.
2. For each entity where status is not "Done"/"Closed": compute age =
   `now - created_at` (in days).
3. Count those exceeding the threshold (default 14 days).
4. Feed the HEALTH row.

**Flaky-CI detection:**

Today the branch_ci kind fetches `--limit 1` (watch_sources.py:121).
To detect flakiness, the steward run's OBSERVE phase would need to
request the last N runs (e.g. `--limit 10`). This means either:

- A new Watch query kind `branch_ci_history` with `--limit 10`, OR
- The steward's OBSERVE phase calls `gh run list --limit 10` directly
  (via the existing `_snapshot_branch_ci` seam, modifying the limit for
  the steward context).

**Recommended:** the steward's OBSERVE phase uses a separate
`_collect_ci_history` call with `--limit 10` for the flaky-CI
derivation. This keeps the Watch's 1-latest snapshot lightweight for the
normal evaluation cadence, while the steward (running less frequently)
pays the cost of the deeper history. The allowlist permits `("run",
"list")` (github_cli.py:34, already present).

**Merge-queue depth:**

1. From PR entities: count open PRs where `checks` = `"SUCCESS"` and
   `state` = `"OPEN"` and `isDraft` = false.
2. This is a read derivation from existing snapshot fields.

### The sixth effect kind: `github_comment`

**Backend:** add `"github_comment"` to `EFFECT_KINDS` (project_steward_
service.py:39). Add a new handler `_effect_github_comment` dispatched
from `_apply_effect` (project_steward_service.py:1094). The handler:

1. Reads the reviewer-latency derivation for the project.
2. For each reviewer exceeding the threshold: proposes a nudge with the
   PR number, the reviewer name, and the comment template.
3. The proposal is stored as a steward step with `state="proposed"` and
   `effect_kind="github_comment"`.
4. The proposal surfaces as a NEEDS YOU row with the `Nudge` verb.
5. On owner approval (`Send` on the nudge card): the execution path
   calls `build_github_pr_connector("comment")` (plugins/builtin/
   github_pr_actuator.py:86) which builds a `GatedConnector` wrapping
   `gh pr comment` (github_pr_actuator.py:42). The connector's
   `WriteConnectorManifest` (github_pr_actuator.py:18) permits ONLY
   `("gh", "pr", "comment")` as an argv prefix.
6. The gated connector (plugins/gated_connector.py) validates the
   operation against the manifest's allowed prefixes, executes the
   subprocess, and returns the output.
7. The terminal receipt is written: comment URL (parsed from `gh pr
   comment` stdout), PR number, reviewer name, timestamp, approval
   principal.

**The actuator already exists.** `github_pr_actuator.py` was built for
the follow-through service's PR comment and status effects. The
`GITHUB_PR_COMMENT_MANIFEST` (github_pr_actuator.py:18) and the
`_comment_plan` function (github_pr_actuator.py:34) already encode the
`gh pr comment` shape: repo, number, body. The steward's nudge reuses
this actuator identically -- the only new code is the steward's effect
handler that builds the proposal payload and passes it to the connector.

**The `gh` allowlist:** the Watch-side allowlist (github_cli.py:30) is
read-only: `pr view`, `pr list`, `issue view`, `run list`. The
actuator's allowlist is separate: `GITHUB_PR_COMMENT_MANIFEST.
allowed_argv_prefixes` = `(("gh", "pr", "comment"),)` (github_pr_
actuator.py:23). These are two different gates: the Watch reads through
`github_cli.is_command_allowed`; the actuator writes through
`WriteConnectorManifest.allows`. The nudge does NOT touch the read-only
allowlist. It uses the write connector's gate.

**Frontend:** add `"github_comment"` to `EFFECT_KINDS` in steward/
model.ts:397. Add its label mapping: `"github_comment"` =>
`"Reviewer nudge"`. `isModelTouchingKind("github_comment")` = false.

### The receipt

The receipt shape for `github_comment`:

```
{
  "effect_kind": "github_comment",
  "outcome": "applied",
  "comment_url": "https://github.com/owner/repo/pull/612#issuecomment-...",
  "pr_number": 612,
  "reviewer": "ania",
  "timestamp": "2026-09-09T18:02:00Z",
  "approval_principal": "owner:<owner_id>",
  "host": "github.com"
}
```

Persisted in the steward step's `observed_state_json` and in the
service event ledger as a `steward.effect.github_comment` event.

### The readiness scorecard

A pure derivation function (no new data collection):

1. Inputs: reviewer-latency median (from above), CI health (from
   branch_ci history), open-blocker count (from Watch entities with
   blocker labels), overdue-commitment count (from follow-through
   service).
2. Output: per-signal green/amber/red + a composite.
3. Exposed on the existing Room API as part of the health payload
   (`GET /api/projects/:id/room` already returns `health`; the
   scorecard extends it).


## D4 -- counsel's hunts

### H1: A nudge fired without opt-in.

The policy gate at project_steward_service.py:898 checks
`effect_kind not in eligible_kinds` and skips. But the nudge also
requires per-nudge owner approval. Hunt: verify BOTH gates are
independent and either one alone is sufficient to block. The opt-in
(policy) prevents the steward from even PROPOSING a nudge; the approval
prevents execution. A regression in either gate is a constitutional
violation (Article V).

### H2: A draft claim without a ref.

The model drafter must preserve every Claim ref from the deterministic
inventory. If the model rewrites a sentence and drops its ref, the
claim appears in the prose without grounding. Hunt: `_parse_model_
output` (project_update_service.py:544) marks claims whose cited_refs
are not in the inventory as `verified=False`. But what if the model
produces a sentence with NO ref at all? Verify that such a sentence
is caught and marked UNVERIFIED (not silently included as fact).

### H3: A latency derived from missing timestamps.

If `createdAt` is not yet added to GH_WATCH_FIELDS, the derivation
falls back to `updatedAt`, which resets on any PR event. A reviewer
who pushes a comment resets the timer, making the latency look shorter
than it is. Hunt: document the approximation honestly on the face
(`WAITING SINCE [date]` not `LATENCY N H`) and prefer `createdAt` once
available.

### H4: The same nudge twice.

The steward runs on a cadence. If a nudge was sent for PR #612 and
the reviewer has not yet responded, the next steward run must NOT
propose the same nudge again. Hunt: the idempotency key
(`_effect_idempotency_key`, project_steward_service.py:1540) is
per-run. A nudge for the same PR in a subsequent run has a different
key. Mitigation: check the receipt ledger for a recent
`steward.effect.github_comment` on the same PR+reviewer before
proposing; if one exists within a configurable cooldown (default 7
days), skip the proposal.

### H5: The `gh` auth gap.

`gh pr comment` requires authentication to the target repo. The
existing Watch evaluation uses `gh pr list` which also requires auth.
If Watch evaluation succeeds, `gh pr comment` should also authenticate.
But: the repo in the Watch query may differ from the repo in the nudge
target (a Watch may cover `org/repo-a` while the PR is on
`org/repo-b`). Hunt: the nudge must verify `gh` auth for the specific
repo before proposing. A failed auth is a refused nudge with a named
reason (`gh: not authenticated for owner/repo`), not a silent skip.

### H6: A health signal from stale snapshots.

Watch snapshots are refreshed on the Watch evaluation cadence
(default: depends on the scheduler, often 15 min). If the steward runs
between evaluations, the health signals are derived from potentially
stale data. Hunt: the HEALTH rows carry a `CHECKED N MIN AGO` token
(secondary step) showing the snapshot age. When stale beyond 2x the
evaluation cadence, the StateChip downgrades to `idle` tone.


## D5 -- the walk on his desk

The walk proves the Tuesday moment on his real desk with his real
projects:

1. **The model-drafted update.** The steward runs (unattended or
   triggered by `Run now` in the Steward posture). The update appears
   in the UpdatePosture with claims, refs, and the model host chip. He
   reads the prose; he edits two sentences; he presses `Publish`. The
   receipt appears. Stopwatch on the draft-to-publish time.
2. **The health signals.** The Room's HEALTH section shows rows derived
   from his real Watch data: review latency (per-person medians),
   issue aging (if he has Jira Watches with overdue issues), CI status
   (if he has branch_ci Watches). Each row's StateChip reflects the
   real data.
3. **The reviewer-latency NEEDS YOU row.** A person with pending PR
   reviews appears in NEEDS YOU with the median, the count, and the
   `Nudge` verb (if `github.comment` is enabled in the policy).
4. **The nudge.** He presses `Nudge`. The card unfolds with the
   proposed comment, the PR number, the host `GITHUB.COM`. He reads
   the text, edits it if he wants, presses `Send`. The comment posts
   to the real PR. The receipt row appears with the comment URL. He
   opens the URL in a browser to verify the comment.
5. **The release-readiness scorecard.** The HEALTH section's RELEASE
   row shows the composite status derived from his real signals.
6. **The 393 walk.** Same beats at 393 width: the health rows stack,
   the nudge card stacks, the update editor stacks. Every verb is
   reachable; no overflow.
7. **His word.** His verdict recorded verbatim. Scars become laws in
   UX-CANON.md.


## Honest sizes

| Story | Size | Notes |
|---|---|---|
| 01 The design | S | Artboards only; this document carries the spec |
| 02 The model drafter | M | Prompt tuning + unverified marking; the wire and face seams exist; the egress chip is wired; the heavy work is prompt engineering for stakeholder prose |
| 03 The health signals | M--L | Four derivations (reviewer latency, issue aging, flaky CI, merge-queue depth); the reviewer-latency derivation may require adding `createdAt` to GH_WATCH_FIELDS; the flaky-CI derivation needs a history call; four new HEALTH rows on the face at both widths |
| 04 The reviewer nudge | L | The first external write: a new effect kind, the policy gate, the nudge card face, the actuator call (existing github_pr_actuator), the receipt, the dedup cooldown, the counsel pass; constitutionally significant |
| 05 The release readiness | S--M | Pure derivation from signals computed in 03; one new row; configurable thresholds |
| 06 The walk | S | His desk, both widths, seven beats |
| 07 The docs | S | Screenshots + the nudge egress statement in SECURITY.md |
| 08 The hygiene lane | S--M | Depends on which files the phase touches |
| 09 The close | S | Suite, baseline, canon ratchet, counsel, PR |
| **Total** | **M--L** | The constitutional weight (the first external write) is the risk, not the LOC |
