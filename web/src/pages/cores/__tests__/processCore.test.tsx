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
import { useDesk } from "../../../desk/store";
import { EMPTY_ITEMS, type Items } from "../../../desk/api";

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
      screen.getByText(/Owner · Node:studio/),
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

    // UX-CANON A8: countLabel strips the zero — section heads read
    // "NEEDS YOU" not "NEEDS YOU 0"; all five still render.
    for (const head of [
      "NEEDS YOU",
      "RUNNING",
      "WAITING",
      "UNKNOWN",
      "RECENTLY ENDED",
    ]) {
      expect(screen.getByText(head)).toBeTruthy();
    }
    expect(screen.getByText(/KERNEL · CURSOR/)).toBeTruthy();
  });
});

describe("ProcessCore names the target, never a raw id and never a blank (Astra, #869)", () => {
  it("names a record the desk holds, tokens one it does not, drops an echo", async () => {
    const { shownTarget } = await import("../ProcessCore");
    const items = { ...EMPTY_ITEMS, decision: [
      { kind: "decision", id: "decision_c9edf19564f8", title: "Freeze the old ledger on Nov 5" },
    ] } as unknown as Items;
    expect(shownTarget({ kind: "channel.save_destination", target: "desk:channel.save_destination" }, items)).toBe("");
    expect(shownTarget({ kind: "decision.create", target: "decision:decision_c9edf19564f8" }, items)).toBe("Freeze the old ledger on Nov 5");
    expect(shownTarget({ kind: "meeting.summarize", target: "meeting:9f8a7b6c5d4e" }, items)).toBe("Meeting 9f8a7b");
    expect(shownTarget({ kind: "note.update", target: "note:note_624495deb1f5" }, items)).toBe("Note 624495");
    expect(shownTarget({ kind: "process.spawn", target: "agent:build" }, items)).toBe("agent:build");
  });

  it("two decisions made in the same second read as two different rows", () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, decision: [
      { kind: "decision", id: "decision_c9edf19564f8", title: "Freeze the old ledger on Nov 5" },
      { kind: "decision", id: "decision_e8da87a9f184", title: "Adopt OpenTelemetry" },
    ] } as unknown as Items });
    const ended = (id: string, target: string): ProcessRow => ({ ...row, operationId: id, correlationId: id,
      latestEventType: "", state: "succeeded", kind: "decision.create", target, timestamp: "2026-10-05T16:12:34Z" });
    useProcessWindow.setState({
      sections: [{ id: "recently-ended", label: "Recently ended", rows: [
        ended("op_a", "decision:decision_c9edf19564f8"), ended("op_b", "decision:decision_e8da87a9f184")] }],
      loading: false, inflight: false, error: "", started: true,
    });
    const { container } = render(<ProcessCore />);
    const lines = [...container.querySelectorAll(".surface-ledger-rows > li")].map((li) => li.textContent);
    expect(lines).toHaveLength(2);
    expect(new Set(lines).size).toBe(2);
    expect(screen.getByText(/DECISION\.CREATE · Freeze the old ledger on Nov 5/)).toBeTruthy();
    expect(screen.getByText(/DECISION\.CREATE · Adopt OpenTelemetry/)).toBeTruthy();
    expect(container.textContent).not.toMatch(/decision_[0-9a-f]/);
  });
});
