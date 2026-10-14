import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow, SurfaceStream, SurfaceStreamDay, SurfaceStreamEntry } from "@w/desk/surface/Surface";
import { FilterTokens } from "@w/desk/surface/FilterTokens";
import { StringGadget } from "@w/desk/surface/gadgets";

function Canvas() {
  const [face, setFace] = useState(new URLSearchParams(location.search).get("face") || "memory");
  const [well, setWell] = useState(false);
  return <div className="desk-next canvas">
    <header className="canvas-bar">Memory and History · Synthetic content · Production components</header>
    <nav aria-label="Artboards">{["memory", "history"].map(id => <Button key={id} variant={face === id ? "primary" : "ghost"} onClick={() => setFace(id)}>{id}</Button>)}</nav>
    <main className="desk-window desk-window-shell canvas-window">
      <div className="canvas-title">{face === "memory" ? "Memory" : "Ledger cutover · History"}</div>
      <div className="canvas-body">
        {face === "memory" ? <>
          <span className="surface-display">Recent work</span>
          <StringGadget label="Search the Desk" value="" onChange={() => {}} />
          <FilterTokens label="Filter the memory" options={["All", "Decisions", "Commitments", "Briefs", "Meetings"].map(label => ({value:label,label}))} value="All" onChange={() => {}} />
          <SurfaceSection label="Owed" count={2}><SurfaceLedger>
            <SurfaceLedgerRow lead="Action" wrap primary="Write the rollback runbook" meta={<span className="canvas-memory-meta">Jordan · No date</span>} trailing={<span className="canvas-memory-verbs"><Button dense variant="ghost">From Ledger cutover sync</Button><Button dense variant="ghost" onClick={() => setWell(!well)}>Set a date</Button></span>} open={well}>
              <StringGadget label="Due" type="date" value="" onChange={() => {}} /><Button dense variant="secondary">Save</Button>
            </SurfaceLedgerRow>
            <SurfaceLedgerRow lead="Action" wrap primary="Write the rollback runbook" meta="Priya · Due Oct 16" trailing={<span className="canvas-memory-verbs"><Button dense variant="ghost">From Platform review</Button><Button dense variant="ghost">Done</Button></span>} />
          </SurfaceLedger></SurfaceSection>
        </> : <SurfaceStream count="2 today" controls={<StringGadget label="Search history" value="Production cutover" onChange={() => {}} />}>
          <SurfaceStreamDay label="Today"><SurfaceStreamEntry when="09:20" dense verbs={<Button dense variant="ghost">Open</Button>}>Added milestone · Production cutover</SurfaceStreamEntry><SurfaceStreamEntry when="09:15" dense verbs={<Button dense variant="ghost">Open</Button>}>Added risk · Replica lag during cutover</SurfaceStreamEntry></SurfaceStreamDay>
        </SurfaceStream>}
      </div>
    </main>
  </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
