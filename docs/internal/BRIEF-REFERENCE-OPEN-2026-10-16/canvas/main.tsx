import {createRoot} from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/surface/surface.css";
import "@w/desk/pullouts/intelligence.css";
import {SurfaceSection, SurfaceLedger, SurfaceLedgerRow} from "@w/desk/surface/Surface";
import {StateChip} from "@w/desk/surface/patterns/StateChip";
import {Material} from "@w/desk/surface/Material";
import {Button} from "@w/components/signal/Signal";
import "./canvas.css";
createRoot(document.getElementById("root")!).render(<main className="desk-next"><div className="specimen">
<div className="follow-through-view"><SurfaceSection label="Follow-through"><SurfaceLedger cols="follow-through"><SurfaceLedgerRow wrap open primary={<span className="follow-through-identity"><strong>Summarize what happened this week.</strong><span className="follow-through-owner">Me</span></span>} cells={<span className="follow-through-facts"><StateChip state="idle" label="No date"/><StateChip state="warning" label="Snoozed until 2026-10-17" wrap/></span>} onToggle={()=>{}} trailing={<Button dense variant="ghost">Details</Button>}><div>Existing task controls and source stay here.</div></SurfaceLedgerRow></SurfaceLedger></SurfaceSection></div>
<SurfaceSection label="Workbench output" actions={<StateChip state="warning" label="Awaiting review"/>}><h3>TODO Agent: Review open PRs</h3><Material>{"## Receipt — Review open PRs\n\nNo PRs are present in the provided materials.\n\nProvide the PRs to review."}</Material></SurfaceSection>
</div></main>);
