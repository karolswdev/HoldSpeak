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
import { AskWell, FoldGadget, SurfaceFooter, TimelineRail } from "@w/desk/surface";
import { SurfaceFacts, SurfaceSection } from "@w/desk/surface/Surface";

function Canvas() {
 const [pose, setPose] = useState("working");
 const [answer, setAnswer] = useState("");
 const [terminal, setTerminal] = useState(false);
 return <div className="desk-next canvas">
  <header className="canvas-bar"><strong>Sessions · Design canvas</strong><span>Synthetic content · production components · owner-approved repair</span></header>
  <nav aria-label="Artboards">{["working", "asking", "launched"].map(id => <Button key={id} variant={pose === id ? "primary" : "ghost"} onClick={() => setPose(id)}>{id}</Button>)}</nav>
  <main className="desk-window desk-window-shell canvas-window">
   <div className="canvas-title">{pose === "launched" ? "Write the rollback runbook" : "payments-ledger"}</div>
   <div className="canvas-body">
    <AppHead fact={pose === "working" ? "Working" : "Needs your answer"}><StatusStrip items={[{text:pose === "launched" ? "Claude Code" : "Codex"}, {text:"10:42"}]} /></AppHead>
    {pose !== "working" ? <AskWell agent={pose === "launched" ? "Claude Code" : "Codex"} question="Who owns the rollback: Jordan or Avery?" value={answer} onChange={setAnswer} onAnswer={() => setAnswer("")} /> : null}
    <SurfaceSection label="Latest report"><p>Added the rollback checkpoint. Checking the migration tests.</p></SurfaceSection>
    {pose === "launched" ? <TimelineRail label="Activity" entries={[{id:"read",time:"10:39",word:"READ",code:"ledger/cutover.py"},{id:"write",time:"10:41",word:"WRITE",code:"docs/runbooks/ledger-rollback.md"}]} /> : null}
    {terminal ? <SurfaceSection label="Terminal"><p role="status">Terminal unavailable · No pane on this session</p><Button dense variant="ghost">Retry</Button><Button dense variant="ghost" onClick={() => setTerminal(false)}>Back to session</Button></SurfaceSection> : null}
    <FoldGadget title="Details"><SurfaceFacts value={{session:"codex:cx-ledger",node:"this Mac",folder:"payments-ledger"}} /><Button dense variant="ghost">Keep as note</Button><Button dense variant="ghost">Pin to story</Button>{pose === "launched" ? <Button dense variant="danger">Stop</Button> : null}</FoldGadget>
   </div>
   <SurfaceFooter receipt="Last report · 10:42" verbs={<Button variant="ghost" onClick={() => setTerminal(!terminal)}>{terminal ? "Back to session" : "Open terminal"}</Button>} />
  </main>
 </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
