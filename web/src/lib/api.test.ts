import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "./api";

describe("apiFetch", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("serializes JSON and returns typed JSON", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetcher);
    await expect(
      apiFetch<{ ok: boolean }>("/api/example", {
        method: "POST",
        json: { name: "Desk" },
      }),
    ).resolves.toEqual({ ok: true });
    expect(fetcher.mock.calls[0][1].body).toBe('{"name":"Desk"}');
  });

  it("turns a server detail into a user-readable typed error", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: "Model unavailable" }), {
            status: 503,
            headers: { "content-type": "application/json" },
          }),
        ),
    );
    const error = await apiFetch("/api/example").catch((reason) => reason);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 503, message: "Model unavailable" });
  });
});
