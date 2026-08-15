// HS-132-03 — the web mirror of the one realtime frame vocabulary.
//
// Canon lives in `holdspeak/realtime_frames.py`. This file is its mirror:
// `tests/test_realtime_frame_registry.py` fails when the two drift, and the
// same guard refuses any frame type that is emitted with no consumer or
// consumed with no emitter.
//
// Consumers still subscribe with plain string literals (that is what the
// guard reads); `RuntimeFrameType` is here so a subscription can be typed
// against the vocabulary instead of `string`.
//
// Article XI.5: `intel_token` is display material only — never journaled.

export const RUNTIME_FRAME_TYPES = [
  "actuator_proposed",
  "actuator_result",
  "aftercare_ready",
  "audio_level",
  "bookmark",
  "capture_recovery",
  "device_health",
  "dictation_preview",
  "duration",
  "intel_complete",
  "intel_status",
  "intel_token",
  "intent_controls_updated",
  "learning_event",
  "meeting_started",
  "meeting_updated",
  "plugin_jobs_processed",
  "runtime_activity",
  "runtime_queue",
  "segment",
  "stopped",
  "wake_armed",
  "wake_preview",
  "workbench.item_claimed",
  "workbench.item_done",
  "workbench.item_failed",
  "workbench.run_complete",
  "workbench.run_start",
] as const;

export type RuntimeFrameType = (typeof RUNTIME_FRAME_TYPES)[number];

export function isRuntimeFrameType(value: string): value is RuntimeFrameType {
  return (RUNTIME_FRAME_TYPES as readonly string[]).includes(value);
}
