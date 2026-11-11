/** Real hub tapes; selection and an explicit owner press are separate acts. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../../lib/api";
import { useDropped } from "../NeedVerbs";
import { useArmingOutcome } from "../arming";
import { NeedsDrawer } from "../NeedsDrawer";
import { fromWireSessionRow, useAgentFlights } from "../../agentFlights";
import { useDesk } from "../../store";
import { refreshNeedsYou } from "../../needsYou";
import { resetSendStore } from "../../surface/send";
import { WindowIdContext } from "../../components/window/windowIdContext";
import { ApplicationMenu } from "../../components/DeskMenuBar";
import { selectedNeed, needName } from "../selection";
import { needFace } from "../needsFace";
import { fixedAnswers } from "../needActions";
import rows from "../__fixtures__/needs_you.rows.json";
import grammar from "../__fixtures__/needs_you.grammar.json";
import needs from "../../__tests__/fixtures/needsYou.recorded.json";
import sendTape from "../../__tests__/fixtures/send-needs/needs-send.json";
import unknownTape from "../../__tests__/fixtures/send-needs/needs-send-unknown.json";
import gateTape from "../../__tests__/wire/needs-you.gate.wire.json";
import programTape from "../../programs/__fixtures__/needs_you.page_none.json";
import { recordedGet, type Gets } from "../../../test/recordedHub";

vi.mock("../../../lib/api", async original => ({...await original<typeof import("../../../lib/api")>(), apiFetch: vi.fn()}));
vi.mock("../../components/MicButton", () => ({MicButton: () => null}));
vi.mock("../../shell", async original => ({...await original<typeof import("../../shell")>(), openCoderSession: vi.fn(), openSurfaceOr: vi.fn()}));
let hub: Gets;
let posts: {path: string; json: any}[];
let post: (path: string, json: any) => Promise<any>;
const wire = (body: any) => {hub = {"/api/desk/needs-you?fresh=1": body};};
const row = (text: string) => screen.getAllByTestId("needs-row").find(el => el.textContent?.includes(text))!;
const reader = () => screen.getByTestId("needs-reader");
const choose = async (text: string) => {await waitFor(() => expect(row(text)).toBeTruthy()); fireEvent.click(row(text)); return reader();};
const press = (label: string) => fireEvent.click(within(reader()).getByRole("button", {name: label}));
const verbs = () => screen.getByRole("toolbar", {name: "Needs you"});
const empty = needs.calendar.quiet.gets["/api/desk/needs-you?fresh=1"];
beforeEach(() => {
  posts = [];
  useDropped.setState({dropped: null});
  useArmingOutcome.setState({receipt: null, refusal: null, busy: false});
  useDesk.setState({scheduledArming: null} as never);
  useAgentFlights.setState({sessions: [], flights: [], loaded: true, settled: true});
  resetSendStore();
  post = async () => ({});
  hub = rows.steps[0].gets;
  vi.mocked(apiFetch).mockImplementation(async (path, init) => {
    if (init?.method && init.method !== "GET") {posts.push({path: String(path), json: init.json}); return post(String(path), init.json);}
    return recordedGet(hub, String(path)) as never;
  });
});

describe("Needs you selection grammar", () => {
  it("a need is a selection row with no action button", async () => {
    hub = rows.program.steps[0].gets;
    render(<NeedsDrawer />);
    await waitFor(() => expect(screen.getByTestId("needs-row")).toBeTruthy());
    expect(screen.getByTestId("needs-row").getAttribute("role")).toBe("row");
    expect(screen.getByTestId("needs-row").querySelector("button")).toBeNull();
  });
  it("click selects and reads; Return and double-click open the source without answering", async () => {
    wire(programTape);
    const open = vi.fn(), real = useDesk.getState().openSurfaceWindow;
    useDesk.setState({openSurfaceWindow: open});
    const view = render(<NeedsDrawer />);
    const title = programTape.items[0].group;
    await choose(title);
    expect(open).not.toHaveBeenCalled();
    expect(posts).toEqual([]);
    expect(row(title).querySelector("button")).toBeNull();
    expect(within(reader()).getByText(programTape.items[0].title)).toBeTruthy();
    expect(within(reader()).getAllByTestId("needs-answer-choice").map(button => button.textContent)).toEqual(["Go on", "Park"]);
    fireEvent.keyDown(row(title), {key: "Enter"});
    await waitFor(() => expect(open).toHaveBeenCalledWith("open-programs", programTape.items[0].openRef));
    fireEvent.doubleClick(row(title));
    await waitFor(() => expect(open).toHaveBeenCalledTimes(2));
    expect(posts).toEqual([]);
    view.unmount(); useDesk.setState({openSurfaceWindow: real});
  });
  it("one declared selection menu serves toolbar, context menu and app menu", async () => {
    render(<WindowIdContext.Provider value="chair:needs"><ApplicationMenu windowId="chair:needs" name="Needs you" /><NeedsDrawer /></WindowIdContext.Provider>);
    const title = "Book the cutover dry run";
    await choose(title);
    const bar = within(verbs()).getAllByRole("button").map(button => button.textContent);
    expect(bar).toContain("Answer…"); expect(bar).toContain("Open source"); expect(bar).toContain("Dismiss");
    fireEvent.contextMenu(row(title), {clientX: 40, clientY: 60});
    const menu = screen.getByRole("menu", {name: "Needs you actions"});
    expect(within(menu).getByRole("menuitem", {name: "Answer…"})).toBeTruthy();
    fireEvent.keyDown(menu, {key: "Escape"});
    fireEvent.click(screen.getByRole("button", {name: "Needs you"}));
    expect(screen.getByRole("menuitem", {name: "Answer…"})).toBeTruthy();
  });
  it("a fixed answer writes once, removes its revision, selects the next row and records the outcome", async () => {
    const [before, after] = rows.steps;
    hub = before.gets;
    post = async () => {hub = after.gets; return after.answer;};
    render(<NeedsDrawer />);
    const title = "openSystemShade() fires an event nobody hears";
    await choose(title);
    fireEvent.click(within(reader()).getByRole("button", {name: "Done"}));
    await waitFor(() => expect(posts).toEqual([{path: after.post, json: after.body}]));
    await waitFor(() => expect(screen.queryByText(title, {selector: ".object-list-selection-name span"})).toBeNull());
    expect(screen.getByTestId("needs-receipt").textContent).toContain("Done");
    expect(document.querySelector('[data-testid="needs-row"][aria-selected="true"]')).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", {name: "Answered"}));
    expect(await screen.findByRole("grid", {name: "Answered"})).toHaveTextContent(title);
    expect(screen.queryByTestId("needs-send-answer")).toBeNull();
  });
  it("a refused write keeps the row and the failure; the next named press retries", async () => {
    post = async () => {throw new Error("The hub did not save it");};
    render(<NeedsDrawer />);
    await choose("Book the cutover dry run"); press("Done");
    await screen.findByText(/Done failed/);
    expect(row("Book the cutover dry run")).toBeTruthy();
    post = async () => ({}); press("Done");
    await waitFor(() => expect(posts).toHaveLength(2));
    await waitFor(() => expect(screen.queryByTestId("needs-failure")).toBeNull());
  });
  it("Dismiss is an in-window question with Cancel first and focused", async () => {
    render(<NeedsDrawer />); await choose("Book the cutover dry run");
    fireEvent.click(within(verbs()).getByRole("button", {name: "Dismiss"}));
    const question = screen.getByTestId("needs-question");
    expect(within(question).getAllByRole("button").map(button => button.textContent)).toEqual(["Cancel", "Dismiss"]);
    expect(document.activeElement).toBe(within(question).getByRole("button", {name: "Cancel"}));
    expect(posts).toEqual([]);
    fireEvent.click(within(question).getByRole("button", {name: "Dismiss"}));
    await waitFor(() => expect(posts[0].json).toEqual({card_id: "rows-plain", verb: "dismiss", payload: {}}));
  });
  it("an armed question closes when selection changes", async () => {
    render(<NeedsDrawer />); await choose("Book the cutover dry run");
    fireEvent.click(within(verbs()).getByRole("button", {name: "Dismiss"}));
    fireEvent.click(row("openSystemShade() fires an event nobody hears"));
    expect(screen.queryByTestId("needs-question")).toBeNull();
    expect(posts).toEqual([]);
  });
  it("Dismiss on a People's promise asks first, then uses its recorded lawful transition", async () => {
    const tape = grammar.promise;
    wire(tape.before);
    post = async () => {wire(tape.after); return tape.answer;};
    render(<NeedsDrawer />);
    await choose("Send Priya the rollout plan");
    fireEvent.click(within(verbs()).getByRole("button", {name: "Dismiss"}));
    const question = screen.getByTestId("needs-question");
    expect(document.activeElement).toBe(within(question).getByRole("button", {name: "Cancel"}));
    expect(posts).toEqual([]);
    fireEvent.click(within(question).getByRole("button", {name: "Dismiss"}));
    await waitFor(() => expect(posts).toContainEqual({path: tape.path, json: {verb: "dismiss"}}));
    await waitFor(() => expect(screen.queryByText("Send Priya the rollout plan", {selector: ".object-list-selection-name span"})).toBeNull());
    fireEvent.click(screen.getByRole("tab", {name: "Answered"}));
    expect(screen.getByRole("grid", {name: "Answered"})).toHaveTextContent("Send Priya the rollout plan");
  });
  it("the same id with a changed saved revision disarms the old answer", async () => {
    hub = rows.steps[0].gets;
    render(<NeedsDrawer />); await choose("Book the cutover dry run");
    fireEvent.click(within(verbs()).getByRole("button", {name: "Dismiss"}));
    const original = hub["/api/desk/needs-you?fresh=1"];
    // A reload of the same real row, with a later saved edit.
    wire({...original, items: original.items.map((item: any) => item.title === "Book the cutover dry run" ? {...item, title: "Book the Friday dry run"} : item)});
    await act(() => refreshNeedsYou(false));
    expect(screen.queryByTestId("needs-question")).toBeNull();
    expect(reader()).toHaveTextContent("Book the Friday dry run");
    expect(posts).toEqual([]);
  });
  it("a late successful answer records its own need and leaves a newer selection alone", async () => {
    let finish!: () => void;
    post = () => new Promise(resolve => {finish = () => resolve({});});
    render(<NeedsDrawer />); await choose("Book the cutover dry run"); press("Done");
    await choose("openSystemShade() fires an event nobody hears");
    await act(async () => finish());
    expect(reader()).toHaveTextContent("openSystemShade() fires an event nobody hears");
    fireEvent.click(screen.getByRole("tab", {name: "Answered"}));
    expect(screen.getByRole("grid", {name: "Answered"})).toHaveTextContent("Book the cutover dry run");
  });
  it("the normal empty state is one line, without a zero count or a ledger below the list", async () => {
    wire(empty); render(<NeedsDrawer />);
    expect(await screen.findByText("Nothing needs you.")).toBeTruthy();
    expect(screen.queryByTestId("needs-first")).toBeNull();
    expect(screen.queryByTestId("needs-ledger")).toBeNull();
    expect(screen.queryByTestId("arrival-headline")).toBeNull();
    fireEvent.click(screen.getByRole("tab", {name: "Answered"}));
    expect(screen.getByText("No answers in this window yet.")).toBeTruthy();
  });
});

describe("the selected agent question", () => {
  beforeEach(() => {
    wire(grammar.typed);
    useAgentFlights.setState({sessions: grammar.sessions.sessions.map(fromWireSessionRow), flights: []});
  });
  it("has one field and Send answer; Return on the list never sends", async () => {
    render(<NeedsDrawer />); await choose("Who owns the rollback runbook?");
    const input = within(reader()).getByRole("textbox", {name: "Answer"});
    fireEvent.change(input, {target: {value: "Jordan"}});
    fireEvent.keyDown(row("Who owns the rollback runbook?"), {key: "Enter"});
    expect(posts).toEqual([]);
    press("Send answer");
    await waitFor(() => expect(posts[0]).toEqual({path: "/api/coders/claude%3Aneeds-typed/steer", json: {text: "Jordan", submit: true, kind: "answer", wait_id: grammar.sessions.sessions[0].session.wait_id}}));
    expect(await screen.findByText("Nothing needs you.")).toBeTruthy();
  });
  it("keeps a refused typed answer and clears no work", async () => {
    post = async () => {throw new ApiError(409, "Question changed", (grammar as any).typedRefusal.body);};
    render(<NeedsDrawer />); await choose("Who owns the rollback runbook?");
    fireEvent.change(within(reader()).getByRole("textbox", {name: "Answer"}), {target: {value: "Jordan"}});
    press("Send answer");
    expect(await screen.findByTestId("needs-failure")).toHaveTextContent("The question changed");
    expect(within(reader()).getByRole("textbox", {name: "Answer"})).toHaveValue("Jordan");
    expect(row("Who owns the rollback runbook?")).toBeTruthy();
  });
  it("returning to the same need keeps its draft without copying it to a different need", async () => {
    wire((grammar as any).send.before);
    useAgentFlights.setState({sessions: (grammar as any).questionSessions.sessions.map(fromWireSessionRow), flights: []});
    render(<NeedsDrawer />); await choose("Who owns the rollback runbook?");
    fireEvent.change(within(reader()).getByRole("textbox", {name: "Answer"}), {target: {value: "Jordan"}});
    const send = (grammar as any).send.before.items.find((item: any) => item.source === "send");
    await act(() => refreshNeedsYou(false));
    expect(within(reader()).getByRole("textbox", {name: "Answer"})).toHaveValue("Jordan");
    await choose(send.title); expect(within(reader()).queryByRole("textbox")).toBeNull();
    await choose("Who owns the rollback runbook?");
    expect(within(reader()).getByRole("textbox", {name: "Answer"})).toHaveValue("Jordan");
    expect(posts).toEqual([]);
  });
  it("a new wait on the same agent drops the old draft and cannot inherit its authority", async () => {
    render(<NeedsDrawer />); await choose("Who owns the rollback runbook?");
    fireEvent.change(within(reader()).getByRole("textbox", {name: "Answer"}), {target: {value: "Jordan"}});
    const item = grammar.typed.items[0];
    wire({...grammar.typed, items: [{...item, waitStartedAt: "2026-11-11T09:00:00Z", question: "Who reviews it?"}]});
    await act(() => refreshNeedsYou(false));
    expect(within(reader()).getByRole("textbox", {name: "Answer"})).toHaveValue("");
    expect(within(reader()).getByRole("button", {name: "Send answer"})).toBeDisabled();
    expect(posts).toEqual([]);
  });
});

describe("recorded agent choices and permission prompts", () => {
  beforeEach(() => {
    wire((grammar as any).questions);
    useAgentFlights.setState({sessions: (grammar as any).questionSessions.sessions.map(fromWireSessionRow), flights: []});
  });
  it("fixed agent choices name their current wait and dispatch only the pressed choice", async () => {
    const item = (grammar as any).questions.items.find((item: any) => item.sessionKey === "claude:needs-choice");
    render(<NeedsDrawer />); await choose(item.question);
    expect(within(reader()).queryByRole("textbox")).toBeNull();
    const choice = within(reader()).getByRole("button", {name: "shared flag"});
    expect(posts).toEqual([]); fireEvent.click(choice);
    const session = (grammar as any).questionSessions.sessions.find((row: any) => row.session.session_id === "needs-choice");
    await waitFor(() => expect(posts[0]).toEqual({path: "/api/coders/claude%3Aneeds-choice/steer", json: {text: "1", submit: true, kind: "answer", wait_id: session.session.wait_id}}));
  });
  it("a permission prompt with no complete command offers Deny and Open raw lane", async () => {
    const item = (grammar as any).questions.items.find((item: any) => item.sessionKey === "claude:needs-permission");
    render(<NeedsDrawer />); await choose(item.question);
    expect(within(reader()).queryByRole("button", {name: "Allow"})).toBeNull();
    expect(within(reader()).getByRole("button", {name: "Open raw lane"})).toBeTruthy();
    fireEvent.keyDown(row(item.question), {key: "Enter"}); expect(posts).toEqual([]);
    press("Deny");
    const session = (grammar as any).questionSessions.sessions.find((row: any) => row.session.session_id === "needs-permission");
    await waitFor(() => expect(posts[0]).toEqual({path: "/api/coders/claude%3Aneeds-permission/keys", json: {keys: ["Escape"], kind: "answer", wait_id: session.session.wait_id}}));
  });
});

describe("prepared sends and permission gates", () => {
  it("selecting a send shows its frozen preview and destination; only Send dispatches", async () => {
    wire(sendTape.needsYou);
    const item = sendTape.needsYou.items[0];
    render(<NeedsDrawer />); await choose(item.title);
    expect(screen.getByTestId("needs-send-preview")).toHaveTextContent("The ledger cutover is on track.");
    expect(screen.getByTestId("needs-send-preview")).toHaveTextContent("private-team-folder");
    fireEvent.keyDown(row(item.title), {key: "Enter"}); expect(posts).toEqual([]);
    // The shared Send adapter owns custody; a refused send must not be called done.
    post = async () => {throw new Error("No answer");};
    hub["/api/channels/sends?document_ref=" + encodeURIComponent(item.documentRef)] = {sends: [item.send]};
    press("Send");
    await screen.findByTestId("needs-failure");
    expect(row(item.title)).toBeTruthy();
    expect(screen.getByTestId("needs-send-preview")).toBeTruthy();
  });
  it("Discard keeps its question after a refusal and never follows another selected revision", async () => {
    wire(sendTape.needsYou); post = async () => {throw new Error("Not discarded");};
    render(<NeedsDrawer />); await choose(sendTape.needsYou.items[0].title);
    fireEvent.click(within(verbs()).getByRole("button", {name: "Discard"}));
    fireEvent.click(within(screen.getByTestId("needs-question")).getByRole("button", {name: "Discard"}));
    await screen.findByTestId("needs-failure"); expect(screen.getByTestId("needs-question")).toBeTruthy();
    expect(posts).toHaveLength(1);
    expect(posts[0].path).toBe(`/api/channels/sends/${sendTape.needsYou.items[0].sendId}/discard`);
    fireEvent.click(within(screen.getByTestId("needs-question")).getByRole("button", {name: "Cancel"}));
    expect(screen.queryByTestId("needs-question")).toBeNull();
  });
  it("the full held call can be approved; a cut call has Deny and Open raw lane only", async () => {
    wire(gateTape.wire); render(<NeedsDrawer />);
    await waitFor(() => expect(screen.getAllByTestId("needs-row")).toHaveLength(2));
    fireEvent.click(screen.getAllByTestId("needs-row")[0]);
    expect(reader()).toHaveTextContent("ls /etc");
    fireEvent.keyDown(screen.getAllByTestId("needs-row")[0], {key: "Enter"}); expect(posts).toEqual([]);
    press("Approve");
    await waitFor(() => expect(posts[0]).toEqual({path: "/api/gate/proposals/toolu_glass_approve/decide", json: {decision: "approved", reason: undefined}}));
    await waitFor(() => expect(reader()).toHaveTextContent("Open raw lane"));
    expect(within(reader()).queryByRole("button", {name: "Approve"})).toBeNull();
    expect(within(reader()).getByRole("button", {name: "Deny"})).toBeTruthy();
  });
  it("an unknown send without the hub's replay command has no Try again", async () => {
    const answer = structuredClone(unknownTape.needsYou);
    delete (answer.items[0].send as any).retry_command;
    wire(answer); render(<NeedsDrawer />); await choose(answer.items[0].title);
    expect(within(reader()).queryByRole("button", {name: "Try again"})).toBeNull();
  });
});
