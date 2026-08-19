import { ApiError, type JsonRecord } from "./api";

export type DictationFailure =
  | "permission_denied"
  | "missing_model"
  | "rejected_token"
  | "unreachable_hub"
  | "delivery_conflict"
  | "transcription_failed"
  | "timeout"
  | "no_speech"
  /* HS-132-05 — the streaming mic's server refusals, kept by NAME. */
  | "mic_interval_closed"
  | "provider_failure"
  | "audio_floor_held"
  | "unknown";

export interface DictationFailureContract {
  message: string;
  retry: boolean;
  setup: boolean;
  /** The failure is about the selected Runs-on destination; another one may work. */
  alternateRunsOn: boolean;
}

export const DICTATION_FAILURES: Record<
  DictationFailure,
  DictationFailureContract
> = {
  permission_denied: {
    message:
      "Microphone access is blocked in your browser or operating system. Your draft remains editable. Allow microphone access there, then retry.",
    retry: true,
    setup: false,
    alternateRunsOn: false,
  },
  missing_model: {
    message:
      "Local transcription is unavailable. Your draft remains editable. Open Setup to see what this device needs.",
    retry: false,
    setup: true,
    alternateRunsOn: true,
  },
  rejected_token: {
    message:
      "This hub rejected the connection. Your draft remains editable. Open Setup to update access.",
    retry: false,
    setup: true,
    alternateRunsOn: false,
  },
  unreachable_hub: {
    message:
      "The hub could not be reached. Your draft remains editable. Retry when it is reachable.",
    retry: true,
    setup: false,
    alternateRunsOn: false,
  },
  delivery_conflict: {
    message:
      "Delivery did not complete because the target changed or is still busy. Your draft remains editable. Retry the same draft.",
    retry: true,
    setup: false,
    alternateRunsOn: true,
  },
  transcription_failed: {
    message:
      "Transcription did not finish. Your draft remains editable. Retry or type below.",
    retry: true,
    setup: false,
    alternateRunsOn: false,
  },
  timeout: {
    message:
      "Transcription timed out. Your draft remains editable. Retry the capture.",
    retry: true,
    setup: false,
    alternateRunsOn: true,
  },
  no_speech: {
    message: "No speech was detected. Your draft remains editable. Retry or type below.",
    retry: true,
    setup: false,
    alternateRunsOn: false,
  },
  /* HS-132-05 (Sol Amendment 3): the interval closed — inactivity, the
     ceiling, the child budget, a cancel, or a revocation. The client drops
     the interval; a fresh click starts a new one. */
  mic_interval_closed: {
    message:
      "The microphone session closed. Your draft remains editable. Click the mic again to continue.",
    retry: true,
    setup: false,
    alternateRunsOn: false,
  },
  provider_failure: {
    message:
      "The speech provider failed. Your draft remains editable. Retry, or run it somewhere else.",
    retry: true,
    setup: false,
    alternateRunsOn: true,
  },
  audio_floor_held: {
    message:
      "Another source holds the microphone. Your draft remains editable. Retry once it is free.",
    retry: true,
    setup: false,
    alternateRunsOn: false,
  },
  unknown: {
    message:
      "Dictation did not finish. Your draft remains editable. Retry the capture.",
    retry: true,
    setup: false,
    alternateRunsOn: false,
  },
};

export type DictationRecoveryAction =
  | "retry"
  | "copy"
  | "keep_as_note"
  | "alternate_runs_on"
  | "setup";

/**
 * HS-93-05: the only-applicable recovery actions for one failure, in the
 * story's order: Retry, Copy, Keep as Note, alternate Runs on, Setup.
 * Copy and Keep as Note act on the retained words, so they require a draft.
 */
export function applicableActions(
  failure: DictationFailure,
  options: { draftPresent: boolean },
): DictationRecoveryAction[] {
  const contract = DICTATION_FAILURES[failure];
  const actions: DictationRecoveryAction[] = [];
  if (contract.retry) actions.push("retry");
  if (options.draftPresent) actions.push("copy", "keep_as_note");
  if (contract.alternateRunsOn) actions.push("alternate_runs_on");
  if (contract.setup) actions.push("setup");
  return actions;
}

/* HS-132-05 — the streaming socket's refusal, exactly as the server named it.
   `/ws/dictation/stream` sends `reason`, `failure_category` and (Sol
   Amendment 3) `mic_interval: "closed"`; before this the client read only
   `error` and every refusal collapsed to "unknown". */
export type StreamRefusal = {
  error?: string;
  reason?: string;
  failure_category?: string;
  mic_interval?: string;
};

/** The server's failure_category vocabulary (holdspeak/web/routes/system/voice.py). */
const SERVER_FAILURE_CATEGORIES: Record<string, DictationFailure> = {
  speech_session_refused: "mic_interval_closed",
  speech_provider_failure: "provider_failure",
  audio_floor_held: "audio_floor_held",
  audio_floor_lost: "audio_floor_held",
  transcription_unavailable: "missing_model",
  transcription_failed: "transcription_failed",
};

/** Map ONE server refusal to its named failure. Never "unknown" when the
 *  server said what happened. */
export function streamFailure(refusal: StreamRefusal): DictationFailure {
  const named = refusal.failure_category
    ? SERVER_FAILURE_CATEGORIES[refusal.failure_category]
    : undefined;
  if (named) return named;
  // The interval is over whatever else the server said about it.
  if (refusal.mic_interval === "closed") return "mic_interval_closed";
  return dictationFailure(new Error(refusal.error ?? ""));
}

/** The refusal's NAME, for the surface that shows it (never prose). */
export function refusalCode(refusal: StreamRefusal): string | null {
  const raw = (refusal.reason || refusal.failure_category || "").trim();
  if (!raw) return null;
  return raw.replace(/[_\s]+/g, " ").trim().toUpperCase();
}

export function dictationFailure(error: unknown): DictationFailure {
  if (error instanceof DOMException) {
    if (error.name === "NotAllowedError") return "permission_denied";
    if (error.name === "AbortError" || error.name === "TimeoutError")
      return "timeout";
  }
  if (error instanceof ApiError) {
    const payload =
      error.payload && typeof error.payload === "object"
        ? (error.payload as JsonRecord)
        : {};
    if (payload.error_code === "delivery_pending") return "delivery_conflict";
    if (error.status === 401 || error.status === 403) return "rejected_token";
    if (error.status === 408 || error.status === 504) return "timeout";
    if (error.status === 409 || error.status === 425)
      return "delivery_conflict";
    if (error.status === 503) return "missing_model";
    return "transcription_failed";
  }
  if (error instanceof TypeError) return "unreachable_hub";
  return "unknown";
}
