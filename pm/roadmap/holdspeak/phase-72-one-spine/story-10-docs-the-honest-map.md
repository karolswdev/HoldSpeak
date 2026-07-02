# HS-72-10 — Docs: the honest map (the docs story)

- **Status:** done
- **Priority:** MED (the phase's dedicated docs story — after features, before closeout)
- **Depends on:** HS-72-01 … HS-72-09
- **Evidence:** [evidence-story-10.md](./evidence-story-10.md)

## Goal

Bring the architecture canon back to measured truth. `docs/ARCHITECTURE.md`
(lines 165–189) describes the iPad as a narrow client (aftercare, facets,
artifacts, proposals, dry-run/readiness/remote) when the real Swift client
also drives agents, chains, activity nudges, dictation blocks, journal,
learning digest, meeting start/stop and import — an undercount of roughly
half. The doc also predates every rename this phase ships. After this story
the map matches the tree, and the parts that can drift are generated, not
written.

## Scope

- **In:** `docs/ARCHITECTURE.md` corrected against the HS-72-02 manifest (the
  device/client section links `API_SURFACE.md` instead of hand-listing
  routes); the companion→coders naming reflected everywhere the docs canon
  uses it (ARCHITECTURE, the backend-runtime doc, SECURITY if touched,
  WEB_DESK); the Mermaid diagrams re-checked (component map + device path
  are the ones the renames touch) with the render guard; POSITIONING gains
  the one canonical sentence for "coder" vs "agent" if it lacks one; the
  docs index + CONTRIBUTING pointers updated; entry points touched (the
  Phase-64 lesson: feature docs stories must touch the entry points too).
- **Out:** HS-IDs in `docs/*.md` (the voice guard rejects them — reference
  phases by name); user-guide feature docs (nothing user-facing changed);
  README marketing surface (no positioning change beyond the one sentence).

## Tasks

- [ ] Rewrite the client/consumer sections from the manifest; delete the
      hand-maintained route lists.
- [ ] Re-trace the two affected Mermaid diagrams; `tests/e2e/test_mermaid_renders.py`
      green.
- [ ] The naming sweep (companion → coders / desk actuators) across docs
      canon; voice + doc guards green.
- [ ] Verify every doc claim edited in this story against the tree (the
      guard for this phase: no prose promises where a generated artifact
      exists).

## Proof required

Doc slice + voice guard + mermaid guard green; the ARCHITECTURE diff showing
generated-artifact links replacing hand lists; a grep showing no stale
`api/companion` references in `docs/`; full suite green.

## Done

Shipped. `docs/ARCHITECTURE.md`'s iPad section tells the measured truth:
the five-extension hand list (the half-undercount) is replaced by the real
client shape (one base + nine extensions, verified against the tree) and a
link to the generated API_SURFACE with the measured 44 iOS-consumed routes.
"iPad companion" → "the iPad app" across prose + both affected Mermaid
diagrams + USER_GUIDE; POSITIONING's canonical-names table gains the
agents/coders/iPad-app rows with the companion-retirement note; the docs
index points at the generated surface with the regenerate command. Guards:
doc-drift 15 passed (it caught two em dashes in this story's own first
draft), mermaid render 2 passed; every edited claim verified against the
tree. See [evidence-story-10.md](./evidence-story-10.md).
