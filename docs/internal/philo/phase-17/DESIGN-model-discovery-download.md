# Find an engine and obtain a valid model — 2026-10-13

Owner report: model selection should find OpenAI-compatible servers on his
LAN; the suggested 2.7 GB Qwen always stops with INTEGRITY. Base: #1198,
`bcd1178b0`. One combined repair. No canon amendment.

## Evidence and Tuesday job

The owner's named server answers a read-only `/v1/models` request. Existing
detection probes loopback and already saved profiles; it has no subnet scanner.
The active picker already supports transient Found rows and explicit Use it.
The Tuesday job is to find the server, see its actual models, and select one
without typing an address or changing assignments during discovery.

The pinned [publisher file](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/blob/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q4_K_M.gguf)
labels `1d203c…` as its Xet hash and `00fe7986…` as SHA-256. Our catalog uses
the former as `file_sha256`. The expected size is correct. A read-only hash
of the newest rejected owner file matches the publisher's actual SHA-256;
four full-size rejected copies exist. The file downloaded correctly.

Tenets 1–3 favor repairing the existing picker and retry. Tenets 4–6 require
plain words and production components. Tenet 7 prioritizes using the owner's
existing engine and avoiding another unnecessary multi-gigabyte download.

## Settled face and behavior

The production-component direction canvas is `canvas/model-discovery/`.
Add **Find on LAN** beside **Add an engine** in Runs on. It starts an explicit
owner-only, read-only search. Busy, empty, partial, and failure states use the
existing receipt pattern. Results join the existing Found area with actual
model, host, port, and **Use it**. Use it retains the existing durable endpoint
definition; job assignment remains an explicit subsequent choice. No second
picker, automatic assignment, modal, or private IP baked into product code.

Scan only attached private IPv4 networks and existing engine ports. Bound
hosts, concurrency, connection/read time, and the whole search. A larger
network cap is reported as partial. Network/interface failures are not a
successful empty scan. The handler runs blocking work outside the hub's event
loop. No prompts, private work, or cloud credentials accompany discovery.
Tests inject interfaces and HTTP/TCP probes; they never scan the owner's LAN.

## Download repair

Correct the 4B content digest, recompute its manifest, update its default
artifact locators, and ship a coherent newly signed catalog revision. Keep
signature, SHA-256, size, and GGUF validation. Tiny Qwen and Hammer metadata
were independently checked against their pinned publisher API and already
match; do not change them.

A fresh acquisition under the corrected catalog can consider bounded prior
integrity failures for the exact repository, revision, filename, format, and
size. Reuse quarantined bytes only after full SHA-256 and GGUF verification
against the new plan. Keep the old failed record and immutable plan. A bad or
unrelated file still downloads normally. No owner state is changed by this
implementation session; reuse occurs only through the owner's retry gesture.

## Lanes and verification

- `lan_discovery`: scanner, owner-only route, Runs on client/controller/face,
  and focused tests. Owns no catalog/acquisition/default code.
- `qwen_integrity`: catalog, acquisition reuse, four default artifact locators,
  and focused tests. Owns no discovery/picker code.
- Root: design/canvas, official metadata and owner read-only observations,
  integrated verification, generated API metadata, PR/status/handover.

Workers verify drifting anchors, run only their named budgets, and HOLD FOR
SHIP without staging/committing. All tests use isolated HOME and the machine
lock. No full suite or metal test. The final quick check, typecheck, and shots
at 1440/393 precede the combined PR; full tape and Astra review follow merge.
Synthetic verification does not establish real model inference quality.
