import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/surface/surface.css";
import "@w/desk/pullouts/intelligence.css";
import "@w/desk/pullouts/views/today.css";
import "@w/features/project-room/recall/recall.css";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow, SurfaceRows, SurfaceRow } from "@w/desk/surface/Surface";
import { StandingPage, RefTokens } from "@w/desk/surface/patterns/StandingPage";
import { StateChip } from "@w/desk/surface/patterns/StateChip";
import { Material } from "@w/desk/surface/Material";
import { Steps } from "@w/desk/surface/kit";
import { Button } from "@w/components/signal/Signal";
import "./canvas.css";

const noop = () => {};
const refs = [{ ref: "action_item:weekly-summary", token: "Weekly summary", opens: true }];
const meetingRef = [{ ref: "meeting:platform-review", token: "Platform architecture review · Oct 15", opens: true }];

function Brief() {
  return <div className="canvas-brief">
    <div className="intelligence-brief-period">Oct 12–18</div>
    <div className="intelligence-brief-generated">GENERATED OCT 16 09:12</div>
    <StandingPage title="What I owe" built="BUILT 09:12" onOpenRef={noop} sentences={[
      { text: "Summarize what happened this week.", refs },
      { text: "Send the platform migration options to Priya Narayanan before the architecture review.", refs: meetingRef },
    ]} />
    <SurfaceSection label="What changed this week">
      <SurfaceRows>
        <SurfaceRow title="Review open PRs" detail="PR context missing" meta={<span className="canvas-facts"><span className="surface-token">Workbench output · Oct 15</span><StateChip state="warning" label="Awaiting review" /></span>} onOpen={noop} />
        <SurfaceRow title="Platform migration: staged delivery approved" detail="Ania Kowalska owns the API compatibility plan." meta={<span className="canvas-facts"><span className="surface-token">Decision · Oct 15</span><span>Platform architecture review · Oct 15</span></span>} onOpen={noop} />
      </SurfaceRows>
    </SurfaceSection>
    <SurfaceSection label="This week"><SurfaceRows><SurfaceRow title="3 meetings" meta="NEXT · FRI 10:00" /><SurfaceRow title="2 due" detail="Platform migration options · Friday" /></SurfaceRows></SurfaceSection>
    <SurfaceSection label="People"><SurfaceRows><SurfaceRow title="Priya Narayanan" detail="You owe 1 · They owe 2 · Next: Architecture review" onOpen={noop} /></SurfaceRows></SurfaceSection>
    <div className="intelligence-brief-blocker"><span>Send this brief</span><Button dense variant="secondary">Send</Button></div>
  </div>;
}

function Day() {
  return <div className="today">
    <div className="today-head"><h2 className="today-day">Friday</h2><span className="today-strip">2 meetings ahead · 1 to finish</span><span className="today-head-sp"/><Button dense variant="secondary">Record now</Button></div>
    <div className="today-grid"><ol className="today-spine" aria-label="Today">
      <li className="today-now"><span className="today-time today-now-time">09:10</span><span className="today-bead"/><span className="today-now-line"/></li>
      <li className="today-node" data-kind="next"><span className="today-time">10:00</span><span className="today-bead"/><div className="today-node-body"><div className="today-next">
        <div className="today-next-bar"><span className="today-next-label">NEXT</span><span className="today-next-in">in 50 min</span></div>
        <div className="today-next-body"><div className="today-next-text"><span className="today-next-title">Platform architecture review with Priya Narayanan</span><span className="today-row-meta">Platform migration · 10:00–10:45</span></div></div>
        <Steps label="Meeting steps" steps={["Prep", "Record", "Summary", "Send follow-up"].map((label, index) => ({key: label, label, state: index === 0 ? "now" : "later"}))}/>
        <div className="today-next-verbs"><Button dense variant="secondary">Open prep</Button><Button dense>Record when it starts</Button></div>
      </div></div></li>
      <li className="today-node" data-kind="later"><span className="today-time">14:30</span><span className="today-bead"/><div className="today-node-body today-row"><div className="today-row-text"><Button variant="chrome" className="today-row-title">Delivery risks and dependency review</Button><span className="today-row-meta">14:30–15:00 · Platform team</span></div><Button dense variant="ghost">Prep</Button></div></li>
      <li className="today-section"><span>TO FINISH</span></li>
      <li className="today-node" data-kind="finish"><span className="today-time">THU</span><span className="today-bead"/><div className="today-node-body today-row"><div className="today-row-text"><Button variant="chrome" className="today-row-title">API compatibility and migration planning</Button><span className="today-row-meta">Summary failed</span></div><Button dense variant="secondary">Retry</Button></div></li>
    </ol><aside className="today-side"><SurfaceSection label="To decide"><strong className="surface-primary">Stage the platform migration by service</strong><span className="surface-token">Platform architecture review · Oct 15</span><div className="canvas-facts"><Button dense variant="secondary">Open decision</Button><Button dense variant="ghost">Confirm</Button><Button dense variant="ghost">Not now</Button></div></SurfaceSection><SurfaceSection label="Owed"><span className="surface-primary">2 you owe · 3 owed to you</span><Button dense variant="ghost">People</Button></SurfaceSection></aside></div>
  </div>;
}

function FollowThrough() {
  return <div className="follow-through-view">
    <div className="surface-display">Open work</div>
    <SurfaceSection label="Your work"><SurfaceLedger cols="follow-through"><SurfaceLedgerRow wrap open primary={<span className="follow-through-identity"><strong>Summarize what happened this week.</strong><span className="follow-through-owner">Me</span></span>} cells={<span className="follow-through-facts"><StateChip state="idle" label="No date"/><StateChip state="warning" label="Snoozed until Oct 17" wrap/></span>} onToggle={noop} trailing={<Button dense variant="ghost">Details</Button>}>
      <div className="follow-through-expanded"><div className="follow-through-provenance"><cite>Weekly summary · Oct 12–18</cite><span>Summarize what happened this week.</span><Button dense variant="ghost">Open source</Button></div><div className="canvas-facts"><Button dense variant="secondary">Assign</Button><Button dense variant="secondary">Set date</Button><Button dense variant="ghost">Done</Button></div></div>
    </SurfaceLedgerRow><SurfaceLedgerRow wrap primary={<span className="follow-through-identity"><strong>Send platform migration options to Priya Narayanan</strong><span className="follow-through-owner">Me</span></span>} cells={<StateChip state="warning" label="Due today"/>} trailing={<Button dense variant="ghost">Details</Button>}/></SurfaceLedger></SurfaceSection>
    <SurfaceSection label="Workbench output" actions={<StateChip state="warning" label="Awaiting review"/>}><div className="surface-primary">TODO Agent: Review open PRs</div><Material>{"## Receipt — Review open PRs\n\nNo PRs are present in the provided materials.\n\nProvide the PRs to review.\n\n### Needed context\n\n- Pull request links\n- Repository and branch\n- Review scope"}</Material></SurfaceSection>
  </div>;
}

function Memory() {
  return <div className="recall-face"><div className="recall-head"><div className="surface-display">Recent work</div><span className="surface-token">READ 09:12</span></div>
    <SurfaceSection label="Current"><article className="recall-card" data-state="current"><div className="recall-card-line"><span className="surface-primary recall-card-title">Stage the platform migration by service, with compatibility checks before each release</span></div><div className="recall-rationale">The platform team can release each service separately while the old API remains available.</div><div className="recall-card-chips"><StateChip state="success" label="Current"/><span className="surface-token">Decision · Oct 15</span><Button dense variant="ghost">Platform migration</Button></div><div className="recall-source"><RefTokens refs={meetingRef} onOpen={noop}/><Button dense variant="ghost">Open source</Button></div><div className="canvas-facts"><Button dense>Carry into brief</Button></div></article></SurfaceSection>
    <SurfaceSection label="Meetings"><SurfaceRows><SurfaceRow title="Platform architecture review: API compatibility and staged migration" detail="Priya Narayanan will review the rollout options. Ania Kowalska owns the compatibility plan." meta="Meeting · Oct 15 · 10:00" onOpen={noop}/></SurfaceRows></SurfaceSection>
    <SurfaceSection label="Owed"><SurfaceRows><SurfaceRow title="Send platform migration options to Priya Narayanan" detail="Me · Due Friday" meta={<RefTokens refs={meetingRef} onOpen={noop}/>} verbs={<Button dense variant="secondary">Done</Button>}/></SurfaceRows></SurfaceSection>
  </div>;
}

const selected = new URLSearchParams(location.search).get("surface") || location.hash.slice(1) || "brief";
const faces = { brief: Brief, day: Day, "follow-through": FollowThrough, memory: Memory };
const Face = faces[selected as keyof typeof faces] || Brief;
createRoot(document.getElementById("root")!).render(<main className="desk-next canvas-ground"><section className="canvas-window"><header className="canvas-window-title">{selected === "day" ? "Day" : selected === "follow-through" ? "Follow-through" : selected === "memory" ? "Memory" : "Brief"}</header><div className="desk-surface-body canvas-body"><Face/></div></section></main>);
