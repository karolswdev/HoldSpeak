// PHILO-13-12 (C2) — THE GADGETS THAT ARE MISSING, to the owner-ratified
// Workbench canvas (2026-10-02, "Ratify, build it"; boards C1-2a–d).
// Red on 8048e13d (no depth, zoom = maximize with one rect, a three-row
// title-bar menu), green after.
//
//   1. Depth: To back sends the window behind every other window; the next
//      one is the ONE front window. Gadget, menu and ⌃B.
//   2. Zoom alternates two remembered rects; both survive a reload.
//   3. The right button anywhere in a window opens its menu bar: Iconify ⌘M,
//      Zoom ⌃M, To back ⌃B, Close window ⌘W, Desk ▸, Go ▸.
//   4. The shortcut fence: every shown key cap is the verb's own registry
//      key, and that key runs THAT verb; no verb without a key shows one.
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DeskWindowFrame } from "../components/DeskWindow";
import { useDesk } from "../store";
import { loadDeskWorkspace } from "../store/workspaceStorage";
import { frontWindowId } from "../components/window/windowRegistry";
import { VERBS, menuVerbs, verbById, type MenuId } from "../verbRegistry";
import { dispatchKey, parseKey } from "../keymap";
import { headMenuEntries } from "../windowMenuAdapter";
import type { WorkMenuEntry } from "../components/DeskMenu";

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    panelZoom: {},
  });
});
afterEach(() => vi.restoreAllMocks());

function Two() {
  return (
    <>
      <DeskWindowFrame id="w-a" title="Alpha" open onClose={() => {}}>
        <p>alpha body</p>
      </DeskWindowFrame>
      <DeskWindowFrame id="w-b" title="Bravo" open onClose={() => {}}>
        <p>bravo body</p>
      </DeskWindowFrame>
    </>
  );
}

const shell = (name: string) => screen.getByRole("region", { name });
const z = (name: string) => Number(shell(name).style.zIndex);

describe("depth (to back)", () => {
  it("the store sends a window behind every other one", () => {
    useDesk.setState({ panelOrder: ["a", "b", "c"] });
    useDesk.getState().sendPanelToBack("c");
    expect(useDesk.getState().panelOrder).toEqual(["c", "a", "b"]);
    const raw = JSON.parse(localStorage.getItem("hs.desk.workspace.v1") || "{}");
    expect(raw.panel.order).toEqual(["c", "a", "b"]);
  });

  it("the depth gadget: the window goes behind; the other is the ONE front window", () => {
    render(<Two />);
    act(() => useDesk.getState().focusPanel("w-b"));
    expect(frontWindowId()).toBe("w-b");
    fireEvent.click(screen.getByRole("button", { name: "To back Bravo" }));
    expect(frontWindowId()).toBe("w-a");
    expect(z("Bravo")).toBeLessThan(z("Alpha"));
    expect(shell("Alpha").classList.contains("is-front")).toBe(true);
    expect(shell("Bravo").classList.contains("is-front")).toBe(false);
    expect(document.querySelectorAll(".desk-window-shell.is-front")).toHaveLength(1);
  });

  it("⌃B sends the front window to the back", () => {
    render(<Two />);
    act(() => useDesk.getState().focusPanel("w-a"));
    const ran = act(() =>
      dispatchKey(new KeyboardEvent("keydown", { key: "b", ctrlKey: true, cancelable: true })),
    );
    void ran;
    expect(frontWindowId()).toBe("w-b");
    expect(z("Alpha")).toBeLessThan(z("Bravo"));
  });
});

describe("zoom: two remembered rects", () => {
  const normal = { x: 40, y: 80, w: 420, h: 300 };
  const zoomed = { x: 12, y: 40, w: 900, h: 640 };

  it("zoom, a resized zoomed state, zoom back: each rect comes back exactly", () => {
    useDesk.getState().setPanelRect("w-a", normal, true);
    render(
      <DeskWindowFrame id="w-a" title="Alpha" open onClose={() => {}}>
        <p>alpha body</p>
      </DeskWindowFrame>,
    );
    const gadget = screen.getByRole("button", { name: "Zoom Alpha" });
    expect(gadget.getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(gadget);
    expect(gadget.getAttribute("aria-pressed")).toBe("true");
    // The user sizes the zoomed window (the frame's resize writes here).
    act(() => useDesk.getState().setZoomRect("w-a", zoomed, true));
    expect(shell("Alpha").style.left).toBe("12px");
    expect(shell("Alpha").style.width).toBe("900px");
    // The normal rect waited untouched.
    expect(useDesk.getState().panelRects["w-a"]).toEqual(normal);
    fireEvent.click(gadget);
    expect(shell("Alpha").style.left).toBe("40px");
    expect(shell("Alpha").style.top).toBe("80px");
    expect(shell("Alpha").style.width).toBe("420px");
    expect(shell("Alpha").style.height).toBe("300px");
    // Zoom again: the remembered zoomed rect, not the work band.
    fireEvent.click(gadget);
    expect(shell("Alpha").style.left).toBe("12px");
    expect(shell("Alpha").style.height).toBe("640px");
  });

  it("both rects survive a reload (the workspace document)", () => {
    useDesk.getState().setPanelRect("w-a", normal, true);
    useDesk.getState().toggleMaximizePanel("w-a");
    useDesk.getState().setZoomRect("w-a", zoomed, true);
    const doc = loadDeskWorkspace();
    expect(doc.panel.rects["w-a"]).toEqual(normal);
    expect(doc.panel.zoom?.["w-a"]).toEqual(zoomed);
    expect(doc.panel.max).toContain("w-a");
  });

  it("⌃M zooms the front window and zooms it back", () => {
    render(<Two />);
    act(() => useDesk.getState().focusPanel("w-a"));
    act(() => {
      dispatchKey(new KeyboardEvent("keydown", { key: "m", ctrlKey: true, cancelable: true }));
    });
    expect(useDesk.getState().panelMax).toContain("w-a");
    expect(useDesk.getState().panelMin).not.toContain("w-a");
    act(() => {
      dispatchKey(new KeyboardEvent("keydown", { key: "m", ctrlKey: true, cancelable: true }));
    });
    expect(useDesk.getState().panelMax).not.toContain("w-a");
  });
});

function items(entries: WorkMenuEntry[]): Extract<WorkMenuEntry, { type: "item" }>[] {
  return entries.flatMap((e) =>
    e.type === "item" ? [e] : e.type === "sub" ? items(e.entries) : [],
  );
}

describe("the right button: the window's menu bar with Amiga-key caps", () => {
  it("right button in the BODY opens the window menu, in the canvas's order", () => {
    render(<Two />);
    fireEvent.contextMenu(screen.getByText("alpha body"));
    const menu = screen.getByRole("menu", { name: "Alpha window menu" });
    const labels = Array.from(menu.querySelectorAll("[role^='menuitem']")).map(
      (el) => el.querySelector(".desk-menu-label")?.textContent?.trim() ?? el.textContent?.trim(),
    );
    expect(labels.slice(0, 4)).toEqual(["Iconify", "Zoom", "To back", "Close window"]);
    expect(labels.join("|")).toMatch(/Desk.*\|.*Go/);
    const caps = Array.from(menu.querySelectorAll(".desk-menu-keycaps")).map((k) =>
      k.getAttribute("aria-label"),
    );
    expect(caps.slice(0, 4)).toEqual(["⌘M", "⌃M", "⌃B", "⌘W"]);
  });

  it("To back from the menu sends THIS window back", () => {
    render(<Two />);
    act(() => useDesk.getState().focusPanel("w-a"));
    fireEvent.contextMenu(screen.getByText("alpha body"));
    const menu = screen.getByRole("menu", { name: "Alpha window menu" });
    fireEvent.click(within(menu).getByText("To back"));
    expect(frontWindowId()).toBe("w-b");
  });

  it("a field keeps its own right button", () => {
    render(
      <DeskWindowFrame id="w-f" title="Field" open onClose={() => {}}>
        <input aria-label="note field" />
      </DeskWindowFrame>,
    );
    fireEvent.contextMenu(screen.getByLabelText("note field"));
    expect(screen.queryByRole("menu", { name: "Field window menu" })).toBeNull();
  });
});

describe("the shortcut fence over the verb registry", () => {
  const shown: { id: string; keycap?: string }[] = [
    ...items(
      headMenuEntries({
        maximized: false,
        compact: false,
        requestMinimize: () => {},
        toggleMaximize: () => {},
        requestClose: () => {},
        toBack: () => {},
      }),
    ).map((e) => ({ id: e.id, keycap: e.keycap })),
    ...(["desk", "object", "go", "window"] as MenuId[]).flatMap((m) =>
      menuVerbs(m).map((v) => ({ id: v.id, keycap: v.key })),
    ),
  ];

  it("the window menu carries Zoom ⌃M and To back ⌃B", () => {
    expect(shown).toContainEqual({ id: "window.maximize", keycap: "⌃M" });
    expect(shown).toContainEqual({ id: "window.depth", keycap: "⌃B" });
  });

  it("no verb without a key shows one; every shown key runs THAT verb", () => {
    for (const { id, keycap } of shown) {
      const verb = verbById(id);
      expect(verb, id).toBeTruthy();
      expect(keycap ?? null, id).toBe(verb!.key ?? null);
      if (!keycap) continue;
      const spec = parseKey(keycap);
      expect(spec, `${id} ${keycap} is bound`).not.toBeNull();
      // Every verb runnable and silent: the fence asks which verb the key
      // reaches, not whether the desk can act now.
      const runs = VERBS.map((v) => [
        vi.spyOn(v, "ghost").mockReturnValue(null),
        vi.spyOn(v, "run").mockImplementation(() => {}),
      ]);
      const key = spec!.plain ? keycap : spec!.key;
      const ev = new KeyboardEvent("keydown", {
        key,
        metaKey: spec!.meta,
        ctrlKey: spec!.ctrl,
        shiftKey: Boolean(spec!.shift),
        cancelable: true,
      });
      expect(dispatchKey(ev)?.id, `${keycap} runs ${id}`).toBe(id);
      expect(verb!.run).toHaveBeenCalledTimes(1);
      for (const [g, r] of runs) {
        g.mockRestore();
        r.mockRestore();
      }
    }
  });
});
