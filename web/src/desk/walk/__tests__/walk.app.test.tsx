/** The Walk (2026-11-07): the desk drives a recorded walk through open →
 * highlight → answer → next, Esc skips, and a refused token shows one line.
 * The walk and the answer are the hub's own recorded answers
 * (tests/integration/test_desk_walks.py writes __fixtures__). */
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import page from "../__fixtures__/walk.page.json";
import answer from "../__fixtures__/walk.answer.json";

const TOKEN = "Rec0rdedWalkT0kenRec0rdedWalkT0kenRec0rdedX";

const mocks = vi.hoisted(() => ({
  openSurface: vi.fn(),
  openSurfaceOr: vi.fn(),
  verbById: vi.fn(),
  captureWindowPng: vi.fn(),
  apiFetch: vi.fn(),
}));

vi.mock("../../shell", () => ({ openSurface: mocks.openSurface, openSurfaceOr: mocks.openSurfaceOr }));
vi.mock("../../verbRegistry", () => ({ verbById: mocks.verbById }));
vi.mock("../../feedback/capture", () => ({ captureWindowPng: mocks.captureWindowPng }));
// The walk's wire is the typed client (the null-read guard); here it rides
// the stubbed global fetch so each case keeps its recorded hub answers.
vi.mock("../../../lib/api", async (importOriginal) => {
  const real = await importOriginal<typeof import("../../../lib/api")>();
  return {
    ...real,
    apiFetch: async (path: string, init: RequestInit & { json?: unknown } = {}) => {
      const { json, ...request } = init;
      const response = await fetch(path, { ...request, body: json === undefined ? request.body : JSON.stringify(json) });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new real.ApiError(response.status, "", body);
      return body;
    },
  };
});

import { WalkRunner } from "../WalkRunner";

function mountWindow(id: string, html: string, z?: number): HTMLElement {
  const element = document.createElement("div");
  element.id = id;
  element.dataset.layer = "window";
  if (z !== undefined) element.style.zIndex = String(z);
  element.innerHTML = html;
  document.body.appendChild(element);
  return element;
}

type Box = { left: number; top: number; width: number; height: number };
/** Layout jsdom does not do: the rects a case sets on its elements. */
const rects = new Map<Element, () => Box>();
function rectOf(box: Box): DOMRect {
  return { ...box, x: box.left, y: box.top, right: box.left + box.width, bottom: box.top + box.height,
    toJSON: () => box } as DOMRect;
}
const realRect = HTMLElement.prototype.getBoundingClientRect;

let posts: Array<Record<string, unknown>> = [];

function hub(status = 200) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    if (status !== 200) {
      return new Response(JSON.stringify({ code: "walk_not_found", detail: "This walk is not known." }), { status });
    }
    if (path === `/api/w/${TOKEN}` && !init?.method) return new Response(JSON.stringify(page), { status: 200 });
    if (path === `/api/w/${TOKEN}/answer` && init?.method === "POST") {
      const body = JSON.parse(String(init.body));
      posts.push(body);
      return new Response(JSON.stringify(body.choice === "skip" ? { ref: body.ref, choice: "skip" } : answer),
        { status: 200 });
    }
    return new Response("null", { status: 404 });
  });
}

beforeEach(() => {
  posts = [];
  HTMLElement.prototype.getBoundingClientRect = function (this: HTMLElement) {
    const box = rects.get(this);
    return box ? rectOf(box()) : realRect.call(this);
  };
  window.history.replaceState({}, "", `/?walk=${TOKEN}`);
  mocks.openSurface.mockImplementation((key: string) => {
    if (key === "open-programs") {
      mountWindow("surface-programs", `<button data-testid="programs-new">New program</button>
        <section data-testid="programs-make"><ul data-testid="programs-make-rows"><li>Project</li></ul></section>`);
    }
    return true;
  });
  mocks.verbById.mockImplementation((id: string) => id === "chair.window.needs"
    ? { id, ghost: () => null, run: () => mountWindow("chair:needs", `<button data-testid="needs-open-people">People</button>`) }
    : undefined);
  mocks.captureWindowPng.mockResolvedValue("iVBORw0KGgo=");
});

afterEach(() => {
  cleanup();
  rects.clear();
  HTMLElement.prototype.getBoundingClientRect = realRect;
  document.documentElement.style.removeProperty("--desk-dock-h");
  Object.assign(window, { innerWidth: 1024, innerHeight: 768 });
  document.body.innerHTML = "";
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("The Walk", () => {
  it("opens, marks, asks, stores the answer with the window shot and goes on", async () => {
    vi.stubGlobal("fetch", hub());
    render(<WalkRunner />);

    // Step 1 opens Programs through the surface opener and goes on by itself.
    await waitFor(() => expect(mocks.openSurface).toHaveBeenCalledWith("open-programs", undefined));
    // Step 2: a mark with words and Next.
    expect(await screen.findByTestId("walk-words", {}, { timeout: 3000 })).toHaveTextContent(
      "Press New program. The well opens.");
    expect(await screen.findByTestId("walk-ring")).toBeInTheDocument();
    // The dim is four sides around the part; none is over it.
    expect(screen.getAllByTestId(/^walk-backdrop-/)).toHaveLength(4);
    expect(screen.getByTestId("walk-count")).toHaveTextContent("1 of 3");
    fireEvent.click(screen.getByTestId("walk-next"));

    // Step 3: the words, the question and the choices as library Buttons.
    expect(await screen.findByTestId("walk-question")).toHaveTextContent("Does the well read clearly?");
    expect(screen.getByTestId("walk-words")).toHaveTextContent("The project rows.");
    expect(screen.getByTestId("walk-count")).toHaveTextContent("2 of 3");
    const redo = screen.getByRole("button", { name: "Redo" });
    expect(redo.className).toMatch(/\bbtn\b/);
    expect(screen.getByRole("button", { name: "Keep" })).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("walk-say-more"));
    fireEvent.change(screen.getByRole("textbox", { name: "Say more" }), { target: { value: "The name is cut." } });
    fireEvent.click(redo);

    await waitFor(() => expect(posts).toHaveLength(1));
    expect(mocks.captureWindowPng).toHaveBeenCalledWith(document.getElementById("surface-programs"));
    expect(posts[0]).toEqual({ ref: "s11-well", choice: "Redo", words: "The name is cut.", window_png: "iVBORw0KGgo=" });

    // Step 4 opens Needs you through the registry verb; Esc skips it.
    expect(await screen.findByTestId("walk-question")).toHaveTextContent("Is the line clear?");
    expect(screen.getByTestId("walk-count")).toHaveTextContent("3 of 3");
    act(() => { fireEvent.keyDown(window, { key: "Escape" }); });
    await waitFor(() => expect(posts).toHaveLength(2));
    expect(posts[1]).toEqual({ ref: "needs-coverage", choice: "skip" });

    expect(await screen.findByTestId("walk-end")).toHaveTextContent("Thanks · 1 answer");
    fireEvent.click(screen.getByTestId("walk-back"));
    expect(window.location.search).toBe("");
    expect(screen.queryByTestId("walk-end")).toBeNull();
    // The windows the walk opened stay open.
    expect(document.getElementById("chair:needs")).not.toBeNull();
  });

  it("records the words as \"words\" when he presses Send and no choice; no choice is the default", async () => {
    vi.stubGlobal("fetch", hub());
    render(<WalkRunner />);
    fireEvent.click(await screen.findByTestId("walk-next", {}, { timeout: 3000 }));
    expect(await screen.findByTestId("walk-question")).toHaveTextContent("Does the well read clearly?");
    // Every choice is the same weight: none reads as the default.
    for (const name of ["Keep", "Redo"]) {
      expect(screen.getByRole("button", { name }).className).not.toMatch(/primary/);
    }
    expect(screen.queryByTestId("walk-send")).toBeNull();
    fireEvent.click(screen.getByTestId("walk-say-more"));
    expect(screen.queryByTestId("walk-send")).toBeNull();
    fireEvent.change(screen.getByRole("textbox", { name: "Say more" }), { target: { value: "No, broken." } });
    fireEvent.click(screen.getByTestId("walk-send"));

    await waitFor(() => expect(posts).toHaveLength(1));
    expect(posts[0]).toEqual({ ref: "s11-well", choice: "words", words: "No, broken.", window_png: "iVBORw0KGgo=" });
    expect(await screen.findByTestId("walk-question")).toHaveTextContent("Is the line clear?");
  });

  it("marks and shoots only the step's window, never a newer window of another app", async () => {
    vi.stubGlobal("fetch", hub());
    // A newer window of another app holds a part that matches the selector.
    const other = mountWindow("surface-project-memory",
      `<section data-testid="programs-make"><ul data-testid="programs-make-rows"><li>Update draft</li></ul></section>`, 30);
    rects.set(other.querySelector("[data-testid='programs-make-rows']")!, () => ({ left: 700, top: 400, width: 200, height: 30 }));
    render(<WalkRunner />);
    const next = await screen.findByTestId("walk-next", {}, { timeout: 3000 });
    // The Programs well paints a moment after the press (a lazy core).
    const programs = document.getElementById("surface-programs")!;
    programs.style.zIndex = "10";
    programs.querySelector("[data-testid='programs-make']")!.remove();
    fireEvent.click(next);
    setTimeout(() => {
      programs.insertAdjacentHTML("beforeend",
        `<section data-testid="programs-make"><ul data-testid="programs-make-rows"><li>Project</li></ul></section>`);
      rects.set(programs.querySelector("[data-testid='programs-make-rows']")!, () => ({ left: 40, top: 120, width: 260, height: 32 }));
    }, 300);

    expect(await screen.findByTestId("walk-question")).toHaveTextContent("Does the well read clearly?");
    await waitFor(() => expect(screen.getByTestId("walk-ring").style.left).toBe("34px"));
    expect(screen.getByTestId("walk-ring").style.top).toBe("114px");
    fireEvent.click(screen.getByRole("button", { name: "Redo" }));
    await waitFor(() => expect(posts).toHaveLength(1));
    expect(mocks.captureWindowPng).toHaveBeenCalledTimes(1);
    expect(mocks.captureWindowPng).toHaveBeenCalledWith(programs);
  });

  it("says the step's window is not open and skips the step", async () => {
    vi.stubGlobal("fetch", hub());
    // Needs you does not open (its verb runs, no window comes).
    mocks.verbById.mockImplementation((id: string) => ({ id, ghost: () => null, run: () => undefined }));
    // A People button in another window must not be marked.
    mountWindow("surface-meetings", `<button data-testid="needs-open-people">Elsewhere</button>`, 40);
    render(<WalkRunner />);
    fireEvent.click(await screen.findByTestId("walk-next", {}, { timeout: 3000 }));
    fireEvent.click(await screen.findByRole("button", { name: "Keep" }));
    await waitFor(() => expect(posts).toHaveLength(1));
    expect(await screen.findByTestId("walk-line", {}, { timeout: 9000 }))
      .toHaveTextContent("The Needs you window is not open · This step is skipped");
    expect(screen.queryByTestId("walk-ring")).toBeNull();
    // Nothing marked, nothing dimmed: the desk stays live.
    expect(screen.queryAllByTestId(/^walk-backdrop-/)).toHaveLength(0);
    expect(await screen.findByTestId("walk-end", {}, { timeout: 4000 })).toHaveTextContent("Thanks · 1 answer");
    expect(posts).toHaveLength(1);
  }, 20000);

  it("docks the card as one sheet above the dock on a 390 x 844 phone and keeps the part above it", async () => {
    vi.stubGlobal("fetch", hub());
    document.documentElement.style.setProperty("--desk-dock-h", "64px");
    act(() => {
      Object.assign(window, { innerWidth: 390, innerHeight: 844 });
      window.dispatchEvent(new Event("resize"));
    });
    // Programs paints its New program press low in a scrolling body.
    let scrolled = 0;
    mocks.openSurface.mockImplementation(() => {
      const element = mountWindow("surface-programs",
        `<div data-testid="body" style="overflow-y: auto"><button data-testid="programs-new">New program</button></div>`);
      const body = element.querySelector<HTMLElement>("[data-testid='body']")!;
      Object.defineProperty(body, "scrollTop", { get: () => scrolled, set: (value: number) => { scrolled = value; } });
      rects.set(body, () => ({ left: 0, top: 60, width: 390, height: 720 }));
      rects.set(element.querySelector("[data-testid='programs-new']")!,
        () => ({ left: 16, top: 700 - scrolled, width: 120, height: 40 }));
      return true;
    });
    render(<WalkRunner />);
    const card = await screen.findByTestId("walk-card", {}, { timeout: 3000 });
    rects.set(card, () => ({ left: 0, top: 844 - 64 - 200, width: 390, height: 200 }));
    act(() => { window.dispatchEvent(new Event("resize")); });

    // One full-width sheet above the dock, at most 40 % of the height.
    expect(card).toHaveAttribute("data-sheet");
    expect(card.style.left).toBe("0px");
    expect(card.style.right).toBe("0px");
    expect(card.style.bottom).toBe("64px");
    expect(card.style.maxHeight).toBe("337px");
    // The part scrolled into the band above the sheet: not covered.
    const target = screen.getByTestId("programs-new");
    await waitFor(() => expect(target.getBoundingClientRect().bottom).toBeLessThanOrEqual(844 - 64 - 200));
    expect(target.getBoundingClientRect().top).toBeGreaterThanOrEqual(60);
    // The dim and the ring still mark it, where it is now: the dim ends at
    // the ring on each side, nothing of it over the part.
    await waitFor(() => expect(screen.getByTestId("walk-ring").style.top)
      .toBe(`${target.getBoundingClientRect().top - 6}px`));
    const ring = screen.getByTestId("walk-ring").style;
    const dim = (side: string) => screen.getByTestId(`walk-backdrop-${side}`).style;
    expect(dim("top").height).toBe(ring.top);
    expect(dim("bottom").top).toBe(`${parseFloat(ring.top) + parseFloat(ring.height)}px`);
    expect(dim("left").width).toBe(ring.left);
    expect(dim("right").left).toBe(`${parseFloat(ring.left) + parseFloat(ring.width)}px`);
  });

  it("shows one plain line and gets out of the way when the hub refuses the token", async () => {
    vi.stubGlobal("fetch", hub(404));
    render(<WalkRunner />);
    const line = await screen.findByTestId("walk-refused");
    expect(line).toHaveTextContent("This walk link does not open. The desk is as usual.");
    expect(screen.queryByTestId("walk-card")).toBeNull();
    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(window.location.search).toBe("");
    expect(mocks.openSurface).not.toHaveBeenCalled();
  });

  it("runs nothing without a walk on the address", () => {
    window.history.replaceState({}, "", "/");
    const fetcher = hub();
    vi.stubGlobal("fetch", fetcher);
    const { container } = render(<WalkRunner />);
    expect(container).toBeEmptyDOMElement();
    expect(fetcher).not.toHaveBeenCalled();
  });
});
