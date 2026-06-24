# Runbook: TLS certificate renewal

**Owner:** platform-primary on-call · **Last reviewed:** 2026-05-28
(post PI-204)

Certificates auto-renew via cert-manager. **You should never renew a
cert by hand.** This runbook is for diagnosing why auto-renewal failed.

## Symptoms

- Alert `CertExpiringSoon` (expiry headroom < 14 days), or
- Ingress serving an expired cert (browser TLS errors, 5xx at the edge).

## Diagnose

1. Check the Certificate and its CertificateRequest:
   ```
   kubectl describe certificate api-prod -n pylon
   kubectl get certificaterequest -n pylon
   ```
2. Inspect the ACME Order/Challenge for a stuck HTTP-01 solver:
   ```
   kubectl get order,challenge -n pylon
   ```
   A pending challenge usually means the solver pod can't be reached
   from the ACME server (this was the PI-204 root cause).
3. Confirm the solver ingress path is reachable end to end:
   ```
   curl -fsS http://api.prod.example.com/.well-known/acme-challenge/healthz
   ```

## Fix

- If the solver path is blocked, restore reachability (ingress rule /
  network policy) and let cert-manager retry — do not hand-issue.
- Force a retry by deleting the stuck CertificateRequest; cert-manager
  recreates it.

## Verify

- `kubectl get certificate api-prod -n pylon` shows `READY=True` and a
  fresh `Not After`.
- `CertExpiringSoon` clears; expiry headroom > 14 days.

## Rollback

There is nothing to roll back — cert-manager owns issuance. If you must
serve traffic during a long outage, fail over to the secondary
ingress with its still-valid cert (see incident commander).
