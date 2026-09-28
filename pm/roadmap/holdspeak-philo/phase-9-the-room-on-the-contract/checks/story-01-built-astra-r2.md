VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **R1-1 paid for the inspected callers.** REFUSE preserves URL ownership, including equal-value IDs; eight additional refusal probes passed without mutation. No affected caller found in `web/src`, MCP, scripts or atlas cases. Filing sends only `relationship` (`web/src/desk/components/DeskFilingStrip.tsx:88`); MCP and rig operations use `/api/mcp`, bypassing this HTTP-body restriction.

2. **R1-2 remains unpaid — P2.** Replay reconstructs the response from the **current** resource row and the original command envelope (`holdspeak/services/project_service.py:3364`). File as `member`, change to `output`, then replay the first command: it returns `output` with the old revision. After removal, it returns `deleted: true`. Also, DELETE of an unfiled resource returns `removed: false`, then `true` on replay (`:3480`). All six HTTP/MCP probes fail; the DELETE response-preservation probe passes on `ffbeb04b`. **Tenets 3/7; Article VI.** [Reproductions](/tmp/astra-pr680-r2.pysfnhkv/test_review_r2.py), [results](/tmp/astra-pr680-r2.pysfnhkv/review-final.log).

3. **R1-3 paid.** The catalogue now advertises `review_id`; the fence resolves advertised paths against real producer responses. Evidence: `holdspeak/operations.py:1607`, `tests/unit/test_philo9_room_contract.py:550`.

4. **R1-4 paid.** The separate published-update query retains the publication and its delivery after eleven newer drafts. Evidence: `holdspeak/services/project_service.py:673`, `tests/unit/test_philo9_room_contract.py:517`.

5. **R1-5 paid.** `source_observation_id` is accepted and returned again; the four descriptor field checks pass. Evidence: `holdspeak/operations.py:1867`, `tests/unit/test_philo9_contract.py:270`.

6. **The automations DB fix is correct.** Partial contexts now use the reaction service’s database; an existing composed registry retains precedence. Evidence: `holdspeak/web/routes/automations.py:124`, `holdspeak/operations.py:2391`. I reproduced the regression test failing before the fix and passing now.

Independent verification: **188 passed, 1 expected failure**. The lane’s eight claimed red fences also reproduce at `74a9bdd5`. [Scoped results](/tmp/astra-pr680-r2.pysfnhkv/verified-scope.log), [earlier-head reds](/tmp/astra-pr680-r2.pysfnhkv/r1-red.log).

CONDITIONS:

- Persist and replay the original resource response, including DELETE’s original boolean. Fence retries after subsequent writes.
- Complete verification on the final mergeable head, including required shots and actual atlas observations.

MISSED:

Ranked by owner cost: changed data presented as an original replay; a no-op DELETE replay claiming removal; incomplete merge verification.

CI run 1’s **75 versus 74, with 71 shared**, is independently confirmed. The different failing sibling supports a flake hypothesis, but does not establish that this exact failure is inherited. At review time, GitHub reports **no run for `c74a214d`** and PR #680 as **conflicted**, not a running second CI check. [CI comparison](/tmp/astra-pr680-r2.pysfnhkv/ci-diff.json).

TUESDAY: Normal filing is preserved, but retry responses still cannot be trusted to describe the original action.

UNKNOWN: No story-01 1440/393 shots or actual atlas-run observations were supplied or found. Final-head full-suite verification remains unavailable. External callers beyond the repository were not verified. Reviewed `c74a214d`; repository tree unchanged.