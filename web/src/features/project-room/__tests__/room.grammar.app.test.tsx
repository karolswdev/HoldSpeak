import { RoomList, roomReadingText, roomFacts } from "../RoomList";
/** Producer replies moved from the retired Room app tape. Only the IO boundary is doubled. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectRoomCore } from "../ProjectRoomCore";
import { useDesk } from "../../../desk/store";
import { EMPTY_ITEMS } from "../../../desk/api";
import { clearEngineCache } from "../../../desk/hooks/useEngine";
import { TitleSlotContext } from "../../../desk/surface/title";
import TAPE from "./room-wires/grammar10.json";
import POLISH from "./room-wires/polish14.json";
import RETIRE from "./room-wires/binding-retire.json";
import { runAsk, parseAskResult } from "../../../desk/ask";
import ASK from "../../../test/wire/ask.thread.wire.json";
import { ApiError } from "../../../lib/api";

import HANDOFF from "./room-wires/send-handoff.json";
import { pickFor, readFact, resetSendTo } from "../../../desk/windowSend";
import { resetSendStore } from "../../../desk/surface/send";

const io = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("../../../lib/api", async original => ({ ...await original<typeof import("../../../lib/api")>(), apiFetch: (...args: unknown[]) => io.api(...args) }));
vi.mock("../../../desk/ask", async original => ({ ...await original<typeof import("../../../desk/ask")>(), runAsk: vi.fn() }));
let room: Record<string, any>, routes: Record<string, any>;
const writes = () => io.api.mock.calls.filter(([, init]) => init?.method && init.method !== "GET");
function wire(raw: Record<string, any> = TAPE.P172_ROOM_BEFORE) {
  room = structuredClone(raw); routes = {};
  io.api.mockImplementation(async (url: string, init: { method?: string; json?: unknown } = {}) => {
    const path = url.split("?")[0], key = `${init.method || "GET"} ${path}`;
    if (key in routes) return typeof routes[key] === "function" ? routes[key](init) : structuredClone(routes[key]);
    if (path.endsWith("/room")) return structuredClone(room);
    if (path.endsWith("/room/read")) return { read_at: room.observed_at };
    if (path.endsWith("/proposals")) return TAPE.P172_PROPOSALS;
    if (path.endsWith("/suggested-sources")) return TAPE.P172_SUGGESTED;
    if (path.endsWith("/items")) return { items: [] };
    if (path.endsWith("/meetings")) return { meetings: [] };
    if (path.endsWith("/resources")) return { resources: [] };
    if (path.includes("/decisions")) return { decisions: [] };
    if (path.includes("/artifacts")) return { artifacts: [] };
    if (path.endsWith("/briefs/route")) return TAPE.PREP2_ROUTE;
    if (path.endsWith("/briefs/manifest")) return TAPE.PREP2_MANIFEST;
    if (path.endsWith("/briefs")) return { briefs: [] };
    if (path.endsWith("/updates")) return { updates: [] };
    if (path.endsWith("/nudges")) return { nudges: [] };
    return {};
  });
}
const mount = (onTitle = vi.fn()) => render(<TitleSlotContext.Provider value={onTitle}><ProjectRoomCore scope={`project:${room.project_id}`} /></TitleSlotContext.Provider>);
async function row(name: string | RegExp) { return screen.findByRole("row", { name }); }
function press(name: string) { fireEvent.click(screen.getByRole("button", { name })); }
async function view(name: string) { press("Project view"); fireEvent.click(screen.getByRole("menuitem", { name })); }

beforeEach(() => {
  resetSendTo(); resetSendStore(); io.api.mockReset(); localStorage.clear(); sessionStorage.clear(); clearEngineCache();
  useDesk.setState({ windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [] });
  wire();
});
describe("Room selection grammar", () => {
  it("uses sentence case, shared dates and omits facts with no value", () => {
    const facts = roomFacts([{label:"Likelihood", value:"high"}, {label:"Impact", value:"critical"}, {label:"Due", value:"2026-10-01"}, {label:"Due", value:"unknown"}]);
    expect(facts.map(fact => fact.value)).toEqual(["High", "Critical", "Oct 1"]);
  });
  it("gives a path inspector a file object", () => {
    render(<RoomList label="Plan" selectedId="path" rows={[{id:"path", kind:"risk", name:"web/src/features/project-room/review/ReviewPosture.tsx: retain the rollback plan", facts:[{label:"State",value:"open"}]}]} />);
    const object = document.querySelector(".surface-inspector-object")!;
    expect(object.querySelector("img")).not.toBeNull();
    expect(object).not.toHaveTextContent("wr");
  });

  it("reads a produced brief's owner separator as words", () => {
    expect(POLISH.brief.body_md).toContain("-- owner Dana");
    expect(roomReadingText(POLISH.brief.body_md)).toContain("Load test rerun · Owner Dana");
    expect(roomReadingText(POLISH.brief.body_md)).not.toContain("-- owner");
  });
  it("shows a source name instead of an account key and says when its project name is unavailable", async () => {
    wire(POLISH.room); mount();
    fireEvent.click(await screen.findByRole("tab", {name:"Sources"}));
    fireEvent.click(await row(/Jira account/));
    const facts = within(document.querySelector(".surface-inspector-facts") as HTMLElement);
    expect(facts.getByText("Project name")).toBeVisible();
    expect(facts.getByText("Not available")).toBeVisible();
    expect(screen.getByRole("grid", {name:"Sources"})).not.toHaveTextContent("team@example.com");
    press("Remove");
    expect(screen.getByRole("region", {name:"Remove Jira account?"})).not.toHaveTextContent("team@example.com");
    press("Cancel");
    expect(writes().some(([url]) => url.endsWith("/retire"))).toBe(false);
  });
  it("keeps the partial-write fact when one source watch was removed", async () => {
    wire(POLISH.room); mount();
    fireEvent.click(await screen.findByRole("tab", {name:"Sources"}));
    fireEvent.click(await row(/Jira account/));
    const source = POLISH.room.sources.items.find(source => source.provider === "jira")!;
    expect(source.watchIds.length).toBeGreaterThan(1);
    routes[`POST /api/watches/${source.watchIds[0]}/retire`] = {};
    routes[`POST /api/watches/${source.watchIds[1]}/retire`] = () => { throw new ApiError(409, RETIRE.stale.message, RETIRE.stale); };
    press("Remove");
    fireEvent.click(within(screen.getByRole("region", {name:"Remove Jira account?"})).getByRole("button", {name:"Remove"}));
    expect(await screen.findByText(/Other changes stay/)).toBeVisible();
    expect(screen.getByRole("button", {name:"Read again"})).toBeEnabled();
  });
  it("gives a history subject the name seat and puts its action on the second line", async () => {
    wire(POLISH.room); mount();
    await screen.findByRole("grid", {name:"Open"}); await view("History");
    const history = POLISH.room.changes.recent[0];
    const subject = JSON.parse(history.summary_json).title;
    const item = document.querySelector(`[data-object-id="${history.id}"]`)!;
    expect(item.querySelector(".object-list-selection-title")).toHaveAttribute("title", subject);
    expect(item.querySelector(".object-list-detail")).toHaveTextContent("Added risk");
    fireEvent.click(item);
    expect(document.querySelector(".surface-inspector-facts")).toHaveTextContent(subject);
  });
  it("uses the singular source word for one source", async () => {
    wire(TAPE.OLDER_ROOM); mount(); await screen.findByRole("grid", {name:"Open"});
    expect(document.querySelector(".kit-statusbar")).toHaveTextContent("1 source");
    expect(document.querySelector(".kit-statusbar")).not.toHaveTextContent("1 sources");
  });
  it("puts the name in the title and has four lists with no folds or row verbs", async () => {
    const title = vi.fn(); mount(title);
    await screen.findByRole("grid", { name: "Open" });
    expect(title).toHaveBeenCalledWith(room.project.name);
    expect(screen.getAllByRole("tab").filter(tab => !tab.closest("[inert]")).map(tab => tab.textContent)).toEqual(["Open", "Plan", "Sources", "Updates"]);
    expect(document.querySelector("summary,.room-plate,.surface-mast")).toBeNull();
    expect(document.querySelector(".object-list-row button,.object-list-row a")).toBeNull();
    expect(writes().some(([url]) => url.endsWith("/room/read"))).toBe(true);
  });
  it("selects with one click and opens with Return", async () => {
    mount();
    const proposal = TAPE.P172_PROPOSALS.proposals[0];
    const item = await row(new RegExp(proposal.text));
    fireEvent.click(item);
    expect(item).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByLabelText("Edit proposal")).toBeNull();
    fireEvent.keyDown(item, { key: "Enter" });
    expect(await screen.findByRole("textbox", { name: "Text" })).toHaveValue(proposal.text);
  });
  it("keeps a failed proposal edit, then confirms the current words", async () => {
    mount(); const proposal = TAPE.P172_PROPOSALS.proposals[0];
    fireEvent.click(await row(new RegExp(proposal.text))); press("Edit");
    const text = screen.getByRole("textbox", { name: "Text" });
    fireEvent.change(text, { target: { value: "Keep these revised words" } });
    routes[`POST /api/proposals/${proposal.id}/confirm`] = () => { throw new ApiError(503, "offline", {}); };
    press("Save and confirm");
    await screen.findAllByText(/Could not confirm/);
    expect(text).toHaveValue("Keep these revised words");
    routes[`POST /api/proposals/${proposal.id}/confirm`] = TAPE.P172_CONFIRM;
    press("Save and confirm");
    await waitFor(() => expect(screen.queryByLabelText("Edit proposal")).toBeNull());
    expect(writes().filter(([url]) => url.includes("/confirm")).at(-1)?.[1].json).toMatchObject({ text: "Keep these revised words" });
  });
  it("asks before dismiss and drops the armed question when selection changes", async () => {
    mount(); const [first, second] = TAPE.P172_PROPOSALS.proposals;
    fireEvent.click(await row(new RegExp(first.text))); press("Dismiss");
    expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
    fireEvent.click(await row(new RegExp(second.text)));
    expect(screen.queryByRole("button", { name: "Cancel" })).toBeNull();
    expect(writes().some(([url]) => url.includes("/dismiss"))).toBe(false);
  });
  it("keeps all source watches behind one selection and no normal OK state", async () => {
    mount(); fireEvent.click(await screen.findByRole("tab", { name: "Sources" }));
    await screen.findByRole("grid", { name: "Sources" });
    expect(document.querySelector(".object-list-row button,.object-list-row a")).toBeNull();
    expect(within(screen.getByRole("grid", { name: "Sources" })).queryByText("OK", { exact: true })).toBeNull();
  });
  it("uses the object kind in Sources and keeps the provider in its facts", async () => {
    wire(TAPE.OLDER_ROOM); mount(); fireEvent.click(await screen.findByRole("tab", { name: "Sources" }));
    const grid = screen.getByRole("grid", { name: "Sources" });
    expect(within(grid).getByText("Repository")).toBeVisible();
    fireEvent.click(await row(new RegExp(TAPE.OLDER_ROOM.sources.items[0].scope)));
    expect(document.querySelector(".surface-inspector-facts")).toHaveTextContent("GitHub");
  });
  it("pauses every grouped watch and retries only the refused watch", async () => {
    wire(TAPE.OLDER_ROOM);
    const source = TAPE.OLDER_ROOM.sources.items[0];
    const [first, second] = source.watchIds;
    routes[`POST /api/watches/${second}/pause`] = () => { throw new ApiError(503,"offline",{}); };
    mount(); fireEvent.click(await screen.findByRole("tab",{name:"Sources"}));
    fireEvent.click(await row(new RegExp(source.scope))); press("Pause");
    await screen.findByText(/Could not pause all watches/);
    expect(writes().filter(([url])=>url.endsWith("/pause")).map(([url])=>url)).toEqual(source.watchIds.map(id=>`/api/watches/${id}/pause`));
    routes[`POST /api/watches/${second}/pause`] = {};
    press("Try again");
    await waitFor(()=>expect(writes().filter(([url])=>url.endsWith("/pause")).map(([url])=>url)).toEqual([`/api/watches/${first}/pause`,`/api/watches/${second}/pause`,`/api/watches/${second}/pause`]));
  });
  it("requires a question for removal and Cancel makes no write", async () => {
    wire(TAPE.OLDER_ROOM); const source=TAPE.OLDER_ROOM.sources.items[0];
    mount(); fireEvent.click(await screen.findByRole("tab",{name:"Sources"}));
    fireEvent.click(await row(new RegExp(source.scope))); press("Remove");
    expect(screen.getByRole("button",{name:"Cancel"})).toHaveFocus();
    expect(writes().some(([url])=>url.endsWith("/retire"))).toBe(false);
    fireEvent.click(screen.getByRole("button",{name:"Cancel"}));
    press("Remove");
    fireEvent.click(screen.getByRole("button",{name:"Cancel"}));
    expect(writes().some(([url])=>url.endsWith("/retire"))).toBe(false);
  });
  it("uses the existing new program form with this project selected", async () => {
    const open = vi.fn(); useDesk.setState({ openSurfaceWindow: open });
    mount(); const grid = await screen.findByRole("grid", { name: "Open" });
    expect(within(grid).queryByRole("row", {selected:true})).toBeNull();
    expect(screen.getByRole("button", {name:"New program"})).toBeEnabled(); press("New program");
    expect(open).toHaveBeenCalledWith("open-programs", `project:${room.project_id}`);
    expect(useDesk.getState().places["programs/new"]).toBe(JSON.stringify({ title: "" }));
  });
  it("opens Add source without selecting a row", async () => {
    mount(); await screen.findByRole("grid", {name:"Open"});
    expect(screen.getByRole("button", {name:"Add source"})).toBeEnabled(); press("Add source");
    expect(await screen.findByRole("toolbar", {name:"Add sources"})).toBeVisible();
  });
  it("shows an Ask from Sources in this window and retains the question", async () => {
    const ask = vi.mocked(runAsk); ask.mockResolvedValue(parseAskResult(ASK.first));
    routes["POST /api/ask"] = ASK.first;
    mount(); fireEvent.click(await screen.findByRole("tab", {name:"Sources"}));
    const input = await screen.findByRole("textbox", { name: "Ask this project" });
    fireEvent.change(input, { target: { value: "What changed?" } }); fireEvent.keyDown(input, { key: "Enter" });
    expect(await screen.findByText(ASK.first.output)).toBeVisible();
    expect(input).toHaveValue("What changed?"); expect(screen.getByText(ASK.first.context_titles[0])).toBeVisible();
    expect(ask).toHaveBeenCalledWith(expect.objectContaining({ prompt: "What changed?", grounding: expect.objectContaining({ refs: [`project:${room.project_id}`] }) }));
  });
  it("gives History names the space of the unused State column", async () => {
    wire(TAPE.OLDER_ROOM); mount(); await screen.findByRole("grid", { name: "Open" });
    await view("History");
    const grid = screen.getByRole("grid", { name: "History" });
    expect(grid.querySelector(".object-list-row")).not.toBeNull();
    expect(within(grid).queryByRole("columnheader", { name: "State" })).toBeNull();
  });
  it("labels the Add source choice beside its current value", async () => {
    mount(); await screen.findByRole("grid", { name: "Open" }); press("Add source");
    const choice = await screen.findByRole("combobox", { name: "View" });
    expect(choice.closest(".gadget-popup")).toHaveTextContent("View:");
  });
  it("reads Brief text directly and keeps the update door live", async () => {
    wire(HANDOFF.room);
    const id = HANDOFF.room.updates.recent[0].id;
    const update = HANDOFF.updates.updates.find(row => row.id === id)!;
    routes[`GET /api/updates/${id}`] = { update };
    routes[`GET /api/projects/${room.project_id}/updates`] = HANDOFF.updates;
    mount(); await screen.findByRole("grid", { name: "Open" }); await view("Brief");
    const reader = await screen.findByText("The rollback path stays ready.", { exact: false });
    expect(reader.closest(".surface-object-reader")).toHaveAttribute("data-feedback-redact", "true");
    expect(document.querySelector(".object-list-row")).toBeNull();
    expect(screen.getByRole("button", { name: "Open update" })).toBeEnabled();
    press("Open update");
    await waitFor(() => expect(screen.getByRole("tab", { name: "Updates" })).toHaveAttribute("aria-selected", "true"));
    expect(screen.queryByTestId("send-well")).toBeNull();
  });
  it("keeps a failed Brief read in its pane and retries the same update", async () => {
    wire(HANDOFF.room); const id = HANDOFF.room.updates.recent[0].id;
    routes[`GET /api/updates/${id}`] = () => { throw new ApiError(503, "offline", {}); };
    mount(); await screen.findByRole("grid", { name: "Open" }); await view("Brief");
    await screen.findByText("Could not read the brief · Nothing changed");
    expect(screen.queryByText("No brief", { exact: true })).toBeNull();
    routes[`GET /api/updates/${id}`] = { update: HANDOFF.updates.updates.find(row => row.id === id)! };
    press("Try again"); await screen.findByText("The rollback path stays ready.", { exact: false });
    expect(screen.queryByRole("alert")).toBeNull();
  });
  it("reaches Prepare through the same window view", async () => {
    mount(); await screen.findByRole("grid", { name: "Open" }); await view("Prepare");
    expect(await screen.findByRole("textbox", { name: "Purpose" })).toBeVisible();
    expect(screen.getByRole("grid", { name: "Prepare" })).toBeInTheDocument();
  });
  it("names an empty project and a failed initial read", async () => {
    wire(TAPE.BARE_ROOM); routes[`GET /api/projects/${room.project_id}/proposals`] = { proposals: [] };
    const mounted = mount(); expect(await screen.findByText("Nothing open")).toBeVisible(); mounted.unmount();
    routes[`GET /api/projects/${room.project_id}/room`] = () => { throw new Error("offline"); };
    mount(); expect(await screen.findByText(/Could not load/)).toBeVisible();
    expect(screen.getByRole("button", { name: /Try again|Retry/ })).toBeEnabled();
  });
});


describe("Room Send-to handoff", () => {
  it("holds a failed fresh read on Updates, hides the former Send and retries without dispatch", async () => {
    wire(HANDOFF.room);
    const projectId = HANDOFF.room.project_id;
    const updatesPath = `GET /api/projects/${projectId}/updates`;
    const selected = HANDOFF.updates.updates.find(update => update.id === HANDOFF.updates.latest_published_update_id)!;
    routes[updatesPath] = HANDOFF.updates;
    routes["GET /api/channels/destinations"] = HANDOFF.destinations;
    routes["GET /api/channels/sends"] = { sends: [] };
    routes["POST /api/channels/preview"] = HANDOFF.preview;
    useDesk.setState({ windowsById: { "surface-project-memory": { id: "surface-project-memory", kind: "surface", scope: `project:${projectId}` } } } as never);
    mount(); fireEvent.click(await screen.findByRole("tab", { name: "Updates" }));
    const grid = await screen.findByRole("grid", { name: "Updates" });
    await waitFor(() => expect(grid.querySelector(`[data-object-id="${selected.id}"]`)).not.toBeNull());
    fireEvent.click(grid.querySelector(`[data-object-id="${selected.id}"]`)!);
    press("Send"); await screen.findByTestId("send-preview");
    expect(screen.getByTestId("send-status")).toHaveTextContent("New");
    expect(screen.queryByTestId("room-headline")).toBeNull();
    // The menu read succeeds; the Room's second read fails with a Send already open.
    await act(async () => { await readFact("project", projectId); });
    routes[updatesPath] = () => { throw new TypeError("Lost fresh update read"); };
    act(() => pickFor("surface-project-memory", HANDOFF.destinations.destinations[0].id));
    await screen.findByText("Could not read the latest update · Nothing changed");
    expect(screen.getByRole("tab", { name: "Updates" })).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByTestId("send-well")).toBeNull();
    expect(screen.queryByText("No updates", { exact: true })).toBeNull();
    expect(writes().some(([path]) => path === "/api/channels/send")).toBe(false);
    let finish!: (value: unknown) => void;
    routes[updatesPath] = () => new Promise(resolve => { finish = resolve; });
    press("Try again");
    await waitFor(() => expect(finish).toBeTypeOf("function"));
    expect(screen.queryByTestId("send-well")).toBeNull();
    routes[updatesPath] = HANDOFF.updates;
    await act(async () => finish(HANDOFF.updates));
    const preview = await screen.findByTestId("send-preview-body");
    expect(preview).toHaveTextContent("The rollback path stays ready.");
    expect(screen.getByRole("combobox", { name: "Destination" })).toHaveValue(HANDOFF.destinations.destinations[0].id);
    expect(screen.getByTestId("send-well")).toHaveAttribute("data-doc", `project_update:${selected.id}`);
    expect(screen.queryByText("Could not read the latest update · Nothing changed")).toBeNull();
    expect(screen.getByTestId("send-verb")).toBeEnabled();
    expect(writes().some(([path]) => path === "/api/channels/send")).toBe(false);
  });
});

it("passes existing Room states to the kit's lamp and pill", () => {
  const {container} = render(<RoomList label="States" rows={[{id:"waiting",kind:"action",name:"Read the plan",state:{label:"Waits on you",tone:"ask"}},{id:"done",kind:"action",name:"Keep the plan",cells:{state:"Done"}},{id:"risk",kind:"risk",name:"Read the risk",cells:{state:"at_risk"}}]} />);
  const waiting = container.querySelector('[data-object-id="waiting"]')!;
  expect(waiting.querySelector('.surface-lamp')).toHaveAttribute("data-state", "waiting");
  expect(waiting.querySelector('[data-col="state"] .object-list-dot-word')).toHaveTextContent("Waits on you");
  const done = container.querySelector('[data-object-id="done"]')!;
  expect(done.querySelector('.surface-lamp')).toHaveAttribute("data-state", "done");
  expect(done.querySelector('[data-col="state"] .object-list-dot-word')).toHaveTextContent("Done");
  expect(container.querySelector('[data-object-id="risk"] .surface-lamp')).toHaveAttribute("data-state", "failed");
});
