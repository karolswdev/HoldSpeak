# Postmortem — prod TLS outage (PI-204)

**Date:** 2026-05-19 · **SEV:** SEV-2 · **Duration:** ~38 minutes
**Incident commander:** on-call (platform-primary) · **Status:** blameless

## Summary

The `api.prod` TLS certificate expired and ingress served an expired
certificate for about 38 minutes. Clients saw TLS errors and edge 5xx.
cert-manager had been failing to renew the cert for days, but nothing
alerted on the shrinking expiry headroom, so the failure was invisible
until the cert actually lapsed.

## Timeline (UTC)

- **2026-05-12** — cert-manager begins failing to renew `api.prod`
  (silent; no alert on headroom).
- **2026-05-19 09:14** — certificate expires. Ingress serves expired
  cert; edge error rate climbs.
- **09:21** — `HighEdge5xx` pages on-call. Cause not yet obvious.
- **09:33** — on-call traces it to a pending ACME HTTP-01 challenge:
  the solver pod was unreachable from the ACME server because a network
  policy change (PI-198) had blocked the `.well-known/acme-challenge`
  path.
- **09:41** — solver path restored; cert-manager retried and issued.
- **09:52** — `api.prod` `READY=True` with a fresh cert; errors clear.

## Root cause

Two faults compounded:

1. **Trigger:** an unrelated network-policy change (PI-198) blocked the
   ACME HTTP-01 solver path, so cert-manager could not complete
   renewal.
2. **Why it became an outage:** no alert on certificate expiry
   *headroom*. We only alerted on edge 5xx — i.e. after the outage had
   already started. The renewal had been failing for a week unnoticed.

## Action items

- [x] Restore the ACME solver ingress path (done in-incident).
- [ ] **Add `CertExpiringSoon` alert at 14-day headroom** (PI-204
      follow-up) — pages before, not after, expiry.
- [ ] **Add a synthetic test of the ACME challenge path** to CI so a
      network-policy change that breaks renewal fails the PR.
- [ ] Update `runbooks/cert-renewal.md` with the solver-reachability
      diagnosis (done 2026-05-28).
- [ ] Review network-policy changes for impact on cert-manager
      (process change).

## Lessons

Alert on the leading indicator (expiry headroom), not the lagging one
(edge errors). A silent week-long failure should have been loud on day
one.
