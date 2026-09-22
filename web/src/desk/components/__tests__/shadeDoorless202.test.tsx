/* HS-202-06 — the owner's sitting (2026-09-21): "I click on 'Open',
 * nothing happens." A finished receipt draws Open only when it has a door;
 * a pipeline receipt with nothing behind it draws no verb at all. */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SystemShade } from "../SystemShade";

vi.mock("../../projections", () => ({
  useProjections: () => ({
    projections: [
      {
        id: "pipeline:ev-sweep",
        title: "SWEEP",
        subject_label: "Heartbeat",
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

describe("SystemShade — a verb only where a door exists (sitting defect 1)", () => {
  it("draws Open for the sweep (Rhythm face) and no Open for a doorless receipt", () => {
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);
    expect(screen.getByText("SWEEP")).toBeTruthy();
    expect(screen.getByText("READ PROJECT_LIST")).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Open" })).toHaveLength(1);
  });
});
