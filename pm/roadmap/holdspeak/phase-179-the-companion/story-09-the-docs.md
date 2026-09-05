# HS-179-09 — The docs

- **Project:** holdspeak
- **Phase:** 179
- **Status:** backlog
- **Depends on:** HS-179-07
- **Unblocks:** HS-179-11
- **Owner:** unassigned

## Problem

The companion introduces a second glass (Article VIII.3), a LAN auth
model for non-owner devices, and a reverse Bonjour notification channel.
The documentation must reflect these.

## Scope

- In:
  - ARCHITECTURE.md updated with the companion's discovery and auth
    flow, the LAN notification channel, and the reverse Bonjour
    pattern.
  - USER_GUIDE.md extended with the companion setup (token entry,
    discovery), the portfolio and Room drill-down, and the
    notification behavior.
  - SECURITY.md updated with the LAN auth model (hub token, companion
    keychain storage, no APNs, no relay).
  - POSITIONING.md canonical feature names table updated: "the iPad
    app" / "the companion" as the canonical name.
  - Guide screenshots re-shot on the real device.
- Out:
  - API docs beyond route docstrings.
  - App Store listing (not in scope for this phase).

## Acceptance criteria

- [ ] ARCHITECTURE.md documents the companion's discovery, auth, and
      notification flow.
- [ ] USER_GUIDE.md describes the companion setup and use.
- [ ] SECURITY.md documents the LAN auth model.
- [ ] POSITIONING.md canonical names updated.
- [ ] Guide screenshots on the real device match the shipped face.

## Test plan

- Unit: n/a (docs story).
- Integration: n/a.
- Manual: doc review; screenshot freshness check.

## Notes / open questions

- None.
