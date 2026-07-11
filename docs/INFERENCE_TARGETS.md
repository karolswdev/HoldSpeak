# Inference destinations

`GET /api/inference-targets` is the versioned “Runs on” discovery contract. It
names the destination kind, boundary, owner, transport, data classes, engine and
model separately, plus readiness derived without probing the destination.
`POST`, `PUT`, and `DELETE` use the same resource shape. Unavailable selections
refuse with an explicit alternate target; they never silently retarget.

`/api/profiles` and the synced `profile` primitive remain supported version-1
aliases over the same stored rows. Their earliest possible removal is
InferenceTarget v3, after a separately published migration window. API keys and
tokens are accepted by neither contract; the hub joins its per-destination
secret locally at execution time.

Before a run, each surface names the target and the data classes it may receive.
Afterward, the attempt receipt names the actual target, destination kind,
boundary, owner, transport, data classes, engine, model, and any fallback
reason. Choosing “This device” is local-only; it cannot fall back across a
boundary. Missing keys, unsupported kinds, offline nodes, and stale manifests
remain selected but unavailable, with a deliberate “choose alternate target”
recovery action.

The machine-readable vocabulary and compatibility plan live in
[`inference-targets.json`](inference-targets.json).
