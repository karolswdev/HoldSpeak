// The Overview app (W7, canvas 2026-10-28 (a), direction A "Captions on a
// slate veil"): every plate has a paper caption with the window's name, its
// 20 px glyph and the kind hue; the front plate wears data-front and takes
// the first focus. The registry and the presentation are the real ones; only
// the front window (the compositor's mounted snapshot) is set by the test.
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const front = vi.hoisted(() => ({ id: null as string | null }));
vi.mock("../windowRegistry", async (original) => ({
  ...(await original<typeof import("../windowRegistry")>()),
  useFrontWindowId: () => front.id,
}));

import { Expose, captionHue } from "../Expose";
import { announceWindow, retractWindow } from "../windowRegistry";
import { windowIcons } from "../seatIcons";
import { SPRITE_BASE } from "../../../sprites";
import { setPresentation } from "../../../compositor/live";

const WINDOWS = [
  { id: "pullout:decision:d1", label: "Use Kafka for the settlement events", glyph: "◆", kind: "Decision" },
  { id: "surface-project-memory", label: "Payments Platform Rewrite", glyph: "▢", kind: undefined },
  { id: "pullout:note:n1", label: "Ledger rollback", glyph: "✎", kind: "Note" },
  { id: "chair:needs", label: "Needs you", glyph: "●", kind: undefined },
];

function openOverview() {
  const plates: Record<string, { rect: { x: number; y: number; w: number; h: number }; k: number }> = {};
  WINDOWS.forEach((w, i) => {
    plates[w.id] = { rect: { x: 40 + i * 340, y: 60, w: 640, h: 400 }, k: 0.5 };
  });
  act(() => setPresentation({ mode: "expose", plates, saved: {}, staged: null }));
}

beforeEach(() => {
  for (const w of WINDOWS) announceWindow(w.id, w.label, w.glyph, () => undefined, true, w.kind);
  windowIcons.set("pullout:note:n1", <img src={`${SPRITE_BASE}note.png`} alt="" width={14} height={14} />);
  front.id = "surface-project-memory";
});

afterEach(() => {
  act(() => setPresentation({ mode: "free", plates: {}, saved: {}, staged: null }));
  act(() => { for (const w of WINDOWS) retractWindow(w.id); });
  windowIcons.clear();
});

describe("Overview captions", () => {
  it("every plate has a caption with the window's name", () => {
    render(<Expose />);
    openOverview();
    const captions = screen.getAllByTestId("desk-expose-caption");
    expect(captions.map((c) => c.textContent?.replace(/^[^A-Za-z]+/, ""))).toEqual(WINDOWS.map((w) => w.label));
    for (const w of WINDOWS) expect(screen.getByRole("button", { name: `Focus ${w.label}` })).toBeTruthy();
  });

  it("a caption wears its kind hue, and the Workbench blue with no kind", () => {
    render(<Expose />);
    openOverview();
    const [decision, project, note, needs] = screen.getAllByTestId("desk-expose-caption");
    expect(decision.style.getPropertyValue("--k")).toBe("var(--kind-decision)");
    expect(project.style.getPropertyValue("--k")).toBe("var(--kind-other)");
    expect(note.style.getPropertyValue("--k")).toBe("var(--kind-note)");
    expect(needs.style.getPropertyValue("--k")).toBe("var(--kind-other)");
    expect(captionHue("Agent session")).toBe("var(--kind-agent)");
    expect(captionHue("Project")).toBe("var(--kind-project)");
  });

  it("a caption draws the title-bar icon at 20 px", () => {
    render(<Expose />);
    openOverview();
    const note = screen.getAllByTestId("desk-expose-caption")[2];
    const img = note.querySelector("img")!;
    expect(img.getAttribute("src")).toBe(`${SPRITE_BASE}20/note.png`);
    expect(img.getAttribute("width")).toBe("20");
  });

  it("the front plate has data-front and the first focus", () => {
    render(<Expose />);
    openOverview();
    const room = screen.getByRole("button", { name: "Focus Payments Platform Rewrite" });
    expect(room).toHaveAttribute("data-front");
    expect(document.activeElement).toBe(room);
    expect(screen.getByRole("button", { name: "Focus Use Kafka for the settlement events" })).not.toHaveAttribute("data-front");
  });

  it("with no front window the first plate takes the focus and none is front", () => {
    front.id = null;
    render(<Expose />);
    openOverview();
    const first = screen.getByRole("button", { name: "Focus Use Kafka for the settlement events" });
    expect(document.activeElement).toBe(first);
    expect(document.querySelector("[data-front]")).toBeNull();
  });
});
