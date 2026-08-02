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
  it("renders the ledger facts as wire tokens and links needs-you rows to the system shade", () => {
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

    const { container } = render(<ProcessCore />);

    // HS-111-06: section heads are count tokens; kinds are the wire
    // tokens themselves; state is a surface-token, never a pill.
    expect(screen.getByText("NEEDS YOU 1")).toBeTruthy();
    expect(screen.getByText(/PROCESS\.SPAWN · agent:build/)).toBeTruthy();
    expect(
      screen.getByText(/owner · node:studio · build the surface · launch:launch_1/),
    ).toBeTruthy();
    expect(container.querySelector(".signal-status")).toBeNull();
    const answer = screen.getByRole("link", { name: "ANSWER" });
    expect(answer).toHaveAttribute("href", "/#attention");
    fireEvent.click(answer);
    expect(activate).toHaveBeenCalledOnce();
  });

  it("renders every section head at zero — an instrument, never a void", () => {
    useProcessWindow.setState({
      sections: sections.map((section) => ({ ...section, rows: [] })),
      loading: false,
      inflight: false,
      error: "",
      started: true,
    });

    render(<ProcessCore />);

    for (const head of [
      "NEEDS YOU 0",
      "RUNNING 0",
      "WAITING 0",
      "UNKNOWN 0",
      "RECENTLY ENDED 0",
    ]) {
      expect(screen.getByText(head)).toBeTruthy();
    }
    expect(screen.getByText(/KERNEL · CURSOR/)).toBeTruthy();
  });
});
