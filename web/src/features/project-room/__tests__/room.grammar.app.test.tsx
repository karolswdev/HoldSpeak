/** Producer replies moved from the retired Room app tape. Only the IO boundary is doubled. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectRoomCore } from "../ProjectRoomCore";
import { useDesk } from "../../../desk/store";
import { EMPTY_ITEMS } from "../../../desk/api";
import { clearEngineCache } from "../../../desk/hooks/useEngine";
import { TitleSlotContext } from "../../../desk/surface/title";
import TAPE from "./room-wires/grammar10.json";
import { runAsk, parseAskResult } from "../../../desk/ask";
import ASK from "../../../test/wire/ask.thread.wire.json";
import { ApiError } from "../../../lib/api";

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
  io.api.mockReset(); localStorage.clear(); sessionStorage.clear(); clearEngineCache();
  useDesk.setState({ windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [] });
  wire();
});
describe("Room selection grammar", () => {
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
    mount(); await screen.findByRole("grid", { name: "Open" }); press("New program");
    expect(open).toHaveBeenCalledWith("open-programs", `project:${room.project_id}`);
    expect(useDesk.getState().places["programs/new"]).toBe(JSON.stringify({ title: "" }));
  });
  it("shows an Ask answer in this window and retains the question", async () => {
    const ask = vi.mocked(runAsk); ask.mockResolvedValue(parseAskResult(ASK.first));
    routes["POST /api/ask"] = ASK.first;
    mount(); const input = await screen.findByRole("textbox", { name: "Ask this project" });
    fireEvent.change(input, { target: { value: "What changed?" } }); fireEvent.keyDown(input, { key: "Enter" });
    expect(await screen.findByText(ASK.first.output)).toBeVisible();
    expect(input).toHaveValue("What changed?"); expect(screen.getByText(ASK.first.context_titles[0])).toBeVisible();
    expect(ask).toHaveBeenCalledWith(expect.objectContaining({ prompt: "What changed?", grounding: expect.objectContaining({ refs: [`project:${room.project_id}`] }) }));
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
