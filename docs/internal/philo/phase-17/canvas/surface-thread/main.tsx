import { createRoot } from "react-dom/client";
import { useState } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceState } from "@w/desk/surface/Surface";
import { StringGadget } from "@w/desk/surface/gadgets";
import "./main.css";

function Canvas() {
 const [sequence, setSequence] = useState(new URLSearchParams(location.search).get("face") === "sequence");
 const [rename, setRename] = useState(false);
 const [title, setTitle] = useState("Architecture review");
 const [mode, setMode] = useState("");
 return <div className="desk-next canvas">
  <header className="canvas-bar">Thread · Synthetic content · Production components</header>
  <nav><Button onClick={() => setSequence(false)}>Thread</Button><Button onClick={() => setSequence(true)}>Sequence</Button></nav>
  <main className="desk-window desk-window-shell canvas-window">
   <div className="canvas-title">{sequence ? "Morning review · Sequence" : `${title} · Thread`}</div>
   <div className="canvas-body">
    {sequence ? <><h3>Steps</h3><SurfaceState empty emptyLabel="No steps" emptyGlyph="○" /></> : <>
     <div className="canvas-tools"><Button dense variant="ghost" onClick={() => setRename(!rename)}>Rename</Button><Button dense variant="ghost">Call</Button></div>
     {rename ? <StringGadget value={title} label="Thread title" onChange={setTitle} /> : null}
     <SurfaceState empty emptyLabel="No turns" emptyGlyph="▬" />
    </>}
   </div>
   <footer className="canvas-foot">{sequence ? <Button dense variant="ghost">Dictate about this</Button> : <>
    <div className="canvas-modes" role="tablist" aria-label="Thread modes">{["Desk", "Interview", "Chase", "Draft", "Plan"].map((name, index) => <Button key={name} variant="chrome" role="tab" aria-selected={mode === name} tabIndex={index === 0 ? 0 : -1} className={`canvas-mode${mode === name ? " is-active" : ""}`} onClick={() => setMode(mode === name ? "" : name)}>{name}</Button>)}</div>
    <StringGadget label="Message" value="" onChange={() => {}} placeholder="Message" />
    <div className="canvas-tools"><Button dense variant="primary" disabled>Send</Button></div>
   </>}</footer>
  </main>
 </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
