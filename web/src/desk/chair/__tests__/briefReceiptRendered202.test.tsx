/* HS-202-02 — Astra's counsel finding 2 on PR #595.
 *
 * "Generate's receipt cannot survive success: `setBrief(data)` replaces
 * the `!brief` branch that holds the receipt." The first round fenced the
 * receipt HELPER, which cannot see that. This fences the RENDERED
 * transition: press Generate on a desk with no brief, and read the foot
 * after the hub answers.
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

/** What `POST /api/brief/generate` answers. Items make the populated
 *  branch take over — the exact transition that ate the receipt. */
let generated: Record<string, unknown> = {
  id: "brief-1",
  headline: "The week ahead",
  generated_at: "2026-09-20T15:41:00",
  is_empty: false,
  sections: {
    changed: [{ id: "i1", text: "Close the reader flag", kind: "note" }],
    waiting: [{ id: "i2", text: "Name an owner", kind: "action" }],
  },
};

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
    const url = String(path);
    if (url === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 } as never;
    if (url.startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    // No brief yet: the `!brief` branch, with Generate on it.
    if (url.startsWith("/api/brief/latest")) return null as never;
    if (url === "/api/brief/generate" && (init as { method?: string })?.method === "POST")
      return generated as never;
    return null as never;
  });
}

describe("Generate is badged before and receipted after (counsel 2)", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    wire();
  });

  it("names the destination on the row, before the press", async () => {
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    expect(section.querySelector(".gadget-chip-egress")?.textContent).toBe(
      "THIS DEVICE",
    );
  });

  it("still shows the receipt after the brief arrives and fills the face", async () => {
    render(<ChairHome />);
    const generate = await screen.findByTestId("arrival-brief-generate");

    await act(async () => {
      generate.click();
    });

    const receipt = await screen.findByTestId("arrival-brief-receipt");
    expect(receipt.textContent).toMatch(/^Brief ready · 2 items · /);
    // The populated branch really did take over — this is the transition
    // that used to erase the receipt.
    expect(screen.queryByText("No brief yet")).toBeNull();
  });

  it("keeps the receipt when the brief has nothing untriaged", async () => {
    generated = { ...generated, is_empty: true, sections: {} };
    render(<ChairHome />);
    const generate = await screen.findByTestId("arrival-brief-generate");

    await act(async () => {
      generate.click();
    });

    await waitFor(() =>
      expect(screen.getByTestId("arrival-brief-receipt").textContent).toMatch(
        /^Brief ready · /,
      ),
    );
  });
});
