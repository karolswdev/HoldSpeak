/* The Automations app and an automation (native, 2026-11-08: the rail, the
 * mast, the plate, the ledger of runs), on the hub's own recorded answers.
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
import { useListMenu } from "../components/window/listMenu";
import { WorkMenu } from "../components/DeskMenu";
import { recordedGet } from "../../test/recordedHub";
import { useDesk } from "../store";
import { AutomationWindow, AUTOMATION_WINDOW_SIZE } from "../components/automation/AutomationWindow";
import empty from "./fixtures/automation-hub/empty.json";
import blankSentence from "./fixtures/automation-hub/blank-sentence.json";
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
import oldQueue from "./fixtures/automation-hub/old-queue.json";
import oldQueueRan from "./fixtures/automation-hub/old-queue-ran.json";
import oldMadeOne from "./fixtures/automation-hub/old-made-one.json";
import folderRan from "./fixtures/automation-hub/folder-ran.json";
import folderEvent from "./fixtures/automation-hub/folder-event.json";
import putNew from "./fixtures/automation-hub/put-new.json";
import putFolder from "./fixtures/automation-hub/put-folder.json";
// Programs PG14 (tests/integration/test_desk_automation_program.py).
import programNew from "./fixtures/automation-hub/program-new.json";
import programRan from "./fixtures/automation-hub/program-ran.json";
import programStill from "./fixtures/automation-hub/program-still.json";
import type { AutomationDetail } from "../components/automation/model";
import { EMPTY_ITEMS, fromWireDirectory, fromWireNote } from "../api";
import { useDropHand } from "../hand";
import type { Directory, Note } from "../../lib/primitives";
import { openPrimitive, openSurfaceOr } from "../shell";
import { seatMounted, seatUnmounted } from "../deleteSeat";
import { OBJECT_DELETE_REQUEST } from "../verbRegistry";

// PG14: a program run's row opens the Program window (its own tests:
// programs/__tests__/programs.app.test.tsx).
vi.mock("../programs/open", () => ({ openProgram: vi.fn() }));
import { openProgram } from "../programs/open";

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
    // PG14: a recorded step may carry the run answer that led to it.
    const answer = () => { hub.step = next; return json({ run: (next as { ran?: unknown }).ran ?? {} }); };
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
  if (method === "GET" && path in hub.step.gets) return Promise.resolve(json(recordedGet(hub.step.gets,path)));
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

const view = (name: string) => fireEvent.click(screen.getByRole("tab",{name}));
async function open(step: Step) {
  hub.step = step;
  render(<AutomationWindow workbenchId={step.workbench_id} />);
  await screen.findByTestId("automation-summary");
}
const edit = async (part="Do") => {
  fireEvent.click(screen.getByTestId("automation-edit"));
  await screen.findByTestId("automation-setup");
  if (part !== "Do") view(part);
};
const result = () => screen.getByTestId("automation-reading");

describe("the automation object grammar", () => {
  it("uses the object title, kit facts and tabs without a mast, card or row button", async () => {
    await open(empty as Step);
    const frame = screen.getByTestId("automation-window").closest(".desk-window-shell")!;
    await waitFor(()=>expect(frame).toHaveTextContent("Friday team update"));
    expect(frame.querySelector(".surface-mast,.automation-plate,.surface-spine")).toBeNull();
    expect(screen.getByTestId("automation-summary")).toHaveTextContent("Write my weekly update");
    expect(screen.getAllByRole("tab").map(row => row.textContent)).toEqual(["About","Runs","Results"]);
    expect(AUTOMATION_WINDOW_SIZE).toEqual({w:900,h:600});
    expect(screen.queryByText("Done")).toBeNull();
  });
  it("keeps a refused Do draft, then shows the acknowledged result after retry", async () => {
    const id = blankSentence.workbench_id;
    const path = "/api/workbenches/" + id;
    let refuse = true;
    vi.mocked(fetch).mockImplementation(async (input,init) => {
      if (String(input) === path && init?.method === "PUT") {
        if(refuse)return json({},503);
        hub.step={workbench_id:id,gets:blankSentence.after.gets};
        return json(blankSentence.write);
      }
      return hubFetch(input,init);
    });
    await open({workbench_id:id,gets:blankSentence.before.gets} as Step);
    await edit();
    const field=screen.getByRole("textbox",{name:"What it does"});
    fireEvent.change(field,{target:{value:blankSentence.write.workbench.instruction}});
    fireEvent.click(screen.getByRole("button",{name:"Save"}));
    expect(await screen.findByRole("alert")).toHaveTextContent("Not saved");
    expect(field).toHaveValue(blankSentence.write.workbench.instruction);
    refuse=false;
    fireEvent.click(screen.getByRole("button",{name:"Save"}));
    await waitFor(() => expect(screen.queryByTestId("automation-setup")).toBeNull());
    expect(screen.getByTestId("automation-summary")).toHaveTextContent(blankSentence.write.workbench.instruction);
  });
  it("runs once while pending, then reads the Markdown result in its own view", async () => {
    await open(empty as Step);hub.afterRun=[one as Step];hub.hold=()=>undefined;
    const run=screen.getByTestId("automation-run-now");
    fireEvent.click(run);fireEvent.click(run);
    await waitFor(() => expect(hub.hold).not.toBeNull());
    expect(run).toBeDisabled();
    expect(screen.getByTestId("automation-results-well").querySelector(".surface-object-reader .surface-elapsed")).toBeTruthy();
    expect(screen.getByTestId("automation-results-well").querySelector(".surface-object-reader .surface-inspector-facts")).toBeTruthy();
    expect(hub.calls.filter(call => call.url.endsWith("/run"))).toHaveLength(1);
    await act(async()=>{hub.hold?.();});
    expect(await screen.findByRole("heading",{name:"Weekly update"})).toBeInTheDocument();
    expect(result().textContent).not.toMatch(/##|\*\*/);
    expect(within(result()).getAllByRole("listitem")).toHaveLength(2);
    await waitFor(()=>expect(hub.calls.some(call=>call.url.includes("/results/") && call.url.endsWith("/open"))).toBe(true));
  });
  it("keeps a failed run visible and Run again renders the next result", async () => {
    await open(failed as Step);view("Results");
    expect(await screen.findByRole("alert")).toHaveTextContent("The stub refuses: no source is attached");
    hub.afterRun=[populated as Step];
    fireEvent.click(screen.getByRole("button",{name:"Run again"}));
    expect(await screen.findByRole("heading",{name:"Weekly update"})).toBeInTheDocument();
  });
  it("selects a run with one press and opens it with Return; the rows contain no verbs", async () => {
    await open(populated as Step);view("Runs");
    const grid=screen.getByRole("grid",{name:"Runs"});
    const rows=within(grid).getAllByRole("row").filter(row=>row.hasAttribute("data-object-id"));
    expect(grid.querySelector("[role=row] button")).toBeNull();
    fireEvent.click(rows[1]);
    expect(rows[1]).toHaveAttribute("aria-selected","true");
    expect(screen.queryByRole("alert")).toBeNull();
    fireEvent.keyDown(rows[1],{key:"Enter"});
    expect(await screen.findByRole("alert")).toHaveTextContent("The stub refuses");
  });
  it("asks before forgetting a selected lesson; Cancel writes nothing", async () => {
    await open(populated as Step);view("Learned");
    const row=screen.getByRole("row",{name:/Keep the update under ten lines/});
    fireEvent.click(row);fireEvent.click(screen.getByRole("button",{name:"Forget"}));
    const question=screen.getByRole("region",{name:"Forget this lesson?"});
    expect(within(question).getByRole("button",{name:"Cancel"})).toHaveFocus();
    await waitFor(() => {
      const current = screen.getByRole("row", {name:/Keep the update under ten lines/});
      expect(current).toBeVisible();
      expect(current).toHaveAttribute("aria-selected", "true");
    });
    expect(question.closest(".surface-pane-actions")).not.toBeNull();
    expect(screen.getByTestId("automation-edit")).toBeDisabled();
    expect(hub.calls.filter(call=>call.method==="DELETE")).toHaveLength(0);
    fireEvent.click(within(question).getByRole("button",{name:"Cancel"}));
    fireEvent.click(screen.getByRole("button",{name:"Forget"}));
    fireEvent.click(within(screen.getByRole("region",{name:"Forget this lesson?"})).getByRole("button",{name:"Forget"}));
    await waitFor(()=>expect(hub.calls.filter(call=>call.method==="DELETE")).toHaveLength(1));
    await waitFor(()=>expect(screen.queryByText("Keep the update under ten lines.")).toBeNull());
  });
  it("shows source and engine values with lamps and one action state",async () => {
    await open(aboutPicked as Step);
    const facts=screen.getByTestId("automation-summary");
    const missing=within(facts).getByText("person · missing");
    expect(missing).toHaveAttribute("data-tone","fail");
    expect(within(facts).queryByText(/Choose Edit/)).toBeNull();
    expect(screen.getByTestId("automation-attention")).toHaveTextContent("Source missing");
    await edit("About");
    const sources=screen.getByRole("grid",{name:"Sources"});
    const row=within(sources).getByRole("row",{name:/person.*missing/});
    expect(within(row).getByText("missing").closest("[data-tone]")).toHaveAttribute("data-tone","fail");
    expect(within(row).getByRole("checkbox",{name:"person"})).toBeChecked();
    expect(screen.queryByText("Clear its tick to remove it.")).toBeNull();
  });
  it("names the absent engine as a value and an action state",async () => {
    await open(withNone as Step);
    const facts=screen.getByTestId("automation-summary");
    expect(within(facts).getByText("No engine")).toHaveAttribute("data-tone","ask");
    expect(screen.getByTestId("automation-attention")).toHaveTextContent("No engine");
    expect(screen.getByTestId("automation-attention").querySelector("[data-tone]")).toHaveAttribute("data-tone","ask");
  });
  it("keeps all schedule choices in the same shared setup form", async () => {
    await open(empty as Step);await edit("When");
    hub.afterWhen=[whenFriday as Step];
    fireEvent.change(screen.getByRole("combobox",{name:"When"}),{target:{value:"week"}});
    fireEvent.change(screen.getByRole("combobox",{name:"Day"}),{target:{value:"5"}});
    fireEvent.change(screen.getByLabelText("At",{selector:"input"}),{target:{value:"15:00"}});
    fireEvent.click(screen.getByRole("button",{name:"Save"}));
    await waitFor(()=>expect(screen.queryByTestId("automation-setup")).toBeNull());
    expect(hub.calls).toContainEqual({method:"PUT",url:DETAIL+"/when",body:{kind:"schedule",every:"week",time:"15:00",day:5}});
    expect(screen.getByTestId("automation-summary")).toHaveTextContent(/Fri/);
  });
  it("keeps output destinations in the shared form and reads the saved choice", async () => {
    await open(putNew as Step);await edit("Put it in");hub.afterTarget=[putFolder as Step];
    fireEvent.change(screen.getByRole("combobox",{name:"Put it in"}),{target:{value:"destination:dest-friday"}});
    fireEvent.click(screen.getByRole("button",{name:"Save"}));
    await waitFor(()=>expect(screen.queryByTestId("automation-setup")).toBeNull());
    expect(hub.calls.some(call=>call.method==="PUT" && call.body && "output_target" in (call.body as object))).toBe(true);
  });
  it("keeps old queue tasks and the Program conversion door", async () => {
    await open(oldQueue as Step);
    expect(screen.getByTestId("automation-set-up-program")).toBeEnabled();
    expect(screen.queryByTestId("automation-run-now")).toBeNull();
    view("Tasks");
    expect(screen.getByRole("grid",{name:"Tasks"})).toBeInTheDocument();
  });
  it("opens the Program from a recorded program run", async () => {
    await open(programRan as Step);view("Results");
    fireEvent.click(screen.getByTestId("automation-open-program"));
    expect(openProgram).toHaveBeenCalled();
  });
  it("keeps the run refusal when a Program is already running", async () => {
    await open(programNew as Step);hub.afterRun=[programStill as Step];
    fireEvent.click(screen.getByTestId("automation-run-now"));
    expect(await screen.findByTestId("automation-run-notice")).toHaveTextContent(/running/);
  });
  it("shows the agent's Looked at, Wrote and Prepared references", async () => {
    await open(used as Step);view("Results");
    expect(await screen.findByTestId("automation-used")).toHaveTextContent("Looked at");
    expect(screen.getByTestId("automation-used")).toHaveTextContent("Wrote");
    expect(screen.getByTestId("automation-used")).toHaveTextContent("Prepared");
  });
});


function AutomationMenu() {
  return <WorkMenu label="Automation app menu" x={0} y={0} entries={useListMenu("workbench:"+WB)} onClose={() => undefined} />;
}
it("the app menu uses the same run declaration and renders its result", async () => {
  await open(empty as Step);
  render(<AutomationMenu />);
  hub.afterRun=[one as Step];
  const menu=screen.getByRole("menu",{name:"Automation app menu"});
  fireEvent.click(within(menu).getByRole("menuitem",{name:"Run now"}));
  expect(await screen.findByRole("heading",{name:"Weekly update"})).toBeInTheDocument();
});
it("a refused clipboard write stays visible and Copy can retry", async () => {
  const writeText=vi.fn().mockRejectedValueOnce(new Error("clipboard refused")).mockResolvedValue(undefined);
  vi.stubGlobal("navigator",Object.assign(Object.create(navigator),{clipboard:{writeText}}));
  await open(one as Step);
  fireEvent.click(screen.getByTestId("automation-copy"));
  expect(await screen.findByText("Copy failed. Text kept. Try again.")).toBeInTheDocument();
  fireEvent.click(screen.getByTestId("automation-copy"));
  expect(await screen.findByText("Copied")).toBeInTheDocument();
});


it("Escape leaves the editor in the object window",async () => {
  await open(empty as Step);await edit();
  fireEvent.keyDown(screen.getByRole("textbox",{name:"What it does"}),{key:"Escape"});
  expect(screen.queryByTestId("automation-setup")).toBeNull();
  expect(screen.getByTestId("automation-summary")).toBeInTheDocument();
});


it("keeps a run refusal through an unrelated result-read acknowledgement, then retries",async () => {
  let release!: () => void;
  let refuse=true;
  vi.mocked(fetch).mockImplementation((input,init) => {
    const path=String(input);
    if(path.endsWith("/run") && refuse)return Promise.resolve(json({detail:"Run not started"},503));
    if(path.includes("/results/") && path.endsWith("/open"))return new Promise(resolve => {release=()=>resolve(json({result:{}}));});
    return hubFetch(input,init);
  });
  await open(one as Step);
  fireEvent.click(screen.getByRole("button",{name:"Run now"}));
  expect(await screen.findByTestId("automation-failure")).toHaveTextContent("Run not started");
  const reads=vi.mocked(fetch).mock.calls.filter(([path])=>String(path)===DETAIL).length;
  await act(async()=>release());
  await waitFor(()=>expect(vi.mocked(fetch).mock.calls.filter(([path])=>String(path)===DETAIL).length).toBeGreaterThan(reads));
  expect(screen.getByTestId("automation-failure")).toHaveTextContent("Run not started");
  refuse=false;hub.afterRun=[populated as Step];
  fireEvent.click(screen.getByRole("button",{name:"Run again"}));
  await waitFor(()=>expect(screen.queryByTestId("automation-failure")).toBeNull());
  expect(await screen.findByRole("heading",{name:"Weekly update"})).toBeInTheDocument();
});


it("a focused run selection owns the app menu until the object toolbar takes focus",async () => {
  await open(populated as Step);view("Runs");
  const grid=screen.getByRole("grid",{name:"Runs"});
  const row=within(grid).getAllByRole("row").filter(row=>row.hasAttribute("data-object-id"))[1];
  fireEvent.focus(row);fireEvent.click(row);
  render(<AutomationMenu />);
  const menu=screen.getByRole("menu",{name:"Automation app menu"});
  fireEvent.click(within(menu).getByRole("menuitem",{name:/Open result/}));
  expect(await screen.findByRole("alert")).toHaveTextContent("The stub refuses");
});
