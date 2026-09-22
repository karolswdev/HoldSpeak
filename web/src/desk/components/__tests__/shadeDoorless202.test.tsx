/* HS-202-06 — the owner's sitting (2026-09-21): "I click on 'Open',
 * nothing happens." A finished receipt draws Open only when it has a door;
 * a pipeline receipt with nothing behind it draws no verb at all. */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SystemShade } from "../SystemShade";

vi.mock("../../projections", () => ({
  useProjections: () => ({
    projections: [
      {
        id: "pipeline:ev-sweep",
        title: "SWEEP",
        subject_label: "Heartbeat",
        subject_ref: "service:HeartbeatService",
        timestamp: new Date().toISOString(),
        attention_state: "resolved",
        source_kind: "pipeline_event",
        source_id: "ev-sweep",
        detail_url: "/cadence",
        outcome: "completed",
      },
      {
        id: "pipeline:ev-read",
        title: "READ project_list",
        subject_label: "Project",
        timestamp: new Date().toISOString(),
        attention_state: "resolved",
        source_kind: "pipeline_event",
        source_id: "ev-read",
        detail_url: "",
        outcome: "completed",
      },
    ],
    counts: { needs_attention: 0, receipts: 2 },
    refresh: vi.fn().mockResolvedValue(undefined),
    present: vi.fn(),
  }),
}));

vi.mock("../../../lib/api", () => ({
  apiFetch: vi.fn().mockResolvedValue({ items: [] }),
}));

const shell = vi.hoisted(() => ({ openSurfaceWhenReady: vi.fn(), openPrimitive: vi.fn() }));
vi.mock("../../shell", async (original) => ({
  ...(await original<typeof import("../../shell")>()),
  openSurfaceWhenReady: shell.openSurfaceWhenReady,
  openPrimitive: shell.openPrimitive,
}));

describe("SystemShade — a verb only where a door exists (sitting defect 1)", () => {
  it("draws Open for the sweep (Rhythm face) and no Open for a doorless receipt", () => {
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);
    expect(screen.getByText("SWEEP")).toBeTruthy();
    expect(screen.getByText("READ PROJECT_LIST")).toBeTruthy();
    const open = screen.getAllByRole("button", { name: "Open" });
    expect(open).toHaveLength(1);
    // Pressing it goes somewhere: the Rhythm face, never the pull-out opener.
    fireEvent.click(open[0]);
    expect(shell.openSurfaceWhenReady).toHaveBeenCalledWith("configure-cadence", "service:HeartbeatService");
    expect(shell.openPrimitive).not.toHaveBeenCalled();
  });
});
