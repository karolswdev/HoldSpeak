import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api.js";

afterEach(() => vi.unstubAllGlobals());

describe("device sitting API", () => {
  it("sends the LAN intent when creating a native sitting", async () => {
    const fetch = vi.fn(async () => ({
      ok: true,
      json: async () => ({ id: "s1" }),
    }));
    vi.stubGlobal("fetch", fetch);

    await api.createSitting("ios-flagship-smoke", null, true);

    expect(fetch).toHaveBeenCalledOnce();
    const [path, options] = fetch.mock.calls[0];
    expect(path).toBe("/api/sittings");
    expect(JSON.parse(options.body)).toEqual({
      pack: "ios-flagship-smoke",
      deck: null,
      lan: true,
    });
  });

  it("posts implementation-bound device attestation", async () => {
    const fetch = vi.fn(async () => ({ ok: true, json: async () => ({ id: "d1" }) }));
    vi.stubGlobal("fetch", fetch);
    const attestation = {
      target: "ios_flagship_swift",
      form_factor: "ipad",
      device_name: "Karol's iPad",
      os_version: "iPadOS 19",
      bundle_id: "dev.holdspeak.flagship",
      build_number: "42",
      install_source: "Xcode",
      pairing_verified: true,
    };

    await api.createDeviceSession("s1", attestation);

    const [path, options] = fetch.mock.calls[0];
    expect(path).toBe("/api/sittings/s1/device-sessions");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual(attestation);
  });
});
