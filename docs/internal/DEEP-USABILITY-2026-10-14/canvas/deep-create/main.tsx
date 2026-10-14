import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { StringGadget, PadGadget } from "@w/desk/surface/gadgets";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow } from "@w/desk/surface/Surface";

function Canvas() {
  const [face, setFace] = useState("Knowledge");
  const [failed, setFailed] = useState(false);
  const [recovery, setRecovery] = useState(false);
  const [name, setName] = useState("Architecture decision context");
  const [prompt, setPrompt] = useState("Find risks and name the accountable person:\n{input}");
  return <div className="desk-next create-canvas">
    <header className="create-canvas-bar"><strong>Create repair · Design canvas</strong><span>Synthetic content · production components</span></header>
    <nav aria-label="Artboards">{["Knowledge", "Workflow", "Prompt", "Agent"].map(label => <Button key={label} variant={face === label ? "primary" : "ghost"} onClick={() => setFace(label)}>{label}</Button>)}<Button variant="ghost" onClick={() => setFailed(!failed)}>Save failure</Button><Button variant="ghost" onClick={() => setRecovery(!recovery)}>Recovery</Button></nav>
    <main className="desk-window desk-window-shell create-canvas-window">
      <div className="create-canvas-title">{face === "Knowledge" ? name : face === "Agent" ? "Architecture reviewer" : "Review decision risks"}</div>
      <div className="create-canvas-body">
        {face === "Knowledge" ? <>
          <StringGadget label="Knowledge name" value={name} onChange={setName} />
          <SurfaceSection label="Items" count={2}><SurfaceLedger count={null} cols="room">
            <SurfaceLedgerRow primary="Rollback owner" meta="Note" trailing={<><Button dense variant="ghost">Open</Button><Button dense variant="ghost">Remove</Button></>} />
            <SurfaceLedgerRow primary="Migration review" meta="Note" trailing={<><Button dense variant="ghost">Open</Button><Button dense variant="ghost">Remove</Button></>} />
          </SurfaceLedger><div className="create-canvas-actions"><Button variant="ghost">Add items</Button></div></SurfaceSection>
          {recovery ? <SurfaceSection label="Recovered text"><p className="create-canvas-copy">Rollback owner: Jordan.</p><Button variant="primary">Save as Note</Button></SurfaceSection> : null}
        </> : face === "Workflow" ? <>
          <StringGadget label="Workflow name" value="Review decision risks" onChange={() => {}} />
          <SurfaceSection label="Steps"><div className="create-canvas-steps">
            <div className="create-canvas-step"><div className="create-canvas-step-head"><strong>Summarize</strong><Button dense variant="ghost" disabled>Move up</Button><Button dense variant="ghost">Remove</Button></div></div>
            <div className="create-canvas-step"><div className="create-canvas-step-head"><strong>AI prompt</strong><Button dense variant="ghost">Move up</Button><Button dense variant="ghost">Remove</Button></div><PadGadget label="Prompt" value={prompt} rows={3} onChange={setPrompt} /></div>
            <div className="create-canvas-step"><div className="create-canvas-step-head"><strong>Action items</strong><Button dense variant="ghost">Move up</Button><Button dense variant="ghost">Remove</Button></div></div>
          </div><div className="create-canvas-actions">{["Summarize", "Decisions", "Action items", "Rewrite", "Keep if", "AI prompt"].map(label => <Button key={label} dense variant="ghost">+ {label}</Button>)}</div></SurfaceSection>
        </> : face === "Prompt" ? <>
          <StringGadget label="Workflow name" value="Legacy prompt review" onChange={() => {}} />
          <PadGadget label="Prompt" value={prompt} onChange={setPrompt} rows={5} />
        </> : <>
          <StringGadget label="Name" value="Architecture reviewer" onChange={() => {}} />
          <StringGadget label="Role" value="Review decisions" onChange={() => {}} />
          <PadGadget label="Instructions" value="Identify unresolved risks and name the owner." onChange={() => {}} rows={4} />
          <Button variant="ghost">More</Button>
        </>}
      </div>
      <footer className="create-canvas-foot"><span role="status">{failed ? "Not saved · HTTP 503" : "Saved 4:27 PM"}</span><div className="create-canvas-actions">{failed ? <Button variant="ghost" onClick={() => setFailed(false)}>Retry</Button> : null}<Button variant="primary">Done</Button></div></footer>
    </main>
  </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
