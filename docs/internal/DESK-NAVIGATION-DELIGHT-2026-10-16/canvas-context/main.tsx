// Direction only: actual production library, with declared sample content.
import { useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { Button } from "@w/components/signal/Signal";
import { CycleGadget, LampGadget, PadGadget } from "@w/desk/surface/gadgets";
import { SurfaceSection } from "@w/desk/surface/Surface";
import { AppHead, StatusStrip } from "@w/desk/surface/kit";
import { NeedsList, NeedsRow } from "@w/desk/surface/objects/NeedsRow";
import "@w/pages/cores/constitutional-context.css";
import "@w/desk/needs/needs.css";
import "./canvas.css";

const noop = () => {};
const face = new URLSearchParams(location.search).get("face") || "context-empty";
const sample = "Senior Software Architect\nStack: Python, TypeScript, PostgreSQL\nKeep decisions and owners explicit.";

function ContextDirection() {
  const [draft, setDraft] = useState(face === "context-empty" ? "" : sample);
  const [version, setVersion] = useState("current");
  const revision = face === "context-empty" ? 0 : 4;
  const dirty = face === "context-unsaved";
  return (
    <div className="constitutional-context-core">
      <SurfaceSection label="Status" actions={
        <div className="constitutional-context-actions">
          {revision > 0 ? <CycleGadget label="Version history" value={version} onChange={setVersion}
            options={[{ value: "current", label: "current" }, { value: "3", label: "rev 3" }]} /> : null}
          <Button dense disabled={!dirty} onClick={noop}>Save</Button>
        </div>
      }>
        <div className="constitutional-context-status" aria-live="polite">
          {revision > 0 ? <span className="constitutional-context-fact">rev {revision}</span> : null}
          {draft.length > 0 ? <>
            <span className="constitutional-context-fact">~{Math.ceil(draft.length / 4)} tokens</span>
            <LampGadget label={`${draft.length}/32,768 chars`} on={false} tone="warn" />
          </> : null}
          {dirty ? <LampGadget label="unsaved" on tone="warn" /> : null}
          {face === "context-saved" ? <LampGadget label="saved" on tone="ok" /> : null}
          {face === "context-refused" ? <LampGadget label="Not saved" on tone="fail" /> : null}
        </div>
      </SurfaceSection>
      <SurfaceSection label="Constitutional context" className="constitutional-context-editor-section">
        <PadGadget label="Constitutional context" value={draft} onChange={setDraft}
          placeholder={"Role, stack, rules\nOne fact per line"} rows={10} autoGrow />
      </SurfaceSection>
    </div>
  );
}

function NeedsDirection() {
  return (
    <div className="needs-drawer">
      <AppHead fact="3 need you"><StatusStrip items={[{ text: "Checked 09:41" }]} /></AppHead>
      <NeedsList label="Needs you">
        <NeedsRow id="direction-question" kind="coder" plate="CC" kindWord="Agent"
          name="The runbook needs a rollback owner. Jordan or Avery?"
          fact="Claude · rollback runbook" lamp={{ label: "TO ANSWER", tone: "ask" }}
          verbs={<><Button dense variant="ghost" onClick={noop}>Open</Button><Button dense variant="primary" onClick={noop}>Answer</Button></>} />
        <NeedsRow id="direction-gate" kind="gate" plate="CX" kindWord="Gate"
          name="Approve: read the staging ledger count"
          fact="psql -h staging-ledger -c 'select count(*) from entries'" factCode
          lamp={{ label: "TO APPROVE", tone: "warn" }}
          verbs={<><Button dense variant="ghost" onClick={noop}>Deny</Button><Button dense variant="primary" onClick={noop}>Approve</Button></>} />
        <NeedsRow id="direction-decision" kind="decision" plate="Decision"
          name="Run a second ops interview" fact="Staff hiring loop"
          lamp={{ label: "TO REVIEW", tone: "warn" }}
          verbs={<Button dense variant="primary" onClick={noop}>Review</Button>} />
      </NeedsList>
    </div>
  );
}

function Direction() {
  const needs = face === "needs";
  const title = needs ? "Needs you" : "Context";
  return (
    <RuntimeBusProvider>
      <main className="desk-next direction-floor">
        <DeskWindowFrame id={`context-needs-direction-${face}`} title={title} label={title}
          glyph={needs ? "!" : "▤"} minW={320} defaultW={needs ? 860 : 660} defaultH={660}
          open entrance={false} onClose={noop} className="desk-surface-window">
          <div className="desk-surface-body direction-body">
            {needs ? <NeedsDirection /> : <ContextDirection />}
          </div>
        </DeskWindowFrame>
      </main>
    </RuntimeBusProvider>
  );
}

createRoot(document.getElementById("root")!).render(<Direction />);
