import { useState, type CSSProperties } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/screen/screen.css";
import { Button } from "@w/components/signal/Signal";
import { DeskIcon } from "@w/desk/surface/objects/DeskIcon";
import { SurfaceFooter } from "@w/desk/surface/SurfaceFooter";
import { SurfaceWell } from "@w/desk/surface/Surface";
import { GadgetGlyph } from "@w/desk/components/window/GadgetGlyph";
import { DOCK_SPRITES } from "@w/desk/systemSprites";
import { objectSprite } from "@w/desk/surface/objects/kinds";
import "./canvas.css";

const params = new URLSearchParams(location.search);
const proposed = params.get("density") !== "current";
const showArtifact = params.get("view") !== "icons";
const stretched = params.get("pose") === "stretched";
const compact = matchMedia("(max-width: 720px)").matches;
const sample = [
  { id: "drawer:people", kind: "person", name: "People", x: 20, row: 0, caption: "1:1 14:30" },
  { id: "drawer:projects", kind: "project", name: "Projects", x: 20, row: 1 },
  { id: "drawer:conductor", kind: "conductor", name: "Conductor", x: 20, row: 2 },
  { id: "drawer:archive", kind: "artifact", name: "Archive", x: 20, row: 3 },
  { id: "artifact:platform-options", kind: "artifact", name: "Platform migration options", x: 210, row: 0 },
  { id: "meeting:platform-review", kind: "meeting", name: "Platform architecture review", x: 330, row: 0 },
  { id: "note:compatibility", kind: "note", name: "API compatibility checks", x: 210, row: 1 },
  { id: "task:rollout", kind: "action", name: "Confirm service rollout owner", x: 330, row: 1 },
];

function DockSpecimen() {
  const apps = compact
    ? [{ id: "intelligence:desk", label: "Today" }, { id: "chair:capture", label: "Capture" }, { id: "surface-meetings", label: "Meetings" }, { id: "surface-people", label: "People" }]
    : [{ id: "intelligence:desk", label: "Today" }, { id: "surface-dictation", label: "Speak" }, { id: "surface-meetings", label: "Meetings" }];
  return <div className="desk-dock" role="toolbar" aria-label="Dock specimen">
    {apps.map((app) => <Button key={app.id} variant="chrome" className={`desk-dock-launch desk-dock-app${app.label === "Today" ? " is-run is-front" : ""}`} data-app={app.id} aria-label={app.label}>
      {DOCK_SPRITES[app.id] ? <img src={DOCK_SPRITES[app.id]} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false}/> : <span aria-hidden="true">●</span>}
      <span className="desk-dock-label">{app.label}</span>
    </Button>)}
  </div>;
}

function ArtifactSpecimen() {
  const [receipt, setReceipt] = useState(false);
  return <section className={`desk-window desk-window-shell desk-pullout is-card density-artifact${compact ? " is-sheet" : ""}`} data-plane="front" data-pose={stretched ? "stretched" : "short"} aria-label="Artifact specimen">
    <header className="desk-pullout-head"><span className="desk-gadgets desk-gadgets-left"><Button variant="chrome" className="desk-gadget desk-gadget-close" aria-label="Close specimen">{compact ? "‹ Back" : <GadgetGlyph kind="close"/>}</Button></span><span className="desk-window-icon"><img src={objectSprite("artifact", "artifact:platform-options")} alt=""/></span><span className="desk-pullout-title">Platform migration options</span><span className="density-title-space"/><span className="desk-gadgets desk-gadgets-right">{!compact ? <><Button variant="chrome" className="desk-gadget desk-gadget-iconify" aria-label="Iconify specimen"><GadgetGlyph kind="iconify"/></Button><Button variant="chrome" className="desk-gadget desk-gadget-zoom" aria-label="Zoom specimen"><GadgetGlyph kind="zoom"/></Button></> : null}<Button variant="chrome" className="desk-gadget desk-gadget-depth" aria-label="Depth specimen"><GadgetGlyph kind="depth"/></Button></span></header>
    <div className="desk-pullout-body desk-surface-body">
      <section><h3>Brief</h3><SurfaceWell><div className="density-material"><h2>Platform migration options</h2><p>Release each service with API compatibility checks. Keep the current API available through the transition.</p><h3>Next work</h3><ul><li>Compare the service rollout options.</li><li>Confirm compatibility test coverage.</li><li>Send the options to Priya Narayanan.</li></ul><h3>Review points</h3><p>Choose the first service and confirm the rollout owner at the architecture review.</p><ul><li>Keep rollback available for each service.</li><li>Attach compatibility results to the review.</li></ul></div></SurfaceWell></section>
      <section><h3>Lineage</h3><Button dense variant="ghost">Platform architecture review</Button></section>
    </div>
    <SurfaceFooter receipt={receipt ? <span className="surface-footer-receipt-line">Copied · sample</span> : undefined} verbs={<><Button dense variant="ghost" onClick={() => setReceipt(true)}>Copy</Button><Button dense variant="ghost" onClick={() => setReceipt(false)}>Dictate about this</Button></>}/>
    <span className="desk-window-edge desk-window-edge-b" aria-hidden="true"/>
    <span className="desk-window-grip desk-gadget-size" aria-hidden="true"><GadgetGlyph kind="size"/></span>
  </section>;
}

function Canvas() {
  const [selected, setSelected] = useState("artifact:platform-options");
  const row = 96;
  const looseRow = 100;
  return <main className={`desk-next density-ground ${proposed ? "density-proposed" : "density-current"}`} style={{ "--desk-dock-h": `${compact ? 56 : 60}px` } as CSSProperties}>
    <header className="density-screenbar"><strong>HoldSpeak</strong><span>Desk</span><span className="density-clock">Fri 14:04</span></header>
    <div className="desk-screen" data-layout={compact ? "grid" : "free"}><div className="desk-icon-grid">
      {sample.map((item) => <div key={item.id} className={`desk-screen-cell${compact ? "" : " desk-screen-placed"}`} style={compact ? undefined : { left: item.x, top: 12 + item.row * (item.x === 20 ? row : looseRow) + (item.x === 20 && item.row > 0 ? 24 : 0) }}>
        <DeskIcon id={item.id} kind={item.kind} name={item.name} selected={selected === item.id} caption={item.caption} badge={item.id === "drawer:conductor" ? objectSprite("agent", "sample-agent") : undefined} onSelect={() => setSelected(item.id)} count={item.id === "drawer:conductor" ? 2 : undefined}/>
      </div>)}
    </div></div>
    {showArtifact ? <ArtifactSpecimen/> : null}
    <DockSpecimen/>
  </main>;
}
createRoot(document.getElementById("root")!).render(<Canvas/>);
