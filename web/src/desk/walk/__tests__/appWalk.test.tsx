/** An app's own walk (owner, 2026-11-09): a native mast whose app declares a
 * walk draws Show me; the press makes the walk record on the hub, the desk's
 * one WalkRunner runs it in place in the mast's window (the halo on the part,
 * the ask bar), and Keep posts to the walk's answer route. An app with no
 * walk draws no verb. The hub answers are recorded by
 * tests/unit/test_app_walks.py (__fixtures__/appwalk.*.json). */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import created from "../__fixtures__/appwalk.create.json";
import page from "../__fixtures__/appwalk.page.json";
import answer from "../__fixtures__/appwalk.answer.json";
import { recordedGet } from "../../../test/recordedHub";

const TOKEN = created.token;

const mocks = vi.hoisted(() => ({
  captureViewportPng: vi.fn(),
  speak: vi.fn(),
  stop: vi.fn(),
  play: vi.fn(),
  hubSeeded: vi.fn(() => true),
}));

vi.mock("../../feedback/capture", () => ({ captureViewportPng: mocks.captureViewportPng, captureScale: () => 2 }));
vi.mock("../../../lib/tts", () => ({ speak: mocks.speak, stop: mocks.stop, enqueueSentence: vi.fn(),
  onStateChange: () => () => undefined }));
vi.mock("../../../lib/sfx", () => ({ play: mocks.play }));
vi.mock("../../compositor/hubWindows", () => ({ hubSeeded: mocks.hubSeeded }));
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
import { ShowMe } from "../ShowMe";
import { forgetAppWalkRecords } from "../appWalks";
import { Mast } from "../../surface/patterns/Mast";
import { WindowIdContext } from "../../components/window/windowIdContext";
import { deskSignals } from "../../compositor/dom";

beforeAll(async () => { await deskSignals; });

let calls: Array<{ path: string; method: string; body?: Record<string, unknown> }> = [];

/** The hub, replaying its recorded answers for the Programs walk. */
function hub() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ path, method, body });
    if (path === "/api/walks" && method === "POST") return new Response(JSON.stringify(created), { status: 201 });
    if (path === `/api/w/${TOKEN}/answer` && method === "POST") return new Response(JSON.stringify(answer), { status: 200 });
    const read = recordedGet({ [`/api/w/${TOKEN}`]: page }, path);
    return new Response(JSON.stringify(read), { status: read ? 200 : 404 });
  });
}

/** The desk after its first read, and the Programs window the mast is in. */
function mountDesk(): HTMLElement {
  const desk = document.createElement("div");
  desk.id = "desk-next";
  const dock = document.createElement("div");
  dock.className = "desk-dock";
  desk.appendChild(dock);
  document.body.appendChild(desk);
  const box = { left: 0, top: 700, width: 600, height: 56 };
  dock.getBoundingClientRect = () => ({ ...box, x: 0, y: 700, right: 600, bottom: 756, toJSON: () => box }) as DOMRect;
  const programs = document.createElement("div");
  programs.id = "surface-programs";
  programs.dataset.layer = "window";
  programs.innerHTML = `<nav data-testid="programs-rail">Programs</nav><div data-testid="mast-slot"></div>
    <section data-testid="programs-plate">Step 2</section><ul data-testid="programs-step-ledger"><li>Step 3</li></ul>`;
  document.body.appendChild(programs);
  return programs.querySelector<HTMLElement>("[data-testid='mast-slot']")!;
}

function renderMast(app: string, slot: HTMLElement) {
  return render(
    <WindowIdContext.Provider value="surface-programs">
      <Mast kind="program" title="Ship the walk" data-testid="programs-mast">
        <ShowMe app={app} />
      </Mast>
    </WindowIdContext.Provider>,
    { container: slot },
  );
}

beforeEach(() => {
  calls = [];
  forgetAppWalkRecords();
  window.history.replaceState({}, "", "/");
  mocks.captureViewportPng.mockResolvedValue("iVBORw0KGgo=");
});

afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("An app's own walk", () => {
  it("Show me runs the app's walk in place and files Keep through the walk's answer route", async () => {
    vi.stubGlobal("fetch", hub());
    const slot = mountDesk();
    render(<WalkRunner />);
    renderMast("surface-programs", slot);

    const showMe = screen.getByTestId("show-me");
    expect(showMe).toHaveTextContent("Show me");
    expect(showMe).toHaveClass("btn--secondary");
    // At the end of the mast's verbs.
    expect(showMe.parentElement).toHaveClass("surface-mast-verbs");
    expect(showMe.parentElement!.lastElementChild).toBe(showMe);
    fireEvent.click(showMe);

    // The first press makes the walk record: title and steps, no open.
    await waitFor(() => expect(calls.find((call) => call.path === "/api/walks")).toBeTruthy());
    const made = calls.find((call) => call.path === "/api/walks")!;
    expect(made.method).toBe("POST");
    expect(made.body).toMatchObject({ title: "Programs", steps: page.steps });

    // The runner starts in place: the first step marks the rail of this window.
    const rail = document.querySelector("#surface-programs [data-testid='programs-rail']")!;
    await waitFor(() => expect(rail).toHaveClass("walk-halo"), { timeout: 4000 });
    expect(screen.getByTestId("walk-edge")).toBeInTheDocument();
    expect(screen.getByTestId("walk-words")).toHaveTextContent("All your programs are here.");
    fireEvent.click(screen.getByTestId("walk-next"));
    await waitFor(() => expect(screen.getByTestId("programs-mast")).toHaveClass("walk-halo"), { timeout: 4000 });
    fireEvent.click(screen.getByTestId("walk-next"));
    await waitFor(() => expect(screen.getByTestId("programs-plate")).toHaveClass("walk-halo"), { timeout: 4000 });
    fireEvent.click(screen.getByTestId("walk-next"));

    // The ask bar: one question, Keep and Redo.
    expect(await screen.findByTestId("walk-question", {}, { timeout: 4000 }))
      .toHaveTextContent("Is this how Programs should feel?");
    expect(screen.getByTestId("programs-step-ledger")).toHaveClass("walk-halo");
    fireEvent.click(screen.getByRole("button", { name: "Keep" }));

    await waitFor(() => expect(calls.find((call) => call.path === `/api/w/${TOKEN}/answer`)).toBeTruthy());
    const posted = calls.find((call) => call.path === `/api/w/${TOKEN}/answer`)!;
    expect(posted.body).toMatchObject({ ref: "programs-feel", choice: "Keep", window_png: "iVBORw0KGgo=" });
    expect(await screen.findByTestId("walk-end")).toHaveTextContent("Thanks · 1 answer");
  }, 20000);

  it("an app with no walk draws no Show me", () => {
    vi.stubGlobal("fetch", hub());
    const slot = mountDesk();
    renderMast("open-intelligence", slot);
    expect(screen.queryByTestId("show-me")).toBeNull();
    expect(screen.queryByText("Show me")).toBeNull();
  });
});
