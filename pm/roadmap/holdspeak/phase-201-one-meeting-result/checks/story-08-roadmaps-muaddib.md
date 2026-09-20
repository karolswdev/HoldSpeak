# HS-201-08 — story-08-roadmaps-muaddib

Invocation confirmed by CLI result: model `claude-fable-5-1`, session `416adc59-a8c4-43b4-9a49-e9db0e8faf36`. Peer clock estimates below are unverified; capture timestamps are UTC. Read-only check.

**Check — Muad'Dib (claude-fable-5-1), scope-extension design check for HS-201-08, 2026-09-20 ~05:55Z.**

- **Artifact:** the proposed repair of `holdspeak/web/routes/roadmaps.py:147`.
- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran no tests and spawned no workers.
  - I did run one command, `.githooks/dw next holdspeak-philo --json` (orientation only).
  - Its output confirmed the producer's real output, so I did not have to trust the diagnosis.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The diagnosis is correct. I confirmed it at the real producer, not only in a log.
   - `.githooks/dw next holdspeak-philo --json` prints `{"next_story": null}` and exits 2.
     Exit 2 means "nothing actionable", which CLAUDE.md documents as a lawful state.
   - roadmaps.py:147 evaluates `next_data.get("next_story", {}).get("story_id")`. The
     `{}` default applies only when the key is ABSENT. An explicit null comes back as
     None, `.get` on None raises AttributeError, and the route returns HTTP 500.
   - The route has been unchanged since 4e8e87e1 (HS-113-07). The Philo project merged in
     #589 was the first completed project to reach it.
   - Classification (b) is right. This is a valid no-action state that product code does
     not handle. The test is not stale.

2. The damage is larger than "GET for completed projects".
   - The LIST route calls the same `_project()` for every directory
     (roadmaps.py:168-176, `/api/roadmaps`).
   - So one completed project returns 500 for the whole list, including the active
     `holdspeak` roadmap.
   - On main today the owner's entire Roadmap face is broken, not only one project.
   - This strengthens the case for the fix and for the tenet-3 objection to leaving it
     red. The amendment should state the real damage.

3. The proposed expression is the right size.
   - `(next_data.get("next_story") or {})` is one expression.
   - It needs no framework and adds no schema validation. Tenet 1 is satisfied.
   - The face already handles the result:
     - api.ts:368 reads nextStoryId with `wireStringOrNull`.
     - RoadmapWindow.tsx:106 hides WHAT'S NEXT when it is null.
     - :110 draws no NEXT chip when it is null.
   - No face changes, and there is no canon exposure.

4. There is no existing route test to extend.
   - A grep for `api/roadmaps` and `build_roadmaps_router` under tests/ finds only
     tests/unit/test_kernel_effect_fence.py, which is a fence test and not a route test.
   - A new tests/unit/test_roadmaps_api.py is therefore correct.
   - Use the `repo_root` seam that the router already offers (roadmaps.py:156).
   - Drive the test through the REAL `_project` with a substituted `_run` that returns
     the producer's exact bytes, `{"next_story": null}` with exit code 2. Do not pass a
     hand-shaped dict.
   - A double that leaves out the explicit null would pass against the broken code too.
     See reference_lying_test_doubles.

5. The adjacent hazard should stay out of scope, and the amendment should say so.
   - If `dw next --json` ever printed a JSON list or scalar, `next_data.get` would
     raise the same way, because the try/except at :143-146 only catches parse failures.
   - The producer does not emit that today, so guarding it would widen for malformed
     schemas.
   - I agree with excluding it. Add a ledger line and no code.

CONDITIONS:
C1. Deterministic red comes first.
    - The focused test for explicit null must FAIL on the unmodified line with the
      AttributeError/500. Capture that through `dw evidence capture` before the edit.
    - The four still-valid states must be green before and after: top-level `story_id`,
      top-level `id`, nested `next_story.story_id`, absent `next_story`.
C2. Pin the LIST route as well.
    - With one completed project beside one active project, `/api/roadmaps` must return
      200 with both projects.
    - The completed project must carry `nextStoryId: null` and the active project its id.
    - That failure is the one the owner would actually meet (finding 2).
C3. The scope amendment goes in story-08 visibly (TWO-BRAINS §3). It must state:
    - the completed-project read path is added to "In";
    - AC6's full green includes this path;
    - classification is (b);
    - files are limited to roadmaps.py and tests/unit/test_roadmaps_api.py;
    - nothing may change in dw or in web/.
C4. Evidence must separate what was reproduced locally from what was only observed in
    CI, and it may not claim a CI red that never happened.
    - Reproduced locally: thought-diagnostic.log and the pre-lane 321 capture.
    - Observed only on CI: run 35478778899 at 675401a8 predates Philo, and the glass
      passed there. Evidence must say that, in those words.
C5. The standing conditions from counsel-on-built are unchanged.
    - The full quiet-tree run must be read to its end.
    - Every failing node must be named.
    - No inherited red may be relabelled as green.
    - This check does not ratify the final suite result.

MISSED (ranked by cost to the owner):
1. The 500 hits the whole roadmap list and not only one project (finding 2).
2. The route has had no test since HS-113-07. That is why a first-ever lawful state got
   through. The new file closes the hole; the evidence should say so plainly.
3. `_project()` runs two dw subprocesses per project per list request (:139, :142), each
   with a 20 s timeout.
   - With a second project the list now costs four subprocesses.
   - This is not this story's problem. Add a ledger line for the Workbench 2.0 tenet.

TUESDAY: Yes. Once this lands he opens Roadmaps and sees both projects. The finished
project shows no "what's next", and that is the correct answer for it.

UNKNOWN:
- Whether this 500 accounts for all of the new full-suite failures, because the run was
  still in progress.
  - Four failures had appeared by 8%, and this check does not cover any of them.
  - I did not read thought-diagnostic.log itself. The producer output settled the
    mechanism.
- Whether other readers of `dw next --json` share the null assumption.
  - A grep for `next_story` in holdspeak/*.py outside roadmaps.py returned no matches.
    The web side already guards for null (delivery.ts:181, missioncontrol.ts:103).
  - I did not check the MCP sidecar or scripts.
```
