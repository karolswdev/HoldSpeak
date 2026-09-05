# HS-173-04 — The reviewer nudge

- **Project:** holdspeak
- **Phase:** 173
- **Status:** backlog
- **Depends on:** HS-173-03
- **Unblocks:** HS-173-06
- **Owner:** unassigned

## Problem

The steward has five V0 effect kinds (project_steward_service.py:39),
all INTERNAL. No external write has ever been executed. The arc says:
"the FIRST bounded external effect: `github.comment` (the reviewer
nudge) behind the policy gate with a terminal receipt and the comment
URL." This is a constitutional event: the first time HoldSpeak writes
to a system it does not own (Article V:1 acting is armed; Article XI:2
admitted, receipted).

## Scope

- In:
  - A new effect kind: `github.comment` added to EFFECT_KINDS.
  - The effect posts a PR review comment via `gh pr comment` (the
    allow-listed `gh` CLI; never a raw REST call).
  - The effect is opt-in per project: the owner must add
    `github.comment` to `eligible_effect_kinds_json` in the steward
    policy (project_steward_service.py:837).
  - The effect fires only with explicit owner approval (Article V:
    propose-approve-execute; the approval is the owner pressing
    Approve on the nudge card).
  - The terminal receipt records: the comment URL, the PR number, the
    reviewer name, the timestamp, the approval principal (Article
    XI:2).
  - The nudge comment template is respectful, factual, and short
    (e.g., "This PR has been waiting for review for N days. Flagged
    by HoldSpeak on behalf of [owner].").
  - Counsel reads the nudge implementation before the owner.
- Out:
  - Automatic nudges (the owner must approve each one).
  - Nudges via other channels (Jira comment, Slack, email).
  - Modifying the PR beyond a comment (no approvals, no merges, no
    label changes).

## Acceptance criteria

- [ ] `github.comment` is a registered effect kind in EFFECT_KINDS.
- [ ] The effect is opt-in: a project without `github.comment` in
      `eligible_effect_kinds_json` cannot trigger it; verified by a
      unit test.
- [ ] The effect fires only with explicit owner approval (Article V);
      verified by a rig that proposes a nudge and asserts it does not
      execute without approval.
- [ ] The terminal receipt contains: comment URL, PR number, reviewer
      name, timestamp, approval principal; verified by reading the
      receipt after an approved nudge.
- [ ] The comment is posted via `gh pr comment` (never a raw REST
      call); verified by asserting the subprocess call.
- [ ] Counsel reads the nudge implementation (a counsel pass is part
      of the acceptance).
- [ ] The nudge card shows the proposed comment text before approval
      (Article V: the user sees what will happen).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k reviewer_nudge`
  - Opt-in enforcement (effect kind not in eligible list = refused).
  - Approval required (no auto-execution).
  - Receipt contains required fields.
  - gh pr comment subprocess call shape.
- Integration: a rig that boots a hub, configures a policy with
  `github.comment` eligible, proposes a nudge, approves it, and reads
  the receipt.
- Manual: the owner approves a nudge on his desk; the comment appears
  on the PR; the receipt shows the URL.

## Notes / open questions

- The comment wording: counsel must review the template for tone. The
  comment should not be embarrassing for the reviewer or the owner.
- `gh pr comment` requires authentication; the existing `gh` auth
  (from Watch source evaluation) should suffice.
- This is a constitutional event: Article V (acting is armed) and
  Article XI (admitted, receipted) apply explicitly. The implementation
  must be reviewed by counsel before the owner.
