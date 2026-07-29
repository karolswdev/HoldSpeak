import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  announceLauncher,
  retractLauncher,
} from "../../../desk/components/DeskWindow";
import { useProcessWindow } from "../../../desk/processWindow";
import type {
  ProcessRow,
  ProcessSection,
} from "../../../desk/processWindowReducer";
import { ProcessCore } from "../ProcessCore";

const row: ProcessRow = {
  operationId: "op_waiting",
  parentOperationId: "",
  correlationId: "op_waiting",
  principal: "owner",
  kind: "process.spawn",
  target: "agent:build",
  placement: "node:studio",
  state: "waiting",
  domainState: "admitted",
  timestamp: "2026-07-29T00:00:00Z",
  refs: ["launch:launch_1"],
  head: "build the surface",
  privacyClass: "private",
  latestEventType: "operation.awaiting_decision",
  children: [],
};

const sections: ProcessSection[] = [
  { id: "needs-you", label: "Needs you", rows: [row] },
  { id: "running", label: "Running", rows: [] },
  { id: "waiting", label: "Waiting", rows: [] },
  { id: "unknown", label: "Unknown", rows: [] },
  { id: "recently-ended", label: "Recently ended", rows: [] },
];

afterEach(() => {
  retractLauncher("attention");
  useProcessWindow.getState().stop();
});

describe("ProcessCore", () => {
  it("renders the projected facts and links needs-you rows to the system shade", () => {
    const activate = vi.fn();
    announceLauncher({
      id: "attention",
      label: "Desk memory",
      glyph: "◎",
      open: false,
      activate,
    });
    useProcessWindow.setState({
      sections,
      loading: false,
      inflight: false,
      error: "",
      started: true,
    });

    render(<ProcessCore />);

    expect(screen.getByText("Needs you · 1")).toBeTruthy();
    expect(screen.getByText(/Process spawn · agent:build/)).toBeTruthy();
    expect(screen.getByText(/owner · node:studio · build the surface · launch:launch_1/)).toBeTruthy();
    const review = screen.getByRole("link", { name: "Review" });
    expect(review).toHaveAttribute("href", "/#attention");
    fireEvent.click(review);
    expect(activate).toHaveBeenCalledOnce();
  });
});
