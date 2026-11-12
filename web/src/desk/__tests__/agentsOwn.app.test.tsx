/** The face half of the moved private-process walk; answers are real hub recordings. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import wire from "./fixtures/agents-own-process.json";
const boundary = vi.hoisted(() => ({fetch:vi.fn(),request:vi.fn()}));
vi.mock("../../lib/api", async original => ({...await original<typeof import("../../lib/api")>(),apiFetch:boundary.fetch,apiRequest:boundary.request}));
vi.mock("../../runtime/RuntimeBus", () => ({useRuntimeBus:()=>({state:"connected",subscribe:()=>()=>undefined}),useOptionalRuntimeBus:()=>null,useRuntimeFrame:()=>null}));
vi.mock("../components/MicButton", () => ({MicButton:()=>null}));
import { ConductorWindow } from "../conductor/ConductorWindow";
import { __resetConductor, useConductor } from "../conductor/store";
import { __resetLane } from "../lane/laneStore";
import { useAgentFlights } from "../agentFlights";
let own: typeof wire.asking | typeof wire.held = wire.asking;
beforeEach(() => {
  vi.useFakeTimers({toFake:["Date"]}); vi.setSystemTime(wire.captured_at*1000);
  __resetConductor(); __resetLane(); useAgentFlights.setState({sessions:[],flights:[],loaded:false});
  own = wire.asking;
  boundary.fetch.mockReset().mockImplementation(async (url:string, init?:{json?:Record<string,unknown>}) => {
    if(url === "/api/coders/own-agents/answer") { own = wire.held; return init?.json?.text ? wire.answered : wire.allowed; }
    if(url.startsWith("/api/coders/own-agents")) return own;
    if(url.startsWith("/api/coders/sessions")) return wire.sessions;
    if(url === "/api/onboarding/agents") return wire.detect;
    throw new Error(`Unrecorded own-agent read: ${url}`);
  });
});
afterEach(() => {__resetConductor(); __resetLane(); vi.useRealTimers();});
it("selects the owner-started process, answers its question and allows its current permission", async () => {
  render(<ConductorWindow />);
  const id=wire.asking.agents[0].id;
  const row = await waitFor(() => {
    const value = document.querySelector<HTMLElement>(`[role="row"][data-object-id="${id}"]`);
    expect(value).not.toBeNull(); return value!;
  });
  fireEvent.click(row);
  const question = await screen.findByTestId("conductor-ask-row");
  expect(question).toHaveTextContent("I found two places for the rollback flag");
  expect(within(question).queryByRole("button",{name:"Stop"})).toBeNull();
  fireEvent.change(within(question).getByRole("textbox",{name:/Answer/}),{target:{value:"config"}});
  fireEvent.click(within(question).getByRole("button",{name:"Answer"}));
  await waitFor(() => expect(boundary.fetch.mock.calls.find(([url])=>url==="/api/coders/own-agents/answer")?.[1].json).toEqual(wire.answer_body));
  // The original walk reloaded after the process reached its permission.
  await act(async () => { await useConductor.getState().readOwnAgents(); });
  const allow=await screen.findByRole("button",{name:"Allow"});
  expect(allow).toBeEnabled(); fireEvent.click(allow);
  await waitFor(() => expect(boundary.fetch.mock.calls.filter(([url])=>url==="/api/coders/own-agents/answer").at(-1)?.[1].json).toEqual(wire.allow_body));
});
