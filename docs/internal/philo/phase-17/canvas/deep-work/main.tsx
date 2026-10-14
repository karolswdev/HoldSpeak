import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow, SurfaceRows, SurfaceRow, SurfaceWell } from "@w/desk/surface/Surface";
import { StringGadget, PadGadget, CycleGadget } from "@w/desk/surface/gadgets";
import { Disclosure } from "@w/desk/surface/patterns/Disclosure";
import { Material } from "@w/desk/surface/Material";

function Canvas() {
 const initial = new URLSearchParams(location.search).get("pose") || "context";
 const [pose, setPose] = useState(initial);
 const [add, setAdd] = useState(initial === "add-note");
 const [topic, setTopic] = useState("Release feedback");
 const [body, setBody] = useState("Priya can lead the release after the rollback review.");
 const [visibility, setVisibility] = useState("leader_private");
 const [text, setText] = useState("Write the release rollback runbook");
 const [owner, setOwner] = useState("Jordan");
 const [due, setDue] = useState("2026-10-22");
 return <div className="desk-next deep-work">
  <header className="canvas-bar"><strong>Work · Component canvas</strong><span>Synthetic content · production components</span></header>
  <nav className="canvas-nav" aria-label="Artboards">{["context","add-note","room-refused"].map(id => <Button key={id} variant={pose === id ? "primary" : "ghost"} onClick={() => { setPose(id); setAdd(id === "add-note"); }}>{id === "context" ? "Read context" : id === "add-note" ? "Add note" : "Refused correction"}</Button>)}</nav>
  <main className="desk-window desk-window-shell canvas-window">
   <div className="canvas-title">{pose === "room-refused" ? "Payments Platform Rewrite · Room" : "Priya Nair · Context"}</div>
   <div className="canvas-body">
    {pose !== "room-refused" ? <>
     <SurfaceSection label="Notes" actions={!add ? <Button dense onClick={() => setAdd(true)}>Add note</Button> : undefined}>
      <SurfaceLedger cols="room"><SurfaceLedgerRow wrap primary={<div className="canvas-note"><strong>Career plan</strong><Material>Lead the ledger cutover next month. Review the rollback plan with the service owners before the release.</Material></div>} cells={<span className="surface-token">Private</span>} /></SurfaceLedger>
      {add ? <SurfaceWell head="Add note"><div className="canvas-fields"><StringGadget label="Topic" value={topic} onChange={setTopic} placeholder="Topic (optional)" /><PadGadget label="Note" value={body} onChange={setBody} rows={3} /><CycleGadget label="Visibility" value={visibility} onChange={setVisibility} options={[{value:"leader_private",label:"Leader private"},{value:"shared_intent",label:"Shared"}]} /><div className="canvas-verbs"><Button dense variant="ghost" onClick={() => setAdd(false)}>Close</Button><Button dense variant="primary">Add note</Button></div></div></SurfaceWell> : null}
     </SurfaceSection>
     <SurfaceSection label="Projects"><SurfaceRows><SurfaceRow title="Payments Platform Rewrite" onOpen={() => {}} detail="Ledger cutover" /></SurfaceRows></SurfaceSection>
     <Disclosure label="Links"><div className="canvas-links"><SurfaceSection label="Projects"><Button dense>Link project</Button></SurfaceSection><SurfaceSection label="Calendar series"><Button dense>Link calendar event</Button></SurfaceSection><SurfaceSection label="Names in meeting notes"><StringGadget label="Name in meeting notes" value="" onChange={() => {}} /><Button dense>Add</Button></SurfaceSection></div></Disclosure>
    </> : <SurfaceSection label="Open here"><SurfaceLedger cols="room"><SurfaceLedgerRow primary="Write the rollback runbook" wrap open onToggle={() => {}}><SurfaceWell head="Edit action"><div className="canvas-fields"><StringGadget label="Text" value={text} onChange={setText} /><StringGadget label="Owner" value={owner} onChange={setOwner} /><StringGadget label="Due" value={due} onChange={setDue} /><div className="canvas-failure" role="alert"><span>Not saved · Project changed</span></div><div className="canvas-verbs"><Button dense variant="ghost">Cancel</Button><Button dense variant="primary">Try again</Button></div></div></SurfaceWell></SurfaceLedgerRow></SurfaceLedger></SurfaceSection>}
   </div>
   <footer className="canvas-foot">{pose === "room-refused" ? "Correction kept" : add ? "Draft kept" : "Encrypted"}</footer>
  </main>
 </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
