import { act, fireEvent, render, screen, within } from "@testing-library/react";
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
  it("draws the runs as a dense list (window grammar) and opens Desk memory for a run that needs him", () => {
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

    // Window grammar (2026-10-24): the toolbar, then one dense row per run:
    // the operation in words, its target, where it runs, a dot and a word.
    expect(screen.getByRole("toolbar", { name: "Processes" })).toBeTruthy();
    const rowEl = container.querySelector("[data-testid=process-row]") as HTMLElement;
    expect(rowEl.textContent).toContain("Process spawn");
    expect(screen.getByTestId("process-target").textContent).toBe("agent:build");
    // W4 (the words): who and where in words; the wire's ids are the hover title.
    const where = screen.getByText("You · Studio");
    expect(where.getAttribute("title")).toBe("owner · node:studio");
    expect(container.textContent).not.toMatch(/Node:/);
    expect(screen.getByTestId("process-state").textContent).toBe("Needs you");
    expect(container.textContent).not.toMatch(/PROCESS\.SPAWN/);
    expect(container.querySelector(".signal-status")).toBeNull();
    // The status bar says it in warm words, never a zero.
    expect(screen.getByTestId("process-status").textContent).toContain("1 needs you");
    expect(screen.getByTestId("process-status").textContent).not.toMatch(/\b0\b/);
    // Selecting the run puts its one verb in the status bar.
    fireEvent.click(within(rowEl).getAllByRole("button")[0]);
    fireEvent.click(screen.getByTestId("process-answer"));
    expect(activate).toHaveBeenCalledOnce();
  });

  it("names the engine the hub resolved for an inference placement (W5-WORDS)", () => {
    const run: ProcessRow = {
      ...row, operationId: "op_infer", correlationId: "op_infer", kind: "inference.invoke",
      placement: "node:inference-d380f9fc7c6dc84f", placementLabel: "Studio engine",
      state: "succeeded", latestEventType: "operation.succeeded",
    };
    useProcessWindow.setState({
      sections: sections.map((section) => section.id === "recently-ended" ? { ...section, rows: [run] } : { ...section, rows: [] }),
      loading: false, inflight: false, error: "", started: true,
    });
    const { container } = render(<ProcessCore />);
    expect(screen.getByText("You · Studio engine").getAttribute("title")).toBe("owner · node:inference-d380f9fc7c6dc84f");
    expect(container.textContent).not.toMatch(/inference-d380/);
  });

  it("shows one truthful empty line, then the populated list", () => {
    useProcessWindow.setState({
      sections: sections.map((section) => ({ ...section, rows: [] })),
      loading: false,
      inflight: false,
      error: "",
      started: true,
    });

    render(<ProcessCore />);

    expect(screen.getByText("No runs yet")).toBeTruthy();
    // DELIGHT 2: the Processes object and one line; nothing to make here.
    const object = document.querySelector('.surface-state[data-object="process"]') as HTMLElement;
    expect(object.querySelector(".surface-state-sprite")?.getAttribute("src")).toMatch(/cartridge\.png$/);
    expect(object.querySelector("button")).toBeNull();
    expect(screen.queryByTestId("process-row")).toBeNull();
    expect(screen.getByTestId("process-status").textContent).toBe("Watching");
    expect(screen.queryByText(/CURSOR/)).toBeNull();

    act(() => useProcessWindow.setState({ sections }));
    expect(screen.getAllByTestId("process-row")).toHaveLength(1);
    expect(screen.queryByText("No runs yet")).toBeNull();
  });
});

describe("ProcessCore: a long operation name wraps in its cell (PHILO-17 desk sweep)", () => {
  it("may break after each dot and underscore, and reads whole", async () => {
    const { breakableKind } = await import("../ProcessCore");
    const { container } = render(<span>{breakableKind("channel.save_destination")}</span>);
    expect(container.textContent).toBe("channel.save_destination");
    expect(container.querySelectorAll("wbr")).toHaveLength(2);
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
    const lines = [...container.querySelectorAll("[data-testid=process-row]")].map((li) => li.textContent);
    expect(lines).toHaveLength(2);
    expect(new Set(lines).size).toBe(2);
    expect(lines.some((l) => /Decision create.*Freeze the old ledger on Nov 5/.test(l ?? ""))).toBe(true);
    expect(lines.some((l) => /Decision create.*Adopt OpenTelemetry/.test(l ?? ""))).toBe(true);
    // The name is its own element, so the face can give it room (glass fences its width).
    expect([...container.querySelectorAll("[data-testid=process-target]")].map((e) => e.textContent)).toEqual(
      ["Freeze the old ledger on Nov 5", "Adopt OpenTelemetry"]);
    expect(container.textContent).not.toMatch(/decision_[0-9a-f]/);
  });
});

describe("W4 (the words): who and where a process ran", () => {
  it("never shows a machine id", async () => {
    const { placementWords, principalWords, shownTarget } = await import("../ProcessCore");
    expect(placementWords("node:inference-d380f9fc7c6dc84f")).toBe("Engine");
    expect(placementWords("node:local")).toBe("This Mac");
    expect(placementWords("node:hub-project-writer")).toBe("Hub");
    expect(principalWords("owner-session")).toBe("You");
    expect(principalWords("local-owner")).toBe("You");
    expect(shownTarget({ kind: "connection.recheck", target: "connection:github" })).toBe("GitHub");
  });
});

describe("Processes names each run by what it did (atlas pass 3, defect 8)", () => {
  it("shows the hub's label, and sentence words from the name when an older hub sends none", () => {
    const done = (id: string, extra: Partial<ProcessRow>): ProcessRow => ({ ...row, operationId: id, correlationId: id,
      latestEventType: "", state: "succeeded", target: "", ...extra });
    useProcessWindow.setState({
      sections: [{ id: "recently-ended", label: "Recently ended", rows: [
        done("op_lan", { kind: "setup.lan.scan", label: "Checked the LAN" }),
        done("op_old", { kind: "project.watch.pause" }),
      ] }],
      loading: false, inflight: false, error: "", started: true,
    });
    const { container } = render(<ProcessCore />);
    const names = [...container.querySelectorAll("[data-testid=process-row] .object-list-name-word")].map((e) => e.textContent);
    expect(names).toEqual(["Checked the LAN", "Project watch pause"]);
    expect(container.textContent).not.toMatch(/Setup lan scan/);
    // At 393 the fold line keeps the clock: each row says how much room
    // Where and Started need, and For gives up the rest (an ellipsis).
    const first = container.querySelector("[data-testid=process-row]") as HTMLElement;
    expect(first.style.getPropertyValue("--process-facts")).toMatch(/^calc\(\d+ch \+ 24px\)$/);
  });
});

