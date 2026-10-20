// PHILO-13-11 (C1, slice two) — THE CHAIR AS WINDOWS, to the owner-ratified
// canvas (2026-10-02: "Ratify, build it"; Capture "Yes"). Red on bbf7e9a4
// (the Chair was one scrolling page), green after.
//
//   1. DeskWindowFrame windows — Needs you, Capture (Betterment daily D5:
//      Brief and The week retired into Today) — each holding its body;
//      registered (front window, screen title)
//      with no Dock chip; Needs you is the front Chair window.
//   2. The work first (R3): the Needs-you window leads with the headline and
//      the actions; SETUP is below the actions.
//   3. R1: Close closes; Window ▸ Chair lists them with a check on the
//      open ones. PHILO-14 A1 (board A-1): the Chair is the screen of
//      objects, so a closed window leaves the screen, not a reopen Button.
//   4. R2 (393): one window at a time, Needs you first; the Speak AppIcon's
//      key ("dictate") opens Capture on demand.
//   5. The A3-W ledger: no `Run summary` beside SUMMARY STORED.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../../lib/api";
import { useDesk } from "../../store";
import { ChairHome } from "../ChairHome";
import { DeskMenuBar } from "../../components/DeskMenuBar";
import {
  frontWindowId,
  registrySnapshot,
  dockSnapshot,
} from "../../components/window/windowRegistry";
import { verbById } from "../../verbRegistry";
import { openSurfaceOr } from "../../shell";
import { useChairWindows } from "../chairWindows";
import { asHub } from "../../../test/hubNeedsYou";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const ROUTE = {
  status: "ready",
  reason_code: null,
  selection_hash: "sha256:chair",
  legs: [{ ordinal: 1, host: "192.168.1.43", boundary: "lan" }],
};

const NEEDS = {
  count: 1,
  items: [{
    id: "item-1", projectId: "p1", projectName: "Q4 Platform", ref: "item-1",
    title: "Sam: send the status by Thursday", why: "DUE TODAY", ageToken: "",
    since: "2026-09-04T09:00:00", source: "github", verbHref: "https://x/1",
    severity: "warning", rankClass: "due_today",
  }],
  coverage: [],
};

function wire() {
  vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
    const p = String(path);
    // a cold roster: the meeting path names its SETUP row
    if (p === "/api/inference/assignments")
      return {
        schema: "InferenceAssignmentSummary@1", rows: [], issue_count: 0,
        task_overrides: [{ id: "meeting.deferred_analysis", has_override: false, effective: { status: "unassigned" } }],
      };
    if (p.startsWith("/api/desk/needs-you")) return NEEDS;
    if (p.startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
    return null;
  }));
}

function setCompact(on: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: on && query.includes("max-width: 720px"),
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}

const region = (name: string) => screen.queryByRole("region", { name });
const realMatchMedia = window.matchMedia;

beforeEach(() => {
  setCompact(false);
  localStorage.clear();
  useChairWindows.setState({ closed: {}, phone: "chair:needs" });
  useDesk.setState({
    panelRects: {}, panelSaved: [], panelOrder: [], panelMin: [], panelMax: [],
    items: { meeting: [] } as never,
  });
  vi.mocked(apiFetch).mockReset();
  wire();
});
afterEach(() => {
  window.matchMedia = realMatchMedia;
});

describe("PHILO-13-11 slice two — the Chair as windows", () => {
  it("renders two windows, Needs you and Capture, each holding its body (no Brief, no The week)", async () => {
    render(<ChairHome />);
    expect(region("Brief")).toBeNull();
    expect(region("The week")).toBeNull();
    for (const name of ["Needs you", "Capture"]) {
      const win = region(name);
      expect(win, name).toBeTruthy();
      expect(win!.classList.contains("desk-window-shell")).toBe(true);
      expect(within(win!).getByRole("button", { name: `Close ${name}` })).toBeTruthy();
      expect(within(win!).getByRole("button", { name: `Zoom ${name}` })).toBeTruthy();
      // design §3: every window carries the full set (depth withheld until C2)
      expect(within(win!).getByRole("button", { name: `Iconify ${name}` })).toBeTruthy();
    }
    // PHILO-14 A5: the Needs-you window body is the smart drawer.
    expect(within(region("Needs you")!).getByTestId("needs-drawer")).toBeTruthy();
    expect(within(region("Capture")!).getByTestId("arrival-capture-bar")).toBeTruthy();
    expect(within(region("Capture")!).getByRole("button", { name: "New note" })).toBeTruthy();
    expect(within(region("Capture")!).getByRole("button", { name: "Record" })).toBeTruthy();
    // Recording lives in Meetings; Capture shows its next two rows.
    expect(within(region("Capture")!).queryByRole("button", { name: "Schedule" })).toBeNull();
    // registered for the front and the screen title; no Dock chip until iconified
    const ids = registrySnapshot.map((w) => w.id);
    for (const id of ["chair:needs", "chair:capture"]) {
      expect(ids).toContain(id);
      expect(dockSnapshot.map((w) => w.id)).not.toContain(id);
    }
    expect(frontWindowId()).toBe("chair:needs");
    expect(region("Needs you")!.classList.contains("is-front")).toBe(true);
    expect(document.querySelectorAll(".desk-window-shell.is-front")).toHaveLength(1);
  });

  it("the work first: the head and the actions lead; SETUP is below the actions", async () => {
    // PHILO-14 A5: the Needs-you window body is the smart drawer; its head
    // leads and the SETUP row follows the action rows.
    render(<ChairHome />);
    const needs = region("Needs you")!;
    await waitFor(() => expect(needs.querySelector('[data-object-id="item-1"]')).toBeTruthy());
    await waitFor(() => expect(needs.querySelector('[data-object-id^="blocker:"]')).toBeTruthy());
    const body = within(needs).getByTestId("chair-window-body-needs");
    expect(body.firstElementChild?.getAttribute("data-testid")).toBe("needs-drawer");
    expect(body.firstElementChild?.firstElementChild?.getAttribute("data-testid")).toBe("arrival-headline");
    const action = needs.querySelector('[data-object-id="item-1"]')!;
    const setup = needs.querySelector('[data-object-id^="blocker:"]')!;
    expect(action.compareDocumentPosition(setup) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("Close closes; the screen stands where it was; Window ▸ Chair checks the open ones", async () => {
    render(<><DeskMenuBar /><ChairHome /></>);
    fireEvent.click(within(region("Capture")!).getByRole("button", { name: "Close Capture" }));
    await waitFor(() => expect(region("Capture")).toBeNull());
    expect(registrySnapshot.map((w) => w.id)).not.toContain("chair:capture");
    // PHILO-14 A1: no reopen Button; the screen of objects is the Chair.
    expect(screen.queryByTestId("chair-reopen-capture")).toBeNull();
    expect(screen.getByTestId("desk-screen")).toBeTruthy();

    // the verbs behind Window ▸ Chair
    expect(verbById("chair.window.capture")!.checked!({ selectedRef: null })).toBe(false);
    expect(verbById("chair.window.needs")!.checked!({ selectedRef: null })).toBe(true);
    // the menu face: Window holds ONE Chair submenu
    const title = screen.getByRole("button", { name: "Window" });
    fireEvent.click(title, { detail: 0 });
    const labels = screen.getAllByRole("menuitem").map((el) => el.textContent ?? "");
    expect(labels.filter((t) => /^Desk\b/.test(t))).toHaveLength(1);
    fireEvent.keyDown(document, { key: "Escape" });

    act(() => verbById("chair.window.capture")!.run({ selectedRef: null }));
    await waitFor(() => expect(region("Capture")).toBeTruthy());
    expect(frontWindowId()).toBe("chair:capture");
    expect(screen.queryByTestId("chair-reopen-capture")).toBeNull();

    // The shared Needs you verb opens it after Close; the duplicate Floor
    // icon has retired into the bell and the Ctrl-J entry.
    fireEvent.click(within(region("Needs you")!).getByRole("button", { name: "Close Needs you" }));
    await waitFor(() => expect(region("Needs you")).toBeNull());
    act(() => verbById("chair.window.needs")!.run({ selectedRef: null }));
    await waitFor(() => expect(region("Needs you")).toBeTruthy());
  });

  it("Iconify falls to a Dock chip; Window ▸ Chair brings it back", async () => {
    render(<ChairHome />);
    fireEvent.click(within(region("Capture")!).getByRole("button", { name: "Iconify Capture" }));
    await waitFor(() => expect(useDesk.getState().panelMin).toContain("chair:capture"));
    expect(dockSnapshot.map((w) => w.id)).toContain("chair:capture");
    expect(dockSnapshot.map((w) => w.id)).not.toContain("chair:needs");
    // iconified is still open: checked in Window ▸ Chair, no reopen Button
    expect(verbById("chair.window.capture")!.checked!({ selectedRef: null })).toBe(true);
    expect(screen.queryByTestId("chair-reopen-capture")).toBeNull();
    act(() => verbById("chair.window.capture")!.run({ selectedRef: null }));
    await waitFor(() => expect(useDesk.getState().panelMin).not.toContain("chair:capture"));
    expect(dockSnapshot.map((w) => w.id)).not.toContain("chair:capture");
    expect(frontWindowId()).toBe("chair:capture");
  });

  it("393: one window at a time, Needs you first; the Dock's Speak opens Capture, Go ▸ Speak does not", async () => {
    setCompact(true);
    render(<ChairHome />);
    expect(region("Needs you")).toBeTruthy();
    for (const name of ["Brief", "The week", "Capture"]) expect(region(name)).toBeNull();
    // Go ▸ Speak, the verb and ⌘1 ask the shell for "dictate" with no Dock
    // press: Capture stays closed (the Speak window keeps its door).
    act(() => openSurfaceOr("dictate", "/dictation"));
    expect(region("Capture")).toBeNull();
    expect(region("Needs you")).toBeTruthy();
    // PHILO-13-13 C3-W: a click on a Speak-labelled Dock element is no
    // longer a signal (the 1.5 s press window is retired) ...
    const dock = document.createElement("div");
    dock.className = "desk-dock";
    const speak = document.createElement("button");
    speak.setAttribute("aria-label", "Speak");
    dock.appendChild(speak);
    document.body.appendChild(dock);
    fireEvent.click(speak);
    act(() => openSurfaceOr("dictate", "/dictation"));
    dock.remove();
    expect(region("Capture")).toBeNull();
    // ... the Dock's explicit launch origin (#744) is the one signal.
    act(() => openSurfaceOr("dictate", "/dictation", undefined, { origin: "dock" }));
    await waitFor(() => expect(region("Capture")).toBeTruthy());
    expect(region("Needs you")).toBeNull();
    // closing Capture gives the work area back to the next Chair window
    fireEvent.click(within(region("Capture")!).getByRole("button", { name: "Back from Capture" }));
    await waitFor(() => expect(region("Needs you")).toBeTruthy());
    // Go lists Capture at 393 too (the phone has no Window menu; Go is the
    // door to every Chair window on an empty desk).
    expect(verbById("chair.window.capture")!.wide).toBeFalsy();
    // with every Chair window closed, the screen of objects (PHILO-14 A1;
    // board A-1-393), not a reopen list
    fireEvent.click(within(region("Needs you")!).getByRole("button", { name: "Back from Needs you" }));
    await waitFor(() => expect(screen.getByTestId("chair-desk").getAttribute("data-phone-shown")).toBeNull());
    expect(screen.queryByTestId("chair-reopen-list")).toBeNull();
    expect(screen.getByTestId("desk-screen").getAttribute("data-layout")).toBe("grid");
  });

});

// PHILO-15-09 (B16): Window ▸ Chair ▸ Brief opened the Brief BEHIND the
// Models and Settings windows ("Nothing happened"). A window the owner's
// gesture opens comes to the front, also when the Chair mounts after it.
describe("PHILO-15-09 B16 — a window he opens comes to the front", () => {
  it("Window ▸ Desk ▸ Capture stays in front when the Chair mounts after the pick", async () => {
    const { openChairWindow } = await import("../chairWindows");
    useChairWindows.setState({
      closed: { "chair:capture": true },
      phone: "chair:needs",
    });
    useDesk.setState({ panelOrder: ["chair:needs", "settings", "models"] });
    openChairWindow("chair:capture");
    render(<ChairHome />);
    await screen.findByRole("region", { name: "Capture" });
    await waitFor(() => expect(useDesk.getState().panelOrder.at(-1)).toBe("chair:capture"));
    expect(frontWindowId()).toBe("chair:capture");
  });

  it("an open Capture behind other windows comes to the front from the menu", async () => {
    const { openChairWindow } = await import("../chairWindows");
    render(<ChairHome />);
    await screen.findByRole("region", { name: "Capture" });
    act(() => {
      useDesk.getState().focusPanel("settings");
      useDesk.getState().focusPanel("models");
    });
    act(() => openChairWindow("chair:capture"));
    expect(useDesk.getState().panelOrder.at(-1)).toBe("chair:capture");
  });
});

// PHILO-17 briefcover (Astra r1 on #1080): the REAL Chair producer. A Chair
// window hidden by the phone's one-window ring (or iconified) is still open:
// it keeps its plane, so back at 1440 it does not jump above the window he
// was using; a close leaves the order and forgets an unsaved rect.
describe("PHILO-17 briefcover — hidden is not closed", () => {
  const order = () => [...useDesk.getState().panelOrder];

  async function chairAndMeetings() {
    const { DeskWindowFrame } = await import("../../components/DeskWindow");
    const view = render(<ChairHome />);
    await screen.findByRole("region", { name: "Capture" });
    render(<DeskWindowFrame id="surface-meetings" title="Meetings" open onClose={() => {}}>m</DeskWindowFrame>);
    act(() => useDesk.getState().focusPanel("surface-meetings"));
    return view;
  }

  it("the Chair mounting after a window he opened (a staged open) goes behind it", async () => {
    const { DeskWindowFrame } = await import("../../components/DeskWindow");
    act(() => useDesk.getState().focusPanel("surface-meetings"));
    render(<DeskWindowFrame id="surface-meetings" title="Meetings" open onClose={() => {}}>m</DeskWindowFrame>);
    render(<ChairHome />);
    await screen.findByRole("region", { name: "Capture" });
    await waitFor(() => expect(order().at(-1)).toBe("surface-meetings"));
    expect(frontWindowId()).toBe("surface-meetings");
    // Among the Chair's own planes Needs you leads.
    const chair = order().filter((id) => id.startsWith("chair:"));
    expect(chair.at(-1)).toBe("chair:needs");
  });

  it("393 then 1440: the Chair's windows keep their planes; Meetings stays in front", async () => {
    const view = await chairAndMeetings();
    const before = order();
    expect(before.at(-1)).toBe("surface-meetings");
    setCompact(true);
    view.rerender(<ChairHome />);
    await waitFor(() => expect(region("Capture")).toBeNull());
    expect(order()).toEqual(before);
    setCompact(false);
    view.rerender(<ChairHome />);
    await screen.findByRole("region", { name: "Capture" });
    expect(order()).toEqual(before);
  });

  it("iconify, then close from the Dock: the close retires it and forgets the unsaved rect; a saved rect stays", async () => {
    const { closeChairWindow } = await import("../chairWindows");
    render(<ChairHome />);
    await screen.findByRole("region", { name: "Capture" });
    const rect = { x: 700, y: 60, w: 500, h: 400 };
    act(() => {
      useDesk.getState().setPanelRect("chair:capture", rect); // the first seat: unsaved
      useDesk.getState().setPanelRect("chair:needs", rect, true); // his arrangement: saved
    });
    fireEvent.click(within(region("Capture")!).getByRole("button", { name: "Iconify Capture" }));
    fireEvent.click(within(region("Needs you")!).getByRole("button", { name: "Iconify Needs you" }));
    await waitFor(() => expect(useDesk.getState().panelMin).toEqual(expect.arrayContaining(["chair:capture", "chair:needs"])));
    expect(order()).toEqual(expect.arrayContaining(["chair:capture", "chair:needs"]));
    act(() => {
      closeChairWindow("chair:capture");
      closeChairWindow("chair:needs");
    });
    const s = useDesk.getState();
    expect(s.panelDepth).not.toHaveProperty("chair:capture");
    expect(s.panelDepth).not.toHaveProperty("chair:needs");
    expect(s.panelRects["chair:capture"]).toBeUndefined();
    expect(s.panelRects["chair:needs"]).toEqual(rect);
  });

  it("393: a window hidden by the ring, then closed, leaves the order", async () => {
    const { closeChairWindow } = await import("../chairWindows");
    const view = render(<ChairHome />);
    await screen.findByRole("region", { name: "Capture" });
    setCompact(true);
    view.rerender(<ChairHome />);
    await waitFor(() => expect(region("Capture")).toBeNull());
    expect(order()).toContain("chair:capture");
    act(() => closeChairWindow("chair:capture"));
    expect(order()).not.toContain("chair:capture");
  });

  it("with the hub: a resize sends no raise, and a hidden window shows another view's raise", async () => {
    const { createHubWindows } = await import("../../compositor/hubWindows");
    const view = await chairAndMeetings();
    const ids = ["chair:needs", "chair:capture", "surface-meetings"];
    const local = order();
    let revision = 10;
    const rows = new Map(ids.map((id) => [id, {
      id, app: id.startsWith("chair:") ? "chair" : "surface", object_ref: null, x: null, y: null, w: null, h: null,
      depth: local.indexOf(id) + 1, minimized: false, zoomed: false, zoom: null, arranged: false, room: null,
      front: false, revision: 1,
    }]));
    const calls: string[] = [];
    const hub = createHubWindows({
      settleMs: 0,
      view: () => ({ x: 10, y: 38, w: 1420, h: 772 }),
      compact: () => false,
      cacheOpen: [],
      transport: {
        list: async () => ({ windows: [...rows.values()], stage_shelf: "left", revision, adopted: true,
          registry: { static: Object.fromEntries(ids.map((id) => [id, "x"])), families: {} } }),
        verb: async (id, verb, body) => {
          calls.push(`${verb} ${id}`);
          // As the service: a write on a stale revision is refused (409).
          const row = rows.get(id)!;
          const expected = (body as { expected_revision?: number }).expected_revision;
          if (expected !== undefined && expected !== row.revision)
            throw new ApiError(409, "window_stale", { error: "window_stale" });
          const next = { ...row, revision: ++revision,
            ...(verb === "raise" ? { depth: Math.max(...[...rows.values()].map((r) => r.depth)) + 1 } : {}) };
          rows.set(id, next);
          return next;
        },
        arrange: async () => ({ windows: [] }),
        shelf: async (side) => ({ stage_shelf: side, revision: 1 }),
      },
    });
    try {
      await hub.start();
      await hub.idle();
      window.dispatchEvent(new Event("pointerdown"));
      calls.length = 0;
      setCompact(true);
      view.rerender(<ChairHome />);
      await waitFor(() => expect(region("Capture")).toBeNull());
      // Another view raises Capture while it is hidden here.
      rows.set("chair:capture", { ...rows.get("chair:capture")!, depth: 99, revision: ++revision });
      hub.onFrame({ kind: "windows", id: "chair:capture" });
      await hub.idle();
      setCompact(false);
      view.rerender(<ChairHome />);
      await screen.findByRole("region", { name: "Capture" });
      hub.sync();
      await hub.idle();
      expect(calls.filter((c) => c.startsWith("raise"))).toEqual([]);
      expect(order().at(-1)).toBe("chair:capture");
    } finally {
      hub.stop();
    }
  });
});
