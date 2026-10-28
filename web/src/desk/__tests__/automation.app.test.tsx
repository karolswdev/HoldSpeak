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
import type { ComponentProps } from "react";
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
import used from "./fixtures/automation-hub/used.json";
import aboutNone from "./fixtures/automation-hub/about-none.json";
import aboutPlatform from "./fixtures/automation-hub/about-platform.json";
import aboutPlatformRan from "./fixtures/automation-hub/about-platform-ran.json";
import aboutPicked from "./fixtures/automation-hub/about-picked.json";
import aboutEvent from "./fixtures/automation-hub/about-event.json";
import aboutDesk from "./fixtures/automation-hub/about-desk.json";
import starters from "./fixtures/automation-hub/starters.json";
import fridayNew from "./fixtures/automation-hub/friday-new.json";
import fridayClaude from "./fixtures/automation-hub/friday-claude.json";
import fridayRan from "./fixtures/automation-hub/friday-ran.json";
import homeRows from "./fixtures/automation-hub/home-rows.json";
import oldQueue from "./fixtures/automation-hub/old-queue.json";
import oldQueueRan from "./fixtures/automation-hub/old-queue-ran.json";
import oldMadeOne from "./fixtures/automation-hub/old-made-one.json";
import folderRan from "./fixtures/automation-hub/folder-ran.json";
import folderEvent from "./fixtures/automation-hub/folder-event.json";
import putNew from "./fixtures/automation-hub/put-new.json";
import putFolder from "./fixtures/automation-hub/put-folder.json";
import { WorkbenchesHomeCore } from "../../pages/cores/WorkbenchesHomeCore";
import { NewWorkbenchChooser } from "../components/NewWorkbenchChooser";
import { AutomationBuilder } from "../components/automation/AutomationBuilder";
import type { AutomationDetail } from "../components/automation/model";
import { EMPTY_ITEMS, fromWireDirectory, fromWireNote } from "../api";
import { useDropHand } from "../hand";
import type { Directory, Note } from "../../lib/primitives";
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
const DETAIL_OF = (step: unknown) => `/api/workbenches/${(step as Step).workbench_id}`;

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
  /** A5: the step an About write (PUT sources) moves to. */
  afterPut: [] as Step[],
  /** A7: the step a starter press (instantiate) moves to. */
  afterCreate: [] as Step[],
  /** The recorded detection answers, before and after Add. */
  detect: [] as unknown[],
  /** A9: the step Make this one automation moves to. */
  afterMakeOne: [] as Step[],
  /** A6: an engine write held open until the test releases it. */
  holdEngine: null as null | (() => void),
  /** A6: the step a Put it in write (PUT output_target) moves to. */
  afterTarget: [] as Step[],
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
  if (method === "POST" && url.startsWith("/api/workbench-templates/") && url.endsWith("/instantiate")) {
    const next = hub.afterCreate.shift();
    if (!next) throw new Error("an unrecorded starter press");
    hub.step = next;
    return Promise.resolve(json({ workbench: { id: next.workbench_id } }, 201));
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
    const answer = () => { hub.step = next; return json({ workbench: {} }); };
    if (hub.holdEngine === null) return Promise.resolve(answer());
    return new Promise((resolve) => { hub.holdEngine = () => resolve(answer()); });
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
  if (method === "POST" && url === "/api/repositories") {
    const answer = hub.step.gets["POST /api/repositories"];
    if (!answer) throw new Error("an unrecorded Add folder");
    return Promise.resolve(json(structuredClone(answer)));
  }
  if (method === "POST" && url === `${detail}/make-one`) {
    const next = hub.afterMakeOne.shift();
    if (!next) throw new Error("an unrecorded Make this one automation");
    hub.step = next;
    return Promise.resolve(json({ workbench: {} }));
  }
  if (method === "POST" && url.includes("/results/")) return Promise.resolve(json({ result: {} }));
  if (method === "PUT" && url === detail && body && "sources" in body) {
    const next = hub.afterPut.shift();
    if (!next) throw new Error("an unrecorded About");
    hub.step = next;
    return Promise.resolve(json({ workbench: {} }));
  }
  if (method === "PUT" && url === detail && body && "output_target" in body) {
    const next = hub.afterTarget.shift();
    if (!next) throw new Error("an unrecorded Put it in");
    hub.step = next;
    return Promise.resolve(json({ workbench: {} }));
  }
  if (method === "PUT" && url === detail) return Promise.resolve(json({ workbench: {} }));
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
  hub.afterPut = [];
  hub.afterCreate = [];
  hub.afterMakeOne = [];
  hub.holdEngine = null;
  hub.afterTarget = [];
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

function blankBuilderDetail(): AutomationDetail {
  const detail = ((fridayNew as Step).gets[DETAIL_OF(fridayNew)] as { workbench: unknown }).workbench;
  return {
    ...(detail as AutomationDetail),
    instruction: "",
    instruction_shown: "",
    results: [],
    items: [],
  };
}

function renderBuilder(
  overrides: Partial<ComponentProps<typeof AutomationBuilder>> = {},
) {
  const callbacks = {
    onSaveDo: vi.fn(async () => true),
    onSaveSources: vi.fn(async () => true),
    onChooseEngine: vi.fn(async () => true),
    onSpendLimit: vi.fn(async () => true),
    onChooseWhen: vi.fn(async () => true),
    onChoosePut: vi.fn(async () => true),
    onChooseReview: vi.fn(async () => true),
    onPending: vi.fn(),
    onDone: vi.fn(),
  };
  render(
    <AutomationBuilder
      detail={blankBuilderDetail()}
      pending={false}
      whenSaving={null}
      saveError={null}
      {...callbacks}
      {...overrides}
    />,
  );
  return callbacks;
}

describe("the guided automation setup", () => {
  it("cannot skip an empty Do through the step rail and finish setup", () => {
    const callbacks = renderBuilder();
    const put = screen.getByTestId("automation-setup-step-put");
    expect(put).toBeDisabled();
    fireEvent.click(put);
    expect(screen.getByTestId("automation-setup-do")).toBeInTheDocument();
    expect(screen.queryByTestId("automation-setup-done")).toBeNull();
    expect(callbacks.onDone).not.toHaveBeenCalled();
    expect(callbacks.onSaveDo).not.toHaveBeenCalled();
  });

  it("keeps a Do draft when Back returns from About", async () => {
    const callbacks = renderBuilder();
    const box = screen.getByRole("textbox", { name: "What it does" });
    fireEvent.change(box, { target: { value: "Keep this draft" } });
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await screen.findByTestId("automation-setup-about");
    expect(callbacks.onSaveDo).toHaveBeenCalledWith("run", "Keep this draft");
    fireEvent.click(screen.getByTestId("automation-setup-back"));
    expect(screen.getByRole("textbox", { name: "What it does" })).toHaveValue("Keep this draft");
  });

  it("stays on Do and keeps the draft when its save fails", async () => {
    const onSaveDo = vi.fn(async () => false);
    renderBuilder({ onSaveDo });
    const box = screen.getByRole("textbox", { name: "What it does" });
    fireEvent.change(box, { target: { value: "Do not lose this" } });
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await waitFor(() => expect(onSaveDo).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId("automation-setup-about")).toBeNull();
    expect(screen.getByRole("textbox", { name: "What it does" })).toHaveValue("Do not lose this");
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await waitFor(() => expect(onSaveDo).toHaveBeenCalledTimes(2));
  });

  it("does not run while Next advances through setup or when Done returns", async () => {
    const onDone = vi.fn();
    renderBuilder({ onDone });
    fireEvent.change(screen.getByRole("textbox", { name: "What it does" }), { target: { value: "Prepare it" } });
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await screen.findByTestId("automation-setup-about");
    for (const step of ["with", "when", "put"] as const) {
      fireEvent.click(screen.getByTestId("automation-setup-next"));
      await screen.findByTestId(`automation-setup-${step}`);
    }
    fireEvent.click(screen.getByTestId("automation-setup-done"));
    expect(onDone).toHaveBeenCalledTimes(1);
  });
});

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
      method: "PUT", url: DETAIL, body: {
        do_kind: "run",
        instruction: "Draft my team update: what shipped and what slipped.",
      },
    }));
    // A6: Put it in is pressable now (its editor unfolds in place).
    expect(within(line("put")).getByRole("button", { name: /Put it in/ })).toBeInTheDocument();
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
    // NEW, the model by name (no scope word: owner ruling 2026-10-25), and
    // its verbs.
    expect(within(newest()).getByTestId("automation-new")).toHaveTextContent("New");
    expect(newest()).toHaveTextContent("stub-model-7b");
    expect(newest()).not.toHaveTextContent("CLOUD");
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
    expect(within(newest()).getByText("Failed")).toBeInTheDocument();
    hub.afterRun = [populated as Step];
    fireEvent.click(within(failure).getByRole("button", { name: "Run again" }));
    await waitFor(() => expect(within(newest()).queryByTestId("automation-failure")).toBeNull());
    expect(hub.calls.filter((c) => c.url === `${DETAIL}/run`)).toHaveLength(1);
    expect(within(newest()).getByRole("heading", { name: "Weekly update" })).toBeInTheDocument();
  });

  it("window grammar: the results are a list view; a press shows that result below the list and reads it", async () => {
    await open(populated as Step);
    const rows = within(screen.getByTestId("automation-result-list")).getAllByTestId("automation-result-row");
    expect(rows).toHaveLength(3);
    // The newest is the selected row, and the reader below shows it.
    expect(rows[0]).toHaveAttribute("aria-selected", "true");
    expect(rows[1]).toHaveTextContent("Failed: The stub refuses: no source is attached");
    expect(within(rows[1]).getByTestId("automation-result-state")).toHaveTextContent("Failed");
    expect(rows[2]).toHaveTextContent("Weekly update");
    expect(within(rows[2]).getByTestId("automation-result-state")).toHaveTextContent("New");
    // A failed result keeps Run again where it reads.
    fireEvent.click(within(rows[1]).getAllByRole("button")[0]);
    expect(within(newest()).getByRole("button", { name: "Run again" })).toBeInTheDocument();
    fireEvent.click(within(rows[2]).getAllByRole("button")[0]);
    await waitFor(() => expect(within(newest()).getByTestId("automation-reading")).toBeInTheDocument());
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
    // A10: an agent engine's egress chip names its vendor.
    expect(line("with")).toHaveTextContent("ANTHROPIC");
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

  it("a refused spend save keeps the draft, handles the rejection and permits a real retry", async () => {
    hub.detect = [detectOf("add")];
    await open(withClaude as Step);
    fireEvent.click(within(line("with")).getByRole("button"));
    const spend = await screen.findByTestId("automation-spend");
    const box = within(spend).getByRole("textbox", { name: "Spend limit per run" });
    const save = within(spend).getByRole("button", { name: "Save limit" });
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) =>
      String(input).endsWith("/engine") && init?.method === "PUT"
        ? Promise.resolve(json({ error: "Spend limit rejected" }, 503))
        : hubFetch(input, init)));
    fireEvent.change(box, { target: { value: "0.75" } });
    fireEvent.click(save);
    expect(await within(spend).findByRole("alert")).toHaveTextContent("Spend limit not saved");
    expect(box).toHaveValue("0.75");
    expect(save).toBeEnabled();

    vi.stubGlobal("fetch", hubFetch);
    hub.afterEngine = [withClaude as Step];
    fireEvent.click(save);
    await waitFor(() => expect(hub.calls).toContainEqual({
      method: "PUT", url: `/api/workbenches/${(withClaude as Step).workbench_id}/engine`,
      body: { spend_limit_usd: 0.75 },
    }));
    await waitFor(() => expect(save).toBeEnabled());
    expect(within(spend).queryByRole("alert")).toBeNull();
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
    expect(await within(prepared).findByText("Prepared ×1")).toBeInTheDocument();
    expect(within(prepared).getByRole("button", { name: "Send…" })).toBeInTheDocument();
    // The run's reported cost is in the head line.
    expect(newest()).toHaveTextContent(`$${result().cost_usd.toFixed(2)}`);
    expect(slot.textContent).not.toMatch(/meeting:|note:|note_|chs_/);
  });

  it("with no delete receipt seat on the desk, Undo keeps its own receipt in place (A6)", async () => {
    await openUsed();
    const note = result().used.wrote[0];
    const id = note.ref.split(":").slice(1).join(":");
    // The receipt's own Undo keeps the note: nothing is deleted.
    fireEvent.click(within(newest()).getByTestId("automation-wrote-undo"));
    const receipt = within(newest()).getByTestId("automation-wrote-receipt");
    expect(receipt).toHaveTextContent(`Removed ${note.label}`);
    fireEvent.click(within(receipt).getByRole("button", { name: "Undo" }));
    expect(receipt).toHaveTextContent(`Restored ${note.label}`);
    expect(hub.calls.filter((c) => c.method === "DELETE")).toEqual([]);
    // Undo again, and the receipt's window ends: the desk's delete runs.
    const deleted: string[] = [];
    const fetchNow = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if ((init?.method ?? "GET") === "DELETE" && String(input).startsWith("/api/notes/")) {
        deleted.push(decodeURIComponent(String(input).slice("/api/notes/".length)));
        return Promise.resolve(json({ success: true }));
      }
      return (fetchNow as typeof fetch)(input, init);
    }));
    await waitFor(() => expect(within(newest()).getByTestId("automation-wrote-undo")).toBeInTheDocument(), { timeout: 3000 });
    vi.useFakeTimers({ toFake: ["setInterval", "setTimeout", "Date"] });
    try {
      fireEvent.click(within(newest()).getByTestId("automation-wrote-undo"));
      await act(async () => { vi.advanceTimersByTime(9000); });
    } finally {
      vi.useRealTimers();
    }
    await waitFor(() => expect(deleted).toEqual([id]));
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

/* ── A5: About ──────────────────────────────────────────────────────────
 * The picker's desk is the hub's own recorded lists (/api/notes,
 * /api/directories; about-desk.json), read into the store the way loadAll
 * reads them. */
function seedDesk() {
  const gets = (aboutDesk as Step).gets as Record<string, { notes?: unknown[]; directories?: unknown[] }>;
  useDesk.setState({ items: {
    ...EMPTY_ITEMS,
    note: (gets["/api/notes"].notes ?? []).map(fromWireNote).filter((n): n is Note => n !== null),
    directory: (gets["/api/directories"].directories ?? []).map(fromWireDirectory).filter((d): d is Directory => d !== null),
  } });
}

describe("About (A5)", () => {
  it("adds Platform sync by typing \"plat\" in 2 presses; the chip is named and the result cites it", async () => {
    seedDesk();
    await open(aboutNone as Step);
    expect(line("about")).toHaveTextContent("What is it about?");
    let presses = 0;
    fireEvent.click(within(line("about")).getByRole("button")); presses += 1;
    const well = await screen.findByRole("textbox", { name: "Find by name" });
    fireEvent.change(well, { target: { value: "plat" } });
    hub.afterPut = [aboutPlatform as Step];
    fireEvent.click(screen.getByRole("button", { name: "Add Platform sync" })); presses += 1;
    await waitFor(() => expect(hub.calls).toContainEqual({ method: "PUT", url: DETAIL_OF(aboutNone), body: { sources: ["note:note-sync"] } }));
    // The chip on the line and in the editor (with its Remove).
    const chips = await within(line("about")).findAllByTestId("automation-about-chips");
    for (const chip of chips) expect(chip).toHaveTextContent("Platform sync");
    expect(presses).toBe(2);
    // The typed text is never deleted: it stays for the next pick.
    expect(screen.getByRole("textbox", { name: "Find by name" })).toHaveValue("plat");
    expect(screen.getByRole("button", { name: "Platform sync (added)" })).toBeDisabled();

    hub.afterRun = [aboutPlatformRan as Step];
    fireEvent.click(screen.getByTestId("automation-run-now"));
    await waitFor(() => expect(within(newest()).getByTestId("automation-reading")).toHaveTextContent("Platform sync"));
  });

  it("finds drawers and the relative sets by name, and Remove takes a chip off", async () => {
    seedDesk();
    await open(aboutPlatform as Step);
    fireEvent.click(within(line("about")).getByRole("button"));
    // An empty well offers the relative sets.
    expect(await screen.findByRole("button", { name: "Add This week's meetings" })).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Find by name" }), { target: { value: "work" } });
    expect(screen.getByRole("button", { name: "Add Notes in Work" })).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Find by name" }), { target: { value: "zzqx" } });
    expect(screen.getByText("Nothing on this desk has that name")).toBeInTheDocument();
    hub.afterPut = [aboutNone as Step];
    fireEvent.click(screen.getByRole("button", { name: "Remove Platform sync" }));
    await waitFor(() => expect(hub.calls).toContainEqual({ method: "PUT", url: DETAIL_OF(aboutPlatform), body: { sources: [] } }));
  });

  it("names every kind of pick (a set, a drawer, a person) and never shows a ref", async () => {
    await open(aboutPicked as Step);
    const about = line("about");
    for (const name of ["Platform sync", "This week's meetings", "Notes in Work", "Mira Chen", "Missing source"]) {
      expect(about).toHaveTextContent(name);
    }
    expect(about.textContent).not.toMatch(/person:|zone:|meetings:this_week|rel-/);
  });

  it("a desk object dropped on the window becomes a chip", async () => {
    await open(aboutNone as Step);
    const body = screen.getByTestId("automation-window");
    act(() => useDropHand.getState().startDrag({
      origin: { kind: "note", id: "note-sync", title: "Platform sync" },
      source: { kind: "note", id: "note-sync" },
      host: "screen",
      from: { x: 0, y: 0 },
    }));
    fireEvent.dragOver(body);
    expect(body).toHaveAttribute("data-drop-ready");
    hub.afterPut = [aboutPlatform as Step];
    fireEvent.drop(body);
    await waitFor(() => expect(hub.calls).toContainEqual({ method: "PUT", url: DETAIL_OF(aboutNone), body: { sources: ["note:note-sync"] } }));
    expect(await within(line("about")).findByText("Platform sync")).toBeInTheDocument();
    expect(useDropHand.getState().drag).toBeNull();
  });

  it("an event start reads the thing that happened, and About is not edited", async () => {
    await open(aboutEvent as Step);
    expect(line("about")).toHaveTextContent("the review request that came in");
    expect(within(line("about")).queryByRole("button")).toBeNull();
  });
});

/* ── A7: home, New automation, and starters ─────────────────────────────
 * The hub's answers from test_a_starter_makes_one_automation_and_the_friday
 * _walk_reads_a_result: the starters and an empty desk, then the Friday team
 * update as made, with Claude Code, and after Run now. A step keeps the
 * starters' reads (the hub still answers them). */
const withStarters = (step: unknown): Step => ({
  workbench_id: (step as Step).workbench_id,
  gets: { ...(starters as Step).gets, ...(step as Step).gets },
});

function Desk() {
  const windows = useDesk((state) => state.workbenchWindows);
  return (
    <>
      <WorkbenchesHomeCore />
      <NewWorkbenchChooser />
      {windows.map((w) => <AutomationWindow key={w.id} workbenchId={w.id} />)}
    </>
  );
}

describe("A7: home, New automation and starters", () => {
  beforeEach(() => {
    // The desk's lists re-read after a create; this test reads the hub's own
    // automation answers only.
    useDesk.setState({ workbenchWindows: [], refresh: vi.fn(async () => undefined) });
  });

  it("DESIGN §6: New → Friday team update → With → Claude Code → Run now reads a result in 5 presses, one window", async () => {
    hub.step = withStarters({ workbench_id: "", gets: {} });
    hub.detect = [detectOf("found"), detectOf("add")];
    render(<Desk />);
    // The empty home: the one line, and the starters as large cards.
    expect(await screen.findByText("An automation does one job for you, again and again.")).toBeInTheDocument();
    expect(await within(screen.getByTestId("automation-home-empty")).findByTestId("automation-starter-friday-team-update")).toBeInTheDocument();
    // DELIGHT 2: the line sits under the automation object with its making verb.
    const object = screen.getByTestId("automation-home-empty").querySelector('.surface-state[data-object="automation"]') as HTMLElement;
    expect(object.querySelector(".surface-state-sprite")?.getAttribute("src")).toMatch(/cartridge\.png$/);
    expect(within(object).getByRole("button", { name: "New automation" })).toBeInTheDocument();
    let presses = 0;

    fireEvent.click(screen.getByTestId("automation-new")); presses += 1;
    const chooser = await screen.findByRole("region", { name: "New Automation" });
    const friday = await within(chooser).findByTestId("automation-starter-friday-team-update");
    expect(friday).toHaveAccessibleName("Friday team update");
    const describedBy = friday.getAttribute("aria-describedby");
    expect(describedBy).toBeTruthy();
    const matchingDescriptions = [...document.querySelectorAll<HTMLElement>("[id]")]
      .filter((element) => element.id === describedBy);
    expect(matchingDescriptions).toHaveLength(1);
    expect(chooser.contains(matchingDescriptions[0])).toBe(true);
    // The starter reads in words: never cron, never "Agent".
    expect(friday).toHaveTextContent("Every Friday at 15:00 · My Inbox");
    expect(chooser.textContent).not.toMatch(/\* \* \*|0 15|Agent|TODO|Triage|Morning Brief/);
    expect(within(chooser).getAllByRole("button").filter((b) => b.className.includes("automation-starter"))).toHaveLength(6);

    hub.afterCreate = [withStarters(fridayNew)];
    fireEvent.click(friday); presses += 1;
    await screen.findByTestId("automation-sentence");
    expect(line("when")).toHaveTextContent("Every Friday at 15:00");
    expect(line("about")).toHaveTextContent("This week's meetings");
    expect(line("about")).toHaveTextContent("This week's notes");
    expect(line("put")).toHaveTextContent("My Inbox");
    // A starter is not a recurring approval: its schedule waits for On.
    expect(within(screen.getByTestId("automation-on")).getByRole("checkbox")).not.toBeChecked();
    const windows = useDesk.getState().workbenchWindows.length;

    fireEvent.click(within(line("with")).getByRole("button")); presses += 1;
    const add = await within(await screen.findByTestId("automation-with-editor")).findByRole("button", { name: "Add Claude Code" });
    hub.afterEngine = [withStarters(fridayClaude)];
    fireEvent.click(add); presses += 1;
    await waitFor(() => expect(line("with")).toHaveTextContent("Claude Code"));

    hub.afterRun = [withStarters(fridayRan)];
    fireEvent.click(screen.getByTestId("automation-run-now")); presses += 1;
    const reading = await waitFor(() => within(newest()).getByTestId("automation-reading"));
    expect(within(reading).getByRole("heading", { name: "Weekly update" })).toBeInTheDocument();
    expect(reading.textContent).not.toMatch(/##|\*\*/);
    expect(presses).toBeLessThanOrEqual(6);
    expect(useDesk.getState().workbenchWindows.length).toBe(windows);
  });

  it("window grammar: home rows are a list view (Name, When, Engine, Last result); a programmatic press selects, one pointer press or Open opens", async () => {
    hub.step = homeRows as Step;
    render(<WorkbenchesHomeCore />);
    const [row] = await screen.findAllByTestId("automation-home-row");
    expect(row).toHaveTextContent("Friday team update");
    expect(row).toHaveTextContent(/Every Friday at 15:00/i);
    expect(row).toHaveTextContent(/Claude Code/i);
    expect(row).toHaveTextContent(/Off/i);
    // W4 (the words): one state word from the result's status; a result not
    // opened yet is the warm dot and the status bar's `1 new`.
    expect(within(row).getByTestId("automation-home-result").textContent).toMatch(/^Done/);
    expect(row.textContent).not.toMatch(/0 NEW|ITEM|PENDING|RECENT RUNS/);
    // The status bar says the count and what is new, never a zero.
    expect(screen.getByTestId("automation-home-count")).toHaveTextContent("1 automation");
    expect(screen.getByTestId("automation-home-status")).toHaveTextContent("1 new");
    expect(screen.getByTestId("automation-home-status").textContent).not.toMatch(/\b0\b/);
    const name = within(row).getAllByRole("button")[0];
    fireEvent.click(name);
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(useDesk.getState().workbenchWindows).toEqual([]);
    expect(screen.getByTestId("automation-home-run")).toBeInTheDocument();
    // W1-KIT: one pointer press (detail 1) opens it.
    fireEvent.click(name, { detail: 1 });
    expect(useDesk.getState().workbenchWindows.map((w) => w.id)).toEqual([(homeRows as Step).workbench_id]);
    fireEvent.click(screen.getByTestId("automation-home-open"));
    expect(useDesk.getState().workbenchWindows.map((w) => w.id)).toEqual([(homeRows as Step).workbench_id]);
  });

  it("one press makes one automation; a failed press says so, keeps its choice, and a second press makes it", async () => {
    hub.step = withStarters({ workbench_id: "", gets: {} });
    render(<Desk />);
    const friday = await screen.findByTestId("automation-starter-friday-team-update");
    fireEvent.click(friday); // no recorded answer: the hub call fails
    expect(await screen.findByRole("alert")).toHaveTextContent("Friday team update was not made");
    expect(friday).toHaveAttribute("aria-pressed", "true");
    expect(friday).toBeEnabled();
    expect(useDesk.getState().workbenchWindows).toEqual([]);
    hub.afterCreate = [withStarters(fridayNew)];
    fireEvent.click(friday);
    await screen.findByTestId("automation-sentence");
    // The failed press and the one that made it: one automation, one window.
    expect(hub.calls.filter((c) => c.url.endsWith("/instantiate"))).toHaveLength(2);
    expect(useDesk.getState().workbenchWindows.map((w) => w.id)).toEqual([(fridayNew as Step).workbench_id]);
    expect(friday).toBeDisabled();
  });

  it("a starter with a blank shows it highlighted until he fills it", async () => {
    hub.step = withStarters({ workbench_id: "", gets: {} });
    render(<WorkbenchesHomeCore />);
    const prep = await screen.findByTestId("automation-starter-one-on-one-prep");
    expect(prep).toHaveTextContent("About: which people?");
    expect(screen.getByTestId("automation-starter-meeting-follow-ups")).toHaveTextContent("Only when I press Run now · Needs you");
  });
});

describe("an old automation (A9)", () => {
  type Item = { id: string; title: string; status: string; result: string | null };
  const itemsOf = (step: unknown): Item[] =>
    ((step as Step).gets[DETAIL_OF(step)] as { workbench: { items: Item[] } }).workbench.items;
  const doOf = (step: unknown): string =>
    ((step as Step).gets[DETAIL_OF(step)] as { workbench: { instruction_shown: string } }).workbench.instruction_shown;

  it("a recorded TODO automation shows its tasks waiting, its agent's prompt as Do, and RAW", async () => {
    hub.step = oldQueue as Step;
    render(<AutomationWindow workbenchId={(oldQueue as Step).workbench_id} onRaw={() => undefined} />);
    await screen.findByTestId("automation-sentence");
    expect(line("do")).toHaveTextContent(doOf(oldQueue).split("\n")[0]);
    const rows = within(screen.getByTestId("automation-tasks")).getAllByTestId("automation-task");
    expect(rows.map((row) => row.textContent)).toEqual(
      itemsOf(oldQueue).map((item) => expect.stringContaining(item.title)));
    rows.forEach((row) => expect(row).toHaveTextContent("Waiting"));
    // No empty card above its tasks; the old queue view stays behind RAW.
    expect(screen.queryByTestId("automation-newest")).toBeNull();
    expect(screen.getByTestId("automation-raw")).toBeInTheDocument();
    expect(screen.getByTestId("automation-make-one")).toHaveTextContent("Make this one automation");
    // A long Do (the agent's prompt) clamps to 3 lines on a phone; "more" opens it.
    const text = line("do").querySelector(".automation-do-text")!;
    expect(text).toHaveAttribute("data-clamped");
    fireEvent.click(screen.getByTestId("automation-do-more"));
    expect(text).not.toHaveAttribute("data-clamped");
    expect(screen.getByTestId("automation-do-more")).toHaveTextContent("less");
  });

  it("its done tasks open in place to their answers, and one press makes it one automation; nothing is lost", async () => {
    hub.step = oldQueueRan as Step;
    render(<AutomationWindow workbenchId={(oldQueueRan as Step).workbench_id} onRaw={() => undefined} />);
    await screen.findByTestId("automation-sentence");
    const [first] = itemsOf(oldQueueRan);
    const row = within(screen.getByTestId("automation-tasks")).getAllByTestId("automation-task")[0];
    expect(row).toHaveTextContent("Done");
    expect(row).toHaveAttribute("aria-label", `${first.title}: Done`);
    fireEvent.click(row);
    const reading = await screen.findByTestId("automation-reading");
    expect(reading.textContent?.trim().length).toBeGreaterThan(0);
    expect(reading.textContent).not.toMatch(/##|\*\*/);

    hub.afterMakeOne = [oldMadeOne as Step];
    fireEvent.click(screen.getByTestId("automation-make-one"));
    await waitFor(() => expect(screen.queryByTestId("automation-make-one")).toBeNull());
    expect(hub.calls).toContainEqual({ method: "POST", url: `${DETAIL_OF(oldQueueRan)}/make-one`, body: undefined });
    expect(line("do")).toHaveTextContent(doOf(oldMadeOne).split("\n")[0]);
    // Its tasks and their answers stay; it is no longer a queue (no RAW).
    expect(within(screen.getByTestId("automation-tasks")).getAllByTestId("automation-task"))
      .toHaveLength(itemsOf(oldQueueRan).length);
    expect(screen.queryByTestId("automation-raw")).toBeNull();
  });
});

/* ── A6: Put it in, and the race of Run now after With ─────────────────────
 * The hub's own answers from tests/integration/test_desk_workbenches.py
 * (test_put_it_in_files_a_fresh_desk_inbox_and_new_results_show_until_opened):
 * put-new (a scheduled result in My Inbox), put-folder (Put it in the
 * HoldSpeak folder). */
describe("A6: Put it in", () => {
  type Dest = { id: string; name: string };
  const FOLDER = ((putFolder as Step).gets["/api/channels/destinations"] as { destinations: Dest[] }).destinations[0];

  it("unfolds in place: My Inbox in use, Needs you, and each saved destination; one press saves it", async () => {
    await open(putNew as Step);
    expect(line("put")).toHaveTextContent("My Inbox");
    const windows = useDesk.getState().workbenchWindows.length;
    fireEvent.click(within(line("put")).getByRole("button"));
    const editor = await screen.findByTestId("automation-put-editor");
    const choices = () => within(editor).getAllByTestId("automation-put-choice");
    await waitFor(() => expect(choices().map((c) => c.querySelector(".automation-engine-name")?.textContent))
      .toEqual(["My Inbox", "Needs you", "Today", FOLDER.name]));
    expect(choices()[0]).toHaveTextContent("In use");
    // A destination only prepares the send: the words say he presses Send.
    expect(editor).toHaveTextContent("Prepare a send (you press Send)");
    hub.afterTarget = [putFolder as Step];
    fireEvent.click(within(editor).getByRole("button", { name: `Put it in ${FOLDER.name}` }));
    await waitFor(() => expect(line("put")).toHaveTextContent(`${FOLDER.name} (you press Send)`));
    // Showing the NEW result read it (its open), then the one Put it in write.
    expect(hub.calls.filter((c) => c.method === "PUT")).toEqual([
      { method: "PUT", url: DETAIL_OF(putNew), body: { output_target: `destination:${FOLDER.id}` } }]);
    expect(useDesk.getState().workbenchWindows.length).toBe(windows);
    expect(screen.getByTestId("automation-window").textContent).not.toMatch(/destination:|holdspeak-folder/);
  });

  it("Run now right after With > Add waits for the engine to be saved, then runs on it", async () => {
    hub.detect = [detectOf("found"), detectOf("add")];
    await open(withNone as Step);
    fireEvent.click(within(line("with")).getByRole("button"));
    const found = await within(await screen.findByTestId("automation-with-editor"))
      .findByRole("button", { name: "Add Claude Code" });
    hub.afterEngine = [withClaude as Step];
    hub.afterRun = [withClaudeRan as Step];
    hub.holdEngine = () => undefined;  // the engine write is still on its way
    fireEvent.click(found);
    await waitFor(() => expect(hub.calls.map((c) => c.url)).toContain(`/api/workbenches/${(withNone as Step).workbench_id}/engine`));
    fireEvent.click(screen.getByTestId("automation-run-now"));
    await act(async () => { await Promise.resolve(); });
    // Nothing runs before the engine is saved.
    expect(hub.calls.map((c) => c.url)).not.toContain(`/api/workbenches/${(withNone as Step).workbench_id}/run`);
    expect(newest()).toHaveAttribute("data-working");
    act(() => { hub.holdEngine?.(); });
    await waitFor(() => expect(within(newest()).getByRole("heading", { name: "Weekly update" })).toBeInTheDocument());
    const order = hub.calls.map((c) => `${c.method} ${c.url.replace(/^\/api\/workbenches\/[^/]+/, "")}`);
    expect(order.indexOf("PUT /engine")).toBeLessThan(order.indexOf("POST /run"));
    expect(screen.queryByTestId("automation-refusal")).toBeNull();
  });
});

/* ── A8: one way to automate; the parked faces stay behind RAW ─────────── */
import { AutomationHost } from "../components/automation/AutomationHost";
import { useBuilderTools } from "../builderTools";
import { VERBS } from "../verbRegistry";

// The parked queue view itself has its own tests (WorkbenchWindow's); here
// only that RAW reaches it.
vi.mock("../components/WorkbenchWindow", () => ({
  WorkbenchWindow: ({ workbenchId }: { workbenchId: string }) => <div data-testid="parked-queue-window" data-id={workbenchId} />,
}));

describe("A8: park what the sentence replaces", () => {
  afterEach(() => { act(() => { useBuilderTools.getState().setOn(false); }); });

  it("the New menu has one Automation verb, and no New Workflow", () => {
    const creates = VERBS.filter((v) => v.menu === "desk" && v.group === "new").map((v) => (typeof v.label === "string" ? v.label : v.label({ selectedRef: null })));
    expect(creates.filter((label) => /automation|workflow|agent/i.test(label))).toEqual(["New Automation"]);
  });

  it("a sentence automation shows no RAW; with Builder tools on, RAW opens the parked queue view", async () => {
    hub.step = empty as Step;
    render(<AutomationHost workbenchId={WB} />);
    await screen.findByTestId("automation-sentence");
    expect(screen.queryByTestId("automation-raw")).toBeNull();
    act(() => { useBuilderTools.getState().setOn(true); });
    fireEvent.click(await screen.findByTestId("automation-raw"));
    expect(await screen.findByTestId("parked-queue-window")).toHaveAttribute("data-id", WB);
    expect(screen.queryByTestId("automation-sentence")).toBeNull();
  });
});

describe("an agent works in a folder (A10)", () => {
  type Repo = { repository: { id: string; name: string } };
  const recorded = (folderRan as Step).gets["POST /api/repositories"] as Repo;

  it("a Folder is offered only when With is an agent engine", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, repository: [
      { kind: "repository", id: "src_billing", name: "billing", sourceId: "src_billing", branch: "main", createdAt: "" },
    ] } });
    await open(empty as Step);  // With: LAN Qwen, an HTTP engine
    fireEvent.click(within(line("about")).getByRole("button"));
    await screen.findByTestId("automation-about-editor");
    expect(screen.queryByTestId("automation-folders")).toBeNull();
    // ... and its egress chip says where the prompt goes, not a vendor.
    expect(line("with")).not.toHaveTextContent("ANTHROPIC");
  });

  it("names the folder and the vendor; the result names the folder's files; a folder adds in place", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, repository: [
      { kind: "repository", id: "src_billing", name: "billing", sourceId: "src_billing", branch: "main", createdAt: "" },
    ] } });
    hub.step = folderRan as Step;
    render(<AutomationWindow workbenchId={(folderRan as Step).workbench_id} />);
    await screen.findByTestId("automation-sentence");
    expect(within(line("about")).getByTestId("automation-about-chips")).toHaveTextContent("Folder ledger");
    expect(line("with")).toHaveTextContent("Claude Code");
    // Owner ruling 2026-10-25: no egress chip in the status bar; With names
    // the engine.
    expect(screen.getByTestId("automation-status")).not.toHaveTextContent("Anthropic");
    expect(screen.getByTestId("automation-status").querySelector(".gadget-chip-egress")).toBeNull();
    const reading = within(newest()).getByTestId("automation-reading");
    expect(reading).toHaveTextContent("ledger.py");
    expect(reading).toHaveTextContent("risky_migration.sql");
    expect(screen.getByTestId("automation-window").textContent).not.toMatch(/\/tmp\/rig|repos\/ledger/);

    // A desk repository is one press; a path he types is Add folder.
    fireEvent.click(within(line("about")).getByRole("button"));
    const folders = await screen.findByTestId("automation-folders");
    const refs = ((folderRan as Step).gets[DETAIL_OF(folderRan)] as { workbench: { sources: string[] } }).workbench.sources;
    hub.afterPut = [folderRan as Step, folderRan as Step];
    fireEvent.click(within(folders).getByRole("button", { name: "Add folder billing" }));
    await waitFor(() => expect(hub.calls).toContainEqual({
      method: "PUT", url: DETAIL_OF(folderRan), body: { sources: [...refs, "repository:src_billing"] } }));
    fireEvent.change(within(folders).getByRole("textbox", { name: "Folder" }), { target: { value: "/Users/me/code/payments" } });
    fireEvent.click(within(folders).getByTestId("automation-folder-add"));
    await waitFor(() => expect(hub.calls).toContainEqual({
      method: "POST", url: "/api/repositories", body: { path: "/Users/me/code/payments" } }));
    // The recorded answer is the ledger folder, already chosen: it is not added twice.
    expect(refs).toContain(`repository:${recorded.repository.id}`);
    await waitFor(() => expect(within(folders).getByRole("textbox", { name: "Folder" })).toHaveValue(""));
    expect(hub.calls.filter((c) => c.method === "PUT")).toHaveLength(1);
  });

  it("a review-request start reads the thing that happened, keeps its folder, and offers only folders", async () => {
    hub.step = folderEvent as Step;
    render(<AutomationWindow workbenchId={(folderEvent as Step).workbench_id} />);
    await screen.findByTestId("automation-sentence");
    expect(line("about")).toHaveTextContent("Folder ledger");
    expect(within(newest()).getByTestId("automation-reading")).toHaveTextContent("risky_migration.sql");
    fireEvent.click(within(line("about")).getByRole("button"));
    expect(await screen.findByTestId("automation-folders")).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Find by name" })).toBeNull();
  });
});
