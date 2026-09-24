# Actual J4 import preflight — 2026-09-23

The actual atlas `case.j4.meetings_import.imported` passed at 1440 through
`scripts/graph_walk.py`, under a fresh HOME, with the retained synthetic WAV.
This used the pre-face frontend build and does not close the Arrival face.
The hub was stopped by the rig on completion.

Observation:
`pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig/preflight-import/20260923T154801Z-case.j4.meetings_import.imported-astra-1440/observation.json`.
Astra read the complete observation and both shots. The initial shot is the
loading canvas; the terminal shot is the first-use screen, not Arrival.

The POST returned 202 with meeting `189e4fac`. The separate completion wait
took 24.165 seconds and 37 polls. The real detail contained transcription
state `complete`, duration 34.67525 seconds, two segments and 299 words.
No ASR result was substituted. The cache held public
`mlx-community/whisper-base-mlx`, snapshot
`1e3e249fb8d01c655324bd6841b1deadffd6d04c`.

Technical import completion is verified. Transcription usefulness is uneven:
the ASR rendered SQLite as “SQ like”, Maya Chen as “Mayyachan”, and generated
a long repetition of “exchange” over the third action. The second decision,
Leo Martinez and Tuesday survived. The third decision and Priya Shah
survived, but the action is damaged. Final usefulness must compare the actual
summary with all planted source facts, including omissions. This preflight
does not claim a summary call or an owner sitting.

The rig recorded the LAN `/v1/models` identity as
`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`, owned by `llamacpp`, at
`http://192.168.1.43:8080`. Identity availability alone is not execution.
