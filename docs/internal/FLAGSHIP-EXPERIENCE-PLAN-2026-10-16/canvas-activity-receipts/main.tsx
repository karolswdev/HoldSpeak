import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/surface/surface.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection, SurfaceRows, SurfaceRow } from "@w/desk/surface/Surface";
import { EgressChip, StringGadget } from "@w/desk/surface/gadgets";
import { ActionNotice } from "@w/desk/surface/patterns/ActionNotice";
import { StatusStrip } from "@w/desk/surface/kit";
import "../canvas-recovery/canvas.css";

const pose = new URLSearchParams(location.search).get("pose") || "populated";
const noop = () => {};
const missing = pose === "missing-door";
const rows = missing ? [
  { id: "pipeline:project-read", title: "Project list read", detail: "Oct 16, 09:12", outcome: "Completed", door: false },
] : [
  { id: "pipeline:sweep", title: "SWEEP 3 ROOMS", detail: "Oct 16, 09:14 · Rhythm", outcome: "Completed", door: true },
  { id: "meeting:review:capture:finalized", title: "Meeting saved", detail: "Oct 16, 09:08 · Platform architecture review", outcome: "Finalized", door: true },
];

function ActivityReceiptsCanvas() {
  return <main className="desk-next recovery-ground"><section className="recovery-window">
    <header className="recovery-window-title">Activity</header>
    <div className="desk-surface-body recovery-body"><div className="recovery-face">
      <div className="recovery-verbs"><Button dense>Refresh now</Button><span className="gadget-chip">Watching</span></div>
      <SurfaceSection label="Records"><StringGadget label="Filter this view" placeholder="FILTER" value="" onChange={noop}/><SurfaceRows>
        <SurfaceRow title="Platform migration and API compatibility" detail="Oct 16, 09:13" meta="Browser"/>
      </SurfaceRows></SurfaceSection>
      <SurfaceSection label="Finished" data-testid="activity-finished">
        {pose === "read-failed" ? <><ActionNotice tone="warn" action={{ label: "Retry", onClick: noop }} role="alert">Finished read failed · Shown receipts kept · Retry</ActionNotice><StatusStrip items={[{ text: "Last read" }]}/></> : null}
        <SurfaceRows>{rows.map((row) => <SurfaceRow key={row.id} id={`activity-receipt-${row.id}`} title={row.title} detail={row.detail} meta={<><span className="gadget-chip">{row.outcome}</span><EgressChip label="THIS DEVICE" scope="local"/></>}>
          {row.door ? <Button dense aria-label={`Open receipt: ${row.title}`} onClick={noop}>Open receipt</Button> : <span className="surface-token">Receipt view unavailable</span>}
        </SurfaceRow>)}</SurfaceRows>
        {!missing ? <Button dense variant="ghost" onClick={noop}>Load more</Button> : null}
      </SurfaceSection>
    </div></div>
  </section></main>;
}

createRoot(document.getElementById("root")!).render(<ActivityReceiptsCanvas/>);
