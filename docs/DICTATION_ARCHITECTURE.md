# Dictation architecture

This page follows the code path from captured audio to a preview or a typed
result. Capture, model inference, and typing have separate custody and receipts.

## End-to-end path

1. A browser or desktop gesture opens an admitted speech session.
2. Audio is captured and sent to the selected local transcriber.
3. The pipeline runs configured correction, intent, knowledge, and rewrite stages.
4. The result is published to a preview or to an admitted delivery.
5. The journal and delivery repository record the outcome.

The route can send text to a model host. The typing route can send final text to
a focused desktop application or a waiting agent session. Neither boundary
proves the other one happened.

## Entry points

| Entry | Source |
| --- | --- |
| Browser microphone | `POST /api/dictation/mic/open`, `/mic/close`, and `/api/dictation/transcribe` |
| Streaming browser mic | `WS /ws/dictation/stream` |
| Desktop hotkey | `holdspeak/runtime/dictation_capture.py` |
| Dry run | `POST /api/dictation/dry-run` |
| Remote delivery | `POST /api/dictation/remote` |
| Voice commands | `holdspeak/dictation_runner.py` and `POST /api/commands/test` |

## Admission and the voice-command branch

Browser capture uses one opaque microphone interval and the shared audio floor.
The stream sends PCM chunks and one end event. The server performs one final
transcription for the utterance. A configured voice command is dispatched only
after complete matching. If the voice command cannot type, plain dictation remains
available and the refusal is recorded.

## Pipeline stages

| Stage | Module family | Model |
| --- | --- | --- |
| Transcription | `holdspeak/transcribe.py` | Whisper backend |
| Corrections | `holdspeak/plugins/dictation` | No |
| Intent | Dictation intent router | Optional |
| Knowledge | `kb-enricher` | No |
| Rewrite | `project-rewriter` | Yes |
| Delivery | Dictation service and desktop relay | No model by itself |

A stage receives a frozen configuration snapshot. A skipped model stage leaves
the current text unchanged. A non-fatal stage failure returns the original
utterance text and a named reason.

## Runtime backends

The transcriber supports MLX on compatible Apple Silicon and faster-whisper.
The selected backend does not silently change when an explicit backend is
unavailable. Audio is mono float data at the runtime sample rate. Empty audio
creates no inference child.

Pipeline inference uses the selected model assignment. A supported CLI can act
as an inference engine. A launched coding agent is a separate process with a
brief, worktree, and process receipt.

## Commit and delivery

Preview publication is not typing. Focused typing uses the desktop typing
driver. Remote delivery requires a delivery id, claims that id before the
effect, and stores a terminal receipt. A reconnect with the same request returns
the known result. A different request under the same id is refused.

The operation policy applies to committed effects. **YOLO** is the default mode
for eligible scoped effects. **Secure** and **Normal** can require a preview or
grant. Authentication, destination binding, payload binding, pane identity, and
audit receipts apply in every mode.

## Tests to read

- `tests/unit/test_dictation_commit_boundary.py`
- `tests/unit/test_dictation_pipeline.py`
- `tests/unit/test_voice_routes.py`
- `tests/unit/test_voice_command_dispatch.py`
- `tests/unit/test_desktop_typing.py`

Default tests use an isolated home and do not type into the owner's desktop.

## See also

- [Dictation Pipeline Guide](DICTATION_PIPELINE_GUIDE.md)
- [The Dictation Copilot](DICTATION_COPILOT.md)
- [Voice commands](VOICE_COMMANDS.md)
- [Authority model](AUTHORITY_MODEL.md)
