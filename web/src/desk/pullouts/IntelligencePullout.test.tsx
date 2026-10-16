import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { FootSlotContext } from "../surface/foot";
import { IntelligencePullout } from "./IntelligencePullout";
import { PULLOUT_CONTENT } from "./registry";

vi.mock("./views/BriefView", () => ({
  BriefView: ({ header, onOpenFollowThrough }: { header: React.ReactNode; onOpenFollowThrough: (id: string) => void }) => {
    const [draft, setDraft] = useState("");
    return <><div className="desk-surface-body" data-testid="retained-brief">{header}
      <input aria-label="Kept draft" value={draft} onChange={(event) => setDraft(event.target.value)} />
      <button onClick={() => onOpenFollowThrough("held-source")}>Brief source</button>
    </div><SurfaceFooter verbs={<button>Brief action</button>} /></>;
  },
}));

const object = {
  kind: "intelligence" as const,
  id: "desk",
  title: "Intelligence",
  ref: { kind: "intelligence" as const, id: "desk", name: "Intelligence" },
};

describe("HS-128-01 Intelligence pullout", () => {
  beforeEach(() => localStorage.clear());

  it("registers the Intelligence primitive in the pullout registry", () => {
    expect(PULLOUT_CONTENT.intelligence).toBe(IntelligencePullout);
  });

  it("opens on Day (the day as a timeline) and changes the active view", () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    // PHILO-17 (owner pick, concept C): the Today window opens on the day.
    expect(screen.getByRole("button", { name: "Day" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    fireEvent.click(screen.getByRole("button", { name: "Follow-through" }));

    expect(
      screen.getByRole("button", { name: "Follow-through" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("restores the last selected view after reopening", () => {
    const first = render(
      <IntelligencePullout object={object} onClose={() => {}} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Decisions" }));
    first.unmount();

    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(
      screen.getByRole("searchbox", { name: "Search decisions" }),
    ).toBeInTheDocument();
  });

  it("keeps Brief draft and scroll through source inspection while hiding inactive footer actions", async () => {
    localStorage.setItem("hs.desk.intelligence-view", "brief");
    const foot = document.createElement("footer");
    document.body.appendChild(foot);
    const view = render(<FootSlotContext.Provider value={foot}><IntelligencePullout object={object} onClose={() => {}} /></FootSlotContext.Provider>);
    try {
      fireEvent.change(screen.getByRole("textbox", { name: "Kept draft" }), { target: { value: "Return context" } });
      const body = screen.getByTestId("retained-brief");
      body.scrollTop = 312;
      fireEvent.scroll(body);
      fireEvent.click(screen.getByRole("button", { name: "Brief source" }));
      expect(screen.queryByRole("textbox", { name: "Kept draft" })).toBeNull();
      expect(screen.queryByRole("button", { name: "Brief action" })).toBeNull();
      expect(screen.getByRole("button", { name: "Follow-through" })).toHaveAttribute("aria-pressed", "true");
      expect([...foot.querySelectorAll(".surface-footer-layout")].filter((node) => !node.closest('[style*="display: none"]'))).toHaveLength(1);
      body.scrollTop = 0;
      fireEvent.click(screen.getByRole("button", { name: "Brief" }));
      await waitFor(() => expect(screen.getByRole("textbox", { name: "Kept draft" })).toHaveValue("Return context"));
      expect(screen.getByTestId("retained-brief")).toBe(body);
      expect(body.scrollTop).toBe(312);
      expect(screen.getAllByRole("button", { name: "Brief action" })).toHaveLength(1);
      expect([...foot.querySelectorAll(".surface-footer-layout")].filter((node) => !node.closest('[style*="display: none"]'))).toHaveLength(1);
      expect(screen.queryByRole("button", { name: "Retry read" })).toBeNull();
    } finally { view.unmount(); foot.remove(); }
  });
});
