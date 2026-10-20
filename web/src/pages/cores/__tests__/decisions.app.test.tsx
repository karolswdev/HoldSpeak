/** The Decisions window (Betterment P4, projects RECIPE): the desk's
 * decisions in a window of their own, the view Today ▸ Decisions shows.
 * The hub's answer is the recorded wire of the honest-faces seed
 * (tests/integration/test_face_wire_fences.py); only `apiFetch` is a double. */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import HONEST_DECISIONS from "../../../test/wire/decisions.honest-faces.wire.json";

const apiFetch = vi.hoisted(() => vi.fn());
vi.mock("../../../lib/api", () => ({
  apiFetch,
  readableError: (reason: unknown) => reason instanceof Error ? reason.message : "Request failed",
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", subscribe: () => () => undefined }),
}));

import { DecisionsCore } from "../DecisionsCore";
import { DESK_APPLICATIONS } from "../../../desk/applications";

describe("P4: the Decisions window", () => {
  it("draws the desk's decisions from the hub's read, by their words", async () => {
    apiFetch.mockImplementation(async () => structuredClone(HONEST_DECISIONS.wire));
    const { container } = render(<DecisionsCore />);
    await screen.findByText("Freeze the old ledger on Nov 5");
    expect(apiFetch).toHaveBeenCalledWith("/api/decision-records?limit=100&offset=0");
    expect(container.querySelectorAll("[data-testid=decisions-row]")).toHaveLength(1);
    expect(screen.getByTestId("decisions-window")).toBeTruthy();
  });

  it("is an application the Go menu lists, with a window of its own", async () => {
    const app = DESK_APPLICATIONS.find((a) => a.action === "open-decisions")!;
    expect(app.windowId).toBe("surface-decisions");
    expect(app.go?.group).toBe("daily");
    const loaded = await app.surface!.load();
    expect(loaded.default).toBe(DecisionsCore);
  });
});
