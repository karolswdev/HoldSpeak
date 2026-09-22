/* HS-202-06 — Astra's counsel on #600 (DO-NOT-RATIFY, P1): with Qlippy on
 * and no queued card, an attention projection with no door fell into the
 * card branch and threw `Cannot read properties of undefined (reading
 * 'frameType')`, outside every error boundary — the whole desk gone for a
 * notification. Rendered regression: the projection draws, offers no
 * "Review source", keeps Dismiss, and nothing throws. */
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AmbientLayer } from "./AmbientLayer";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../lib/api", () => ({
  ApiError: class extends Error {},
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));

vi.mock("../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

vi.mock("../desk/projections", () => {
  const state = {
    ambient: [
      {
        id: "actuator:proposal-1:proposed",
        projection_kind: "attention",
        subject_label: "Actuator",
        subject_ref: "proposal:proposal-1",
        title: "Send to Slack: the standup recap",
        summary: "",
        attention_state: "needs_attention",
        detail_url: "/",
        source_kind: "actuator_proposal",
        source_id: "proposal-1",
      },
    ],
    refreshAmbient: vi.fn(),
    present: vi.fn(),
  };
  const useProjections = Object.assign(
    (selector: (value: typeof state) => unknown) => selector(state),
    { getState: () => state },
  );
  return { useProjections };
});

describe("Qlippy — a doorless projection never enters the card branch", () => {
  it("renders the projection with Dismiss and no Review source, without throwing", async () => {
    mocks.apiFetch.mockImplementation((path: string) =>
      path === "/api/settings"
        ? Promise.resolve({ presence: { enabled: true, mascot: true } })
        : Promise.resolve({ success: true }),
    );
    render(<AmbientLayer />);
    await waitFor(() =>
      expect(screen.getByText("Send to Slack: the standup recap")).toBeTruthy(),
    );
    expect(screen.queryByRole("button", { name: "Review source" })).toBeNull();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeTruthy();
  });
});
