/* Betterment A3 — the automation window, on the hub's own recorded answers.
 *
 * The answers come from tests/integration/test_desk_workbenches.py
 * (test_the_automation_window_reads_its_sentence_results_and_lessons: the
 * real routes, the real runner, a recorded engine reply; HOLDSPEAK_WIRE_WRITE=1
 * rewrites web/src/desk/__tests__/fixtures/automation-hub/*.json). Only
 * `fetch` is replaced: a GET replays the current step's answer; Run now,
 * Forget and Open move to the step the hub recorded after that press.
 * The sends read of the Send fold answers an empty list (its own tests:
 * desk/__tests__/send.app.test.tsx). */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../store";
import { AutomationWindow, AUTOMATION_WINDOW_SIZE } from "../components/automation/AutomationWindow";
import empty from "./fixtures/automation-hub/empty.json";
import one from "./fixtures/automation-hub/one.json";
import failed from "./fixtures/automation-hub/failed.json";
import populated from "./fixtures/automation-hub/populated.json";
import forgot from "./fixtures/automation-hub/forgot.json";
import used from "./fixtures/automation-hub/used.json";
import { openPrimitive, openSurfaceOr } from "../shell";
import { seatMounted, seatUnmounted } from "../deleteSeat";
import { OBJECT_DELETE_REQUEST } from "../verbRegistry";

vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openPrimitive: vi.fn(),
  openSurfaceOr: vi.fn(),
}));

type Step = { workbench_id: string; gets: Record<string, unknown> };
const WB = (empty as Step).workbench_id;
const DETAIL = `/api/workbenches/${WB}`;

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

const hub = {
  step: empty as Step,
  /** The step a Run now press moves to. */
  afterRun: [] as Step[],
  calls: [] as Array<{ method: string; url: string; body?: unknown }>,
  hold: null as null | (() => void),
};

function hubFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = String(input);
  const method = (init?.method ?? "GET").toUpperCase();
  const body = init?.body ? JSON.parse(String(init.body)) : undefined;
  if (method !== "GET") hub.calls.push({ method, url, body });
  if (url.startsWith("/api/channels/sends")) return Promise.resolve(json({ sends: [] }));
  if (method === "POST" && url === `${DETAIL}/run`) {
    const next = hub.afterRun.shift();
    if (!next) throw new Error("an unrecorded run");
    const answer = () => { hub.step = next; return json({ run: {} }); };
    if (hub.hold === null) return Promise.resolve(answer());
    return new Promise((resolve) => { hub.hold = () => resolve(answer()); });
  }
  if (method === "DELETE" && url.startsWith(`${DETAIL}/memory/`)) {
    hub.step = forgot as Step;
    return Promise.resolve(json({ success: true }));
  }
  if (method === "POST" && url.includes("/results/")) return Promise.resolve(json({ result: {} }));
  if (method === "PUT" && url === DETAIL) return Promise.resolve(json({ workbench: {} }));
  const path = url.split("?")[0];
  if (method === "GET" && path in hub.step.gets) return Promise.resolve(json(structuredClone(hub.step.gets[path])));
  throw new Error(`unrecorded ${method} ${url}`);
}

beforeEach(() => {
  hub.step = empty as Step;
  hub.afterRun = [];
  hub.calls = [];
  hub.hold = null;
  vi.stubGlobal("fetch", vi.fn(hubFetch));
  useDesk.setState({ workbenchWindows: [{ id: WB, origin: null }] });
});
afterEach(() => { vi.unstubAllGlobals(); });

const sentence = () => screen.getByTestId("automation-sentence");
const line = (name: string) => within(sentence()).getByTestId(`automation-line-${name}`);
const newest = () => screen.getByTestId("automation-newest");
/** A recorded result's artifact id (the step's own answer, never typed). */
const artifactOf = (step: unknown, index: number): string =>
  ((step as Step).gets[DETAIL] as { workbench: { results: Array<{ artifact_id: string }> } })
    .workbench.results[index].artifact_id;

async function open(step: Step) {
  hub.step = step;
  render(<AutomationWindow workbenchId={WB} />);
  await screen.findByTestId("automation-sentence");
}

describe("the sentence on top", () => {
  it("reads When, Do, About, With and Put it in in words, with no ref and no id", async () => {
    await open(empty as Step);
    expect(line("when")).toHaveTextContent("Only when I press Run now");
    expect(line("do")).toHaveTextContent("Write my weekly update from these notes.");
    expect(within(line("about")).getByText("Platform sync")).toBeInTheDocument();
    expect(within(line("about")).getByText("Hiring")).toBeInTheDocument();
    expect(line("with")).toHaveTextContent("LAN Qwen");
    expect(line("put")).toHaveTextContent("My Inbox");
    const words = screen.getByTestId("automation-window").textContent ?? "";
    expect(words).not.toMatch(/note:|note-sync|wb-friday|artifact_|wbocc_|\* \* \*/);
    // No result yet: one true line, no verbs, no fold of zero lessons.
    expect(newest()).toHaveTextContent("No results yet. Run now makes the first one.");
    expect(screen.queryByText("What it has learned")).toBeNull();
    // Only when he presses Run now: there is no start to switch on or off.
    expect(screen.queryByTestId("automation-on")).toBeNull();
  });

  it("the window opens at no less than 880 x 640 at 1440", () => {
    expect(AUTOMATION_WINDOW_SIZE.w).toBeGreaterThanOrEqual(880);
    expect(AUTOMATION_WINDOW_SIZE.h).toBeGreaterThanOrEqual(640);
    vi.stubGlobal("innerWidth", 1440);
    vi.stubGlobal("innerHeight", 900);
    useDesk.setState({ workbenchWindows: [], panelRects: {} });
    act(() => { useDesk.getState().openWorkbenchWindow("wb-sized"); });
    const rect = useDesk.getState().panelRects["workbench:wb-sized"];
    expect(rect.w).toBeGreaterThanOrEqual(880);
    expect(rect.h).toBeGreaterThanOrEqual(640);
  });

  it("Do edits in place with the mic, and Save writes the instruction", async () => {
    await open(empty as Step);
    fireEvent.click(within(line("do")).getByRole("button"));
    const box = await screen.findByRole("textbox", { name: "What it does" });
    expect(within(screen.getByTestId("automation-do-editor")).getByRole("button", { name: /Speak/ })).toBeInTheDocument();
    fireEvent.change(box, { target: { value: "Draft my team update: what shipped and what slipped." } });
    fireEvent.click(screen.getByTestId("automation-do-save"));
    await waitFor(() => expect(hub.calls).toContainEqual({
      method: "PUT", url: DETAIL, body: { instruction: "Draft my team update: what shipped and what slipped." },
    }));
    // The other lines show their value: no dead press (their editors are A4 to A6).
    for (const name of ["when", "about", "with", "put"]) expect(within(line(name)).queryByRole("button")).toBeNull();
  });
});

describe("Run now and the results", () => {
  it("shows Working… in place, then the rendered result, and nothing above it moves", async () => {
    await open(empty as Step);
    hub.afterRun = [one as Step];
    hub.hold = () => undefined;
    const card = newest();
    const sentenceBefore = sentence().innerHTML;
    fireEvent.click(screen.getByTestId("automation-run-now"));
    await waitFor(() => expect(newest()).toHaveTextContent(/Working…/));
    expect(newest()).toBe(card);
    expect(newest()).toHaveTextContent("LAN Qwen");
    expect(screen.getByTestId("automation-run-now")).toBeDisabled();
    expect(sentence().innerHTML).toBe(sentenceBefore);

    await act(async () => { hub.hold?.(); });
    await waitFor(() => expect(newest()).not.toHaveTextContent(/Working…/));
    expect(newest()).toBe(card);
    // The answer is rendered: a heading and a list, no `##`, no `**`.
    const reading = within(newest()).getByTestId("automation-reading");
    expect(within(reading).getByRole("heading", { name: "Weekly update" })).toBeInTheDocument();
    expect(within(reading).getAllByRole("listitem")).toHaveLength(2);
    expect(reading.textContent).not.toMatch(/##|\*\*/);
    // NEW, the model, where the prompt went, and its verbs.
    expect(within(newest()).getByTestId("automation-new")).toHaveTextContent("NEW");
    expect(newest()).toHaveTextContent("stub-model-7b");
    expect(newest()).toHaveTextContent("CLOUD");
    expect(within(newest()).getByTestId("automation-open-note")).toBeInTheDocument();
    expect(within(newest()).getByTestId("automation-copy")).toBeInTheDocument();
    // Showing it reads it on the hub; NEW stays while the window is open.
    const artifact = artifactOf(one, 0);
    await waitFor(() => expect(hub.calls).toContainEqual({
      method: "POST", url: `${DETAIL}/results/${artifact}/open`, body: undefined,
    }));
  });

  it("a failure says why in words, and Run again runs at once", async () => {
    await open(failed as Step);
    const failure = within(newest()).getByTestId("automation-failure");
    expect(failure).toHaveTextContent("The stub refuses: no source is attached");
    expect(within(newest()).getByText("FAILED")).toBeInTheDocument();
    hub.afterRun = [populated as Step];
    fireEvent.click(within(failure).getByRole("button", { name: "Run again" }));
    await waitFor(() => expect(within(newest()).queryByTestId("automation-failure")).toBeNull());
    expect(hub.calls.filter((c) => c.url === `${DETAIL}/run`)).toHaveLength(1);
    expect(within(newest()).getByRole("heading", { name: "Weekly update" })).toBeInTheDocument();
  });

  it("each older result is one line; a failed one keeps Run again; a line opens in place and reads it", async () => {
    await open(populated as Step);
    const lines = screen.getAllByTestId("automation-older");
    expect(lines).toHaveLength(2);
    expect(lines[0]).toHaveTextContent("Failed: The stub refuses: no source is attached");
    expect(within(lines[0]).getByRole("button", { name: "Run again" })).toBeInTheDocument();
    expect(lines[1]).toHaveTextContent("Weekly update");
    expect(within(lines[1]).getByText("NEW")).toBeInTheDocument();
    fireEvent.click(lines[1]);
    const opened = await screen.findAllByTestId("automation-reading");
    expect(opened).toHaveLength(2);
    const older = artifactOf(populated, 2);
    await waitFor(() => expect(hub.calls).toContainEqual({
      method: "POST", url: `${DETAIL}/results/${older}/open`, body: undefined,
    }));
  });
});

describe("What it has learned", () => {
  it("is a fold, closed by default; Forget removes that one lesson", async () => {
    await open(populated as Step);
    const fold = screen.getByText("What it has learned").closest("details")!;
    expect(fold).not.toHaveAttribute("open");
    const lessons = within(fold).getAllByRole("listitem");
    expect(lessons.map((l) => l.textContent)).toEqual([
      expect.stringContaining("Keep the update under ten lines."),
      expect.stringContaining("Mira owns the rollback runbook; name her first."),
    ]);
    fireEvent.click(within(lessons[0]).getByRole("button", { name: /Forget/ }));
    await waitFor(() => expect(within(screen.getByTestId("automation-lessons")).getAllByRole("listitem")).toHaveLength(1));
    const forget = hub.calls.find((c) => c.method === "DELETE")!;
    const stamp = ((populated as Step).gets[`${DETAIL}/memory`] as { entries: Array<{ timestamp: string }> }).entries[0].timestamp;
    expect(forget.url).toBe(`${DETAIL}/memory/0?at=${encodeURIComponent(stamp)}`);
    expect(screen.getByTestId("automation-lessons")).toHaveTextContent("Mira owns the rollback runbook");
  });
});

/* MCP M2: what the run's agent used, on tests/integration/test_desk_engines_tools.py's
 * recorded answers (a real hub; the fake claude CLI read 3 meetings, wrote 1 note
 * and prepared 1 send over MCP; automation-hub/used.json). */
describe("Looked at, Wrote, Prepared", () => {
  const USED = used as Step;
  type UsedResult = {
    cost_usd: number;
    used: {
      looked_at: Array<{ ref: string; label: string }>;
      wrote: Array<{ ref: string; label: string }>;
      prepared: Array<{ ref: string; label: string; destination: string }>;
    };
  };
  const result = () =>
    (USED.gets[`/api/workbenches/${USED.workbench_id}`] as { workbench: { results: UsedResult[] } })
      .workbench.results[0];

  async function openUsed() {
    hub.step = USED;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = decodeURIComponent(String(input));
      if ((init?.method ?? "GET") === "GET" && url in USED.gets) {
        return Promise.resolve(json(structuredClone(USED.gets[url])));
      }
      return hubFetch(input, init);
    }));
    useDesk.setState({ workbenchWindows: [{ id: USED.workbench_id, origin: null }] });
    render(<AutomationWindow workbenchId={USED.workbench_id} />);
    await screen.findByTestId("automation-used");
  }

  it("says what it looked at, wrote and prepared in words, each a link, and its cost", async () => {
    await openUsed();
    const slot = within(newest()).getByTestId("automation-used");
    const folds = slot.querySelectorAll("details");
    expect([...folds].map((f) => f.querySelector("summary")?.textContent)).toEqual([
      expect.stringMatching(/Looked at.*3 meetings/),
      expect.stringMatching(/Wrote.*1 note/),
      expect.stringMatching(/Prepared.*1 send/),
    ]);
    // Each read object by its name, never its ref; a press opens it.
    const looked = within(slot).getByTestId("automation-looked-at");
    const names = result().used.looked_at.map((r) => r.label);
    expect(within(looked).getAllByRole("button").map((b) => b.textContent)).toEqual(names);
    fireEvent.click(within(looked).getByRole("button", { name: names[0] }));
    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", result().used.looked_at[0].ref);
    const wrote = within(slot).getByTestId("automation-wrote");
    fireEvent.click(within(wrote).getByRole("button", { name: result().used.wrote[0].label }));
    expect(openPrimitive).toHaveBeenCalledWith(result().used.wrote[0].ref);
    // The prepared send: its document to its destination, and the Send fold
    // that holds it (PREPARED ×1 from the hub's own sends read).
    const prepared = within(slot).getByTestId("automation-prepared");
    const [send] = result().used.prepared;
    expect(prepared).toHaveTextContent(`${send.label} to ${send.destination}`);
    expect(await within(prepared).findByText("PREPARED ×1")).toBeInTheDocument();
    expect(within(prepared).getByRole("button", { name: "Send" })).toBeInTheDocument();
    // The run's reported cost is in the head line.
    expect(newest()).toHaveTextContent(`$${result().cost_usd.toFixed(2)}`);
    expect(slot.textContent).not.toMatch(/meeting:|note:|note_|chs_/);
  });

  it("with no delete receipt seat on the desk, Undo is withheld (no dead verb)", async () => {
    await openUsed();
    expect(within(newest()).queryByTestId("automation-wrote-undo")).toBeNull();
  });

  it("Undo asks the desk's one delete for the note the run made", async () => {
    seatMounted();
    const asked: string[] = [];
    const listen = (event: Event) => asked.push(String((event as CustomEvent<{ ref: string }>).detail.ref));
    window.addEventListener(OBJECT_DELETE_REQUEST, listen);
    try {
      await openUsed();
      fireEvent.click(within(newest()).getByTestId("automation-wrote-undo"));
      expect(asked).toEqual([result().used.wrote[0].ref]);
      expect(within(newest()).queryByTestId("automation-wrote-undo")).toBeNull();
    } finally {
      window.removeEventListener(OBJECT_DELETE_REQUEST, listen);
      seatUnmounted();
    }
  });

  it("draws nothing for a result whose agent touched nothing", async () => {
    await open(one as Step);
    expect(within(newest()).queryByTestId("automation-used")).toBeNull();
  });
});
