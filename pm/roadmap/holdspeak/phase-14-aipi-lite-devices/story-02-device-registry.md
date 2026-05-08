# HS-14-02 - DeviceRegistry + Device Descriptor Model

- **Project:** holdspeak
- **Phase:** 14
- **Status:** done
- **Depends on:** HS-14-01
- **Unblocks:** HS-14-03, HS-14-04
- **Owner:** unassigned

## Problem

Once `RemoteAudioRecorder` exists, multiple of them can coexist. The
runtime needs a way to track which devices are currently registered,
their human-readable label (which becomes `TranscriptSegment.speaker`
for their stream), their last-seen timestamp, and their queue depth.
A single dict-of-dicts is enough to start; the abstraction matters
more than the storage.

## Scope

- **In:**
  - `DeviceDescriptor` dataclass in `holdspeak/device_audio.py`:
    `id: str`, `label: str`, `connected_at: datetime`,
    `last_seen: datetime`, `queue_depth: int = 0`.
  - `DeviceRegistry` class with: `register(id, label) -> DeviceDescriptor`,
    `unregister(id)`, `get(id) -> DeviceDescriptor | None`,
    `active() -> list[DeviceDescriptor]`, `touch(id)` (updates
    `last_seen`).
  - Label uniqueness: `register` raises a typed
    `DuplicateLabelError` if another *active* device already holds
    the requested label. Unregistered labels are reusable.
  - Hold a `RemoteAudioRecorder` per registered device internally,
    but expose accessor `recorder_for(id) -> AudioSource`.
  - One global `DeviceRegistry` instance reachable from the
    runtime; lifecycle owned by the FastAPI app startup.
  - `tests/unit/test_device_registry.py` covering happy paths +
    duplicate label rejection + idempotent unregister.

- **Out:**
  - WebSocket route or any networking — HS-14-04.
  - Auth — HS-14-03.
  - Persistence — registry is in-memory only this phase. Devices
    re-register on reconnect.

## Acceptance Criteria

- [x] `DeviceDescriptor` and `DeviceRegistry` exist in
  `holdspeak/device_audio.py`.
- [x] `register()` rejects a duplicate active label with a typed
  exception that downstream callers can map to a 409 Conflict.
- [x] `unregister()` is idempotent — calling it on an unknown id
  is a no-op (logged at info, not raised).
- [x] A `RemoteAudioRecorder` is created on register and torn
  down on unregister.
- [x] `tests/unit/test_device_registry.py` ≥ 5 cases green:
  register-then-get, double-register-different-label,
  duplicate-label-fails, unregister-removes-recorder,
  idempotent-unregister.

## Test Plan

- Unit: `uv run pytest tests/unit/test_device_registry.py`.
- Integration: n/a.
- Manual: n/a.

## Notes

- Where the registry lives: `holdspeak/web_runtime.py` is the
  natural owner of runtime-wide singletons. Add a property there
  rather than module-global state.
- Why label uniqueness: speaker labels surface verbatim in
  `TranscriptSegment.speaker`; two devices both labeled "Karol"
  would produce ambiguous transcripts.
- A device that disconnects and reconnects with the same id but
  a new label is allowed — old descriptor was removed on
  disconnect.
