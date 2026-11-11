import { useState } from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { adjust, amendedFixture, titledFixture, bindingUnboundFixture, bindingBoundFixture, roundsFixture, mocks, hub, ApiError, type Program } from "./programs.seats.test-setup";
import visual from "../__fixtures__/program.visual10.json";
import seats from "../__fixtures__/program.seats10.json";
import { ProgramSteps } from "../ProgramSteps";
import { ProgramInterview } from "../ProgramInterview";
import { ProgramRace } from "../ProgramRecords";
const press=(name:string)=>fireEvent.click(screen.getByRole("button",{name}));
const tab=(name:string)=>fireEvent.click(screen.getByRole("tab",{name}));
const change=(label:string,value:string)=>fireEvent.change(screen.getByLabelText(label),{target:{value}});
function Steps({initial=adjust,selected=initial.steps[0].id}:{initial?:Program;selected?:string}){
 const [p,setP]=useState(initial),[id,setId]=useState(selected),[error,setError]=useState("");
 return <><ProgramSteps program={p} selected={id} onSelect={setId} onApplied={next=>{if(next)setP(next)}} onError={setError}/><output>{error}</output></>;
}
describe("Steps inspector seats",()=>{
 it("a started brief stays read-only while its title and later gates remain editable",async()=>{
  const p=adjust; hub({[`PATCH /api/programs/${p.id}/steps/${p.steps[0].id}`]:titledFixture});
  render(<Steps/>); press("Edit step");
  expect(screen.queryByLabelText("Step brief")).toBeNull();
  change("Step name","The call runner, renamed"); press("Save");
  await screen.findByText((titledFixture as unknown as Program).steps[0].title);
  expect(mocks.apiFetch).toHaveBeenCalledWith(expect.any(String),expect.objectContaining({json:expect.not.objectContaining({brief:expect.anything()})}));
 });
 it("Amend brief sends only the new sentence and draws the saved brief",async()=>{
  const p=adjust;hub({[`POST /api/programs/${p.id}/steps/${p.steps[0].id}/amend`]:amendedFixture});
  render(<Steps/>);press("Amend brief");change("Step brief","Also keep the transcript.");press("Amend brief");
  await waitFor(()=>expect(screen.queryByLabelText("Step brief")).toBeNull());
  expect(mocks.apiFetch).toHaveBeenCalledWith(expect.stringContaining("/amend"),expect.objectContaining({json:{line:"Also keep the transcript."}}));
 });
 it("a move above a dependency is refused before dispatch",()=>{
  render(<Steps selected={adjust.steps[1].id}/>);press("Move up");expect(screen.getByText("This step must stay after its dependency.")).toBeTruthy();expect(mocks.apiFetch).not.toHaveBeenCalled();
 });
 it("a manually added step carries the action only after its choice is pressed",async()=>{
  const p=bindingUnboundFixture as unknown as Program;hub({[`POST /api/programs/${p.id}/plan`]:bindingBoundFixture});
  render(<Steps initial={p}/>);press("Add step");change("Step name","Check the action");
  const carry=screen.getByRole("checkbox",{name:"Carry the program action"});expect((carry as HTMLInputElement).checked).toBe(false);fireEvent.click(carry);press("Add step");
  await waitFor(()=>expect(screen.queryByLabelText("Step name")).toBeNull());
  expect(mocks.apiFetch).toHaveBeenCalledWith(expect.stringContaining("/plan"),expect.objectContaining({json:expect.objectContaining({replace:false,steps:[expect.objectContaining({origin_ref:p.origin_ref})]})}));
 });
 it("an uncertain Add retains input, blocks a second POST and reads the stored steps",async()=>{
  const p=adjust;hub({[`POST /api/programs/${p.id}/plan`]:()=>{throw new TypeError("Network lost")},[`GET /api/programs/${p.id}`]:p});
  render(<Steps/>);press("Add step");change("Step name","Keep this");press("Add step");
  await screen.findByText(/The hub did not confirm/);expect((screen.getByRole("button",{name:"Add step"}) as HTMLButtonElement).disabled).toBe(true);
  expect((screen.getByLabelText("Step name") as HTMLInputElement).value).toBe("Keep this");press("Read the steps");await screen.findByRole("grid",{name:"Steps"});
  expect(mocks.apiFetch.mock.calls.filter(([,init])=>init?.method==="POST")).toHaveLength(1);
 });
 it("a three-agent race sends its choice and renders the acknowledged contenders count",async()=>{
  const p=seats.program as unknown as Program;const after=seats.race_three as unknown as Program;
  hub({[`POST /api/programs/${p.id}/steps/${p.steps[0].id}/race`]:after});render(<Steps initial={p}/>);press("Race");change("Race contenders","3");press("Start race");
  await screen.findByRole("grid",{name:"Race contenders"});expect(mocks.apiFetch).toHaveBeenCalledWith(expect.stringContaining("/race"),expect.objectContaining({json:{n:3}}));
 });
 it("a selected contender answers its own revision and the chosen result replaces the question",async()=>{
  const tape=visual.wires.race_choice,p=tape.program as unknown as Program;const step=p.steps[0],item=p.your_turn_items.find(x=>x.step_id===tape.step_id)!;
  hub({[`POST /api/programs/${p.id}/steps/${item.step_id}/decide`]:tape.picked});
  function Race(){const [program,setP]=useState(p);return <ProgramRace program={program} step={program.steps[0]} creating={false} onCreated={()=>{}} onApplied={next=>{if(next)setP(next)}} onError={()=>{}}/>}
  render(<Race/>);fireEvent.click(screen.getByRole("grid",{name:"Race contenders"}).querySelector(`[data-object-id="${item.step_id}"]`)!);press("Pick this one");change("Race answer note","Keep this result.");fireEvent.click(within(document.querySelector<HTMLElement>("[data-question]")!).getByRole("button",{name:"Pick this one"}));
  await waitFor(()=>expect((screen.getByRole("button",{name:"Pick this one"}) as HTMLButtonElement).disabled).toBe(true));
  expect(mocks.apiFetch).toHaveBeenCalledWith(expect.any(String),expect.objectContaining({json:expect.objectContaining({reason:"Keep this result.",binding:expect.objectContaining({step_id:item.step_id,step_revision:[step,...step.contenders].find(s=>s.id===item.step_id)!.updated_at})})}));
 });
});

describe("Rounds inspector",()=>{
 it("an offered answer sends its question id and opens the proposed changes",async()=>{
  const fx=roundsFixture as any,q=fx.steps["architecture.next"],p=q.program as Program;
  hub({[`POST /api/programs/${p.id}/rounds/Architecture/answer`]:fx.steps["architecture.answer"]});
  function Round(){const [program,setP]=useState(p);return <ProgramInterview program={program} onApplied={next=>{if(next)setP(next)}} onError={()=>{}}/>}
  render(<Round/>);change("Offered answer",q.question.choices[0]);press("Answer");
  await screen.findByRole("grid",{name:"Text changes"});expect(mocks.apiFetch).toHaveBeenCalledWith(expect.stringContaining("/answer"),expect.objectContaining({json:expect.objectContaining({question_id:q.question.id,option:q.question.choices[0]})}));
 });
});
