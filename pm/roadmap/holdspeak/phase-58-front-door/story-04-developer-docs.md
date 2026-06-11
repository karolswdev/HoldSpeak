# HS-58-04 — The developer + ops docs

- **Project:** holdspeak
- **Phase:** 58
- **Status:** done
- **Depends on:** HS-58-01
- **Unblocks:** HS-58-05
- **Owner:** unassigned

## Problem
The extend-it docs are the pitch to contributing developers, and they are
the most dash-saturated files in the corpus (PLUGIN_AUTHORING: 82).

## Scope
- **In:** PLUGIN_AUTHORING, CONNECTOR_DEVELOPMENT, DEVICE_PROTOCOL,
  MODELS, SECURITY, RELEASING, AGENT_HOOK_INSTALL, AIPI_LITE_DEV_WORKFLOW:
  the same treatment as 03, with ledes that make building on HoldSpeak
  sound as deliberate as using it (the contributor pitch).
- **Out:** changing any documented contract, schema, or protocol fact.

## Acceptance criteria
- [x] Every listed doc: why-lede where the register calls for one (the
      contributor pitches on PLUGIN_AUTHORING + CONNECTOR_DEVELOPMENT),
      canonical names, humanizer-clean, zero em/en dashes in prose
      (101 prose sites removed across six files; example code exempt).
- [x] No contract/protocol/schema fact altered (review recorded in
      `evidence-story-04.md`; bare "—" table cells now say "none").
- [x] Doc locks green.

## Test plan
- Doc-guard slice per batch + full suite.
