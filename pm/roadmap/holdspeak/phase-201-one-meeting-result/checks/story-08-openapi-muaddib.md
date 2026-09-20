# HS-201-08 — OpenAPI continuation

CLI confirms claude-fable-5-1, session 416adc59-a8c4-43b4-9a49-e9db0e8faf36. Root accepts: no OpenAPI workflow step; the existing unit guard remains unchanged.

**Check — Muad'Dib (claude-fable-5-1), continuation ruling on the OpenAPI completion for HS-201-08, 2026-09-20.**

- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran one grep, read `scripts/philo_openapi_reference.py:6-17`, read `tests/unit/test_api_surface.py:101-108`, and checked `.github/workflows/test.yml` for any mention of the generator.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. This scope is a completion of the docs extension already ratified. It is the same
   defect family, so it does not count as a fourth extension.
   - The generated artifact went stale against an inherited Phase 201 route.
   - Classification (a) is correct. test_api_surface.py:104-108 compares the committed
     file with the live `build_reference_app().openapi()`, and the invariant is valid
     and unchanged.
   - Its failure message names the remedy: "run scripts/philo_openapi_reference.py with
     isolated HOME". Follow that and keep HOME isolated for the regeneration.
2. The provenance edit is safe for the test, and the reason is specific.
   - The test pops `x-philo-note` and `x-source-snapshot` before comparing
     (test_api_surface.py:106-107).
   - A change to the note STRING therefore cannot affect the comparison. The keys must
     remain, because `.pop` without a default raises if one is missing.
   - "Same keys, no schema change" is therefore the correct constraint, and a required
     one.
3. This generator is NOT in the docs CI job. `grep openapi .github/workflows/test.yml`
   returns nothing.
   - The only CI guard for openapi.json is the unit test.
   - "Add it to the existing generator list" can therefore mean only root's local
     regeneration list and the README maintenance note.
   - It must NOT mean adding a step to test.yml:27-37. That would change a CI check,
     which the earlier amendment promised not to do.
   - Confirm that this is the intent.
4. The ten glass failures all trace to the `/api/roadmaps` NoneType defect I already
   checked. (b) stands for them.
   - Eleven named failures = ten glass + one OpenAPI, which matches the run's count.
   - One fix closes ten of the glass failures. The roadmaps conditions are unchanged:
     deterministic red first, and the list route pinned.

CONDITIONS:
O1. Capture red before any edit. Root is already doing this.
    - After regeneration, review the diff of openapi.json and record it.
    - The expected diff is ADDITIVE: `POST /api/concierge/summary-selection` with its
      request and response schemas, plus any Phase 201 schema touch-ups.
    - If any path or component is removed or narrowed, stop and review it explicitly,
      as root proposes.
O2. The note string changes and the two `info` keys stay. No other line of the generator
    changes. The test file is untouched.
O3. No edit to test.yml for this. See finding 3.
    - If root did intend a CI step, that is a separate amendment. I would want it
      argued. The unit test already guards the file.
O4. Evidence states the interpreter split plainly.
    - The eleven docs commands ran under Python 3.12.
    - OpenAPI regeneration and the 6-test file ran under the uv 3.13 venv.
    - Pydantic/FastAPI schema output can differ between resolver results.
    - CI's unit job runs 3.12 from `uv run --extra test`. The PR's Unit job is therefore
      the only proof that the committed bytes match there, as root says. Put that under
      UNKNOWN in the lane report. Do not treat it as closed.
O5. The order from R3 still holds.
    - Apply the product edit first (roadmaps.py), then the label strings.
    - Regenerate ALL the generators in one pass.
    - Then take the T1 capture sequence from R2. openapi.json counts as an input in the
      T1 tree.
O6. Carried forward from K2-K6:
    - The interrupted run is labelled not-proof, with all eleven failures named.
    - The final run goes to 100% under worksteal with nothing deselected beyond metal.
    - There is no partial closure.
    - Counsel-on-built is owed on the final tree.

MISSED:
1. openapi.json has no `--check` in the docs job, while three sibling generators do.
   - This asymmetry is why it surfaced late, through pytest and not the docs run.
   - Ledger line only.
2. 10,813 passed with 11 failed, all in two known families, is a strong diagnostic
   signal.
   - Still, an interrupted run cannot say what never ran, so the twelve-inherited-
     failures ledger entry in current-phase-status.md is neither confirmed nor cleared
     by it.
   - The final run settles that. If those twelve have in fact healed, evidence should
     say so.

TUESDAY: Not applicable to a face. Indirectly yes, because the roadmaps fix behind ten
of these restores his Roadmap list.

UNKNOWN:
- The actual openapi.json diff. It does not exist yet.
- Byte-equality under CI's Python 3.12.
- Whether the twelve previously ledgered inherited failures still exist.
- I did not read full-final.log. The eleven names are root's report.
```
