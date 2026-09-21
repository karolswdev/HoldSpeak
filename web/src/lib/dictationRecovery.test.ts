import { describe, expect, it } from "vitest";
import { ApiError } from "./api";
import {
  DICTATION_FAILURES,
  applicableActions,
  dictationFailure,
  refusalCode,
  streamFailure,
  type DictationFailure,
} from "./dictationRecovery";

describe("dictation recovery contract", () => {
  it("maps permission, token, model, conflict, timeout, and network failures", () => {
    expect(
      dictationFailure(new DOMException("denied", "NotAllowedError")),
    ).toBe("permission_denied");
    expect(dictationFailure(new ApiError(401, "bad token", {}))).toBe(
      "rejected_token",
    );
    expect(dictationFailure(new ApiError(503, "no model", {}))).toBe(
      "missing_model",
    );
    expect(dictationFailure(new ApiError(409, "conflict", {}))).toBe(
      "delivery_conflict",
    );
    expect(dictationFailure(new ApiError(504, "timeout", {}))).toBe("timeout");
    expect(dictationFailure(new TypeError("offline"))).toBe("unreachable_hub");
  });

  it("keeps every failure factual, retained, and actionable", () => {
    for (const contract of Object.values(DICTATION_FAILURES)) {
      expect(contract.message).not.toMatch(/sorry|don.t worry|magic/i);
      expect(contract.message).toMatch(/draft|type below|words/i);
      expect(contract.retry || contract.setup).toBe(true);
    }
  });

  it("maps every failure to its only-applicable actions", () => {
    const expected: Record<DictationFailure, string[]> = {
      permission_denied: ["retry", "copy", "keep_as_note"],
      no_microphone: ["retry", "copy", "keep_as_note", "setup"],
      microphone_unavailable: ["retry", "copy", "keep_as_note", "setup"],
      missing_model: ["copy", "keep_as_note", "alternate_runs_on", "setup"],
      rejected_token: ["copy", "keep_as_note", "setup"],
      unreachable_hub: ["retry", "copy", "keep_as_note"],
      delivery_conflict: [
        "retry",
        "copy",
        "keep_as_note",
        "alternate_runs_on",
      ],
      transcription_failed: ["retry", "copy", "keep_as_note"],
      timeout: ["retry", "copy", "keep_as_note", "alternate_runs_on"],
      no_speech: ["retry", "copy", "keep_as_note"],
      // HS-132-05 — the streaming mic's named server refusals
      mic_interval_closed: ["retry", "copy", "keep_as_note"],
      provider_failure: [
        "retry",
        "copy",
        "keep_as_note",
        "alternate_runs_on",
      ],
      audio_floor_held: ["retry", "copy", "keep_as_note"],
      unknown: ["retry", "copy", "keep_as_note"],
    };
    for (const [failure, actions] of Object.entries(expected)) {
      expect(
        applicableActions(failure as DictationFailure, { draftPresent: true }),
      ).toEqual(actions);
    }
  });

  it("drops draft-bound actions when no draft is retained", () => {
    expect(
      applicableActions("delivery_conflict", { draftPresent: false }),
    ).toEqual(["retry", "alternate_runs_on"]);
    expect(applicableActions("rejected_token", { draftPresent: false })).toEqual(
      ["setup"],
    );
  });

  it("keeps first-value recovery copy factual with one exact next action", () => {
    expect(DICTATION_FAILURES.permission_denied).toMatchObject({
      retry: true,
      setup: false,
    });
    expect(DICTATION_FAILURES.permission_denied.message).toMatch(/browser or operating system/i);
    expect(DICTATION_FAILURES.no_speech).toMatchObject({ retry: true, setup: false });
    expect(DICTATION_FAILURES.no_speech.message).toMatch(/No speech/i);
    expect(DICTATION_FAILURES.missing_model).toMatchObject({ retry: false, setup: true });
    expect(DICTATION_FAILURES.missing_model.message).toMatch(/Open Setup/i);
    for (const failure of ["timeout", "transcription_failed"] as const) {
      expect(DICTATION_FAILURES[failure]).toMatchObject({ retry: true, setup: false });
      expect(DICTATION_FAILURES[failure].message).toMatch(/Retry/i);
    }
  });

  it("offers an alternate Runs-on only for destination failures", () => {
    const alternates = Object.entries(DICTATION_FAILURES)
      .filter(([, contract]) => contract.alternateRunsOn)
      .map(([failure]) => failure)
      .sort();
    expect(alternates).toEqual([
      "delivery_conflict",
      "missing_model",
      "provider_failure",
      "timeout",
    ]);
  });
});

/* HS-132-05 — the streaming socket's refusals arrive NAMED (`reason`,
   `failure_category`, `mic_interval: "closed"`). Before this the client read
   only `error`, so every one of them landed as "unknown". */
describe("named server refusals (HS-132-05)", () => {
  it("maps the server's failure_category vocabulary", () => {
    expect(
      streamFailure({ failure_category: "speech_session_refused" }),
    ).toBe("mic_interval_closed");
    expect(
      streamFailure({ failure_category: "speech_provider_failure" }),
    ).toBe("provider_failure");
    expect(streamFailure({ failure_category: "audio_floor_held" })).toBe(
      "audio_floor_held",
    );
    expect(streamFailure({ failure_category: "audio_floor_lost" })).toBe(
      "audio_floor_held",
    );
    expect(
      streamFailure({ failure_category: "transcription_unavailable" }),
    ).toBe("missing_model");
    expect(
      streamFailure({ failure_category: "transcription_failed" }),
    ).toBe("transcription_failed");
  });

  it("honors the closed interval on its own (Sol Amendment 3)", () => {
    expect(
      streamFailure({
        error: "The microphone session closed.",
        reason: "speech_session_cancelled",
        mic_interval: "closed",
      }),
    ).toBe("mic_interval_closed");
  });

  it("falls back to unknown only when the server named nothing", () => {
    expect(streamFailure({ error: "Connection lost." })).toBe("unknown");
  });

  it("states the refusal by name, never as prose", () => {
    expect(
      refusalCode({ reason: "speech_child_budget_exhausted" }),
    ).toBe("SPEECH CHILD BUDGET EXHAUSTED");
    expect(refusalCode({ failure_category: "audio_floor_lost" })).toBe(
      "AUDIO FLOOR LOST",
    );
    expect(refusalCode({ error: "Connection lost." })).toBeNull();
  });
});

/* HS-202-02 job 1 — the microphone failure names the microphone.
   The sober eye (docs/internal/surface-inventory-2026-09-20/04-sober-eye.md,
   Job 1 and rank 7) clicked "Click to speak" on a machine with no microphone
   and read: "Dictation did not finish. Your draft remains editable. Retry the
   capture." The word microphone was missing and the offered recovery could
   never work. `getUserMedia` rejects with a DOMException the mapper never
   read: NotFoundError (no device), NotReadableError (the device is held),
   SecurityError (the origin is refused). */
describe("the microphone failures are named (HS-202-02)", () => {
  it("names a missing device instead of falling to unknown", () => {
    expect(dictationFailure(new DOMException("no device", "NotFoundError"))).toBe(
      "no_microphone",
    );
    expect(
      dictationFailure(new DOMException("no device", "DevicesNotFoundError")),
    ).toBe("no_microphone");
    expect(
      dictationFailure(new DOMException("constraints", "OverconstrainedError")),
    ).toBe("no_microphone");
    // Measured on the walk host: headless Chromium with no audio device
    // rejects `getUserMedia` with this name, not NotFoundError.
    expect(
      dictationFailure(new DOMException("Not supported", "NotSupportedError")),
    ).toBe("no_microphone");
  });

  /* Astra's counsel finding 7 on PR #595: `NotReadableError` covers a
     hardware failure as well as another owner, so it must not be reported
     as `audio_floor_held` — a name that asserts an owner the exception
     never established (and one the hub's first-value vocabulary
     rejects). */
  it("names a device that would not start, without naming a culprit", () => {
    expect(
      dictationFailure(new DOMException("in use", "NotReadableError")),
    ).toBe("microphone_unavailable");
    expect(
      dictationFailure(new DOMException("in use", "TrackStartError")),
    ).toBe("microphone_unavailable");
    expect(DICTATION_FAILURES.microphone_unavailable.message).toMatch(
      /could not start/i,
    );
    expect(DICTATION_FAILURES.microphone_unavailable.message).not.toMatch(
      /another (source|application) holds/i,
    );
  });

  it("reads a refused origin as a permission refusal", () => {
    expect(dictationFailure(new DOMException("insecure", "SecurityError"))).toBe(
      "permission_denied",
    );
  });

  it("says the word microphone on every device failure", () => {
    for (const failure of [
      "no_microphone",
      "microphone_unavailable",
      "permission_denied",
      "audio_floor_held",
      "mic_interval_closed",
    ] as const) {
      expect(DICTATION_FAILURES[failure].message).toMatch(/microphone/i);
    }
  });

  it("offers a recovery that can work, and claims only what was observed", () => {
    const contract = DICTATION_FAILURES.no_microphone;
    expect(contract.retry).toBe(true);
    expect(contract.setup).toBe(true);
    // The browser handed back no device; that is NOT proof the hardware
    // is absent, so the copy does not say so (counsel finding 7).
    expect(contract.message).toMatch(/browser gave no microphone/i);
    expect(contract.message).not.toMatch(/was found on this device/i);
    expect(applicableActions("no_microphone", { draftPresent: true })).toEqual([
      "retry",
      "copy",
      "keep_as_note",
      "setup",
    ]);
  });
});
