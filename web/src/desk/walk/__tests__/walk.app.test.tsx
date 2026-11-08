/** The Walk (2026-11-07): the desk drives a recorded walk through open →
 * highlight → answer → next, Esc skips, and a refused token shows one line.
 * The walk and the answer are the hub's own recorded answers
 * (tests/integration/test_desk_walks.py writes __fixtures__). */
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import page from "../__fixtures__/walk.page.json";
import answer from "../__fixtures__/walk.answer.json";
import handheld from "../__fixtures__/walk.handheld.page.json";

const TOKEN = "Rec0rdedWalkT0kenRec0rdedWalkT0kenRec0rdedX";

const mocks = vi.hoisted(() => ({
  openSurface: vi.fn(),
  openSurfaceOr: vi.fn(),
  verbById: vi.fn(),
  captureViewportPng: vi.fn(),
  apiFetch: vi.fn(),
  speak: vi.fn(),
  stop: vi.fn(),
  play: vi.fn(),
  requestRoomAt: vi.fn(),
  hubSeeded: vi.fn(() => true),
}));

vi.mock("../../shell", () => ({ openSurface: mocks.openSurface, openSurfaceOr: mocks.openSurfaceOr }));
vi.mock("../../verbRegistry", () => ({ verbById: mocks.verbById }));
vi.mock("../../feedback/capture", () => ({ captureViewportPng: mocks.captureViewportPng, captureScale: () => 2 }));
// The guide's voice is the desk's one TTS seam.
vi.mock("../../../lib/tts", () => ({ speak: mocks.speak, stop: mocks.stop, enqueueSentence: vi.fn(),
  onStateChange: () => () => undefined }));
vi.mock("../../../lib/sfx", () => ({ play: mocks.play }));
vi.mock("../../openObject", () => ({ requestRoomAt: mocks.requestRoomAt }));
// The compositor's own flag: the hub's window list landed.
vi.mock("../../compositor/hubWindows", () => ({ hubSeeded: mocks.hubSeeded }));
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

import { GHOSTS, WalkRunner, arcFrames, tiltFor, travelMs } from "../WalkRunner";
import { READY_BEAT_MS, deskReady, deskSignals } from "../walk";

// The compositor's flag loads lazily (no import cycle through the registry).
beforeAll(async () => { await deskSignals; });

/** The desk as it stands after its first read: `#desk-next` and the Dock. */
function mountDesk(): { desk: HTMLElement; dock: HTMLElement } {
  const desk = document.createElement("div");
  desk.id = "desk-next";
  const dock = document.createElement("div");
  dock.className = "desk-dock";
  desk.appendChild(dock);
  document.body.appendChild(desk);
  rects.set(dock, () => ({ left: 0, top: 700, width: 600, height: 56 }));
  return { desk, dock };
}

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

function hub(status = 200, read: unknown = page) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    if (status !== 200) {
      return new Response(JSON.stringify({ code: "walk_not_found", detail: "This walk is not known." }), { status });
    }
    if (path === `/api/w/${TOKEN}` && !init?.method) return new Response(JSON.stringify(read), { status: 200 });
    if (path === "/api/projects") return new Response(JSON.stringify({ projects: [{ id: "p-1" }] }), { status: 200 });
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
  mocks.hubSeeded.mockReturnValue(true);
  mountDesk();
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
  mocks.captureViewportPng.mockResolvedValue("iVBORw0KGgo=");
});

afterEach(() => {
  cleanup();
  rects.clear();
  HTMLElement.prototype.getBoundingClientRect = realRect;
  document.documentElement.style.removeProperty("--desk-dock-h");
  Object.assign(window, { innerWidth: 1024, innerHeight: 768 });
  document.body.innerHTML = "";
  window.localStorage.removeItem("hs:walk-voice");
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("The Walk", () => {
  it("opens, marks, asks, stores the answer with the window shot and goes on", async () => {
    vi.stubGlobal("fetch", hub());
    render(<WalkRunner />);

    // Step 1 opens Programs through the surface opener and goes on by itself.
    // The walk moves one 900 ms beat after the desk is ready.
    await waitFor(() => expect(mocks.openSurface).toHaveBeenCalledWith("open-programs", undefined), { timeout: 3000 });
    // Step 2: a mark with words and Next.
    expect(await screen.findByTestId("walk-words", {}, { timeout: 3000 })).toHaveTextContent(
      "Press New program. The well opens.");
    // The mark is the part itself: it lifts and wears the warm halo; nothing
    // dims and nothing is drawn over it.
    await waitFor(() => expect(screen.getByTestId("programs-new")).toHaveClass("walk-halo"));
    expect(document.querySelectorAll(".walk-backdrop, .walk-ring")).toHaveLength(0);
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
    // The shot is the whole viewport he sees, with its metrics for the crop.
    expect(mocks.captureViewportPng).toHaveBeenCalledTimes(1);
    expect(posts[0]).toMatchObject({ ref: "s11-well", choice: "Redo", words: "The name is cut.", window_png: "iVBORw0KGgo=",
      view: { width: 1024, height: 768, dpr: 1, scale: 2 } });

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
    expect(posts[0]).toMatchObject({ ref: "s11-well", choice: "words", words: "No, broken.", window_png: "iVBORw0KGgo=" });
    expect(await screen.findByTestId("walk-question")).toHaveTextContent("Is the line clear?");
  });

  it("marks only the step's window, never a newer window of another app, and crops to its part", async () => {
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
    // The halo lands on the step's window's part, never on the other one.
    await waitFor(() => expect(programs.querySelector("[data-testid='programs-make-rows']")).toHaveClass("walk-halo"));
    expect(other.querySelector("[data-testid='programs-make-rows']")).not.toHaveClass("walk-halo");
    fireEvent.click(screen.getByRole("button", { name: "Redo" }));
    await waitFor(() => expect(posts).toHaveLength(1));
    expect(mocks.captureViewportPng).toHaveBeenCalledTimes(1);
    expect(posts[0].view).toMatchObject({ rect: { left: 40, top: 120, width: 260, height: 32 } });
  });

  it("treats a part that is in the DOM but not drawn as missing and skips the step", async () => {
    vi.stubGlobal("fetch", hub());
    // The project rows are in the window's DOM but folded away (display: none),
    // as the Room's Programs fold was live on 2026-11-08: the guide must say
    // the part is not there, not ask about a zero rectangle.
    mocks.openSurface.mockImplementation((key: string) => {
      if (key === "open-programs") {
        mountWindow("surface-programs", `<button data-testid="programs-new">New program</button>
          <section data-testid="programs-make" style="display: none"><ul data-testid="programs-make-rows"><li>Project</li></ul></section>`);
      }
      return true;
    });
    render(<WalkRunner />);
    fireEvent.click(await screen.findByTestId("walk-next", {}, { timeout: 3000 }));
    expect(await screen.findByTestId("walk-line", {}, { timeout: 9000 })).toHaveTextContent(/here yet/);
    expect(screen.queryByTestId("walk-question")).toBeNull();
    expect(document.querySelectorAll(".walk-halo")).toHaveLength(0);
  }, 20000);

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
    // Nothing marked, nothing dimmed: the desk stays live.
    expect(document.querySelectorAll(".walk-halo, .walk-backdrop")).toHaveLength(0);
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
    // The part itself is marked (the halo), and nothing dims around it.
    expect(target).toHaveClass("walk-halo");
    expect(document.querySelectorAll(".walk-backdrop")).toHaveLength(0);
    // The caption rides over the sheet, never under it.
    const slot = document.querySelector<HTMLElement>(".walk-caption-slot")!;
    expect(parseFloat(slot.style.getPropertyValue("--walk-caption-bottom"))).toBeGreaterThanOrEqual(64 + 200);
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

  it("holds his hand: the edge and the caption, a say, a press it makes itself, a scroll, an empty part skipped", async () => {
    vi.stubGlobal("fetch", hub(200, handheld));
    window.localStorage.setItem("hs:walk-voice", "on");
    // Programs: New program opens the well when it is PRESSED; its foot is
    // low in a scrolling body.
    let scrolled = 0;
    const pressed = vi.fn();
    mocks.openSurface.mockImplementation(() => {
      const element = mountWindow("surface-programs", `<div data-testid="body" style="overflow-y: auto">
        <button data-testid="programs-new">New program</button><p data-testid="programs-foot">Foot</p></div>`);
      const body = element.querySelector<HTMLElement>("[data-testid='body']")!;
      Object.defineProperty(body, "scrollTop", { get: () => scrolled, set: (value: number) => { scrolled = value; } });
      rects.set(body, () => ({ left: 0, top: 40, width: 1024, height: 700 }));
      rects.set(element.querySelector("[data-testid='programs-foot']")!,
        () => ({ left: 16, top: 1500 - scrolled, width: 200, height: 30 }));
      element.querySelector("[data-testid='programs-new']")!.addEventListener("click", () => {
        pressed();
        body.insertAdjacentHTML("beforeend",
          `<section data-testid="programs-make"><ul data-testid="programs-make-rows"><li>Project</li></ul></section>`);
      });
      return true;
    });
    // Needs you holds no person rows.
    mocks.verbById.mockImplementation((id: string) => ({ id, ghost: () => null,
      run: () => mountWindow("chair:needs", `<p>Nothing here</p>`) }));
    // The cursor shows for about a second: note it whenever it is drawn.
    let cursorSeen = false;
    const watch = new MutationObserver(() => {
      if (document.querySelector("[data-testid='walk-cursor']")) cursorSeen = true;
    });
    watch.observe(document.body, { childList: true, subtree: true });
    render(<WalkRunner />);

    // The edge is up before anything moves; no robot, no bubble, no frame.
    // With the voice on, the walk waits for one tap (iOS plays audio after
    // a gesture).
    expect(await screen.findByTestId("walk-edge")).toBeInTheDocument();
    expect(document.querySelectorAll(".walk-guide, .walk-guide-bot, .walk-bubble, .walk-frame, .walk-ring, img"))
      .toHaveLength(0);
    expect(mocks.openSurface).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("walk-begin"));

    // Step 1 says its words in the caption and the voice, and dims nothing.
    expect(await screen.findByTestId("walk-words")).toHaveTextContent("We start in Programs.");
    expect(screen.getByTestId("walk-words")).toHaveClass("walk-caption");
    await waitFor(() => expect(mocks.speak).toHaveBeenCalledWith("We start in Programs."));
    expect(screen.queryAllByTestId(/^walk-backdrop-/)).toHaveLength(0);
    expect(screen.queryByTestId("walk-card")).toBeNull();

    // Step 2: the guide presses New program itself; the cursor travels.
    expect(await screen.findByText("I press New program.", {}, { timeout: 6000 })).toBeInTheDocument();
    await waitFor(() => expect(pressed).toHaveBeenCalledTimes(1), { timeout: 4000 });
    expect(cursorSeen).toBe(true);
    watch.disconnect();
    expect(await screen.findByTestId("walk-question", {}, { timeout: 4000 })).toHaveTextContent("Does the well read clearly?");
    await waitFor(() => expect(screen.getByTestId("programs-make-rows")).toHaveClass("walk-halo"));
    await waitFor(() => expect(mocks.speak).toHaveBeenCalledWith(expect.stringContaining("Does the well read clearly?")));
    // Keep in the confirm hue, Redo in the attention hue; neither is primary.
    expect(screen.getByTestId("walk-choice-0")).toHaveAttribute("data-tone", "ok");
    expect(screen.getByTestId("walk-choice-1")).toHaveAttribute("data-tone", "warn");
    expect(screen.getByTestId("walk-dots").children).toHaveLength(3);
    fireEvent.click(screen.getByRole("button", { name: "Keep" }));
    await waitFor(() => expect(posts).toHaveLength(1));
    expect(mocks.stop).toHaveBeenCalled();
    expect(mocks.play).toHaveBeenCalledWith("latch");
    expect(posts[0]).toMatchObject({ ref: "s11-well", choice: "Keep", window_png: "iVBORw0KGgo=",
      view: { width: 1024, height: 768, dpr: 1, scale: 2, agent: expect.stringMatching(/ · /) } });

    // Step 3: the foot scrolls into the clear area before the ring draws.
    expect(await screen.findByTestId("walk-question", {}, { timeout: 4000 })).toHaveTextContent("Is the foot clear?");
    expect(scrolled).toBeGreaterThan(0);
    const foot = screen.getByTestId("programs-foot").getBoundingClientRect();
    expect(foot.top).toBeGreaterThanOrEqual(40);
    expect(foot.bottom).toBeLessThanOrEqual(768);
    expect(screen.getByTestId("walk-dots").querySelector("[data-state='done']")).not.toBeNull();
    mocks.stop.mockClear();
    fireEvent.click(screen.getByTestId("walk-skip"));
    await waitFor(() => expect(posts).toHaveLength(2));
    expect(posts[1]).toEqual({ ref: "programs-foot", choice: "skip" });
    expect(mocks.stop).toHaveBeenCalled();

    // Step 4: Needs you has no person rows: the guide says so, no question.
    expect(await screen.findByTestId("walk-line", {}, { timeout: 9000 })).toHaveTextContent("No people rows here yet");
    expect(screen.queryByTestId("walk-question")).toBeNull();
    expect(await screen.findByTestId("walk-end", {}, { timeout: 4000 })).toHaveTextContent("Thanks · 1 answer");
    expect(posts).toHaveLength(2);
    // The edge holds to the end and goes with the walk; no halo is left.
    expect(screen.getByTestId("walk-edge")).toBeInTheDocument();
    expect(document.querySelectorAll(".walk-halo")).toHaveLength(0);
    fireEvent.click(screen.getByTestId("walk-back"));
    expect(screen.queryByTestId("walk-edge")).toBeNull();
  }, 30000);

  it("swipes the sheet's handle down to skip, and keeps focus inside the sheet", async () => {
    vi.stubGlobal("fetch", hub());
    act(() => {
      Object.assign(window, { innerWidth: 430, innerHeight: 932 });
      window.dispatchEvent(new Event("resize"));
    });
    render(<WalkRunner />);
    fireEvent.click(await screen.findByTestId("walk-next", {}, { timeout: 3000 }));
    expect(await screen.findByTestId("walk-question")).toHaveTextContent("Does the well read clearly?");
    const card = screen.getByTestId("walk-card");
    expect(card).toHaveAttribute("data-sheet");
    await waitFor(() => expect(document.activeElement).toBe(card));
    // Tab from the last verb wraps to the first one in the sheet.
    const verbs = Array.from(card.querySelectorAll<HTMLElement>("button:not([disabled])"));
    verbs[verbs.length - 1].focus();
    fireEvent.keyDown(card, { key: "Tab" });
    expect(document.activeElement).toBe(verbs[0]);
    const handle = screen.getByTestId("walk-handle");
    // jsdom has no PointerEvent: a MouseEvent carries the clientY of the swipe.
    if (typeof window.PointerEvent === "undefined") {
      vi.stubGlobal("PointerEvent", class extends MouseEvent { pointerId = 1; });
    }
    fireEvent.pointerDown(handle, { clientY: 500, pointerId: 1 });
    fireEvent.pointerUp(handle, { clientY: 580, pointerId: 1 });
    await waitFor(() => expect(posts).toHaveLength(1));
    expect(posts[0]).toEqual({ ref: "s11-well", choice: "skip" });
  });

  it("opens a Project Room on the Room itself, never on its kept update posture", async () => {
    const { openWalkApp } = await import("../walk");
    expect(await openWalkApp("open-project-memory", "project:p-1")).toBe(true);
    expect(mocks.openSurface).toHaveBeenCalledWith("open-project-memory", "project:p-1");
    expect(mocks.requestRoomAt).toHaveBeenCalledWith("p-1", "room");
  });

  it("names the browser by platform and name only", async () => {
    const { walkAgent } = await import("../walk");
    expect(walkAgent("Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Mobile/15E148 Safari/604.1"))
      .toBe("iPhone · Safari 26");
    expect(walkAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"))
      .toBe("Mac · Chrome 142");
  });
});

describe("The walk waits for the desk (owner 2026-11-07: \"only launch when all is loaded\")", () => {
  afterEach(() => { vi.useRealTimers(); });

  const pressWalk = {
    title: "Ready",
    answers: {},
    steps: [
      { open: { app: "surface-programs" } },
      { press: { target: "programs-new", words: "I press New program." },
        highlight: { target: "programs-make-rows", words: "The project rows." },
        ask: { ref: "s-ready", question: "Does the well read clearly?", choices: ["Keep", "Redo"] } },
    ],
  };
  const run = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });
  // The clock and the timers are fake; the fetch's own I/O ticks stay real.
  /** The walk's own read lands (real I/O ticks; the fake clock stands). */
  const walkRead = async () => {
    for (let tick = 0; tick < 200 && !screen.queryByTestId("walk"); tick += 1) {
      await act(async () => { await new Promise((resolve) => setImmediate(resolve)); });
    }
    expect(screen.getByTestId("walk")).toBeInTheDocument();
  };
  const fakeTimers = () => vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date"] });

  it("is ready only on the desk's own signals: windows restored, desk read, Dock drawn, no window reading", () => {
    expect(deskReady()).toBe(true);
    mocks.hubSeeded.mockReturnValue(false);
    expect(deskReady()).toBe(false);
    mocks.hubSeeded.mockReturnValue(true);
    const desk = document.getElementById("desk-next")!;
    desk.setAttribute("aria-busy", "true");
    expect(deskReady()).toBe(false);
    desk.removeAttribute("aria-busy");
    const dock = document.querySelector(".desk-dock")!;
    rects.set(dock, () => ({ left: 0, top: 0, width: 0, height: 0 }));
    expect(deskReady()).toBe(false);
    rects.set(dock, () => ({ left: 0, top: 700, width: 600, height: 56 }));
    const reading = mountWindow("surface-meetings", `<div role="status" aria-busy="true"></div>`);
    expect(deskReady()).toBe(false);
    reading.remove();
    expect(deskReady()).toBe(true);
    document.querySelector(".desk-dock")!.remove();
    expect(deskReady()).toBe(false);
  });

  it("opens nothing before the desk is ready, then moves one 900 ms beat later", async () => {
    fakeTimers();
    vi.stubGlobal("fetch", hub(200, pressWalk));
    mocks.hubSeeded.mockReturnValue(false);
    render(<WalkRunner />);
    await walkRead();
    await run(5000);
    expect(screen.getByTestId("walk")).not.toHaveAttribute("data-desk-ready");
    expect(mocks.openSurface).not.toHaveBeenCalled();
    // The hub's window list lands: the marker, then the beat.
    mocks.hubSeeded.mockReturnValue(true);
    await run(100);
    expect(screen.getByTestId("walk")).toHaveAttribute("data-desk-ready");
    await run(READY_BEAT_MS - 150);
    expect(mocks.openSurface).not.toHaveBeenCalled();
    await run(200);
    expect(mocks.openSurface).toHaveBeenCalledWith("open-programs", undefined);
  });

  it("says the desk is still loading after 15 s and starts on his tap", async () => {
    fakeTimers();
    vi.stubGlobal("fetch", hub(200, pressWalk));
    mocks.hubSeeded.mockReturnValue(false);
    render(<WalkRunner />);
    await walkRead();
    await run(14_000);
    expect(screen.queryByTestId("walk-still-loading")).toBeNull();
    await run(1200);
    expect(screen.getByTestId("walk-still-loading")).toHaveTextContent("The desk is still loading");
    expect(mocks.openSurface).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("walk-still-loading"));
    await run(100);
    expect(mocks.openSurface).toHaveBeenCalledWith("open-programs", undefined);
  });

  it("presses only after the window's first read, and finds rows that land after 6 s", async () => {
    fakeTimers();
    vi.stubGlobal("fetch", hub(200, pressWalk));
    const pressed = vi.fn();
    let win: HTMLElement | null = null;
    mocks.openSurface.mockImplementation(() => {
      // The toolbar draws at once; the body reads for 2.5 s.
      win = mountWindow("surface-programs", `<button data-testid="programs-new">New program</button>
        <div data-testid="body"><div role="status" aria-busy="true"></div></div>`);
      win.querySelector("[data-testid='programs-new']")!.addEventListener("click", () => {
        pressed();
        // The well reads its projects for 8 s (past the 6 s target wait).
        win!.querySelector("[data-testid='body']")!.innerHTML =
          `<section data-testid="programs-make"><div role="status" aria-busy="true"></div></section>`;
        setTimeout(() => {
          win!.querySelector("[data-testid='programs-make']")!.innerHTML =
            `<ul data-testid="programs-make-rows"><li>Project</li></ul>`;
        }, 8000);
      });
      return true;
    });
    render(<WalkRunner />);
    await walkRead();
    await run(READY_BEAT_MS + 1000);
    expect(mocks.openSurface).toHaveBeenCalled();
    await run(2000);
    expect(pressed).not.toHaveBeenCalled();
    expect(screen.queryByTestId("walk-cursor")).toBeNull();
    win!.querySelector("[data-testid='body']")!.innerHTML = "";
    await run(1500);
    expect(pressed).toHaveBeenCalledTimes(1);
    await run(9000);
    expect(screen.getByTestId("walk-question")).toHaveTextContent("Does the well read clearly?");
    expect(screen.getByTestId("programs-make-rows")).toHaveClass("walk-halo");
    expect(screen.queryByTestId("walk-line")).toBeNull();
  });

  it("presses like a hand: travels with a comet trail, hovers, taps with a ripple, then the real click", async () => {
    fakeTimers();
    vi.stubGlobal("fetch", hub(200, pressWalk));
    const pressed = vi.fn();
    let pressedLook = false;
    mocks.openSurface.mockImplementation(() => {
      const win = mountWindow("surface-programs", `<button data-testid="programs-new">New program</button>`);
      const button = win.querySelector<HTMLElement>("[data-testid='programs-new']")!;
      rects.set(button, () => ({ left: 900, top: 100, width: 120, height: 40 }));
      button.addEventListener("click", () => {
        pressed();
        pressedLook = button.hasAttribute("data-walk-pressed");
        win.insertAdjacentHTML("beforeend", `<ul data-testid="programs-make-rows"><li>Project</li></ul>`);
      });
      return true;
    });
    render(<WalkRunner />);
    await walkRead();
    await run(READY_BEAT_MS + 200);
    expect(mocks.openSurface).toHaveBeenCalled();
    // On its way: the cursor and its five ghosts, the click not yet.
    for (let step = 0; step < 100 && !screen.queryByTestId("walk-cursor"); step += 1) await run(10);
    await run(100);
    const cursor = screen.getByTestId("walk-cursor");
    expect(cursor).toHaveAttribute("data-phase", "travel");
    expect(screen.getAllByTestId("walk-cursor-ghost")).toHaveLength(GHOSTS);
    // The tip lands on the part's centre.
    expect(cursor.style.transform).toBe("translate(960px, 120px)");
    expect(screen.getByTestId("walk-words")).toHaveTextContent("I press New program.");
    expect(pressed).not.toHaveBeenCalled();
    // Arrived (650 ms at most): one beat of hover, still no click.
    await run(600);
    expect(screen.getByTestId("walk-cursor")).toHaveAttribute("data-phase", "hover");
    expect(pressed).not.toHaveBeenCalled();
    // The tap: the squash, the ripple at the tap point, the pressed look.
    await run(250);
    expect(screen.getByTestId("walk-cursor")).toHaveAttribute("data-phase", "tap");
    expect(screen.getByTestId("walk-ripple").style.transform).toBe("translate(960px, 120px)");
    expect(screen.getByTestId("programs-new")).toHaveAttribute("data-walk-pressed");
    expect(pressed).not.toHaveBeenCalled();
    // 120 ms later the real click lands; the cursor rests, the trail is gone.
    await run(150);
    expect(pressed).toHaveBeenCalledTimes(1);
    expect(pressedLook).toBe(false);
    expect(screen.getByTestId("walk-cursor")).toHaveAttribute("data-phase", "rest");
    expect(screen.queryAllByTestId("walk-cursor-ghost")).toHaveLength(0);
    // The asked part wears the halo; the caption carries the step's words.
    await run(2000);
    expect(screen.getByTestId("walk-question")).toHaveTextContent("Does the well read clearly?");
    expect(screen.getByTestId("programs-make-rows")).toHaveClass("walk-halo");
    expect(screen.getByTestId("walk-words")).toHaveTextContent("The project rows.");
  });
});

describe("The guide's cursor (direction C)", () => {
  it("travels 450 to 650 ms by distance, leans 8 to 12 degrees its way, and bows upward", () => {
    expect(travelMs({ x: 0, y: 0 }, { x: 10, y: 0 })).toBeGreaterThanOrEqual(450);
    expect(travelMs({ x: 0, y: 0 }, { x: 2000, y: 2000 })).toBe(650);
    expect(tiltFor({ x: 0, y: 0 }, { x: 600, y: 0 })).toBe(12);
    expect(tiltFor({ x: 600, y: 0 }, { x: 590, y: 300 })).toBe(-8);
    const frames = arcFrames({ x: 0, y: 500 }, { x: 400, y: 500 }, 10);
    expect(frames[0]).toBe("translate(0.0px, 500.0px) rotate(0.00deg)");
    expect(frames[frames.length - 1]).toMatch(/^translate\(400\.0px, 500\.0px\) rotate\(0\.00deg\)$/);
    // Mid-way it is above the straight line and leans the full 10 degrees.
    expect(frames[6]).toMatch(/translate\(200\.0px, (4[0-9]{2})\.\dpx\) rotate\(10\.00deg\)/);
  });
});
