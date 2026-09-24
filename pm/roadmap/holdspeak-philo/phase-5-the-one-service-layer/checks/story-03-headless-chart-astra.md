# PHILO-5-03 — Headless execution chart

Status: RATIFY-WITH-CONDITIONS by Muad'Dib; implementation in progress;
no closing proof claimed. His verbatim check is
[story-03-headless-chart-muaddib.md](story-03-headless-chart-muaddib.md).

Base: `c4d46498` (stories 01 and 02 merged). This chart implements the
ratified Proof position and Muad'Dib's lane brief. It changes no acceptance
criterion. Astra owns the lane; Muad'Dib checks on built.

The Tuesday job is the architect's meeting → summary → decision → dated
brief → saved Thought loop. This story proves that the operation path does
the same durable work while retaining the independent browser observations.
It adds no owner-facing interface (Tenets 1, 2, 3 and 7).

## Path

An `op` step sends JSON-RPC to the owning rig hub's existing `/api/mcp`
endpoint, with that hub's owner token. A small rig adapter maps the canonical
operation names to the existing tool or resource names and their argument
envelopes. The hub transport calls the registry already installed at hub
composition. There is no second service composition and no new product
endpoint. Import uses the existing owner-only MCP file intake; custody stays
inside the hub.

The record retains the canonical operation name, decoded result or named
refusal, protocol envelope and duration separately. Captures bind arguments
for later steps. An unresolved argument blocks before dispatch.

## Execution

`--headless` runs setup → preconditions → before observation → trigger →
bounded wait → terminal observation without creating a Playwright page.
Protocol snapshots call the owning hub directly. Operation observations use
`{kind: "op", name: "meeting.read", args: {…}}` at `observe_at` and in
supplementary reads. `op_field` reads the domain result; `op_refusal` checks
the named refusal. A requested face or UI act without a page is blocked.
Headless runs confer no face verdict and produce no fabricated screenshot.
Operation observations are reads. A refusal predicate examines the retained
trigger result; polling must not execute the failed write again. Its before
and after reads prove that the refusal did not alter durable state.

The adapter decodes tool `content` and resource `contents` separately and
preserves JSON-RPC resource error codes. A transport HTTP error blocks the
rig; it is not a domain refusal. Invalid decision status has no MCP code,
so that pair matches the specific error text. Coded refusals match their
codes. The projection map is checked against descriptor exposures. Import
records the input file hash, as the browser fixture step does.

Restart remains a rig action: capture before, stop the owned process, start
it with the same HOME/database and published port, capture after, and retain
PID, database, identity, summary and receipt relationships. Snapshot and
retention must work with no page. Polling has a bound and a sleep.
The summary-restart pair fails if any of `summary_retained`,
`receipt_retained` or `meeting_identity_retained` is absent or false.

## Evidence

Each named existing atlas case retains its browser/API path and gets an
`.op` sibling. Cases without model work use `--engine none`. Summary-quality
cases use the named LAN engine. Recorded provider replies run separately
with `--engine replayed`; the records retain that label.
Headless summary setup follows the existing Add engine producer: discover
the actual model through `/api/setup/discover-models`, define its profile
through `/api/inference/model-library/define-endpoint`, then assign the
captured profile through `/api/concierge/summary-selection`. The atlas uses
the fresh hub's initial assignment revision 0 and the new profile's revision
1; both producer responses remain in setup evidence. Astra's diagnostic
sequence also read `/api/concierge/detect` to confirm the initial revision.
The producer returned `succeeded` and `READY`, and actual S2/S3 operation runs
then returned successful LAN receipts. This corrects the route names in C5;
no product route is added. The recorded engine identity comes from the LAN
endpoint. Replayed operation runs retain
their identity through `meeting.read.run_receipt`, without a DOM selector.

Pair checks compare durable results and relationships inside each run,
including read-back identity, retained `created_at`, summary/receipt after
restart, next-day brief identity, brief-scoped item IDs, shelf state and
Thought body/revision/time. Independent generated IDs, wall-clock values
and model prose are not required to be equal across isolated runs. Missing
evidence cannot pass. Browser verdicts at 1440 and 393 remain separate.

The pair index names both run IDs, observation paths, engine modes, measured
operation-run duration, each comparison and its verdict. A mutation that
skews one real-produced field must fail equivalence. Removing `op` support
must block its calibration; reintroducing a page dependency must fail the
headless fence. Calibration is followed by the actual named atlas runs.

## Verification limits

The lane brief overrides the standing full-suite instruction: scoped tests
only, every pytest invocation with a temporary HOME, never `test_metal.py`.
Walks use one isolated hub per invocation and unique `--out` directories.
No story completion, commit or pair success is claimed by this chart.
