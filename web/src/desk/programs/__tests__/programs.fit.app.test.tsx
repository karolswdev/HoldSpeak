import { useState } from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { hub, mocks, running, type Program } from "./programs.seats.test-setup";
import review from "../__fixtures__/program.review-fit.json";
import start from "../__fixtures__/program.start-fit.json";
import visual from "../__fixtures__/program.visual10.json";
import { TextChanges, type ChangeProposal } from "../ProgramText";
import { ProgramLedger } from "../Ledger";
import { ProgramNow } from "../ProgramWindow";
import { ProgramRace } from "../ProgramRecords";
import type { TextApplyAnswer } from "../types";
import { bindingId } from "../liveModel";

const press=(name:string)=>fireEvent.click(screen.getByRole("button",{name}));
describe("Programs fit review regressions",()=>{
  it("replacement content clears lowerings and the armed callback before Apply",async()=>{
    const program=review.program as unknown as Program;
    const proposal=(second=false):ChangeProposal=>({answer:(second?review.second:review.first) as TextApplyAnswer,text:second?review.second_text:review.first_text,base:review.base,binding:review.binding,target:bindingId(program)});
    hub({[`POST /api/programs/${program.id}/text`]:review.applied});
    const applied=vi.fn(), props={program,onApplied:applied,onCancel:()=>{},onError:()=>{}};
    const view=render(<TextChanges {...props} proposal={proposal()}/>);
    fireEvent.click(screen.getByRole("grid",{name:"Text changes"}).querySelector('[data-object-id="program.control"]')!);
    fireEvent.click(screen.getByRole("checkbox",{name:"Allow this change"}));
    press("Apply"); expect(screen.getByRole("region",{name:"Apply these changes?"})).toBeTruthy();
    view.rerender(<TextChanges {...props} proposal={proposal(true)}/>);
    expect(screen.queryByRole("region",{name:"Apply these changes?"})).toBeNull();
    expect(screen.getByRole("button",{name:"Apply"})).toBeDisabled();
    fireEvent.click(screen.getByRole("grid",{name:"Text changes"}).querySelector('[data-object-id="program.control"]')!);
    expect(screen.getByRole("checkbox",{name:"Allow this change"})).not.toBeChecked();
    fireEvent.click(screen.getByRole("checkbox",{name:"Allow this change"}));press("Apply");
    fireEvent.click(within(screen.getByRole("region",{name:"Apply these changes?"})).getByRole("button",{name:"Apply"}));
    await waitFor(()=>expect(applied).toHaveBeenCalledWith(review.applied.program));
    expect(mocks.apiFetch).toHaveBeenCalledWith(expect.stringContaining("/text"),expect.objectContaining({json:expect.objectContaining({proposal_id:review.second.proposal_id,text:review.second_text})}));
  });
  it("Start from here keeps one pending press and draws the acknowledged checkpoint",async()=>{
    let resolve:(value:unknown)=>void=()=>{};
    const before=start.program as unknown as Program, after=start.answer.program as unknown as Program;
    hub({[`POST /api/programs/${before.id}/checkpoints/${start.checkpoint_id}/start-from`]:()=>new Promise(done=>{resolve=done;})});
    function Host(){const [p,setP]=useState(before);return <ProgramLedger program={p} onApplied={next=>{if(next)setP(next);}} onError={()=>{}}/>;}
    render(<Host/>);
    fireEvent.click(screen.getByRole("grid",{name:"Program ledger"}).querySelector(`[data-object-id="${start.checkpoint_id}"]`)!);
    press("Start from here"); press("Start from here");
    expect(mocks.apiFetch.mock.calls.filter(([path])=>path.endsWith("/start-from"))).toHaveLength(1);
    resolve(start.answer);
    const added=after.checkpoints.find(row=>!before.checkpoints.some(old=>old.id===row.id))!;
    await screen.findByText(added.line);
    expect(mocks.apiFetch).toHaveBeenCalledWith(expect.stringContaining("/start-from"),expect.objectContaining({json:expect.objectContaining({binding:expect.objectContaining({program_id:before.id,revision:before.revision})})}));
  });
  it("Now and contender briefs stay inside feedback redaction regions",()=>{
    const view=render(<ProgramNow program={running} onApplied={()=>{}} onError={()=>{}}/>);
    expect(view.container.querySelector('.surface-live-content .surface-inspector-facts')).toHaveAttribute("data-feedback-redact","true");
    view.unmount();
    const program=visual.wires.race_choice.program as unknown as Program;
    render(<ProgramRace creating={false} onCreated={()=>{}} program={program} step={program.steps[0]} onApplied={()=>{}} onError={()=>{}}/>);
    const grid=screen.getByRole("grid",{name:"Race contenders"});fireEvent.click(grid.querySelector('[data-object-id]')!);
    expect(screen.getByRole("region",{name:"Contender"})).toHaveAttribute("data-feedback-redact","true");
  });
});
