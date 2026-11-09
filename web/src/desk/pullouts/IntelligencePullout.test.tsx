// Betterment daily D4: the Today window is one page (no wings). The wing
// cases are parked in _parked/IntelligencePullout.wings.test.tsx.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { openIntelligence } from "../intelligenceNavigation";
import { IntelligencePullout } from "./IntelligencePullout";
import { PULLOUT_CONTENT } from "./registry";
import { useDesk } from "../store";

const chair = vi.hoisted(() => ({ openChairWindow: vi.fn() }));
vi.mock("../chair/chairWindows", async (original) => ({
  ...await original<typeof import("../chair/chairWindows")>(),
  openChairWindow: chair.openChairWindow,
}));
vi.mock("./views/TodayView", () => ({
  TodayView: ({ sinceRequest }: { sinceRequest: number }) => {
    const [draft, setDraft] = useState("");
    return <><div className="desk-surface-body" data-testid="retained-today" data-since={sinceRequest}>
      <input aria-label="Kept draft" value={draft} onChange={(event) => setDraft(event.target.value)} />
    </div><SurfaceFooter verbs={<button>Today action</button>} /></>;
  },
}));
const object = {
  kind: "intelligence" as const,
  id: "desk",
  title: "Today",
  ref: { kind: "intelligence" as const, id: "desk", name: "Today" },
};

describe("Betterment D4: the Today window is one page", () => {
  beforeEach(() => {
    localStorage.clear();
    chair.openChairWindow.mockReset();
    vi.useRealTimers();
  });

  it("registers the Today window in the pullout registry", () => {
    expect(PULLOUT_CONTENT.intelligence).toBe(IntelligencePullout);
  });

  it("opens on Today with no wings", () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    expect(screen.getByTestId("retained-today")).toBeTruthy();
    expect(screen.queryByRole("group", { name: "Intelligence view" })).toBeNull();
    for (const wing of ["Day", "Brief", "Follow-through", "Decisions"]) {
      expect(screen.queryByRole("button", { name: wing })).toBeNull();
    }
  });

  it("a decision drill opens the Decisions window; Today keeps its state", async () => {
    const realOpen = useDesk.getState().openSurfaceWindow;
    const openSurfaceWindow = vi.fn();
    useDesk.setState({ openSurfaceWindow } as never);
    const view = render(<IntelligencePullout object={object} onClose={() => {}} />);
    try {
      fireEvent.change(screen.getByRole("textbox", { name: "Kept draft" }), { target: { value: "Return context" } });
      act(() => openIntelligence({ view: "receipts", decisionId: "dec-1" }));
      expect(openSurfaceWindow).toHaveBeenCalledWith("open-decisions", "decision:dec-1");
      expect(screen.getByRole("textbox", { name: "Kept draft" })).toHaveValue("Return context");
    } finally { view.unmount(); useDesk.setState({ openSurfaceWindow: realOpen } as never); }
  });

  it("Show since yesterday opens Today with the fold asked open; Follow-through opens the Needs-you window", async () => {
    const realOpen = useDesk.getState().openPullout;
    const openPullout = vi.fn();
    useDesk.setState({ openPullout } as never);
    try {
      render(<IntelligencePullout object={object} onClose={() => {}} />);
      act(() => openIntelligence({ view: "brief" }));
      await waitFor(() => expect(Number(screen.getByTestId("retained-today").getAttribute("data-since"))).toBeGreaterThan(0));
      expect(openPullout).toHaveBeenCalledWith("intelligence:desk");
      openPullout.mockClear();
      openIntelligence({ view: "follow-through", followThroughId: "ai-1" });
      await waitFor(() => expect(chair.openChairWindow).toHaveBeenCalledWith("chair:needs"));
      expect(openPullout).not.toHaveBeenCalled();
    } finally { useDesk.setState({ openPullout: realOpen } as never); }
  });
});
