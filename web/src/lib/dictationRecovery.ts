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
  | "unknown";

export interface DictationFailureContract {
  message: string;
  retry: boolean;
  setup: boolean;
}

export const DICTATION_FAILURES: Record<
  DictationFailure,
  DictationFailureContract
> = {
  permission_denied: {
    message:
      "Microphone access is off. Your draft remains editable. Allow access, then retry.",
    retry: false,
    setup: true,
  },
  missing_model: {
    message:
      "Local transcription is not ready. Your draft remains editable. Open Setup to choose a model.",
    retry: false,
    setup: true,
  },
  rejected_token: {
    message:
      "This hub rejected the connection. Your draft remains editable. Open Setup to update access.",
    retry: false,
    setup: true,
  },
  unreachable_hub: {
    message:
      "The hub could not be reached. Your draft remains editable. Retry when it is reachable.",
    retry: true,
    setup: false,
  },
  delivery_conflict: {
    message:
      "Delivery did not complete because the target changed or is still busy. Your draft remains editable. Retry the same draft.",
    retry: true,
    setup: false,
  },
  transcription_failed: {
    message:
      "Transcription did not finish. Your draft remains editable. Retry the capture.",
    retry: true,
    setup: false,
  },
  timeout: {
    message:
      "Transcription timed out. Your draft remains editable. Retry when the model is ready.",
    retry: true,
    setup: false,
  },
  no_speech: {
    message: "No words were detected. Type below or hold to try again.",
    retry: true,
    setup: false,
  },
  unknown: {
    message:
      "Dictation did not finish. Your draft remains editable. Retry the capture.",
    retry: true,
    setup: false,
  },
};

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
