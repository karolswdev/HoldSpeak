import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection, SurfaceState, SurfaceLedger, SurfaceLedgerRow } from "@w/desk/surface/Surface";
import { GadgetGroup, GadgetRow, StringGadget, CycleGadget } from "@w/desk/surface/gadgets";

function Canvas() {
  const [face, setFace] = useState(new URLSearchParams(location.search).get("face") || "commands");
  return <div className="desk-next canvas">
    <header className="canvas-bar">Action feedback · Synthetic content · Production components</header>
    <nav aria-label="Artboards">{["commands", "rhythm", "workbenches", "picker"].map(id => <Button key={id} variant={face === id ? "primary" : "ghost"} onClick={() => setFace(id)}>{id}</Button>)}</nav>
    <main className="desk-window desk-window-shell canvas-window">
      <div className="canvas-title">{face}</div>
      <div className="canvas-body">
        {face === "commands" ? <>
          <SurfaceState error="Command not saved · Settings unavailable" />
          <SurfaceSection label="New command"><GadgetGroup>
            <GadgetRow label="Spoken keyword"><StringGadget label="Spoken keyword" value="open ledger" onChange={() => {}} /></GadgetRow>
            <GadgetRow label="Command behavior"><CycleGadget label="Command behavior" value="open_url" options={[{value:"open_url",label:"Open URL"}]} onChange={() => {}} /></GadgetRow>
            <GadgetRow label="Payload"><StringGadget label="Payload" value="https://ledger.example" onChange={() => {}} /></GadgetRow>
          </GadgetGroup><Button dense variant="primary">Save command</Button></SurfaceSection>
        </> : face === "rhythm" ? <>
          <span className="surface-display">Every 15 min</span>
          <SurfaceState error="Settings not saved · Settings unavailable" />
          <SurfaceLedger count={null} cols="hub"><SurfaceLedgerRow primary="Sweep" cells={<CycleGadget label="Sweep interval" value="15" options={[{value:"15",label:"EVERY 15 MIN"}]} onChange={() => {}} />} trailing={<Button dense variant="ghost">Run now</Button>} /><SurfaceLedgerRow primary="Daily brief" trailing={<Button dense variant="ghost">Generate</Button>} /><SurfaceLedgerRow primary="Notify" cells={<CycleGadget label="Notification mode" value="edge" options={[{value:"edge",label:"ON THE EDGE"}]} onChange={() => {}} />} /></SurfaceLedger>
        </> : face === "workbenches" ? <SurfaceState error="Workbenches not loaded · Hub unavailable" onRetry={() => {}} /> : <>
          <SurfaceState error="Daily Brief created · Desk not refreshed · Hub unavailable" onRetry={() => {}} />
          <SurfaceSection label="Start from a template"><Button variant="chrome" className="canvas-choice" aria-pressed="true" disabled>Daily Brief · Selected</Button><Button dense variant="ghost">Open workbench</Button></SurfaceSection>
        </>}
      </div>
      <footer className="canvas-foot">{face === "rhythm" ? "Not saved" : ""}</footer>
    </main>
  </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
