import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { AppHead } from "@w/desk/surface/kit";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow } from "@w/desk/surface/Surface";

function Canvas() {
  const [searched, setSearched] = useState(false);
  const [used, setUsed] = useState(false);
  return <div className="desk-next canvas">
    <header className="canvas-bar">Direction canvas · synthetic content · production components</header>
    <main className="desk-window desk-window-shell canvas-window">
      <div className="canvas-title">Engines</div>
      <div className="canvas-body">
        <AppHead fact="Choose what runs your work" />
        <SurfaceSection label="Available"><SurfaceLedger cols="room">
          <SurfaceLedgerRow primary="Qwen 3.5 4B" meta="THIS DEVICE · 2.7 GB" trailing={<Button dense variant="secondary">Download</Button>} wrap />
        </SurfaceLedger></SurfaceSection>
        {searched ? <SurfaceSection label={used ? "Available" : "Found"} count={1}><SurfaceLedger cols="room">
          <SurfaceLedgerRow primary="Qwen 3.8 27B" meta="LAN · 192.0.2.20:8080" trailing={<Button dense variant="secondary" disabled={used} onClick={() => setUsed(true)}>{used ? "Added" : "Use it"}</Button>} wrap />
        </SurfaceLedger></SurfaceSection> : null}
        <div className="canvas-verbs"><Button variant="secondary" onClick={() => setSearched(true)}>Find on LAN</Button><Button variant="ghost">Add an engine</Button></div>
      </div>
      <footer className="canvas-foot">{used ? "ADDED" : searched ? "FOUND 1 SERVER" : "READY"}</footer>
    </main>
  </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
