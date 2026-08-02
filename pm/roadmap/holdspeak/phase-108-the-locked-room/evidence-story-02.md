# Evidence - HS-108-02

- **Story:** HS-108-02 - Confine the desktop primitives
- **Status:** done
- **Date:** 2026-07-29

## Real-metal proof

```text
$ uv run --extra test python scripts/phase108_desktop_metal.py
{"kernel_outcome": "succeeded", "kernel_state": "succeeded", "marker_landed": true, "native_state": "succeeded", "operation_id": "op_b73ba81d0fdc41c98a0ed092d4c74681", "target_ref": "desktop-input:focus-1-23bc257daf3e91d66761"}
```

A blank TextEdit document was opened on this Mac, a non-sensitive marker
was sent through the real spawned child and raw keyboard/clipboard driver,
then the document was closed without saving. The marker landed and both
receipt layers succeeded. The clipboard driver restored the previous
clipboard before returning.

The fence also pins that only
`holdspeak/privileged_effects/desktop_executor.py` imports the raw driver,
and `TextTyper`'s direct-call test refuses
`desktop_effect_warrant_required`.
