# Turning dictation into a precise infra task

Produce a task spec, not a transcript. Always:

1. **Name concrete files/modules.** Reference real paths
   (`terraform/cluster.tf`, `k8s/base/deployment.yaml`,
   `operator/main.go`), not "the cluster config".
2. **Write an imperative spec.** "Add a `min_size` of 3 to the
   `spot` node pool in `terraform/cluster.tf`", not "we should
   probably make the pool bigger".
3. **Add an acceptance-criteria checklist.** Concrete, checkable
   items: plan is clean, CI green, dashboard shows X.
4. **Require a rollback plan.** Every task states how to undo it
   (revert PR, scale back, restore prior tag).
5. **Call out invariants in scope.** If the task touches prod,
   restate that the rollout must be progressive (canary→10%→100%)
   and that no manual kubectl is allowed — fold these into the
   acceptance criteria.

If the dictation conflicts with an invariant (e.g. "just kubectl it on
prod"), do not silently comply: surface the conflict and propose the
compliant path.
