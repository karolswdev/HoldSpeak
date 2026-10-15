// Direction specimens only, composed from the production library.
import { useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { Button } from "@w/components/signal/Signal";
import { GadgetGroup, GadgetRow, StringGadget, PadGadget, CycleGadget, EgressChip } from "@w/desk/surface/gadgets";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceState, SurfaceSection } from "@w/desk/surface/Surface";
import { StateChip } from "@w/desk/surface/patterns";
import { SurfaceFooter } from "@w/desk/surface/SurfaceFooter";
import "./canvas.css";
const noop=()=>{};
const face=new URLSearchParams(location.search).get("face")||"schedule";
const titles:Record<string,string>={schedule:"Schedule recording",history:"Architecture delivery",knowledge:"Architecture knowledge",recipients:"Email destination",terminal:"Architecture cutover"};
function Schedule(){const[title,setTitle]=useState("Architecture review"),[when,setWhen]=useState("2026-10-19T09:00");return <>
 <GadgetGroup label="Recording" material="inset"><GadgetRow label="Title" controlWidth="full"><StringGadget label="Title" value={title} onChange={setTitle}/></GadgetRow><GadgetRow label="Mode" controlWidth="standard"><CycleGadget label="Mode" value="once" options={[{value:"once",label:"Once"},{value:"recurring",label:"Recurring"}]} onChange={noop}/></GadgetRow><GadgetRow label="When" controlWidth="full"><StringGadget type="datetime-local" inputProps={{style:{colorScheme:"light"}}} label="When" value={when} onChange={setWhen}/></GadgetRow><GadgetRow label="Duration" controlWidth="standard"><CycleGadget label="Duration" value="60" options={[{value:"30",label:"30 min"},{value:"60",label:"60 min"}]} onChange={noop}/></GadgetRow></GadgetGroup>
</>}
function History(){const[q,setQ]=useState("migration");return <><GadgetGroup label="History" material="inset"><StringGadget label="Search history" value={q} onChange={setQ} placeholder="Search history"/><SurfaceState error="History unavailable" onRetry={noop}/></GadgetGroup></>}
function Knowledge(){return <SurfaceSection label="Entries"><SurfaceLedger cols="room"><SurfaceLedgerRow wrap primary="Migration checkpoints" cells="Note" trailing={<Button dense onClick={noop}>Open</Button>}/><SurfaceLedgerRow wrap primary="Item unavailable" meta="Note" cells={<StateChip state="unreachable" label="Unavailable"/>}/></SurfaceLedger></SurfaceSection>}
function Recipients(){const[to,setTo]=useState(Array.from({length:6},(_,i)=>`architecture-report-owner-${i+1}@example.invalid`).join("\n")),[cc,setCc]=useState("platform-reviewer@example.invalid\nrelease-owner@example.invalid");return <><GadgetGroup label="Email" material="inset"><GadgetRow label="From" controlWidth="full"><StringGadget label="From" value="owner@example.invalid" onChange={noop}/></GadgetRow><GadgetRow label="To" controlWidth="full"><PadGadget label="To" value={to} onChange={setTo} rows={3} autoGrow/></GadgetRow><GadgetRow label="Cc" controlWidth="full"><PadGadget label="Cc" value={cc} onChange={setCc} rows={2} autoGrow/></GadgetRow></GadgetGroup></>}
function Terminal(){return <GadgetGroup label="Terminal" material="inset"><SurfaceState error="Terminal unavailable · no pane on this session" onRetry={noop}/></GadgetGroup>}
function Canvas(){const content=face==="history"?<History/>:face==="knowledge"?<Knowledge/>:face==="recipients"?<Recipients/>:face==="terminal"?<Terminal/>:<Schedule/>;const verbs=face==="schedule"?<><Button dense onClick={noop}>Cancel</Button><Button dense variant="primary" onClick={noop}>Schedule</Button></>:face==="recipients"?<><Button dense onClick={noop}>Cancel</Button><Button dense variant="primary" onClick={noop}>Save</Button></>:face==="knowledge"?<><Button dense onClick={noop}>Copy</Button><Button dense variant="primary" onClick={noop}>Edit</Button></>:face==="terminal"?<Button dense onClick={noop}>Back to session</Button>:<Button dense onClick={noop}>Refresh</Button>;return <RuntimeBusProvider><main className="desk-next canvas-desk"><DeskWindowFrame id="surface-refinement-canvas" title={titles[face]} label={titles[face]} minW={320} defaultW={660} defaultH={620} fitContent open entrance={false} onClose={noop} className="desk-surface-window"><div className="desk-surface-body canvas-body">{content}</div><div className="desk-surface-foot"><SurfaceFooter egress={face==="recipients"?<EgressChip label="api.sendgrid.com" scope="cloud"/>:undefined} receipt={face==="history"?<StateChip state="unreachable" label="History unavailable"/>:undefined} verbs={verbs}/></div></DeskWindowFrame></main></RuntimeBusProvider>}
createRoot(document.getElementById("root")!).render(<Canvas/>);
