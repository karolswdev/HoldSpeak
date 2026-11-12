/** Recorded sends and Program choices, through an explicit press in the reader. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { recordedGet } from "../../test/recordedHub";
import { NeedsDrawer, useDropped } from "../needs/NeedsDrawer";
import { useAgentFlights } from "../agentFlights";
import { resetSendStore } from "../surface/send";
import { useDesk } from "../store";
import grammar from "../needs/__fixtures__/needs_you.grammar.json";
import unknown from "./fixtures/send-needs/needs-send-unknown.json";
import audit from "../programs/__fixtures__/needs_you.audit.json";
import lesson from "../programs/__fixtures__/needs_you.lesson.json";
import phone from "../calls/__fixtures__/needs_you.phone.json";
import engine from "../needs/__fixtures__/needs_you.rows.json";
import daily from "./fixtures/daily-week/needs-you-arrival.json";

vi.mock("../../lib/api", async original => ({...await original<typeof import("../../lib/api")>(), apiFetch: vi.fn()}));
vi.mock("../components/MicButton", () => ({MicButton: () => null}));
vi.mock("../documentSendsLazy", () => ({NoteSendWells: ({id}: {id: string}) => <div data-testid="note-send-wells" data-note={id} />}));
let answer: any, gets: Record<string, unknown>, posts: {path: string; json: any}[];
let onPost: (path: string, json: any) => Promise<any>;
const rows = () => screen.queryAllByTestId("needs-row");
async function select(title: string) {
  await waitFor(() => expect(rows().some(row => row.textContent?.includes(title))).toBe(true));
  fireEvent.click(rows().find(row => row.textContent?.includes(title))!);
  return screen.getByTestId("needs-reader");
}
const press = (name: string) => fireEvent.click(within(screen.getByTestId("needs-reader")).getByRole("button", {name}));
const bar = () => within(screen.getByRole("toolbar", {name: "Needs you"}));
beforeEach(() => {
  gets = {}; posts = []; answer = grammar.typed; onPost = async () => ({});
  resetSendStore(); useDropped.setState({dropped: null});
  useAgentFlights.setState({sessions: [], flights: [], loaded: true, settled: true});
  useDesk.setState({scheduledArming: null} as never);
  vi.mocked(apiFetch).mockImplementation(async (path, init) => {
    const url = String(path);
    if (init?.method && init.method !== "GET") {posts.push({path: url, json: init.json}); return onPost(url, init.json);}
    return recordedGet({"/api/desk/needs-you?fresh=1": answer, ...gets}, url) as never;
  });
});

describe("the shared Send adapter in Needs you", () => {
  it("an acknowledged file send leaves the selected need and is kept in Answered", async () => {
    const scenario = (grammar as any).send;
    answer = scenario.before;
    const item = answer.items.find((item: any) => item.source === "send");
    onPost = async path => {if (path === "/api/channels/send") {answer = scenario.after; return scenario.answer;} return {};};
    render(<NeedsDrawer />); await select(item.title);
    expect(screen.getByTestId("needs-send-preview")).toHaveTextContent("Jordan owns the rollback runbook.");
    expect(posts).toEqual([]);
    press("Send");
    await waitFor(() => expect(posts).toContainEqual({path: "/api/channels/send", json: expect.objectContaining({send_id: item.sendId, command_id: expect.any(String)})}));
    await waitFor(() => expect(rows().some(row => row.dataset.objectId === item.id)).toBe(false));
    expect(screen.getByTestId("needs-receipt")).toHaveTextContent("Sent");
    fireEvent.click(screen.getByRole("tab", {name: "Answered"}));
    expect(screen.getByRole("grid", {name: "Answered"})).toHaveTextContent(item.title);
  });
  it("Discard asks, keeps Cancel focused, and uses the hub's discard receipt", async () => {
    const scenario = (grammar as any).discard;
    answer = scenario.before;
    const item = answer.items.find((item: any) => item.source === "send");
    onPost = async path => {if (path.endsWith("/discard")) {answer = scenario.after; return scenario.answer;} return {};};
    render(<NeedsDrawer />); await select(item.title);
    fireEvent.click(bar().getByRole("button", {name: "Discard"}));
    expect(posts).toEqual([]);
    const question = screen.getByTestId("needs-question");
    expect(document.activeElement).toBe(within(question).getByRole("button", {name: "Cancel"}));
    fireEvent.click(within(question).getByRole("button", {name: "Discard"}));
    await waitFor(() => expect(rows().some(row => row.dataset.objectId === item.id)).toBe(false));
    expect(posts).toContainEqual({path: `/api/channels/sends/${item.sendId}/discard`, json: {command_id: expect.any(String)}});
    expect(screen.getByTestId("needs-receipt")).toHaveTextContent("Discard");
  });
  it("an unknown result keeps Check and an exact replay; a lost retry reuses its command", async () => {
    answer = structuredClone(unknown.needsYou);
    const item = answer.items[0];
    gets[`/api/channels/sends?document_ref=${encodeURIComponent(item.documentRef)}`] = {sends: [item.send]};
    onPost = async () => {throw new Error("No answer");};
    render(<NeedsDrawer />); await select(item.title);
    press("Check");
    await waitFor(() => expect(screen.getByTestId("needs-receipt")).toHaveTextContent("Checked destination"));
    expect(posts).toEqual([]);
    press("Try again"); await screen.findByTestId("needs-failure");
    press("Try again"); await waitFor(() => expect(posts).toHaveLength(2));
    expect(posts[0].json.command_id).toBe(item.send.retry_command.command_id);
    expect(posts[1].json).toEqual(posts[0].json);
    expect(rows().some(row => row.dataset.objectId === item.id)).toBe(true);
  });
});

describe("all recorded Program choices stay on their selected object", () => {
  for (const tape of [audit, lesson]) {
    for (const item of tape.items) {
      for (const choice of item.program.choices) {
        it(`${item.program.kind}: ${choice} names the saved step and optional finding or lesson`, async () => {
          answer = {...tape, items: [item]};
          render(<NeedsDrawer />); await select(item.group);
          const button = within(screen.getByTestId("needs-reader")).getAllByTestId("needs-answer-choice").find(button => button.dataset.choice === choice)!;
          fireEvent.click(button);
          if (screen.queryByTestId("needs-question")) fireEvent.click(within(screen.getByTestId("needs-question")).getAllByRole("button")[1]);
          await waitFor(() => expect(posts).toContainEqual({path: item.program.decide, json: expect.objectContaining({kind: item.program.kind, choice,
            ...(item.program.findingId ? {finding_id: item.program.findingId} : {}), ...("lessonId" in item.program ? {lesson_id: item.program.lessonId} : {})})}));
        });
      }
    }
  }
  it("Retry on a recorded engine failure runs that same job and removes its need", async () => {
    const [before, after] = engine.engine.steps; answer = before.gets["/api/desk/needs-you?fresh=1"];
    onPost = async () => {answer = after.gets["/api/desk/needs-you?fresh=1"]; return {};};
    render(<NeedsDrawer />); await select(engine.engine.title); press("Retry");
    await waitFor(() => expect(posts).toEqual([{path: after.post, json: after.body}]));
    await waitFor(() => expect(rows().some(row => row.textContent?.includes(engine.engine.title))).toBe(false));
  });
  it("the Phone's own recorded choices keep their method, route and body", async () => {
    answer = phone;
    render(<NeedsDrawer />);
    const item = (phone.items as Array<{title: string; phone: {verbs: Array<{label: string; href: string; needs_text?: boolean; body?: unknown}>}}>).find(item => item.phone.verbs.some(verb => !verb.needs_text))!;
    const pane = await select(item.title);
    const verb = item.phone.verbs.find(verb => !verb.needs_text)!;
    fireEvent.click(within(pane).getByRole("button", {name: verb.label}));
    await waitFor(() => expect(posts).toContainEqual({path: verb.href, json: verb.body ?? {}}));
  });
  it("new promises remain single rows; selecting one records that its meeting was read", async () => {
    answer = daily.needsYou;
    render(<NeedsDrawer />); const title = "Email Dana about the cutover window";
    await select(title);
    const item = answer.items.find((item: any) => item.title === title);
    expect(rows().filter(row => row.textContent?.includes(title))).toHaveLength(1);
    await waitFor(() => expect(posts).toContainEqual({path: "/api/desk/needs-you/seen", json: {meeting_ids: [item.arrival.meetingId]}}));
  });
});
