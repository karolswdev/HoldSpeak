// Direction specimens. Real library controls, local canvas state only.
import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/pullouts/thread-pullout.css";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection } from "@w/desk/surface/Surface";
import { DOCK_SPRITES } from "@w/desk/systemSprites";
import "./canvas.css";

const noop = () => {};
const face = new URLSearchParams(location.search).get("face") || "thread";
const titles: Record<string, string> = { thread: "Migration reply", rails: "Rails", phase: "Migration checkpoints" };

function Reply({ active = false, children }: { active?: boolean; children: string }) {
  const [speaking, setSpeaking] = useState(active);
  return <div className="canvas-reply">
    <span className="surface-token">ASSISTANT</span>
    <div className="canvas-reply-text">{children}</div>
    <div className="thread-row-actions">
      <Button dense variant="ghost" className={`thread-speaker-glyph${speaking ? " thread-speaker-glyph--active" : ""}`} aria-label={speaking ? "Stop speaking" : "Speak message"} title={speaking ? "Stop" : "Speak"} onClick={() => setSpeaking(!speaking)}>{speaking ? "■" : "▶"}</Button>
      <Button dense variant="ghost" onClick={noop}>Keep as note</Button>
      <Button dense variant="ghost" onClick={noop}>Keep as artifact</Button>
      <Button dense variant="ghost" onClick={noop}>Edit</Button>
    </div>
  </div>;
}
function Thread() {
  return <><Reply>Migration checkpoints are ready.</Reply><Reply active>Rollback steps are ready.</Reply></>;
}
function Rails({ onCollapse = noop }: { onCollapse?: () => void }) {
  const [picked, setPicked] = useState(false);
  return <div className="desk-mc canvas-rails">
    <div className="desk-mc-head"><span className="desk-mc-title"><span className="surface-token">WAITING 2</span><span className="surface-token">RUNS 4</span></span><Button dense variant="ghost" aria-label="Collapse" onClick={onCollapse}>▾</Button></div>
    <div className="desk-mc-repo-head"><span className="desk-mc-repo-name">architecture</span></div>
    <div className="desk-mc-project">
      <div className="desk-mc-phases"><span className="desk-mc-slug">migration</span><span className="desk-mc-phase current">12</span></div>
      <div className="desk-mc-belt">
        <span className={`desk-mc-story st-in-progress next${picked ? " picked" : ""}`}>
          <Button dense variant="ghost" className="desk-mc-story-pick" title="Migration checkpoints [in-progress] ·evidence" aria-pressed={picked} onClick={() => setPicked(!picked)}>ARC-12-01</Button>
          <Button dense variant="ghost" className="desk-mc-evidence-open" aria-label="Open evidence for ARC-12-01" title="open the evidence in place" onClick={noop}><span aria-hidden="true">✓</span></Button>
          <Button dense variant="ghost" className="desk-mc-pin awaiting" title="claude:checkpoints: watch live" onClick={noop}>⌁claude NEEDS YOU</Button>
        </span>
        <span className="desk-mc-story st-ready"><Button dense variant="ghost" className="desk-mc-story-pick" title="Rollback steps [ready]" onClick={noop}>ARC-12-02</Button><Button dense variant="ghost" className="desk-mc-pin stale" title="codex:rollback: watch live (stale)" onClick={noop}>⌁codex</Button></span>
        <span className="desk-mc-story st-ready"><Button dense variant="ghost" className="desk-mc-story-pick" title="Migration report [ready]" onClick={noop}>ARC-12-03</Button><Button dense variant="ghost" className="desk-mc-pin manual" title="claude:report: watch live; manually pinned" onClick={noop}>⌁claude</Button></span>
      </div>
    </div>
    <div className="desk-mc-sessions"><Button dense variant="ghost" className="desk-mc-needs" title="claude:review: Review requested" onClick={noop}>NEEDS YOU · claude · review</Button></div>
  </div>;
}
function DockPlate() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const publish = () => document.documentElement.style.setProperty("--desk-dock-h", `${Math.ceil(el.offsetHeight)}px`);
    publish();
    const observer = new ResizeObserver(publish);
    observer.observe(el);
    return () => { observer.disconnect(); document.documentElement.style.removeProperty("--desk-dock-h"); };
  }, []);
  return <div className="desk-dock" role="toolbar" aria-label="Dock" ref={ref}>
    {[["surface-dictation", "Speak"], ["surface-meetings", "Meetings"], ["surface-people", "People"], ["conductor", "Conductor"]].map(([id, name]) => <Button key={id} variant="chrome" className="desk-dock-launch" aria-label={name} onClick={noop}><img className="desk-dock-sprite" src={DOCK_SPRITES[id]} alt=""/><span className="desk-dock-label">{name}</span></Button>)}
  </div>;
}
function RailsScene() {
  const [open, setOpen] = useState(new URLSearchParams(location.search).get("state") !== "closed");
  return <main className="desk-next canvas-desk">{open ? <Rails onCollapse={() => setOpen(false)}/> : <Button className="desk-mc-tab" title="Rails panel" onClick={() => setOpen(true)}><span className="surface-token">RAILS</span><span className="surface-token">WAITING 2</span><span className="surface-token">RUNS 4</span></Button>}<DockPlate/></main>;
}
function Phase() {
  return <><div className="desk-dlv-facts-line"><span className="surface-token">OPEN</span><span className="surface-token">1/3</span></div><SurfaceSection label="Stories"><ul className="desk-dlv-phase-stories">
    <li><Button dense variant="ghost" className="desk-dlv-story-open" onClick={noop}>ARC-12-01 · Migration checkpoints</Button><small>2 pass · 1 fail</small></li>
    <li><Button dense variant="ghost" className="desk-dlv-story-open" onClick={noop}>ARC-12-02 · Rollback steps</Button><small>3 pass</small></li>
    <li><span className="desk-dlv-story-unavail">ARC-12-03 · unavailable</span></li>
  </ul></SurfaceSection></>;
}
function Canvas() {
  if (face === "rails") return <RailsScene/>;
  return <main className="desk-next canvas-desk"><DeskWindowFrame id="cohesive-actions-canvas" title={titles[face]} label={titles[face]} minW={320} defaultW={720} defaultH={540} fitContent open entrance={false} dockChip="minimized" onClose={noop} className="desk-surface-window"><div className="desk-surface-body canvas-body">{face === "rails" ? <Rails/> : face === "phase" ? <Phase/> : <Thread/>}</div></DeskWindowFrame></main>;
}
createRoot(document.getElementById("root")!).render(<Canvas/>);
