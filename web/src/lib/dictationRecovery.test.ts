import { describe, expect, it } from "vitest";
import { ApiError } from "./api";
import {
  DICTATION_FAILURES,
  applicableActions,
  dictationFailure,
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
      permission_denied: ["copy", "keep_as_note", "setup"],
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

  it("offers an alternate Runs-on only for destination failures", () => {
    const alternates = Object.entries(DICTATION_FAILURES)
      .filter(([, contract]) => contract.alternateRunsOn)
      .map(([failure]) => failure)
      .sort();
    expect(alternates).toEqual([
      "delivery_conflict",
      "missing_model",
      "timeout",
    ]);
  });
});
