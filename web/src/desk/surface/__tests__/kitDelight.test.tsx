/** DELIGHT (2026-10-27, docs/internal/betterment/canvases/delight-2026-10-27.html):
 *  the kit's share of the delight system — the object empty state, the
 *  status-bar lamp that pulses once per save, and the list row that names
 *  its kind for its hue. */
import { readFileSync } from "node:fs";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { StatusBar, TickNumber } from "../kit";
import { SurfaceState } from "../Surface";
import { ObjectList } from "../objects/ObjectList";

describe("DELIGHT — the kit", () => {
  it("an empty state with a kind is an object, one line, one verb", () => {
    const onAction = vi.fn();
    const { container } = render(
      <SurfaceState empty emptyKind="meeting" emptyImage="/m.png" emptyLabel="Record or import a meeting" onAction={onAction} actionLabel="Import a recording" />,
    );
    const state = container.querySelector(".surface-state")!;
    expect(state.getAttribute("data-object")).toBe("meeting");
    expect(state.querySelector(".surface-state-object img")?.getAttribute("src")).toBe("/m.png");
    expect(state.querySelector(".surface-state-line")?.textContent).toBe("Record or import a meeting");
    fireEvent.click(screen.getByRole("button", { name: "Import a recording" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("an empty state without a kind keeps the plain form", () => {
    const { container } = render(<SurfaceState empty emptyImage="/m.png" emptyLabel="Nothing here" />);
    expect(container.querySelector(".surface-state-object")).toBeNull();
    expect(container.querySelector(".surface-state-sprite")).not.toBeNull();
  });

  it("the status-bar lamp pulses on a change after the first paint, never on the first paint", () => {
    const bar = (pulse: string | null) => (
      <StatusBar items={[{ key: "save", lamp: "ok", text: "Saved just now", pulse }]} />
    );
    const { container, rerender } = render(bar("2026-10-27T09:00:00Z"));
    const dot = () => container.querySelector(".kit-statusbar-item > .kit-dot")!;
    expect(dot().hasAttribute("data-pulse")).toBe(false);
    rerender(bar(null));
    expect(dot().hasAttribute("data-pulse")).toBe(false);
    rerender(bar("2026-10-27T09:00:05Z"));
    expect(dot().hasAttribute("data-pulse")).toBe(true);
    const first = dot();
    rerender(bar("2026-10-27T09:00:05Z"));
    expect(dot()).toBe(first);
    rerender(bar("2026-10-27T09:00:09Z"));
    expect(dot()).not.toBe(first);
    expect(dot().hasAttribute("data-pulse")).toBe(true);
  });

  it("slice 2: a count ticks (fades in once) when it changes after the first paint, never on the first paint", () => {
    const { container, rerender } = render(<TickNumber value={4} />);
    const tick = () => container.querySelector(".kit-tick")!;
    expect(tick().textContent).toBe("4");
    expect(tick().hasAttribute("data-tick")).toBe(false);
    rerender(<TickNumber value={4} />);
    expect(tick().hasAttribute("data-tick")).toBe(false);
    rerender(<TickNumber value={3} />);
    expect(tick().textContent).toBe("3");
    expect(tick().hasAttribute("data-tick")).toBe(true);
    const first = tick();
    rerender(<TickNumber value={2} />);
    expect(tick()).not.toBe(first);
    expect(tick().textContent).toBe("2");
  });

  it("slice 2: a status item with a tick fades its words in once when its number changes", () => {
    const bar = (n: number) => <StatusBar items={[{ key: "head", lamp: "ask", text: `${n} need you`, tick: n, testId: "head" }]} />;
    const { rerender } = render(bar(8));
    const head = () => screen.getByTestId("head");
    expect(head().textContent).toBe("8 need you");
    expect(screen.getByText("8 need you").hasAttribute("data-tick")).toBe(false);
    rerender(bar(7));
    expect(head().textContent).toBe("7 need you");
    expect(screen.getByText("7 need you").classList.contains("kit-tick")).toBe(true);
    expect(screen.getByText("7 need you").hasAttribute("data-tick")).toBe(true);
  });

  it("slice 4: a live lamp (on a call) is marked live, red too; a plain lamp is not", () => {
    const { container } = render(
      <StatusBar items={[
        { key: "live", lamp: "fail", live: true, text: "On a call", testId: "live" },
        { key: "fail", lamp: "fail", text: "Failed", testId: "fail" },
      ]} />,
    );
    const dots = [...container.querySelectorAll(".kit-statusbar-item > .kit-dot")];
    expect(dots.map((dot) => dot.hasAttribute("data-live"))).toEqual([true, false]);
    expect(dots[0].getAttribute("data-tone")).toBe("fail");
  });

  it("a dense list row names its kind (its hue reads from data-kind)", () => {
    const { container } = render(
      <ObjectList label="Mixed" density="dense" sort={{ key: "name", dir: "asc" }} rows={[
        { id: "m1", kind: "meeting", name: "Vendor sync" },
        { id: "d1", kind: "decision", name: "Freeze on Nov 12" },
      ]} />,
    );
    const kinds = [...container.querySelectorAll(".object-list-row")].map((row) => row.getAttribute("data-kind"));
    expect(kinds.sort()).toEqual(["decision", "meeting"]);
  });
});

/** DELIGHT slice 3 — the motion audit. jsdom does not match media queries,
 *  so these read the sheets: the browser half is the desk sweep's `still`
 *  fence, which runs every case under reduced motion. */
describe("DELIGHT — motion honours reduced motion", () => {
  const sheet = (path: string) => readFileSync(path, "utf8");
  /** The at-rule preludes that hold each `animation:` declaration naming one
   *  of the `names`. */
  function contexts(source: string, names: string[]): Array<{ name: string; at: string[] }> {
    const css = source.replace(/\/\*[\s\S]*?\*\//g, "");
    const out: Array<{ name: string; at: string[] }> = [];
    const stack: string[] = [];
    let start = 0;
    for (let i = 0; i < css.length; i += 1) {
      const ch = css[i];
      if (ch === "{") { stack.push(css.slice(start, i).trim()); start = i + 1; }
      else if (ch === "}") { stack.pop(); start = i + 1; }
      else if (ch === ";") {
        const decl = css.slice(start, i).trim();
        const m = /^animation:\s*([\w-]+)/.exec(decl);
        if (m && names.includes(m[1])) out.push({ name: m[1], at: stack.filter((p) => p.startsWith("@")) });
        start = i + 1;
      }
    }
    return out;
  }

  it("the desk's kill switch stops every animation and transition under reduced motion", () => {
    const css = sheet("src/styles/react-app.css");
    const block = /@media \(prefers-reduced-motion: reduce\) \{\s*\*,\s*\*::before,\s*\*::after \{([^}]*)\}/.exec(css);
    expect(block, "react-app.css: the global reduced-motion block").not.toBeNull();
    expect(block![1]).toMatch(/animation-duration:\s*0ms !important/);
    expect(block![1]).toMatch(/transition-duration:\s*0ms !important/);
  });

  it("the kit's delight motions run only with no motion preference", () => {
    const found = contexts(sheet("src/desk/surface/kit.css"), ["kit-lamp-pulse", "kit-tick-in"]);
    expect(found.map((f) => f.name).sort()).toEqual(["kit-lamp-pulse", "kit-tick-in"]);
    for (const f of found) expect(f.at, f.name).toContain("@media (prefers-reduced-motion: no-preference)");
  });

  it("slice 4: the live breath and the Calls answer settle run only with no motion preference; a dot turns only in data-turns", () => {
    const kit = sheet("src/desk/surface/kit.css");
    const live = contexts(kit, ["kit-lamp-live"]);
    expect(live).toHaveLength(1);
    expect(live[0].at).toContain("@media (prefers-reduced-motion: no-preference)");
    const settle = contexts(sheet("src/desk/calls/calls.css"), ["calls-hold-settle-yes"]);
    expect(settle).toHaveLength(1);
    expect(settle[0].at).toContain("@media (prefers-reduced-motion: no-preference)");
    const turn = /@media \(prefers-reduced-motion: no-preference\) \{\s*\[data-turns\] \.kit-dotword > \.kit-dot \{([^}]*)\}/.exec(kit);
    expect(turn, "kit.css: the opt-in dot turn").not.toBeNull();
    expect(turn![1]).toMatch(/transition:\s*background-color 160ms/);
    expect(turn![1]).not.toMatch(/\btransform\b/);
  });

  it("slice 4: the Record tile breathes a red ring (paint only), never the hard blink", () => {
    const orb = sheet("src/desk/components/record-orb.css").replace(/\/\*[\s\S]*?\*\//g, "");
    expect(orb).toMatch(/\.desk-orb\.is-recording \.desk-orb-face \{[^}]*animation:\s*desk-next-orb-breath 2\.4s ease-in-out infinite/);
    expect(orb).not.toMatch(/steps\(2/);
    const breath = /@keyframes desk-next-orb-breath \{([\s\S]*?)\n\}/.exec(orb);
    expect(breath![1]).toMatch(/drop-shadow/);
    expect(breath![1]).not.toMatch(/transform|scale/);
    expect(orb).toMatch(/prefers-reduced-motion: reduce\)[\s\S]*?\.desk-orb\.is-recording \.desk-orb-face \{\s*animation: none;/);
  });

  it("nothing in the kit moves on hover", () => {
    const css = sheet("src/desk/surface/kit.css");
    const hovers = [...css.matchAll(/([^{}]*:hover[^{}]*)\{([^}]*)\}/g)];
    expect(hovers.length).toBeGreaterThan(0);
    for (const [, selector, body] of hovers) expect(body, selector.trim()).not.toMatch(/\btransform\s*:/);
  });

});
