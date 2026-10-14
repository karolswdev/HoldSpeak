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
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow } from "@w/desk/surface/Surface";

function Canvas() {
 const [face, setFace] = useState("prep");
 const [edit, setEdit] = useState(false);
 const [confirmed, setConfirmed] = useState(false);
 const [quote, setQuote] = useState(true);
 return <div className="desk-next canvas">
  <header className="canvas-bar"><strong>Daily journeys · Design canvas</strong><span>Synthetic content · production components</span></header>
  <nav aria-label="Artboards">{["prep", "outcomes", "note"].map(id => <Button key={id} variant={face === id ? "primary" : "ghost"} onClick={() => setFace(id)}>{id === "prep" ? "Prepare" : id === "outcomes" ? "Review" : "Develop"}</Button>)}</nav>
  <main className="desk-window desk-window-shell canvas-window">
   <div className="canvas-title">{face === "prep" ? "Mira · Prep" : face === "outcomes" ? "Ledger standup · Outcomes" : "Rollback plan · Ask"}</div>
   <div className="canvas-body">
    {face === "prep" ? <>
     <AppHead fact="Next 1:1"><StatusStrip items={[{text:"Thu 10:00"}, {text:"30 min"}]} /></AppHead>
     <SurfaceSection label="To raise" count={2}><SurfaceLedger count={null} cols="room"><SurfaceLedgerRow primary="Confirm rollback ownership" /><SurfaceLedgerRow primary="Review the migration checkpoint" /></SurfaceLedger></SurfaceSection>
     <div className="canvas-verbs"><Button variant="primary">Record meeting</Button><Button variant="ghost">Add to agenda</Button></div>
     <SurfaceSection label="They owe you" count={1}><SurfaceLedger count={null} cols="room"><SurfaceLedgerRow primary="Write the rollback runbook" meta="from Ledger standup · by Friday" trailing={<Button dense variant="ghost">Done</Button>} /></SurfaceLedger></SurfaceSection>
     <SurfaceSection label="Last time"><SurfaceLedger count={null} cols="room"><SurfaceLedgerRow primary="Ledger standup" meta="Tuesday" trailing={<Button dense variant="ghost">Open meeting</Button>} /></SurfaceLedger></SurfaceSection>
    </> : face === "outcomes" ? <>
     <AppHead fact={confirmed ? "Reviewed" : "1 to review"}><StatusStrip items={[{text:"Tue 14:00"}, {text:"30 min"}]} /></AppHead>
     <SurfaceSection label="Summary"><p className="canvas-copy">The team agreed to prepare the rollback runbook before the migration review.</p></SurfaceSection>
     <SurfaceSection label="Who owes what" count={1}><SurfaceLedger count={null} cols="room"><SurfaceLedgerRow primary="Write the rollback runbook" meta={confirmed ? "Mira · Fri · Confirmed" : "Mira · Fri"} trailing={<><Button dense variant={confirmed ? "ghost" : "primary"} onClick={() => setConfirmed(true)}>{confirmed ? "Done" : "Confirm"}</Button><Button dense variant="ghost" onClick={() => setEdit(!edit)}>More</Button></>} />{edit ? <div className="canvas-edit"><span>Who · Mira</span><span>When · Friday</span><Button dense variant="ghost">Show in transcript</Button></div> : null}</SurfaceLedger></SurfaceSection>
     {confirmed ? <div className="canvas-verbs"><Button variant="primary">Open follow-through</Button><Button variant="ghost">Open project</Button></div> : null}
    </> : <>
     <AppHead fact="Ask about your note" />
     {quote ? <SurfaceSection label="Selected text"><blockquote>Write the rollback runbook before Friday’s migration review.</blockquote><Button dense variant="ghost" onClick={() => setQuote(false)}>Remove</Button></SurfaceSection> : null}
     <div className="canvas-question">What is missing from this plan?</div>
     <StatusStrip items={[{text:"Reads Rollback plan"}, {text:"Selected engine"}]} />
     <div className="canvas-verbs"><Button variant="primary">Ask</Button><Button variant="ghost">Back to note</Button></div>
    </>}
   </div>
   <footer className="canvas-foot">{face === "prep" ? "Prepared just now" : face === "outcomes" ? confirmed ? "Action confirmed" : "Saved" : "Question kept"}</footer>
  </main>
 </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
