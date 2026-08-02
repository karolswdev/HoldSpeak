// HS-111-11 — the PaneWell's xterm interior: mounts READ-ONLY, themed
// from the Signal Workbench tokens, full-repaint per snapshot, cursor
// parked from the pane geometry, search wired to the well-head gadget,
// and the honest stripped fallback when the wire has no raw stream.
// xterm itself is faked at the module seam — jsdom has no canvas; the
// smoke pins OUR wiring, not xterm's renderer.
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fakes = vi.hoisted(() => {
  class FakeTerminal {
    static instances: FakeTerminal[] = [];
    options: any;
    cols = 80;
    rows = 24;
    writes: string[] = [];
    resizes: Array<[number, number]> = [];
    onDataCalls = 0;
    selectionHandler: (() => void) | null = null;
    selection = "";
    host: HTMLElement | null = null;
    disposed = false;
    constructor(options: any) {
      this.options = options;
      FakeTerminal.instances.push(this);
    }
    loadAddon() {}
    open(host: HTMLElement) {
      this.host = host;
    }
    onData() {
      this.onDataCalls += 1;
      return { dispose() {} };
    }
    onSelectionChange(handler: () => void) {
      this.selectionHandler = handler;
      return { dispose() {} };
    }
    getSelection() {
      return this.selection;
    }
    write(data: string, done?: () => void) {
      this.writes.push(data);
      done?.();
    }
    resize(cols: number, rows: number) {
      this.cols = cols;
      this.rows = rows;
      this.resizes.push([cols, rows]);
    }
    scrollToBottom() {}
    dispose() {
      this.disposed = true;
    }
  }
  class FakeFitAddon {
    static fits = 0;
    activate() {}
    dispose() {}
    fit() {
      FakeFitAddon.fits += 1;
    }
  }
  class FakeSearchAddon {
    static calls: Array<{ query: string; options: any }> = [];
    activate() {}
    dispose() {}
    findNext(query: string, options: any) {
      FakeSearchAddon.calls.push({ query, options });
      return true;
    }
    clearDecorations() {}
  }
  return { FakeTerminal, FakeFitAddon, FakeSearchAddon };
});

vi.mock("@xterm/xterm", () => ({ Terminal: fakes.FakeTerminal }));
vi.mock("@xterm/addon-fit", () => ({ FitAddon: fakes.FakeFitAddon }));
vi.mock("@xterm/addon-search", () => ({ SearchAddon: fakes.FakeSearchAddon }));
vi.mock("@xterm/xterm/css/xterm.css", () => ({}));

import { PaneWell } from "../Surface";

const { FakeTerminal, FakeFitAddon, FakeSearchAddon } = fakes;

const COLORED = "[32mPASS[0m tests\nplain tail";

async function mountedTerminal(): Promise<InstanceType<typeof FakeTerminal>> {
  await waitFor(() => expect(FakeTerminal.instances.length).toBe(1));
  return FakeTerminal.instances[0];
}

beforeEach(() => {
  FakeTerminal.instances.length = 0;
  FakeSearchAddon.calls.length = 0;
  FakeFitAddon.fits = 0;
});

describe("PaneWell xterm interior (HS-111-11)", () => {
  it("mounts a READ-ONLY workbench-themed terminal and repaints in one write", async () => {
    render(<PaneWell live lines={[]} raw={COLORED} />);
    const term = await mountedTerminal();
    // Read-only viewer: stdin disabled, no onData handler ever wired.
    expect(term.options.disableStdin).toBe(true);
    expect(term.onDataCalls).toBe(0);
    // Signal Workbench material: opaque screen, mono, steady block.
    expect(term.options.theme.background).toBe("#0f1115");
    expect(term.options.cursorStyle).toBe("block");
    expect(term.options.cursorBlink).toBe(false);
    expect(term.options.fontFamily).toContain("Mono");
    // Full repaint: ONE write carrying clear + the untouched ANSI.
    await waitFor(() => expect(term.writes.length).toBe(1));
    expect(term.writes[0]).toContain("[2J");
    expect(term.writes[0]).toContain(COLORED);
    // Copy-on-select is wired.
    expect(term.selectionHandler).not.toBeNull();
  });

  it("sizes to the pane geometry and parks the cursor there", async () => {
    render(
      <PaneWell
        live
        lines={[]}
        raw={COLORED}
        pane={{ width: 120, height: 32, cursorX: 4, cursorY: 7 }}
      />,
    );
    const term = await mountedTerminal();
    await waitFor(() => expect(term.resizes).toContainEqual([120, 32]));
    expect(term.writes[0]).toContain("[8;5H"); // row 8, col 5 (1-based)
    expect(FakeFitAddon.fits).toBe(0); // pane-sized, not container-fit
  });

  it("wires the well-head finder to the search addon (mic included)", async () => {
    render(<PaneWell live lines={[]} raw={COLORED} />);
    await mountedTerminal();
    const finder = screen.getByLabelText("Find in scrollback");
    expect(screen.getByRole("button", { name: /speak find/i })).toBeTruthy();
    await userEvent.type(finder, "PASS");
    await waitFor(() =>
      expect(FakeSearchAddon.calls.at(-1)?.query).toBe("PASS"),
    );
    expect(FakeSearchAddon.calls.at(-1)?.options.decorations).toBeTruthy();
    const before = FakeSearchAddon.calls.length;
    await userEvent.type(finder, "{Enter}");
    await waitFor(() =>
      expect(FakeSearchAddon.calls.length).toBeGreaterThan(before),
    );
  });

  it("shows the operator facts as head tokens", async () => {
    render(
      <PaneWell live lines={[]} raw={COLORED} changedAt={Date.now() - 3000} />,
    );
    await mountedTerminal();
    expect(screen.getByText("RAW")).toBeInTheDocument();
    expect(screen.getByText("LINES 2")).toBeInTheDocument();
    expect(screen.getByText(/^Δ \dS$/)).toBeInTheDocument();
  });

  it("falls back to the stripped pre with the honest token when raw is unavailable", () => {
    const { container } = render(
      <PaneWell live lines={["$ ls", "README.md"]} raw={null} />,
    );
    expect(screen.getByText("STRIPPED · RAW UNAVAILABLE")).toBeInTheDocument();
    const pre = container.querySelector("pre.desk-session-pane");
    expect(pre?.textContent).toBe("$ ls\nREADME.md");
    expect(FakeTerminal.instances.length).toBe(0); // never a blank, never xterm
  });

  it("keeps the honest absence face when the peek is not live", () => {
    const { container } = render(
      <PaneWell live={false} lines={[]} absence={<>✕ pane gone</>} />,
    );
    expect(screen.getByText(/pane gone/)).toBeTruthy();
    expect(container.querySelector(".terminal-well")).toBeNull();
  });
});
