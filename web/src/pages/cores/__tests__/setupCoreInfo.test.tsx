import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SetupCore } from "../SetupCore";

const inventory = {
  rows: [
    { id: "speech", kind: "speech", label: "Speech", state: "works", action: null },
    { id: "connection:github:not-found", kind: "account", label: "GitHub", state: "does_not_work", reason: "No GitHub account was found on this Mac" },
  ],
  owner_name: "Karol",
  people: [],
  suggestions: [],
  first_run: false,
};

function response(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
}

afterEach(() => vi.unstubAllGlobals());

describe("SetupCore", () => {
  it("uses the same producer-backed Setup face after first launch", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (path.endsWith("/api/setup/found")) return response(inventory);
      if (path.endsWith("/api/setup/lan")) return response({ rows: [] });
      if (path.endsWith("/api/settings")) return response({ owner: { name: "Karol", aliases: [] }, _revision: "1" });
      return response({});
    }));

    render(<SetupCore />);
    const face = await screen.findByTestId("setup-face");
    expect(face).toHaveTextContent("Ready, Karol.");
    expect(face).toHaveTextContent("Not found");
  });

  it("does not reopen the retired runtime docs when inventory is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith("/api/setup/found")) return Promise.reject(new Error("Setup inventory is unavailable"));
      return response({});
    }));

    render(<SetupCore />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Setup inventory is unavailable");
    expect(screen.queryByText("Readiness checks")).toBeNull();
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
  });
});
