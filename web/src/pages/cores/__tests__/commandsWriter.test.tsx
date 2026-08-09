// HS-130-07 — the command board is ONE honest writer of macro `items`.
// A checkbox toggle can no longer round-trip (and clobber) the whole macro
// array, and every write carries the `_revision` it read.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CommandsCore } from "../CommandsCore";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
}));
vi.mock("../../../desk/shell", () => ({ openSurfaceOr: vi.fn() }));

type Init = { method?: string; json?: any };

function callsTo(path: string): Init[] {
  return mocks.apiFetch.mock.calls
    .filter((c: unknown[]) => String(c[0]) === path)
    .map((c: unknown[]) => (c[1] ?? {}) as Init);
}

const SETTINGS = {
  _revision: "rev-1",
  dictation: {
    macros: {
      enabled: true,
      items: [
        { keyword: "docs", action: { kind: "open_url", payload: "https://x" } },
      ],
    },
  },
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiFetch.mockImplementation((path: string, init?: Init) => {
    if (path === "/api/settings" && init?.method === "PUT")
      return Promise.resolve({ settings: SETTINGS });
    if (path === "/api/settings") return Promise.resolve(SETTINGS);
    return Promise.resolve({});
  });
});

describe("CommandsCore is one honest items-writer (HS-130-07)", () => {
  it("has no persistent enablement toggle — it links to Settings", async () => {
    render(<CommandsCore />);
    await screen.findByText("“docs”");
    // The old "Commands enabled" checkbox is gone (Settings owns enablement).
    expect(
      screen.queryByRole("checkbox", { name: /Commands enabled/i }),
    ).toBeNull();
    // The effective state is shown and a link opens Settings.
    expect(screen.getByText("Commands on")).toBeVisible();
    expect(
      screen.getByRole("button", { name: /Manage in Settings/i }),
    ).toBeVisible();
  });

  it("deleting a macro PUTs items-only with the revision — never the enabled bit", async () => {
    render(<CommandsCore />);
    await screen.findByText("“docs”");
    // ConfirmVerb: arm, then confirm.
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete?" }));

    await waitFor(() =>
      expect(
        callsTo("/api/settings").filter((c) => c.method === "PUT"),
      ).toHaveLength(1),
    );
    const [put] = callsTo("/api/settings").filter((c) => c.method === "PUT");
    // The write carries ONLY items (no `enabled` — no clobber) + the revision.
    expect(put.json).toEqual({
      dictation: { macros: { items: [] } },
      _revision: "rev-1",
    });
    expect(put.json.dictation.macros).not.toHaveProperty("enabled");
  });
});
