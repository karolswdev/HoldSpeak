import {fireEvent, render, screen, waitFor} from "@testing-library/react";
import {beforeEach, expect, it, vi} from "vitest";
import {apiFetch} from "../../../lib/api";
import {AgentRow} from "../AgentRow";
import {fromWireSessionRow} from "../../agentFlights";
import {conductorMembers} from "../../conductor/members";
import tape from "../../needs/__fixtures__/needs_you.grammar.json";

vi.mock("../../../lib/api", async original => ({...await original<typeof import("../../../lib/api")>(),apiFetch:vi.fn()}));
vi.mock("../../../components/MicButton", () => ({MicButton:()=>null}));

beforeEach(() => vi.mocked(apiFetch).mockImplementation(async () => ({gated:[],wait:{kind:"TO ANSWER",question:"A different lane question",wait_id:"different-wait"}}) as never));

it("the Agents caller displays and sends the same recorded prompt binding even when its lane read differs", async () => {
  const sessions=tape.typedAnswer.sessions.sessions.map(fromWireSessionRow);
  const member=conductorMembers({detect:[],sessions,flights:[],launchedAt:{}}).find(row => row.sessionKey === "claude:needs-typed")!;
  render(<AgentRow member={{...member,launchId:"binding-reader"}} question="An older question" waitId="older-wait" lead selected
    onSelect={()=>{}} onTerminal={()=>{}} onOpenAnswer={()=>{}} onOpen={()=>{}} />);
  await waitFor(() => expect(apiFetch).toHaveBeenCalled());
  expect(screen.getByTestId("agent-row-question").textContent).toBe(member.answerQuestion);
  expect(screen.queryByText("A different lane question")).toBeNull();
  fireEvent.change(screen.getByTestId("agent-row-answer-field"),{target:{value:"Jordan"}});
  fireEvent.click(screen.getByRole("button",{name:"Answer",exact:true}));
  await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/coders/claude%3Aneeds-typed/steer",{
    method:"POST",json:{text:"Jordan",submit:true,kind:"answer",...member.answerBinding},
  }));
});
