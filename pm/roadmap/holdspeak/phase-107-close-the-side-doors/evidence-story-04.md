# Evidence - HS-107-04

- **Story:** HS-107-04 - The egress family — triage before migration
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-29T06:59:33Z

- **Command:** `uv run pytest -q tests/unit/test_external_egress_kernel.py tests/unit/test_kernel_effect_fence.py tests/unit/test_dictation_commit_boundary.py tests/unit/test_gated_connector.py tests/integration/test_actuator_kernel_real_hub.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4e609516f020bcab812f3fe635f562a8566bd46

```text
..................................                                       [100%]
34 passed in 5.54s
```

### Captured run — 2026-07-29T07:00:03Z

- **Command:** `git diff --exit-code --stat -- holdspeak/kernel/broker.py holdspeak/kernel/admission.py holdspeak/kernel/journal.py holdspeak/kernel/model.py holdspeak/kernel/executor.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4e609516f020bcab812f3fe635f562a8566bd46

```text
(no output)
```

## The eleven, resolved (arguments in `holdspeak/kernel/external_egress.py`'s docstring)

| site | verdict |
|---|---|
| N01 connector socket | **migrated** — manifest permission, destination scope, and `connector_request` data class become kernel admission prerequisites; `PermissionGate` makes no second decision |
| N02 gated connector raw-socket branch | **dormant eliminated** — every production outbound injects its opener; the incomplete no-opener branch now refuses by name and cannot open a socket |
| N05 intel-queue "model call" | **migrated** — the label was STALE: it is the queue failure-alert webhook, consequential egress carrying `queue_failure_metrics` |
| N06-N09 intel engine remote requests | **migrated** — each OpenAI-compatible remote request (initial + retry, non-streaming + streaming) is its own admitted, receipted operation; token iteration after dispatch stays computation; local llama siblings cross no egress boundary |
| N10-N12 dictation transcription | **exempt_computation** — returns to the hold-key caller on the permanently low-latency path (RFC §12, Article XI.5); explicitly triaged, not pattern-exempted |
| N13 Cadence Telegram | **migrated** — the receipt names the method/chat destination |

**The charter's "11 migratable egress" corrected to 7.**

## Register delta

29 total / 5 covered / 3 reads / 21 debt →
**21 total / 5 covered / 3 reads / 3 exempt_computation / 10 debt**
(statuses: covered 5, read 3, exempt_computation 3, bypass 9,
dormant 1; families: tmux 2, text_typer 1, subprocess 3, egress 5,
raw_desktop 10). **All ten remaining debt rows are the raw-desktop
primitives** — the §5b confinement remainder, exactly as chartered.
The new `exempt_computation` status is non-debt, requires a per-site
reason, and is never inferred from shape: the fence still catches a
new transcription-shaped call
(`UNLEDGERED effect site: …runtime_openai_compatible_new.py:2`) and
demands triage.

## Live proofs (implementation session, this machine, 2026-07-29)

Telegram was genuinely unconfigured (`token_configured: False`), so
the live outbound proof used N05's migrated production path against a
real local HTTP sink — honestly declared:

- **Outbound with destination in the receipt:** op
  `op_08456b4c509f43cc8cf101bb8870c883`, native receipt
  `destination=127.0.0.1:64071`,
  `data_classes=["queue_failure_metrics"]`, kernel receipt
  `rcpt_8a6a0da6…` `succeeded`; the sink received the real
  intel-queue failure-alert payload. The desk's egress badge now
  reads migrated destinations from the kernel journal, not a
  per-surface guess.
- **Refusal receipt:** destination `blocked.example:443` refused as
  `external_egress_destination_not_allowed:blocked.example:443`,
  state `refused`, socket never called (`"called": false`).

## Transcription latency — unchanged

Contemporaneous A/B against the same LAN endpoint (isolating source
change from endpoint drift): clean base transcribe median 171.688 ms
vs patched 171.543 ms (−0.08%); pipeline +0.06%; release-to-landed
869.1 → 854.9 ms. The hold-key path was not modified.

## Full suite (implementation session)

`uv run pytest -q --ignore=tests/e2e/test_metal.py` →
`2 failed, 4311 passed, 39 skipped in 880.05s`; the two failures are
the pre-existing UAT pair (build ledger staleness, voice-notes 502
copy). No new failures. Post-apply on this branch: 3402 unit +
749 integration passed.
