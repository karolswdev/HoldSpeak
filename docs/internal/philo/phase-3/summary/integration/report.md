# PHILO-3-02 — main integration and runtime preparation

The owner authorized integrating `origin/main` before the PR. Astra merged
`8c078662` (PHILO-3-04) without conflicts through the Delivery Workbench gate as
`aac7544e`. PHILO-3-02 stays in progress. The gate counted the already shipped
PHILO-3-04 status and retained its paired evidence from the merged parent.

Focused integration checks: 80 Python tests (graph atlas and refinement thought
service) and 11 web tests (Thought receipt and receipt type floor) passed.
`main-python-raw.txt` retains the combined tool output;
`main-web-raw.txt` is the command's redirected output. These are integration
checks, not the quiet full-suite claim.

An unauthenticated GET of `http://192.168.1.43:8080/v1/models` returned
`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`, owned by `llamacpp`. `lan-models.json` retains
the response. This identifies the reachable endpoint before execution; each
real summary run must still retain its own executed receipt.

The public `mlx-community/whisper-base-mlx` model was downloaded with a fresh
HOME into the lane's isolated `.tmp/philo3-model-cache` HF cache. The resolved
snapshot and download output are in `asr-cache-raw.txt`. Subsequent rig runs use
this model cache and a fresh HOME for every run. No owner model credentials,
database, microphone or keychain were used.
