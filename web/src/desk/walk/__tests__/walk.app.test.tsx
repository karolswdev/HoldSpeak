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
vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));

import { WalkRunner } from "../WalkRunner";

function mountWindow(id: string, html: string): void {
  const element = document.createElement("div");
  element.id = id;
  element.dataset.layer = "window";
  element.innerHTML = html;
  document.body.appendChild(element);
}

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
  window.history.replaceState({}, "", `/?walk=${TOKEN}`);
  mocks.openSurface.mockImplementation((key: string) => {
    if (key === "open-programs") {
      mountWindow("surface-programs", `<button data-testid="programs-new">New program</button>
        <section data-testid="programs-make"><div class="gadget-row">Project</div></section>`);
    }
    return true;
  });
  mocks.verbById.mockImplementation((id: string) => id === "chair.window.needs"
    ? { id, ghost: () => null, run: () => mountWindow("chair:needs", `<p data-testid="needs-people-coverage">Yours</p>`) }
    : undefined);
  mocks.captureWindowPng.mockResolvedValue("iVBORw0KGgo=");
});

afterEach(() => {
  cleanup();
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
    expect(screen.getByTestId("walk-backdrop")).toBeInTheDocument();
    expect(screen.getByTestId("walk-count")).toHaveTextContent("1 of 3");
    fireEvent.click(screen.getByTestId("walk-next"));

    // Step 3: the words, the question and the choices as library Buttons.
    expect(await screen.findByTestId("walk-question")).toHaveTextContent("Does the well read clearly?");
    expect(screen.getByTestId("walk-words")).toHaveTextContent("The project choice.");
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
