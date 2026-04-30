# HS-11-01 - Connector manifest and SDK shape

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-9-13
- **Unblocks:** reusable local connector packs
- **Owner:** unassigned

## Problem

Phase 9 connectors should not remain ad hoc Python modules. To build an
ecosystem, each connector needs a manifest that declares identity,
capabilities, permissions, source boundaries, dry-run support, and output
types.

## Scope

- **In:**
  - Connector manifest schema.
  - Python SDK interfaces for discover, preview, import/enrich, and clear.
  - Permission declaration model.
  - Capability names for records, annotations, candidates, and commands.
  - Validation errors for malformed connectors.
- **Out:**
  - Remote marketplace.
  - Third-party package loading from the internet.
  - OAuth connector support.

## Acceptance Criteria

- [x] Connector manifest schema is documented and validated.
- [x] SDK interfaces map cleanly to Phase 9 connector state/output tables.
- [x] Permission declarations are required for network-capable connectors.
- [x] Invalid manifests fail with actionable errors.
- [x] Unit tests cover validation.
