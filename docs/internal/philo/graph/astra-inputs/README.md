# Astra live-pass inputs and review records

Source revision: `f575a5829b179548a2729dd58eb291f7d812b8c7`.

- `j6-runtime-atlas.json` is the original atlas with only the seven J6 address
  fills resolved to the lane brief's exact `/v1` endpoint. The field-level
  changes are in `j6-address-resolution.json`. Live graph case declarations
  remain verbatim from the original atlas.
- `preflight.json` names cases not invoked because their required recorded
  engine reply is missing. These are not fabricated rig observations.
- `state-gaps.json` preserves the atlas's unreachable state mechanisms.
- `execution-notes.json` records the declared dependency bootstrap, configured
  engine identity, fixture limits, and the separate J6 completion judgments.
- `execution-incidents.json` names the two overlapping J10 attempts, the
  interrupted record, and their serial replacements. Original records remain
  unchanged and excluded from strict serial proof.
- `brief-identity-review.json` records Astra's direct comparison of the retained
  and returned brief IDs in the serial same-day runs.
- The text logs preserve actual dependency and scoped-test command output.
- `verify-live-astra.py` checks the sealed graph against raw records, source
  inputs, hashes, case and viewport coverage, execution mode, ordering, and
  incident replacements. Run it from the repository root with `python3`.

The report is [live-astra.md](../live-astra.md). The graph serializes nested
observation values into schema string fields and hashes each complete raw
record and shot. A raw `pass` proves its predicate, not an entire owner job.
Temporary database paths identify isolated runtimes; they are not the owner's
database or claims of a surviving database after the rig exits.
