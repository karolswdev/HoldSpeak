/* PHILO-15 02 — the key's wire: Check sends it for one call; Define sends
 * it as the write-only secret the Model Library hands to the key store. */

import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>(
    "../../../lib/api",
  );
  return { ...actual, apiFetch };
});

import { checkEndpoint, defineEndpoint } from "../api";
import { endpointDraft } from "../endpointDraft";

const URL_ = "http://192.168.1.43:8080/v1";

beforeEach(() => {
  apiFetch.mockReset();
});

describe("checkEndpoint", () => {
  it("sends api_key when a key is typed", async () => {
    apiFetch.mockResolvedValue({ ok: true, models: ["m"], detail: "" });
    await checkEndpoint(URL_, " local ");
    expect(apiFetch).toHaveBeenCalledWith("/api/setup/discover-models", {
      method: "POST",
      json: { base_url: URL_, api_key: "local" },
    });
  });

  it("sends no api_key when the field is empty", async () => {
    apiFetch.mockResolvedValue({ ok: true, models: ["m"], detail: "" });
    await checkEndpoint(URL_, "  ");
    expect(apiFetch.mock.calls[0][1]).toEqual({
      method: "POST",
      json: { base_url: URL_ },
    });
  });
});

describe("checkEndpoint reasons", () => {
  it("carries the key reason from a refusal", async () => {
    const { ApiError } = await import("../../../lib/api");
    apiFetch.mockRejectedValue(
      Object.assign(Object.create(ApiError.prototype), {
        message: "400",
        payload: { ok: false, models: [], detail: "Key has characters a header cannot carry.", reason: "key_invalid" },
      }),
    );
    const result = await checkEndpoint(URL_, "a b");
    expect(result.reason).toBe("key_invalid");
    expect(result.ok).toBe(false);
  });
});

describe("defineEndpoint", () => {
  const draft = (requiresKey: boolean) =>
    endpointDraft({ url: URL_, model: "m", requestId: "r", requiresKey });

  it("sends the key as the secret value", async () => {
    apiFetch.mockResolvedValue({ provider: { profile_id: "p", profile_revision: 1 } });
    await defineEndpoint(draft(true), "local");
    const body = apiFetch.mock.calls[0][1].json;
    expect(body.secret).toEqual({ value: "local" });
    expect(body.draft.requires_key).toBe(true);
  });

  it("sends secret null with no key", async () => {
    apiFetch.mockResolvedValue({ provider: { profile_id: "p", profile_revision: 1 } });
    await defineEndpoint(draft(false));
    const body = apiFetch.mock.calls[0][1].json;
    expect(body.secret).toBeNull();
    expect(body.draft.requires_key).toBe(false);
  });
});
