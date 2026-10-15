// Direction only: existing production species with declared sample data.
import { useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { Button } from "@w/components/signal/Signal";
import { GadgetGroup, GadgetRow, StringGadget, PadGadget, CycleGadget, CheckGadget, FoldGadget, EgressChip } from "@w/desk/surface/gadgets";
import { SurfaceWell, SurfaceState } from "@w/desk/surface/Surface";
import { StateChip } from "@w/desk/surface/patterns";
import { SurfaceFooter } from "@w/desk/surface/SurfaceFooter";
import "./canvas.css";
const noop = () => {};
const face = new URLSearchParams(location.search).get("face") || "inspector";
const names: Record<string,string> = {inspector:"Custom webhook",recipe:"Architecture reviewer",question:"Question",workbench:"Architecture review",calendar:"Calendar"};
function Inspector(){return <>
  <div className="canvas-facts"><StateChip state="warning" label="Approval needed"/><EgressChip label="hooks.example.invalid" scope="cloud"/></div>
  <GadgetGroup label="Source" material="inset"><GadgetRow label="Note" controlWidth="full"><strong>Release checklist</strong></GadgetRow><FoldGadget title="Source text"><p>Confirm the rollback owner and release gate before the migration.</p></FoldGadget></GadgetGroup>
  <SurfaceWell head="Preview"><p>Post Release checklist to Custom webhook</p></SurfaceWell>
  <FoldGadget title="Details"><GadgetGroup material="inset"><GadgetRow label="Destination" controlWidth="full">hooks.example.invalid</GadgetRow><GadgetRow label="Control">Normal</GadgetRow><GadgetRow label="Data">Selected text</GadgetRow></GadgetGroup></FoldGadget>
</>}
function Recipe(){const[name,setName]=useState("Architecture reviewer"),[role,setRole]=useState("Review platform changes"),[text,setText]=useState("Review the proposed change. Identify risks, dependencies and a clear next action.");return <>
  <GadgetGroup label="Agent" material="inset"><GadgetRow label="Name" controlWidth="full"><StringGadget label="Name" value={name} onChange={setName}/></GadgetRow><GadgetRow label="Role" controlWidth="full"><StringGadget label="Role" value={role} onChange={setRole}/></GadgetRow></GadgetGroup>
  <GadgetGroup label="Instructions" material="inset"><PadGadget label="Instructions" value={text} onChange={setText} rows={6}/></GadgetGroup>
  <FoldGadget title="Advanced"><GadgetGroup material="inset"><GadgetRow label="Tools" controlWidth="full"><StringGadget label="Tools" value="desk.read, project.read" onChange={noop}/></GadgetRow><GadgetRow label="Knowledge" controlWidth="full"><CycleGadget label="Knowledge" value="platform" options={[{value:"platform",label:"Platform decisions"},{value:"",label:"None"}]} onChange={noop}/></GadgetRow></GadgetGroup></FoldGadget>
</>}
function Question(){const[owner,setOwner]=useState("Jordan"),[count,setCount]=useState("3"),[check,setCheck]=useState(false);return <>
  <p className="canvas-question">Who owns the rollback?</p><GadgetGroup label="Answer" material="inset" actions={<><Button dense onClick={noop}>Decline</Button><Button dense variant="primary" onClick={noop}>Submit</Button></>}><GadgetRow label="Owner *" controlWidth="full"><StringGadget label="Owner *" value={owner} onChange={setOwner}/></GadgetRow><GadgetRow label="Attempts" controlWidth="short"><StringGadget label="Attempts" type="number" value={count} onChange={setCount}/></GadgetRow><GadgetRow label="Notify owner"><CheckGadget variant="state" label="Notify owner" checked={check} onChange={setCheck}/></GadgetRow><GadgetRow label="Priority" controlWidth="standard"><CycleGadget label="Priority" value="normal" options={[{value:"normal",label:"Normal"},{value:"high",label:"High"}]} onChange={noop}/></GadgetRow></GadgetGroup>
</>}
function Workbench(){return <>
  <div className="canvas-facts"><StateChip state="idle" label="Manual"/><span className="surface-token">Runs</span></div>
  <GadgetGroup label="Runs" material="inset"><SurfaceState error="Runs not loaded" onRetry={noop}/></GadgetGroup>
  <GadgetGroup label="Latest output" material="inset"><div className="canvas-facts"><strong>Migration review</strong><StateChip state="warning" label="Review needed"/></div><p>Confirm one rollback owner for each stage. Keep the release gate closed until the reconciliation checks pass.</p><div className="canvas-actions"><Button dense onClick={noop}>Copy</Button><Button dense onClick={noop}>Open artifact</Button></div></GadgetGroup>
</>}
function Calendar(){const[url,setUrl]=useState("https://calendar.example.invalid/architecture.ics");return <>
  <GadgetGroup label="Mac calendars" material="inset" actions={<Button dense onClick={noop}>Check again</Button>}><StateChip state="unreachable" label="Unavailable"/></GadgetGroup>
  <GadgetGroup label="Calendar URL" material="inset" actions={<><EgressChip label="calendar.example.invalid" scope="cloud"/><Button dense disabled={!url.trim()} onClick={noop}>Add</Button></>}><StringGadget label="Calendar URL" value={url} onChange={setUrl} placeholder="https://…/calendar.ics"/></GadgetGroup>
</>}
function Canvas(){const content=face==="recipe"?<Recipe/>:face==="question"?<Question/>:face==="workbench"?<Workbench/>:face==="calendar"?<Calendar/>:<Inspector/>;const verbs=face==="inspector"?<><Button dense onClick={noop}>Reject</Button><Button dense variant="primary" onClick={noop}>Approve</Button></>:face==="question"?<><Button dense onClick={noop}>Decline</Button><Button dense variant="primary" onClick={noop}>Submit</Button></>:face==="recipe"?<Button dense variant="primary" onClick={noop}>Done</Button>:<Button dense onClick={noop}>Back</Button>;return <RuntimeBusProvider><main className="desk-next canvas-desk"><DeskWindowFrame id="visual-refinement-canvas" title={names[face]} label={names[face]} minW={320} defaultW={620} defaultH={640} fitContent open entrance={false} onClose={noop} className="desk-surface-window"><div className="desk-surface-body canvas-body">{content}</div>{face!=="question" ? <div className="desk-surface-foot"><SurfaceFooter egress={face==="inspector"?<EgressChip label="hooks.example.invalid" scope="cloud"/>:undefined} receipt={face==="inspector"?<StateChip state="warning" label="Awaiting approval"/>:undefined} verbs={verbs}/></div> : null}</DeskWindowFrame></main></RuntimeBusProvider>}
createRoot(document.getElementById("root")!).render(<Canvas/>);
