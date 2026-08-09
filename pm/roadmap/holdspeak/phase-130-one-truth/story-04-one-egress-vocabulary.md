# HS-130-04 — One egress vocabulary: the four lies become one truth

- **Project:** holdspeak
- **Phase:** 130
- **Status:** backlog
- **Depends on:** HS-130-03
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Egress truth is derived in four places that disagree, and the disagreements
are shown to the user as safety claims:

1. `_private_endpoint` / the `openAICompatible` branch (inference_targets.py
   :30-43, :280-285) correctly yields `boundary="private_network"` for a LAN
   endpoint.
2. `endpoint_egress` (providers.py:249-267) has only `{mesh, cloud, local}`,
   collapses every remote endpoint to `cloud`, and stamps `DEFAULT_CLOUD_HOST`
   — a host the run never contacted — when the host parse fails. Call sites
   pass a flat `cloud=True` (ask_service.py:174, support.py:153).
3. `intel_egress_posture` (providers.py:442-463) judges only `intel_provider`,
   so with `intel_provider="local"` + a `meshNode` pointer it prints "Local
   only — transcripts never leave this machine" while the run routes to the
   mesh relay.
4. Duplicated `_run_egress` copies (support.py:151-159, ask_service.py
   :171-180) — two owners of the badge rule the docstring claims is central.

A LAN 192.168.x destination is badged "cloud"; a mesh route is badged "Local
only." Both are false, and both are what doctor/web status show.

### What changes

1. One boundary vocabulary — `{local, private_network, mesh, cloud}` — derived
   from the **executed deployment** (HS-130-03's identity), through one
   function. Badges, doctor, receipts, and the posture string all read it.
2. `endpoint_egress`'s three-value model is replaced by the full vocabulary;
   the `DEFAULT_CLOUD_HOST` fabrication is removed (no host is named unless it
   was contacted).
3. `intel_egress_posture` derives from the same boundary as the run, not from
   `intel_provider` alone — the "Local only" string cannot appear for a
   mesh-routed run.
4. The duplicated `_run_egress` copies collapse to one caller of the shared
   function.
5. A frozen mapping table (every current endpoint shape → boundary) lands as a
   test so consolidation cannot silently move a verdict.

## Acceptance criteria

1. A LAN/private endpoint reports `private_network` in the badge, doctor, and
   receipt — never `cloud`.
2. A mesh-routed run never shows a "Local only" posture; the posture equals
   the run's actual boundary.
3. No user-facing surface names a host the run did not contact.
4. Exactly one function computes boundary; the frozen mapping test passes and
   fails on any moved verdict.
5. Proven on real metal: control-vs-treatment on .43 (LAN endpoint) shows
   `private_network` end to end (badge + doctor + receipt).

## Test plan

- Backend: the frozen endpoint→boundary table; a mesh-posture regression; a
  no-fabricated-host test; single-owner assertion (grep + call-graph).
- Metal: .43 LAN run, capture badge/doctor/receipt (walk leg in HS-130-11 also
  covers this; this story's own capture is the backend + one live run).
- Full backend suite read from file before flip.

## Out of scope

- Meeting placement selection (HS-130-05); this story governs how the chosen
  route is *described*, not which route is chosen.
- Deployment revisions (Phase 131).
