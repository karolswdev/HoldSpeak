import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { FoldGadget, StateChip, EgressChip, SurfaceSection, SurfaceLedger, SurfaceLedgerRow } from "@w/desk/surface";

function Canvas() {
 return <main className="desk-next canvas">
  <div className="canvas-note">Direction canvas · synthetic content · production components</div>
  <section className="desk-window desk-window-shell canvas-window" aria-label="Get ready">
   <header className="canvas-title">Get ready <Button variant="ghost" dense>Continue later</Button></header>
   <div className="canvas-body">
    <SurfaceSection label="Speech"><div className="canvas-controls"><EgressChip label="HUGGINGFACE.CO" scope="cloud" /><Button variant="primary">Set up speech · 144 MB</Button></div></SurfaceSection>
    <SurfaceSection label="First words"><StateChip state="idle" label="WAITS FOR SPEECH" /><Button variant="secondary" disabled>Dictate one sentence</Button></SurfaceSection>
    <FoldGadget title="Chat engines"><div className="canvas-controls"><Button variant="secondary">Use a server</Button><Button variant="secondary">Set up local AI · 3.0 GB</Button></div></FoldGadget>
    <FoldGadget title="Optional setup"><SurfaceSection label="You · Calendar · Accounts · Agents" /></FoldGadget>
   </div>
  </section>
  <section className="desk-window desk-window-shell canvas-window" aria-label="Engines">
   <header className="canvas-title">Engines</header><div className="canvas-body">
    <h2 className="surface-display">No engine yet</h2>
    <div className="canvas-controls"><Button variant="primary">Find on LAN</Button><Button variant="ghost">Add an engine</Button></div>
    <SurfaceSection label="Found"><SurfaceLedger cols="room"><SurfaceLedgerRow primary="Qwen · server" meta="LAN · 192.0.2.20:8080" trailing={<Button dense>Use it</Button>} wrap /></SurfaceLedger></SurfaceSection>
    <FoldGadget title="Download a local model"><SurfaceSection label="Local models" /></FoldGadget>
   </div>
  </section>
  <section className="desk-window desk-window-shell canvas-window" aria-label="Readiness">
   <header className="canvas-title">Readiness <Button variant="secondary" dense>Get ready</Button></header><div className="canvas-body">
    <SurfaceSection label="Needs you"><SurfaceLedger cols="room"><SurfaceLedgerRow primary="Model missing" trailing={<Button dense>Choose engine</Button>} wrap /></SurfaceLedger></SurfaceSection>
    <FoldGadget title="Ready"><SurfaceSection label="Microphone" /></FoldGadget><FoldGadget title="RAW · READINESS"><code>/models/model.gguf</code></FoldGadget>
   </div>
  </section>
 </main>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
