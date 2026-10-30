# The Dictation Copilot

The Dictation Copilot is the staged dictation pipeline. It keeps the original
speech text, applies configured corrections and project stages, and reports the
route before a delivery. It does not turn a model result into an automatic
keyboard action.

## One real run

One run has these boundaries:

1. An owner gesture admits microphone capture.
2. The local speech backend produces a transcript.
3. Correction and configured pipeline stages produce a preview.
4. The owner or an admitted destination commits the delivery.
5. The journal stores the route and terminal result.

The model stage and the typing stage are different operations. A remote model
can receive transcript or project context, while typing can still be local or
can use a paired desktop relay.

## How it works

The browser and desktop paths use the same pipeline service. The dry-run route
returns the frozen stages and egress boundary without typing. The remote route
uses a delivery id so reconnects can return a receipt instead of typing twice.

The selected engine can be a local model, an OpenAI-compatible endpoint, a
supported CLI inference engine, or a mesh node. A CLI inference engine is not a
launched coding agent.

## The four depth features

| Feature | Behavior | Boundary |
| --- | --- | --- |
| Intent routing | Selects a configured target or command. | A voice command needs a complete match and its own connector policy. |
| Correction memory | Applies saved owner corrections. | It records rules. It does not train a model. |
| Project knowledge | Adds facts or context to a rewrite. | It does not grant file or keyboard authority. |
| Preview and replay | Shows or re-runs stored transcript text. | It does not type or re-capture audio. |

## Configure it

Open **Settings > Speak** and unfold **More**. The **Pipeline** group holds
**Stages**, **Latency budget**, **Rewrite passes**, **LLM target detect**, and
**Detect below**. Choose the dictation model in **HoldSpeak > Engines**. See
the [Dictation Pipeline Guide](./DICTATION_PIPELINE_GUIDE.md).

For a headless setup, edit `~/.config/holdspeak/config.json`:

```json
{
  "dictation": {
    "pipeline": {
      "stages": ["intent-router", "kb-enricher", "project-rewriter"],
      "rewrite_passes": 2,
      "target_detect_llm_enabled": true,
      "target_detect_llm_below": 0.8
    }
  }
}
```

The endpoint and model are not dictation config keys. Assign them in
**HoldSpeak > Engines**. See [Models](./MODELS.md).

Use the Dictation face to select stages and the output target. The relevant API
surfaces are:

- `GET /api/dictation/readiness`
- `POST /api/dictation/dry-run`
- `POST /api/dictation/remote`
- `GET /api/dictation/journal`
- `GET /api/dictation/corrections`

The readiness response describes microphone custody, route readiness, and the
available delivery targets. A readiness result is not proof that a later target
will accept a committed send.

## Run the demo yourself

Run the dry path with an isolated home and a disposable project. Inspect the
egress boundary and the original and final text before testing delivery. The
default unit tests do not open a real microphone or type through a real
keyboard.

## See also

- [Dictation Pipeline Guide](DICTATION_PIPELINE_GUIDE.md)
- [Dictation architecture](DICTATION_ARCHITECTURE.md)
- [Models](MODELS.md)
- [Security](SECURITY.md)
