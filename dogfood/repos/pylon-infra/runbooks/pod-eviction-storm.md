# Runbook: pod eviction storm

> **STALE — tracked as PI-220.** This runbook predates the Pylon
> operator and the (planned) cluster autoscaler. It still tells you to
> `kubectl drain` aggressively, which can cascade evictions through
> PodDisruptionBudgets. **Do not follow steps 2-3 verbatim.** Rewrite
> is blocked on the PI-215 autoscaler design.

**Owner:** platform-primary on-call · **Last reviewed:** 2025-11-04

## Symptoms

- Many pods `Terminating`/`Pending` at once.
- `FailedScheduling` events spiking.
- Service availability dipping (SLO burn) without a deploy.

## Procedure (OUTDATED)

1. Identify the affected nodes:
   ```
   kubectl get nodes
   kubectl describe node <node>
   ```
2. ~~Cordon and drain the suspect nodes:~~
   ```
   kubectl cordon <node>
   kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
   ```
   **RISK:** draining several nodes back-to-back evicts faster than
   PDBs allow pods to reschedule, which starts the storm it's meant to
   stop. This is the PI-220 hazard.
3. ~~Repeat for each node showing pressure.~~

## What it SHOULD say (PI-220 rewrite, not yet done)

- Drain at most one node at a time and wait for pods to go `Ready`
  elsewhere before the next.
- Respect PDBs; if a drain blocks on a PDB, that is correct — do not
  `--force`.
- Let the operator and (soon) the autoscaler add capacity before
  removing it. Under autoscaling, routine evictions become normal and
  must not page.
