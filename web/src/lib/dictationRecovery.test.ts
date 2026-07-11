import { describe, expect, it } from "vitest";
import { ApiError } from "./api";
import { DICTATION_FAILURES, dictationFailure } from "./dictationRecovery";

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
});
