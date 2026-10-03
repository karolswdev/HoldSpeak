// PHILO-13-11 (C1) — the Workbench frame: the material tokens, the gadget
// set, ONE front window, the screen title bar, and the §3a strip menu.
// The ratified canvas: pm/roadmap/holdspeak-philo/phase-13-the-desk/
// assets/story-11-canvas/ (design/workbench-look.md §2–§4).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DeskWindowFrame } from "../components/DeskWindow";
import { DeskChrome } from "../components/DeskChrome";
import { FilterTokens } from "../surface/FilterTokens";
import { SurfaceWings } from "../surface/wings";
import { useDesk } from "../store";

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
}));

const WEB = resolve(__dirname, "../../..");
const read = (rel: string) => readFileSync(resolve(WEB, rel), "utf-8");

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

const realMatchMedia = window.matchMedia;
beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    windowsById: {},
    zoneWindows: [],
    zoneViewPrefs: {},
  });
});
afterEach(() => {
  window.matchMedia = realMatchMedia;
});

describe("the material (design-tokens.json → tokens.css, COMPONENT layer)", () => {
  it("defines the Workbench Steel pens and sizes once, at the ratified values", () => {
    const css = read("src/styles/tokens.css");
    const want: Record<string, string> = {
      "--wb-steel": "#9ea4b0",
      "--wb-steel-2": "#b3b8c2",
      "--wb-ink": "#0b0c10",
      "--wb-paper": "#eef0f3",
      "--wb-blue": "#6688bb",
      "--wb-backdrop": "#3c4454",
      "--wb-dither": "#363e4d",
      "--wb-rec": "#b3261e",
      "--wb-frame": "4px",
      "--wb-bar-h": "26px",
      "--wb-screen-h": "28px",
      "--wb-gadget-w": "26px",
      "--wb-drop": "4px 4px 0 rgba(0, 0, 0, 0.32)",
      "--accent-text": "#bc8058",
    };
    for (const [name, value] of Object.entries(want)) {
      const hits = css.match(new RegExp(`^\\s*${name}:\\s*([^;]+);`, "gm")) ?? [];
      expect(hits, name).toHaveLength(1);
      expect(hits[0]).toContain(value);
    }
  });

  it("every DeskWindowFrame host wears the frame: the shell, the bar and the gadgets name --wb-* tokens", () => {
    const chrome = read("src/desk/components/window-chrome.css");
    const rule = (selector: string) => {
      const at = chrome.indexOf(`${selector} {`);
      expect(at, selector).toBeGreaterThan(-1);
      return chrome.slice(at, chrome.indexOf("}", at));
    };
    expect(rule(".desk-next .desk-window.desk-window-shell")).toMatch(/var\(--wb-frame\) solid var\(--wb-steel\)/);
    expect(rule(".desk-next .desk-window.desk-window-shell.is-front")).toContain("var(--wb-blue)");
    expect(rule(".desk-next .desk-window-shell > .desk-pullout-head")).toContain("var(--wb-steel)");
    expect(rule(".desk-next .desk-window-shell.is-front > .desk-pullout-head")).toContain("var(--wb-blue)");
    // The inherited head-tone rule that painted EVERY is-front head is gone
    // (R4): a stale is-front can no longer paint a second front bar.
    expect(chrome).not.toMatch(/\.desk-window-shell\.is-front \.desk-pullout-head \{/);
    // The traffic lights are removed (§3).
    expect(read("src/desk/components/pullout.css")).not.toMatch(/^[^/*\n]*\.desk-(light|traffic)\b[^{\n]*\{/m);
    // The host tokens are NOT re-pointed (R5): body strips still wear them.
    const tokens = read("src/styles/tokens.css");
    expect(tokens).toMatch(/--desk-window-head-fill: var\(--surface-2\);/);
    expect(tokens).toMatch(/--gadget-fill: var\(--surface-2\);/);
  });
});

function Frame({ id, title }: { id: string; title: string }) {
  return (
    <DeskWindowFrame id={id} title={title} open onClose={() => {}}>
      <p>{title} body</p>
    </DeskWindowFrame>
  );
}

describe("the gadget set (§3)", () => {
  it("close flush left; iconify, zoom then depth flush right; every gadget a library Button; no traffic lights", () => {
    setCompact(false);
    render(<Frame id="g1" title="Meetings" />);
    const head = screen.getByRole("region", { name: "Meetings" }).querySelector("header")!;
    const kids = Array.from(head.children) as HTMLElement[];
    expect(kids[0].className).toContain("desk-gadgets-left");
    expect(kids.at(-1)!.className).toContain("desk-gadgets-right");
    const labels = (el: HTMLElement) =>
      Array.from(el.querySelectorAll("button")).map((b) => b.getAttribute("aria-label"));
    expect(labels(kids[0])).toEqual(["Close Meetings"]);
    // PHILO-13-12 (C2): depth is built (send to back), so it is drawn.
    expect(labels(kids.at(-1)!)).toEqual(["Iconify Meetings", "Zoom Meetings", "To back Meetings"]);
    // The library Button stamps `btn--chrome` on a chrome verb (Signal.tsx).
    for (const b of Array.from(head.querySelectorAll("button"))) expect(b.className).toMatch(/(^|\s)btn--chrome(\s|$)/);
    expect(head.querySelector(".desk-traffic, .desk-light")).toBeNull();
    // The sizing gadget sits on the frame, bottom right.
    expect(document.querySelector(".desk-window-grip.desk-gadget-size svg")).toBeTruthy();
  });

  it("at the phone width the set is close and depth (a window fills the work area)", () => {
    setCompact(true);
    render(<Frame id="g2" title="People" />);
    const head = screen.getByRole("region", { name: "People" }).querySelector("header")!;
    expect(Array.from(head.querySelectorAll("button")).map((b) => b.getAttribute("aria-label"))).toEqual([
      "Close People",
      "To back People",
    ]);
  });
});

// The two-front bug (R4; grounding faces-surfaces.md:219): the frame read the
// window registry without subscribing to it, so a window that re-rendered
// after announcing itself computed "front" while the old front kept its mark.
function Rerenderable() {
  const [n, setN] = useState(0);
  return (
    <>
      <button type="button" data-testid="bump" onClick={() => setN(n + 1)} />
      <DeskWindowFrame id="b" title="Bravo" open onClose={() => {}}>
        <p>{n}</p>
      </DeskWindowFrame>
    </>
  );
}

describe("ONE front window (R4)", () => {
  it("exactly one frame wears is-front after a second window opens and re-renders", () => {
    setCompact(false);
    const { rerender } = render(<Frame id="a" title="Alpha" />);
    rerender(
      <>
        <Frame id="a" title="Alpha" />
        <Rerenderable />
      </>,
    );
    fireEvent.click(screen.getByTestId("bump"));
    const front = document.querySelectorAll(".desk-window-shell.is-front");
    expect(Array.from(front).map((e) => e.getAttribute("aria-label"))).toEqual(["Bravo"]);
    act(() => useDesk.getState().focusPanel("a"));
    expect(
      Array.from(document.querySelectorAll(".desk-window-shell.is-front")).map((e) =>
        e.getAttribute("aria-label"),
      ),
    ).toEqual(["Alpha"]);
  });
});

describe("the screen title bar (§4)", () => {
  it("names the front window — the same one the blue frame marks — and the time", () => {
    setCompact(false);
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 200 })));
    render(
      <MemoryRouter>
        <DeskChrome />
        <Frame id="a" title="Alpha" />
        <Frame id="b" title="Bravo" />
      </MemoryRouter>,
    );
    const title = screen.getByTestId("desk-screen-title");
    expect(title.textContent).toBe("Bravo");
    act(() => useDesk.getState().focusPanel("a"));
    expect(title.textContent).toBe("Alpha");
    expect(document.querySelector(".desk-window-shell.is-front")?.getAttribute("aria-label")).toBe("Alpha");
    expect(document.querySelector(".desk-clock strong")?.textContent).toMatch(/\d/);
    vi.unstubAllGlobals();
  });

  it("with no window open it names the screen", () => {
    setCompact(false);
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 200 })));
    render(
      <MemoryRouter>
        <DeskChrome />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("desk-screen-title").textContent).toBe("Chair");
    vi.unstubAllGlobals();
  });
});

/* §3a — the strip menu. jsdom lays nothing out, so the test gives the strip
   a measured box: a 200 px row that its content (600 px) overruns. */
function measuredStrip(rowWidth: number, contentWidth: number) {
  const cw = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "clientWidth");
  const sw = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "scrollWidth");
  Object.defineProperty(HTMLElement.prototype, "clientWidth", { configurable: true, get: () => rowWidth });
  Object.defineProperty(HTMLElement.prototype, "scrollWidth", { configurable: true, get: () => contentWidth });
  return () => {
    if (cw) Object.defineProperty(HTMLElement.prototype, "clientWidth", cw);
    if (sw) Object.defineProperty(HTMLElement.prototype, "scrollWidth", sw);
  };
}

const RANKING = [
  { value: "", label: "RANKED" },
  { value: "due", label: "DUE" },
  { value: "decision", label: "DECISIONS" },
  { value: "followup", label: "FOLLOW-UPS" },
];

describe("strips of choices: nothing clips, nothing scrolls sideways (§3a)", () => {
  it("at 393 a strip that does not fit is ONE menu Button with the current choice; its menu checks the current one", () => {
    setCompact(true);
    const restore = measuredStrip(200, 600);
    const onChange = vi.fn();
    try {
      render(<FilterTokens label="Ranking" options={RANKING} value="" onChange={onChange} />);
      expect(screen.queryAllByRole("button", { pressed: false })).toHaveLength(0);
      const menuButton = screen.getByRole("button", { name: "Ranking: RANKED" });
      expect(menuButton.textContent).toBe("RANKED ▾");
      expect(menuButton.className).toContain("btn");
      fireEvent.click(menuButton);
      const checked = screen.getAllByRole("menuitemcheckbox").filter((r) => r.getAttribute("aria-checked") === "true");
      expect(checked.map((r) => r.textContent)).toEqual(["RANKED"]);
      fireEvent.click(screen.getByRole("menuitemcheckbox", { name: /DECISIONS/ }));
      expect(onChange).toHaveBeenCalledWith("decision");
    } finally {
      restore();
    }
  });

  it("a strip that fits stays a strip (measured, not counted)", () => {
    setCompact(true);
    const restore = measuredStrip(600, 300);
    try {
      render(<FilterTokens label="Ranking" options={RANKING} value="" onChange={() => {}} />);
      expect(screen.getAllByRole("button")).toHaveLength(4);
      expect(screen.queryByTestId("surface-strip-menu")).toBeNull();
    } finally {
      restore();
    }
  });

  it("the desktop strip never folds", () => {
    setCompact(false);
    const restore = measuredStrip(200, 600);
    try {
      render(<FilterTokens label="Ranking" options={RANKING} value="" onChange={() => {}} />);
      expect(screen.queryByTestId("surface-strip-menu")).toBeNull();
    } finally {
      restore();
    }
  });

  it("window wings that do not fit fold the same way; the gear door joins after a separator", () => {
    setCompact(true);
    const restore = measuredStrip(200, 600);
    const onDoor = vi.fn();
    try {
      render(
        <SurfaceWings
          wings={[
            { id: "outcomes", label: "Outcomes" },
            { id: "review", label: "Review" },
            { id: "record", label: "Record" },
            { id: "artifacts", label: "Artifacts" },
          ]}
          active="outcomes"
          onChange={() => {}}
          door="Meeting plumbing"
          onDoor={onDoor}
        />,
      );
      const menuButton = screen.getByRole("button", { name: "Window faces: Outcomes" });
      expect(menuButton.textContent).toBe("Outcomes ▾");
      fireEvent.click(menuButton);
      const menu = screen.getByRole("menu");
      expect(within(menu).getByRole("separator")).toBeTruthy();
      fireEvent.click(within(menu).getByRole("menuitemcheckbox", { name: /Meeting plumbing/ }));
      expect(onDoor).toHaveBeenCalledTimes(1);
    } finally {
      restore();
    }
  });
});
