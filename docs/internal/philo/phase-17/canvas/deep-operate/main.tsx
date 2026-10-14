import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow, SurfaceWell } from "@w/desk/surface/Surface";
import { StringGadget, CycleGadget } from "@w/desk/surface/gadgets";
import { MicButton } from "@w/desk/components/MicButton";

function Canvas() {
 const initial = new URLSearchParams(location.search).get("pose") || "empty";
 const [pose, setPose] = useState(initial);
 const [instruction, setInstruction] = useState(initial === "empty" ? "" : "Review release ownership with the team");
 const [priority, setPriority] = useState(2);
 const [config, setConfig] = useState(false);
 return <div className="desk-next deep-operate">
  <header className="canvas-bar"><strong>Operate · Component canvas</strong><span>Synthetic content · production components</span></header>
  <nav className="canvas-nav" aria-label="Artboards">{["empty", "draft", "refused", "schedule"].map(id => <Button key={id} variant={pose === id ? "primary" : "ghost"} onClick={() => { setPose(id); setInstruction(id === "empty" ? "" : "Review release ownership with the team"); }}>{id === "empty" ? "New workbench" : id === "draft" ? "Return to draft" : id === "refused" ? "Refused Add" : "Recurring draft"}</Button>)}</nav>
  <main className="desk-window desk-window-shell canvas-window">
   <div className="canvas-title">{pose === "schedule" ? "Schedule recording" : "Release review"}</div>
   {pose === "schedule" ? <div className="canvas-body canvas-fields">
    <SurfaceSection label="Recording"><StringGadget label="Title" value="Release owner check" onChange={() => {}} /><CycleGadget label="Mode" value="recurring" onChange={() => {}} options={[{value:"one-shot",label:"Once"},{value:"recurring",label:"Recurring"}]} /><StringGadget label="Cron expression" value="30 14 * * 2" onChange={() => {}} /><CycleGadget label="Duration" value="90" onChange={() => {}} options={[{value:"60",label:"60 min"},{value:"90",label:"90 min"}]} /></SurfaceSection>
    <div className="canvas-actions"><Button dense variant="ghost">Back</Button><Button dense variant="primary">Schedule</Button></div>
   </div> : <>
    <div className="canvas-wings"><Button variant="chrome">Items</Button><Button variant="chrome">Runs</Button><Button variant="chrome">Memory</Button></div>
    <div className="canvas-body">
     <div className="canvas-setup"><span>No agent · Manual</span><Button dense variant="ghost" onClick={() => setConfig(!config)}>{config ? "Close setup" : "Choose agent"}</Button></div>
     {config ? <SurfaceWell head="Agent"><StringGadget label="Search agents" value="" onChange={() => {}} /><Button dense>Choose Desk</Button></SurfaceWell> : <>
      <SurfaceSection label="Add item"><div className="canvas-inlet"><MicButton label="Speak instruction" onText={setInstruction} /><input type="text" role="combobox" aria-label="New item instruction" aria-expanded="false" placeholder="What needs doing?" value={instruction} onChange={event => setInstruction(event.target.value)} /><Button dense variant="ghost" onClick={() => setPriority(priority === 3 ? 1 : priority + 1)}>P{priority}</Button><Button dense variant="primary" disabled={!instruction.trim()}>Add</Button></div></SurfaceSection>
      {pose === "empty" ? <div className="canvas-empty">No items yet</div> : <SurfaceLedger count="Items"><SurfaceLedgerRow wrap primary="Check the rollback owner before Friday" cells={<span className="surface-token">Pending</span>} /></SurfaceLedger>}
      {pose === "refused" ? <div className="canvas-refusal" role="alert"><span>Add failed · Hub unavailable</span><Button dense variant="ghost">Try again</Button></div> : null}
     </>}
    </div>
   </>}
   <footer className="canvas-foot">{pose === "refused" ? "Draft kept" : pose === "draft" || pose === "schedule" ? "Draft kept" : ""}<span>No engine</span><Button dense variant="ghost">Choose an engine</Button></footer>
  </main>
 </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
