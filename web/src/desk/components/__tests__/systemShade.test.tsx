// HS-101 B6 — the system shade: honest groups from real feeds,
// zero says zero, Escape closes, Desk memory one verb away.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SystemShade } from "../SystemShade";

const present = vi.fn();
const refresh = vi.fn().mockResolvedValue(undefined);

vi.mock("../../projections", () => ({
  useProjections: () => ({
    projections: [
      {
        id: "p1",
        title: "Send to Slack: the standup recap",
        subject_label: "Actuator",
        timestamp: new Date().toISOString(),
        attention_state: "needs_attention",
        detail_url: "/x",
        outcome: "proposed",
      },
      {
        id: "p2",
        title: "Dictation delivered",
        subject_label: "Dictation",
        timestamp: new Date().toISOString(),
        attention_state: "quiet",
        detail_url: "/y",
        outcome: "completed",
      },
    ],
    counts: { needs_attention: 1, receipts: 1 },
    refresh,
    present,
  }),
}));

vi.mock("../../../lib/api", () => ({
  apiFetch: vi.fn().mockResolvedValue({ items: [] }),
}));

describe("SystemShade (canon §6.1)", () => {
  it("groups honestly: needs-you verbs inline, finished with Open, learned zero says zero", async () => {
    const onClose = vi.fn();
    const onOpenMemory = vi.fn();
    render(
      <SystemShade open onClose={onClose} onOpenMemory={onOpenMemory} />,
    );
    expect(screen.getByText(/Needs you/)).toBeTruthy();
    expect(
      screen.getByText("Send to Slack: the standup recap"),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: "Acknowledge" })).toBeTruthy();
    expect(screen.getByText("Dictation delivered")).toBeTruthy();
    await waitFor(() =>
      expect(screen.getByText("No corrections taught yet")).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Acknowledge" }));
    expect(present).toHaveBeenCalledWith("p1", "acknowledge");
    fireEvent.click(screen.getByRole("button", { name: "Desk memory" }));
    expect(onOpenMemory).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  it("closed renders nothing; Escape closes when open", () => {
    const onClose = vi.fn();
    const { container, rerender } = render(
      <SystemShade open={false} onClose={onClose} onOpenMemory={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
    rerender(
      <SystemShade open onClose={onClose} onOpenMemory={() => {}} />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
