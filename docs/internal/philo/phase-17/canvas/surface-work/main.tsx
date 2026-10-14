import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { AppHead, StatusStrip } from "@w/desk/surface/kit";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow, SurfaceWell } from "@w/desk/surface/Surface";

function Canvas() {
 const [face, setFace] = useState(new URLSearchParams(location.search).get("face") || "meeting");
 const [send, setSend] = useState(false);
 const [notes, setNotes] = useState(false);
 const [coverage, setCoverage] = useState(false);
 return <div className="desk-next canvas">
  <header className="canvas-bar">Daily work · Synthetic content · Production components</header>
  <nav aria-label="Artboards">{["meeting", "week", "ask", "needs"].map(id => <Button key={id} variant={face === id ? "primary" : "ghost"} onClick={() => setFace(id)}>{id === "meeting" ? "Meeting" : id === "week" ? "The week" : id === "ask" ? "Ask AI" : "Needs you"}</Button>)}</nav>
  <main className="desk-window desk-window-shell canvas-window">
   <div className="canvas-title">{face === "meeting" ? "Ledger standup · Meetings" : face === "week" ? "The week" : face === "ask" ? "Ask AI" : "Needs you"}</div>
   <div className="canvas-body">
    {face === "meeting" ? <>
     <Button dense variant="ghost">Back</Button>
     <AppHead fact="Ready"><StatusStrip items={[{text:"Thu 10:00"}, {text:"30 min"}]} /></AppHead>
     <SurfaceSection label="Decisions" count={1}><SurfaceLedger count={null} cols="room"><SurfaceLedgerRow kind="DEC" primary="Freeze the ledger on Nov 12" meta="Not in the transcript" trailing={<><Button dense>Confirm</Button><Button dense variant="ghost">More</Button></>} /></SurfaceLedger></SurfaceSection>
     <SurfaceSection label="Summary"><p className="canvas-copy">We move the cutover to Friday. Mira will write the rollback runbook.</p></SurfaceSection>
     {send ? <SurfaceWell head="Send"><div className="canvas-verbs"><Button dense variant="ghost">Destination</Button><Button dense>Send</Button></div></SurfaceWell> : null}
    </> : face === "week" ? <>
     <AppHead fact="This week" />
     <SurfaceSection label="Meetings" count={2}><SurfaceLedger count={null} cols="room"><SurfaceLedgerRow kind="MTG" primary="Ledger standup" meta="Thu 10:00 · We move the cutover to Friday." trailing={<Button dense variant="ghost">Open</Button>} /><SurfaceLedgerRow kind="MTG" primary="Migration checkpoint" meta="Wed 14:00 · The canary passed. Rollback remains ready." trailing={<Button dense variant="ghost">Open</Button>} /></SurfaceLedger></SurfaceSection>
    </> : face === "ask" ? <>
     <div className="canvas-question">What changed in the rollback plan?</div>
     <div className="canvas-verbs"><Button dense variant="ghost">Mic</Button><Button dense>Ask</Button></div>
     <StatusStrip items={[{text:"No engine"}, {verb:<Button dense variant="ghost">Choose engine</Button>}]} />
     <div className="canvas-copy">With: Ledger rollback</div>
     <Button dense variant="ghost" aria-expanded={notes} onClick={() => setNotes(!notes)}>Add notes</Button>
     {notes ? <SurfaceWell head="Notes"><Button dense variant="ghost">Choose notes</Button></SurfaceWell> : null}
    </> : <>
     <AppHead fact="3 need you"><StatusStrip items={[{verb:<Button dense variant="ghost" aria-expanded={coverage} onClick={() => setCoverage(!coverage)}>8 of 8 available</Button>}]} /></AppHead>
     {coverage ? <SurfaceWell head="Coverage"><div className="canvas-copy">Calendar · Meetings · Projects · Agents</div></SurfaceWell> : null}
     <div className="canvas-verbs"><Button dense variant="primary">All</Button><Button dense variant="ghost">No due date</Button></div>
     <SurfaceSection label="Work" count={3}><SurfaceLedger count={null} cols="room"><SurfaceLedgerRow kind="DEC" primary="Freeze the ledger on Nov 12" meta="Ledger standup" trailing={<><Button dense>Confirm</Button><Button dense variant="ghost">More</Button></>} /><SurfaceLedgerRow kind="ACT" primary="Write the rollback runbook" meta="Mira · by Friday · Ledger standup" trailing={<Button dense variant="ghost">Open</Button>} /><SurfaceLedgerRow kind="ACT" primary="Review the migration checkpoint" meta="Me · by Tuesday" trailing={<Button dense variant="ghost">Open</Button>} /></SurfaceLedger></SurfaceSection>
    </>}
   </div>
   <footer className="canvas-foot"><span>{face === "needs" ? "Checked 09:14" : face === "ask" ? "Draft recovered" : ""}</span><div className="canvas-verbs">{face === "meeting" ? <><Button dense onClick={() => setSend(!send)}>Send</Button><Button dense variant="ghost">More</Button></> : null}</div></footer>
  </main>
 </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
