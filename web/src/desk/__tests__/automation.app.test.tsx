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
import whenFriday from "./fixtures/automation-hub/when-friday.json";
import withNone from "./fixtures/automation-hub/with-none.json";
import withClaude from "./fixtures/automation-hub/with-claude.json";
import withClaudeRan from "./fixtures/automation-hub/with-claude-ran.json";
// The Engines app's own recorded answers (scripts/record_engines_fixture.py):
// detection with Claude Code found, then after its Add.
import engines from "../../features/runson/__tests__/fixtures/engines.recorded.json";

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
  /** A4: the step a When press or a With write moves to. */
  afterWhen: [] as Step[],
  afterEngine: [] as Step[],
  /** The recorded detection answers, before and after Add. */
  detect: [] as unknown[],
};

const CLAUDE = (engines as unknown as { claude: { steps: Array<{ name: string; gets: Record<string, unknown>; answer?: unknown }> } }).claude.steps;
const detectOf = (name: string) => CLAUDE.find((s) => s.name === name)!.gets["/api/concierge/detect"];

function hubFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = String(input);
  const method = (init?.method ?? "GET").toUpperCase();
  const body = init?.body ? JSON.parse(String(init.body)) : undefined;
  if (method !== "GET") hub.calls.push({ method, url, body });
  if (url.startsWith("/api/channels/sends")) return Promise.resolve(json({ sends: [] }));
  const detail = `/api/workbenches/${hub.step.workbench_id}`;
  if (method === "GET" && url === "/api/concierge/detect") return Promise.resolve(json(structuredClone(hub.detect[0])));
  if (method === "POST" && url === "/api/inference/model-library/connect-cli-engine") {
    hub.detect.shift();
    return Promise.resolve(json(CLAUDE.find((s) => s.name === "add")!.answer));
  }
  if (method === "PUT" && url === `${detail}/when`) {
    const next = hub.afterWhen.shift();
    if (!next) throw new Error("an unrecorded When");
    hub.step = next;
    return Promise.resolve(json({ workbench: {} }));
  }
  if (method === "PUT" && url === `${detail}/engine`) {
    const next = hub.afterEngine.shift();
    if (!next) throw new Error("an unrecorded With");
    hub.step = next;
    return Promise.resolve(json({ workbench: {} }));
  }
  if (method === "POST" && url === `${detail}/run`) {
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
  if (method === "GET" && path === `${detail}/memory` && !(path in hub.step.gets)) return Promise.resolve(json({ entries: [] }));
  if (method === "GET" && path in hub.step.gets) return Promise.resolve(json(structuredClone(hub.step.gets[path])));
  throw new Error(`unrecorded ${method} ${url}`);
}

beforeEach(() => {
  hub.step = empty as Step;
  hub.afterRun = [];
  hub.calls = [];
  hub.hold = null;
  hub.afterWhen = [];
  hub.afterEngine = [];
  hub.detect = [];
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
  render(<AutomationWindow workbenchId={step.workbench_id} />);
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
    // About and Put it in show their value: no dead press (their editors are A5, A6).
    for (const name of ["about", "put"]) expect(within(line(name)).queryByRole("button")).toBeNull();
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
    // A4: the fold says how many in words, never a bare count.
    expect(fold.querySelector("summary")).toHaveTextContent("2 lessons");
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

describe("A4: When, in plain choices", () => {
  it("Every Friday at 3 PM takes three presses and shows when it runs next; looking writes nothing", async () => {
    await open(empty as Step);
    expect(line("when")).toHaveTextContent("Only when I press Run now");
    hub.afterWhen = [whenFriday as Step];
    // 1: open the When line. Looking at the choices writes nothing.
    fireEvent.click(within(line("when")).getByRole("button"));
    const editor = await screen.findByTestId("automation-when-editor");
    expect(hub.calls).toEqual([]);
    // Only the events the hub can deliver; each needs its repository first.
    const events = within(editor).getByRole("group", { name: "Events" });
    expect(within(events).getAllByRole("button").map((b) => b.textContent)).toEqual([
      "GitHub asks me to review", "A pull request's checks fail", "A pull request is merged"]);
    for (const button of within(events).getAllByRole("button")) expect(button).toBeDisabled();
    expect(editor.textContent).not.toMatch(/meeting ends|Jira/);
    expect(editor.textContent).not.toMatch(/\* \*|0 15/);
    // 2: the time. 3: the day.
    fireEvent.change(within(editor).getByRole("combobox", { name: "At" }), { target: { value: "15:00" } });
    expect(hub.calls).toEqual([]);
    fireEvent.click(within(editor).getByRole("button", { name: "Every Friday" }));
    await waitFor(() => expect(hub.calls).toContainEqual({
      method: "PUT", url: `${DETAIL}/when`, body: { kind: "schedule", every: "week", time: "15:00", day: 5 },
    }));
    await waitFor(() => expect(line("when")).toHaveTextContent("Every Friday at 15:00"));
    // Next: the recorded fire time, in this machine's zone.
    const next = new Date(((whenFriday as Step).gets[DETAIL] as { workbench: { next_run_at: string } }).workbench.next_run_at);
    const day = next.toLocaleDateString("en-US", { weekday: "short" });
    const at = `${String(next.getHours()).padStart(2, "0")}:${String(next.getMinutes()).padStart(2, "0")}`;
    expect(screen.getByTestId("automation-next")).toHaveTextContent(`Next: ${day} ${at}`);
    expect(within(line("when")).getByRole("button", { name: /When/ })).toBeInTheDocument();
    // Its choice reads as chosen; the switch is on.
    expect(within(screen.getByTestId("automation-when-editor")).getByRole("button", { name: "Every Friday" }))
      .toHaveAttribute("aria-pressed", "true");
    expect(within(screen.getByTestId("automation-on")).getByRole("checkbox")).toBeChecked();
    expect(hub.calls.filter((c) => c.method !== "POST")).toHaveLength(1);
  });
});

describe("A4: With, the engine in place", () => {
  it("on a desk with no engine, With > Add makes Run now work, with no other window", async () => {
    hub.detect = [detectOf("found"), detectOf("add")];
    await open(withNone as Step);
    const windows = useDesk.getState().workbenchWindows.length;
    expect(line("with")).toHaveTextContent("Choose an engine");
    // 1: open With. The found engine says where its prompt goes.
    fireEvent.click(within(line("with")).getByRole("button"));
    const editor = await screen.findByTestId("automation-with-editor");
    const found = await within(editor).findByRole("button", { name: "Add Claude Code" });
    const row = found.closest("li")!;
    expect(row).toHaveTextContent("ANTHROPIC");
    // 2: Add (the Engines app's own path), then this automation uses it.
    hub.afterEngine = [withClaude as Step];
    fireEvent.click(found);
    await waitFor(() => expect(hub.calls.map((c) => [c.method, c.url])).toEqual([
      ["POST", "/api/inference/model-library/connect-cli-engine"],
      ["PUT", `/api/workbenches/${(withNone as Step).workbench_id}/engine`],
    ]));
    expect(hub.calls[0].body).toMatchObject({ draft: { preset: "claude", profile_id: "agent-claude", expected_profile_revision: 0 } });
    expect(hub.calls[1].body).toEqual({ profile_id: "agent-claude" });
    await waitFor(() => expect(line("with")).toHaveTextContent("Claude Code"));
    expect(line("with")).toHaveTextContent("CLOUD");
    // The engine in use offers this automation's own Spend limit per run.
    await waitFor(() => expect(within(screen.getByTestId("automation-with-editor")).getByText("In use")).toBeInTheDocument());
    expect(screen.getByTestId("automation-spend")).toBeInTheDocument();
    // 3: Run now gives the result.
    hub.afterRun = [withClaudeRan as Step];
    fireEvent.click(screen.getByTestId("automation-run-now"));
    await waitFor(() => expect(within(newest()).getByRole("heading", { name: "Weekly update" })).toBeInTheDocument());
    expect(useDesk.getState().workbenchWindows.length).toBe(windows);
  });

  it("the Spend limit per run saves the automation's own amount, and refuses one out of range", async () => {
    hub.detect = [detectOf("add")];
    await open(withClaude as Step);
    fireEvent.click(within(line("with")).getByRole("button"));
    const spend = await screen.findByTestId("automation-spend");
    const box = within(spend).getByRole("textbox", { name: "Spend limit per run" });
    fireEvent.change(box, { target: { value: "2000" } });
    fireEvent.click(within(spend).getByRole("button", { name: "Save limit" }));
    expect(within(spend).getByRole("alert")).toHaveTextContent("Type an amount above $0 and at most $1000.");
    expect(hub.calls).toEqual([]);
    hub.afterEngine = [withClaude as Step];
    fireEvent.change(box, { target: { value: "$0.50" } });
    fireEvent.click(within(spend).getByRole("button", { name: "Save limit" }));
    await waitFor(() => expect(hub.calls).toContainEqual({
      method: "PUT", url: `/api/workbenches/${(withClaude as Step).workbench_id}/engine`, body: { spend_limit_usd: 0.5 },
    }));
  });
});
