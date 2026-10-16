// Library direction with declared sample data; no hub/owner-state evidence.
import { useState, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/pullout.css";
import "@w/desk/components/delivery.css";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { Button } from "@w/components/signal/Signal";
import { PadGadget, StringGadget } from "@w/desk/surface/gadgets";
import { SurfaceSection } from "@w/desk/surface/Surface";
import { SurfaceFooter } from "@w/desk/surface/SurfaceFooter";
import { FootSlotContext } from "@w/desk/surface/foot";
import { PrReceiptsSection } from "@w/desk/components/PrReceiptsSection";
import { usePrReceipts, type PrRow } from "@w/desk/prReceipts";
import "./canvas.css";

const noop = () => {};
const face = new URLSearchParams(location.search).get("face") || "material";
if (face === "pr-result") {
  const row: PrRow = {
    source_id: "direction-pr", number: 393, title: "Release controls", url: "https://github.com/example/review/pull/393",
    head_ref: "review-controls", base_ref: "main", head_sha: "a".repeat(40), base_sha: "b".repeat(40),
    state: "open", ci: "passing", author: "reviewer", observed_at: "2026-10-16T12:00:00Z", attribution: "exact", basis: "Declared direction", agent_gate: "gated",
    verbs: { send_agent: { available: false, reason: "Not part of this direction" }, draft_review: { available: true, reason: "" }, post_comment: { available: false, reason: "Not part of this direction" }, post_status: { available: false, reason: "Not part of this direction" } },
  };
  usePrReceipts.setState({ sources: [{ source_id: row.source_id, label: "Review repository", status: "live", detail: "", observed_at: row.observed_at, prs: [row] }], loaded: true,
    load: async () => {}, draftReview: async () => ({ output: "Confirm the snapshot retry keeps the edited title.\n\nKeep the material paragraphs intact.", operation_id: "delivery-pr-review:7a1b", artifact_id: "review-42" }) });
}

function Frame({ title, children, verbs, receipt }: { title: string; children: ReactNode; verbs: ReactNode; receipt?: ReactNode }) {
  const [foot, setFoot] = useState<HTMLElement | null>(null);
  return <DeskWindowFrame id={`material-direction-${face}`} label={title} title={title} glyph="▤" minW={320} defaultW={face === "pr-result" ? 640 : 680} defaultH={540} open entrance={false} onClose={noop} className="desk-surface-window">
    <FootSlotContext.Provider value={foot}>
      <div className="desk-surface-body material-direction-body">{children}</div>
      <SurfaceFooter receipt={receipt} verbs={verbs}/>
      <footer ref={setFoot} className="desk-surface-foot surface-footer"/>
    </FootSlotContext.Provider>
  </DeskWindowFrame>;
}

function MaterialDirection() {
  const [material, setMaterial] = useState("## Release review\nConfirm the restore path.\n\n## Reports\nReview the reconciliation results with the team.");
  return <Frame title="Review workflow" verbs={<Button dense onClick={noop}>Close</Button>}>
    <SurfaceSection label="Material">
      <div className="desk-chat-well"><div className="material-direction-composer">
        <PadGadget label="Run Review" placeholder="Material" value={material} onChange={setMaterial} rows={7} micLabel="Speak to fill run review material" micDraftScope="capability:workflow:review"/>
        <Button dense variant="primary" disabled={!material.trim()} onClick={noop}>Run</Button>
      </div></div>
    </SurfaceSection>
    <div className="desk-pullout-capability-foot"><span className="quiet">Runs on This machine · Creates artifact</span><Button dense variant="ghost" onClick={noop}>Assignments</Button></div>
  </Frame>;
}

function PrDirection() {
  return <Frame title="Companion" verbs={<Button dense onClick={noop}>Close</Button>}>
    <PrReceiptsSection/>
  </Frame>;
}

function FooterDirection() {
  return <Frame title="Calendar snapshot" receipt={<span className="surface-footer-receipt-line" data-tone="danger">CALENDAR SNAPSHOT FAILED</span>} verbs={<Button dense variant="primary" onClick={noop}>Retry</Button>}>
    <SurfaceSection label="Monday · 12 October"><StringGadget label="Event title" value="Release review ready" onChange={noop}/><span className="surface-token">09:00–09:30 · Room 1</span></SurfaceSection>
    <SurfaceSection label="Friday · 16 October"><span>Architecture review</span><span className="surface-token">14:00–15:00</span></SurfaceSection>
  </Frame>;
}

createRoot(document.getElementById("root")!).render(<RuntimeBusProvider><main id="desk-next" className={`desk-next material-direction-floor material-direction-${face}`}>{face === "material" ? <MaterialDirection/> : face === "pr-result" ? <PrDirection/> : <FooterDirection/>}</main></RuntimeBusProvider>);
