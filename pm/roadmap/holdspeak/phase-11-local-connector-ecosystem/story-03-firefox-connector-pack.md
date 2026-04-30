# HS-11-03 - Firefox companion connector pack

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-9-03, HS-11-01
- **Unblocks:** reusable browser-event connector distribution
- **Owner:** unassigned

## Problem

The Firefox companion should graduate from an endpoint into a packaged
connector with manifest metadata, privacy boundaries, local install docs,
and fixture coverage.

## Scope

- **In:**
  - Firefox connector manifest.
  - Local WebExtension development bundle.
  - Loopback endpoint compatibility tests.
  - Privacy review for captured fields.
  - Local install and uninstall guide.
- **Out:**
  - Browser extension store submission.
  - Safari extension.
  - Page bodies, cookies, credentials, form values, screenshots, or
    private browsing data.

## Acceptance Criteria

- [x] Firefox connector pack can be installed locally for development.
- [x] Events are accepted only through loopback.
- [x] Manifest declares captured fields and permissions.
- [x] Fixture tests cover accepted and rejected payloads.
