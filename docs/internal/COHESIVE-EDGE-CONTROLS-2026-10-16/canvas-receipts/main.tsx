// Library canvas with declared sample data. No hub or owner-state claim.
import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/mission-control.css";
import "@w/desk/components/ask-panel.css";
import "@w/desk/components/workbench-config.css";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { Button } from "@w/components/signal/Signal";
import { ConfirmVerb, SurfaceTraffic, SurfaceTrafficTurn } from "@w/desk/surface/Surface";
import { SurfaceFooter } from "@w/desk/surface/SurfaceFooter";
import { CheckGadget, GadgetGroup, GadgetRow, StepperGadget } from "@w/desk/surface/gadgets";
import { groundedMatchCount, sourceLabel } from "@w/desk/surface/citations";
import { Material } from "@w/desk/surface/Material";
import { useWriteReceipt } from "@w/desk/hooks/useWriteReceipt";
import "./canvas.css";

const noop = () => {};
const face = new URLSearchParams(location.search).get("face") || "ask-zero";

function ResourcefulDirection() {
  const [enabled, setEnabled] = useState(face === "resourceful-enabled" || face === "resourceful-failure");
  const [settings, setSettings] = useState({ idle: 30, cooldown: 6, target: 2, overnight: true, start: 22, end: 7 });
  const [loose, setLoose] = useState(true), [failed, setFailed] = useState(true);
  const step = (key: "idle" | "cooldown" | "target" | "start" | "end", label: string, min: number, max: number, unit: string) =>
    <StepperGadget label={label} value={settings[key]} min={min} max={max} unit={unit} onChange={(value) => setSettings((current) => ({ ...current, [key]: value }))} />;
  return <div className="wb-resourceful">
    <div className="wb-resourceful-contract" role="status">
      <span className="surface-token">LOCAL DATA</span><span className="surface-token">ONE ITEM / RUN</span>
      <span className="desk-chip">{settings.idle} MIN IDLE</span><span className="desk-chip">{settings.cooldown}H COOLDOWN</span>
      <span className="desk-chip">TARGET {settings.target} / NIGHT</span><span className="desk-chip">{settings.overnight ? `${String(settings.start).padStart(2, "0")}:00–${String(settings.end).padStart(2, "0")}:00` : "ANY TIME"}</span>
    </div>
    <GadgetGroup label="Idle policy">
      <GadgetRow label="Idle after" fact="1–1440 min">{step("idle", "Idle after minutes", 1, 1440, "min")}</GadgetRow>
      <GadgetRow label="Cooldown" fact="1–168 hr">{step("cooldown", "Cooldown hours", 1, 168, "hr")}</GadgetRow>
      <GadgetRow label="Nightly target" fact="1–8 items">{step("target", "Nightly target", 1, 8, "items")}</GadgetRow>
      <GadgetRow label="Overnight only"><CheckGadget label="Overnight only" checked={settings.overnight} onChange={(overnight) => setSettings((current) => ({ ...current, overnight }))}/></GadgetRow>
      {settings.overnight ? <><GadgetRow label="Night starts" fact="local time">{step("start", "Night starts hour", 0, 23, ":00")}</GadgetRow><GadgetRow label="Night ends" fact="local time">{step("end", "Night ends hour", 0, 23, ":00")}</GadgetRow></> : null}
    </GadgetGroup>
    <div className="wb-resourceful-routines">
      <div className="wb-resourceful-routine"><CheckGadget variant="token" label="Develop loose ideas" checked={loose} onChange={setLoose}/><span className="surface-token wb-resourceful-routine-fact">LOOSE IDEAS DIRECTORY · OLDEST REVISED NOTE</span></div>
      <div className="wb-resourceful-routine"><CheckGadget variant="token" label="Prepare recovery plans" checked={failed} onChange={setFailed}/><span className="surface-token wb-resourceful-routine-fact">INCOMPLETE WORK · DRAFT PLAN</span></div>
      <div className="wb-resourceful-limits" aria-label="Execution limits"><span className="surface-token">SELECTED MAINTENANCE ONLY</span><span className="surface-token">PENDING WORK UNTOUCHED</span><span className="surface-token">SOURCE DATA · REVIEW-ONLY</span></div>
    </div>
    <div className="wb-automation-verbs"><span className="surface-token">RUNS AS OWNER</span>{enabled ? <><Button dense disabled={!loose && !failed} onClick={noop}>Save policy</Button><Button dense data-tone="warn" onClick={() => setEnabled(false)}>Pause</Button></> : <ConfirmVerb label={settings.overnight ? "Enable overnight resourcefulness" : "Enable resourcefulness"} confirmLabel="RUN AS OWNER?" disabled={!loose && !failed} onConfirm={() => setEnabled(true)}/>}</div>
    <div className="wb-resourceful-status" role="status"><span className="surface-token">{enabled ? "READY WHEN IDLE" : "PAUSED"}</span>{enabled ? null : <span className="surface-token">NO RESOURCEFUL WORK STARTS</span>}</div>
  </div>;
}

function AskDirection() {
  const names: Record<string, string> = {
    "note:release-checks": "Release checklist",
    "note:release-review": "Architecture migration review and release readiness across every platform and integration",
  };
  const receipt = face === "ask-positive" ? { matchedCount: 5, overflowCount: 2, sourceRefs: ["note:release-checks", "note:release-review"] } : { matchedCount: 3, overflowCount: 3, sourceRefs: ["note:release-checks"] };
  const grounded = groundedMatchCount(receipt);
  return <div className="desk-ask-reading conversation-reading"><SurfaceTraffic showEmpty={false}>
    <SurfaceTrafficTurn prefix="You">What are the release checks?</SurfaceTrafficTurn>
    <SurfaceTrafficTurn prefix="Answer" verbs={<Button dense onClick={noop}>Copy</Button>}>
      <div className="desk-ask-answer"><Material>{"## Release checks\n\nConfirm the restore path and review the reconciliation results."}</Material>
        <div className="desk-ask-receipt"><p className="desk-ask-grounded">{grounded > 0 ? `GROUNDED ON ${grounded} OF ${receipt.matchedCount}` : "UNGROUNDED"}</p><div className="surface-citations" aria-label="Citations">{receipt.sourceRefs.map((ref) => <Button key={ref} variant="chrome" className="desk-chip quiet" title={ref} onClick={noop}>{sourceLabel(`${ref.split(":", 1)[0]}:${names[ref]}`)}</Button>)}</div><p className="desk-ask-claim" title="Possibly unsupported by the cited material">◇ Release timing needs confirmation.</p></div>
      </div>
    </SurfaceTrafficTurn>
  </SurfaceTraffic></div>;
}

function Direction() {
  const ask = face.startsWith("ask-");
  const { attempt, receipt } = useWriteReceipt();
  useEffect(() => {
    if (face === "resourceful-failure") void attempt("SAVE POLICY", async () => new Response("{}", { status: 503 }));
  }, [attempt]);
  return <RuntimeBusProvider><main className="desk-next receipt-direction-floor"><DeskWindowFrame id={`receipt-direction-${face}`} label={ask ? "Ask AI" : "Architecture review"} title={ask ? "Ask AI" : "Architecture review"} glyph={ask ? "✦" : "▤"} minW={320} defaultW={680} defaultH={ask ? 510 : 880} open entrance={false} onClose={noop} className="desk-surface-window">
    <div className="desk-surface-body receipt-direction-body">{ask ? <AskDirection/> : <ResourcefulDirection/>}</div>
    <div className="desk-surface-foot"><SurfaceFooter receipt={ask ? <span className="surface-footer-receipt-line">{face === "ask-positive" ? "Answered in 3 s" : "Answered"}</span> : receipt} verbs={ask ? <><Button dense variant="ghost" onClick={noop}>Bin</Button><Button dense variant="primary" onClick={noop}>Keep</Button></> : <Button dense variant="ghost" onClick={noop}>Close</Button>}/></div>
  </DeskWindowFrame></main></RuntimeBusProvider>;
}
createRoot(document.getElementById("root")!).render(<Direction/>);
