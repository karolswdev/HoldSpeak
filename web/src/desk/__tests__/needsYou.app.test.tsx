/** The hub's one answer, rendered as a selection list and its reader. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { recordedGet, type Gets } from "../../test/recordedHub";
import { NeedsDrawer, useDropped, useSourceReceipt } from "../needs/NeedsDrawer";
import { useAgentFlights } from "../agentFlights";
import { refreshNeedsYou } from "../needsYou";
import { useDesk } from "../store";
import RECORDED from "./fixtures/needsYou.recorded.json";
import rowTape from "../needs/__fixtures__/needs_you.rows.json";
import daily from "./fixtures/daily-week/needs-you.json";
import locked from "./fixtures/daily-week/needs-you-people-locked.json";
import { INTELLIGENCE_NAVIGATE } from "../intelligenceNavigation";
import { openSurfaceOr } from "../shell";

vi.mock("../../lib/api", async original => ({...await original<typeof import("../../lib/api")>(), apiFetch: vi.fn()}));
vi.mock("../components/MicButton", () => ({MicButton: () => null}));
vi.mock("../shell", async original => ({...await original<typeof import("../shell")>(), openSurfaceOr: vi.fn()}));
let hub: Gets, posts: Array<{path: string; json: any}>;
let steps: any[];
let failure = false;
const listRows = () => screen.queryAllByTestId("needs-row");
const row = (title: string) => listRows().find(el => el.textContent?.includes(title));
const select = async (title: string) => {await waitFor(() => expect(row(title)).toBeTruthy()); fireEvent.click(row(title)!); return screen.getByTestId("needs-reader");};
const tab = () => screen.getByRole("toolbar", {name: "Needs you"});
const scope = (name: string, value: string) => fireEvent.change(within(tab()).getByRole("combobox", {name}), {target: {value}});
beforeEach(() => {
  steps = []; failure = false; posts = []; hub = rowTape.steps[0].gets;
  useDropped.setState({dropped: null}); useSourceReceipt.setState({receipt: null});
  useAgentFlights.setState({sessions: [], flights: [], loaded: true, settled: true});
  useDesk.setState({scheduledArming: null} as never);
  vi.mocked(apiFetch).mockImplementation(async (path, init) => {
    const url = String(path);
    if (init?.method && init.method !== "GET") {
      posts.push({path: url, json: init.json});
      if (failure) throw new Error("Not saved");
      const step = steps.find(step => step.post === url);
      if (step) {hub = step.gets; return step.answer;}
      return {} as never;
    }
    return recordedGet(hub, url) as never;
  });
});

describe("the owner's work on recorded hub answers", () => {
  it("keeps the hub's count while People narrows the list", async () => {
    hub = {"/api/desk/needs-you?fresh=1": daily.needsYou};
    render(<NeedsDrawer />);
    expect(await screen.findByTestId("arrival-display")).toHaveTextContent(`${daily.needsYou.count} need`);
    const mine = listRows().map(el => el.textContent);
    scope("Whose", "people");
    await waitFor(() => expect(listRows().length).toBeGreaterThan(0));
    expect(listRows().map(el => el.textContent)).not.toEqual(mine);
    expect(screen.getByTestId("arrival-display")).toHaveTextContent(`${daily.needsYou.count} need`);
    scope("Whose", "mine");
    expect(listRows().map(el => el.textContent)).toEqual(mine);
  });
  it("Confirm on a later proposal retains the obligation and records the answer", async () => {
    steps = RECORDED.unfiled.steps; hub = steps[0].gets;
    render(<NeedsDrawer />); const title = RECORDED.unfiled.action;
    fireEvent.click(within(await screen.findByRole("toolbar", {name: "Needs you"})).getByRole("button", {name: "More"}));
    fireEvent.click(await screen.findByRole("menuitem", {name: "Show later items"}));
    const pane = await select(title);
    fireEvent.click(within(pane).getByRole("button", {name: "Confirm"}));
    await waitFor(() => expect(posts).toContainEqual({path: steps[1].post, json: {binding: steps[0].gets["/api/desk/needs-you?fresh=1"].items.find((item: any) => item.proposalId && item.title === title)?.binding}}));
    await waitFor(() => expect(listRows().some(el => el.dataset.objectId?.startsWith("proposal:") && el.textContent?.includes(title))).toBe(false));
    // The hub retains the new action item. It is read through its own source,
    // separate from the old proposal revision recorded in Answered.
    expect(screen.getByTestId("needs-receipt")).toHaveTextContent("Confirm");
    fireEvent.click(screen.getByRole("tab", {name: "Answered"}));
    expect(screen.getByRole("grid", {name: "Answered"})).toHaveTextContent(title);
  });
  it("Not now posts the recorded defer route and the decision leaves", async () => {
    steps = RECORDED.unfiled.steps; hub = steps[1].gets;
    render(<NeedsDrawer />); const title = RECORDED.unfiled.decision;
    fireEvent.click(within(await select(title)).getByRole("button", {name: "Not now"}));
    await waitFor(() => expect(posts).toContainEqual({path: steps[2].post, json: {}}));
    await waitFor(() => expect(row(title)).toBeUndefined());
  });
  it("a follow-through ref selects the item in this window and shows its whole text", async () => {
    render(<NeedsDrawer />); await screen.findByTestId("needs-list");
    act(() => window.dispatchEvent(new CustomEvent(INTELLIGENCE_NAVIGATE, {detail: {view: "follow-through", followThroughId: "rows-plain"}})));
    expect(await screen.findByTestId("needs-reader-text")).toHaveTextContent("Book the cutover dry run");
    expect(screen.getByTestId("needs-reader")).toHaveTextContent("Yours");
  });
  it("the date form retains a refused save and uses one completion row", async () => {
    render(<NeedsDrawer />); await select("Book the cutover dry run");
    fireEvent.click(within(tab()).getByRole("button", {name: "More"}));
    fireEvent.click(screen.getByRole("menuitem", {name: "Set a date"}));
    const pane = screen.getByTestId("needs-reader"), due = within(pane).getByLabelText("Due");
    fireEvent.change(due, {target: {value: "2026-12-01"}}); failure = true;
    fireEvent.click(within(pane).getByRole("button", {name: "Save"}));
    await screen.findByTestId("needs-failure");
    expect(due).toHaveValue("2026-12-01");
    expect(pane.querySelectorAll(".surface-inspector-actions")).toHaveLength(1);
    expect(posts[0].json).toEqual({card_id: "rows-plain", verb: "due", payload: {due_at: "2026-12-01"}});
  });
  it("a failed People read remains a named failure with the existing work", async () => {
    hub = locked.gets; render(<NeedsDrawer />);
    expect(await screen.findByText("People could not be read")).toBeTruthy();
    expect(listRows().length).toBeGreaterThan(0);
    fireEvent.click(within(tab()).getByRole("button", {name: "More"}));
    expect(screen.getByRole("menuitem", {name: "Read again"})).toBeTruthy();
  });
  it("a failed source is a plain row; Reconnect opens its saved provider settings", async () => {
    hub = RECORDED.evalError.steps.at(-1)!.gets;
    render(<NeedsDrawer />);
    const source = await screen.findByTestId("needs-source-row");
    expect(source.querySelector("button")).toBeNull(); fireEvent.click(source);
    const pane = screen.getByTestId("needs-reader");
    expect(within(pane).getByRole("button", {name: "Reconnect"})).toBeTruthy();
    fireEvent.click(within(pane).getByRole("button", {name: "Reconnect"}));
    expect(openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "integration:github");
    expect(source.textContent).not.toMatch(/Traceback|token=/);
  });
  it("Done on a People's promise still uses its recorded transition route", async () => {
    steps = rowTape.done.steps; hub = steps[0].gets;
    render(<NeedsDrawer />);
    const title = rowTape.done.promise;
    await select(title);
    fireEvent.click(within(screen.getByTestId("needs-reader")).getByRole("button", {name: "Done"}));
    const step = steps.find(step => step.post?.startsWith("/api/people/commitments/"));
    await waitFor(() => expect(posts).toContainEqual({path: step.post, json: {verb: "done"}}));
    await waitFor(() => expect(row(title)).toBeUndefined());
  });
});
