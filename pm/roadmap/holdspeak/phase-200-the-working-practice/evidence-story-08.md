# Evidence - HS-200-08

- **Story:** HS-200-08 - Establish repeatable live-model quality evaluation
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T22:36:38Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run pytest -q tests/unit/test_phase200_semantic_evaluation.py tests/integration/test_phase200_semantic_evaluation.py tests/unit/test_api_surface.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_doc_drift_guard.py -p no:cacheprovider 2>&1 | tail -1; HOME=$T uv run python scripts/phase200_eval.py manifest --check 2>&1 | tail -1; HOME=$T uv run python scripts/phase200_eval.py run --engine canned --canned tests/fixtures/phase200/canned/harness.json --report $T/eval.json 2>&1 | grep -E "episodes|critical|route" | head -3; uv run python scripts/check_docs.py 2>&1 | tail -1; echo "the LIVE run against 192.168.1.43 is the owner's (unreachable from the sandbox); no model result is claimed"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b99a37ef11ae4a2adf273945b9430a0bc2707a61

```text
90 passed in 20.57s
manifest current: 33 episodes
route: {"boundary": "private_network", "capability": "ask.answer", "endpoint": "http://127.0.0.1:61527/v1", "engine": "canned", "host": "127.0.0.1", "legs": [{"boundary": "private_network", "deploymentRevisionId": "dep_31e24ebb8d1519fb7a59df1aae2bd715bb5bf9fe230d61f9674cd6e01e8b599a", "ordinal": 1, "profileId": "canned"}], "model": "canned", "off_machine": true, "plan_id": "irp_9a476f4a45beb66b27ec0cc1fcab7815ec9014cc57d52415c6fdd265172938c7", "probe_engine": "openai_compatible", "probe_latency_ms": 202, "probe_model": "canned", "reason_code": "", "state": "READY"}
episodes 33 · passed 28 · failed 5 · critical 0
verdict: fail (critical: pass)
Documentation navigation: 38 files checked; local targets and Markdown headings resolve.
the LIVE run against 192.168.1.43 is the owner's (unreachable from the sandbox); no model result is claimed
```
