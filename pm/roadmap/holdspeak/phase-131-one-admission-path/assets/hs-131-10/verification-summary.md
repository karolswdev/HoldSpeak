# HS-131-10 blocked-checkpoint verification

**Date:** 2026-08-12
**Disposition:** fence implementation ratified; story blocked on the chartered
HS-131-13–17 amendment wave.

## Focused fence

Command, with `HOME`, `TMPDIR`, and `--basetemp` under the session scratchpad:

```text
.venv/bin/python -m pytest -q \
  tests/unit/test_one_path_census.py \
  tests/unit/test_one_path_context.py \
  tests/unit/test_one_path_spine.py \
  tests/unit/test_one_path_cardinality.py \
  tests/unit/test_one_path_provenance.py
```

Result: **133 passed in 35.96s**. Raw quiet output is in
[`focused-tests.txt`](./focused-tests.txt).

The five suites cover the 145-site AST census, exact opaque context issuance and
rejection, all fifteen named product surfaces, seventeen actual invocation
children, physical-leaf cardinality, retries, both cancellation cohorts,
provenance, journal hygiene, late-publication fencing, and immutable receipts.

## Official full-suite gate

Command, with isolated scratch-resident `HOME`, `TMPDIR`, XDG roots, and the
owner-installed Playwright browser path:

```text
sh scripts/test_gate.sh
```

The script's two lanes reported:

```text
68 failed, 4897 passed, 8 skipped in 180.88s
9 failed, 240 passed, 36 skipped, 16 deselected, 14 errors in 673.59s
```

The 91 normalized names are checked in as
[`gate-failures.txt`](./gate-failures.txt). HS-131-09's pinned baseline has 90
names. The mechanical diff was:

```text
new (2)
  tests/unit/test_inference_kernel.py::test_tool_effect_is_causally_linked_child_with_own_receipt
  tests/unit/test_meeting_session_admission.py::test_a_failed_local_entry_admits_a_second_child_naming_the_cloud_revision

repaired (1)
  tests/e2e/test_live_bus.py::test_every_live_page_opens_exactly_one_runtime_socket
```

Both new names were reproduced three times together under fresh isolated HOME:

- With a short scratch-resident pytest root: **2 passed**, repeated **3/3**.
- The meeting fallback therefore remains an xdist-contention failure.
- The tool-effect test fails only when the session scratch prefix makes its
  synthetic `file:` result reference 174 characters, beyond the kernel's
  intentional 160-character reference grammar. It passes **3/3** with the short
  scratch root and is not a production behavior regression.

**Full-suite judgment:** zero product regressions; one inherited live-bus name
repaired. The red inherited ledger remains explicit rather than being treated as
green.

## Discarded run

A prior serial run reached 100% but used a nonexistent scratch `TMPDIR`, no
isolated-HOME Playwright browser path, and a `--basetemp` outside the mandated
session scratchpad. Its `79 failed, 5131 passed, 45 skipped, 17 errors` result is
discarded and does not support the checkpoint judgment.

## Hostile counsel

A fresh independent read of the ratified design, dirty implementation, and all
five fence suites returned:

```text
RATIFY BLOCKED CHECKPOINT
```

The counsel sustained all eleven finding families as blockers rather than
adapter exceptions. The exact 48-site ledger is
[`findings-inventory.md`](./findings-inventory.md).
