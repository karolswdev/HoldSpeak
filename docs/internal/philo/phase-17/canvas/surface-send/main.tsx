import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/components/window-interior.css";
import "@w/desk/surface/surface.css";
import "@w/features/channels/channels.css";
import "@w/desk/surface/send/send-well.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow, SurfaceWell, SurfaceState } from "@w/desk/surface/Surface";
import { EgressChip } from "@w/desk/surface/gadgets";
import { StateChip } from "@w/desk/surface/patterns";

const pose = new URLSearchParams(location.search).get("state") || "ready";
const email = pose === "email";
const loading = pose === "loading";
const sent = pose === "sent";
const destination = email ? "Mira · Work" : "HoldSpeak folder";
const fields = email
 ? [{ label: "From", value: "Karol <karol@example.test>" }, { label: "To", value: "mira@example.test" }, { label: "Subject", value: "Ledger rollback" }]
 : [{ label: "Folder", value: "HoldSpeak/Sent" }];

function Canvas() {
 return <div className="desk-next canvas">
  <header className="canvas-bar">CANVAS · Synthetic saved note · {pose.toUpperCase()} · No dispatch</header>
  <main className="desk-window desk-window-shell canvas-window">
   <div className="canvas-title">Ledger rollback · Note</div>
   <div className="canvas-body">
    <div data-send="well" aria-label="Send Ledger rollback">
     <SurfaceSection label="Send" actions={<Button dense variant="ghost">Add destination</Button>}>
      {loading ? <SurfaceState loading /> : <SurfaceLedger count="" cols="room">
       <ul className="surface-ledger-rows">
        <SurfaceLedgerRow wrap open primary={<span className="surface-primary">{destination}</span>}
         lead={<span className="send-pick" aria-hidden="true">●</span>} onToggle={() => {}}
         cells={<span className="send-cells"><span className="surface-token" data-chip>{email ? "EMAIL" : "FILE"}</span>{email ? <StateChip state="success" label="KEY SET" /> : null}<EgressChip label={email ? "RESEND" : "THIS DEVICE"} scope={email ? "cloud" : "local"} />{sent ? <StateChip state="success" label="SAVED 09:14" /> : null}</span>}>
         <div className="send-open">
          <div className="send-preview">
           <SurfaceSection label="Preview">
            <dl className="send-fields">{fields.map(field => <div key={field.label} className="send-field"><dt className="surface-token">{field.label}</dt><dd>{field.value}</dd></div>)}</dl>
            <SurfaceWell><div className="send-preview-body"><h2>Ledger rollback</h2><p>Keep the rollback plan ready for Friday.</p><p>Mira will check the runbook before the cutover.</p></div></SurfaceWell>
           </SurfaceSection>
           <div className="send-verbs">
            <Button dense variant="primary">{sent ? "Send again" : "Send"}</Button>
            <EgressChip label={email ? "RESEND" : "THIS DEVICE"} scope={email ? "cloud" : "local"} />
            {sent ? <><StateChip state="success" label="SAVED" /><span className="surface-token send-literal" data-chip>Ledger rollback.md</span></> : null}
           </div>
          </div>
         </div>
        </SurfaceLedgerRow>
        <SurfaceLedgerRow wrap primary={<span className="surface-primary">{email ? "HoldSpeak folder" : "Mira · Work"}</span>}
         lead={<span className="send-pick" aria-hidden="true">○</span>} onToggle={() => {}}
         cells={<span className="send-cells"><span className="surface-token" data-chip>{email ? "FILE" : "EMAIL"}</span><span className="surface-token send-literal" data-chip>{email ? "HoldSpeak/Sent" : "mira@example.test"}</span><EgressChip label={email ? "THIS DEVICE" : "RESEND"} scope={email ? "local" : "cloud"} /></span>} />
       </ul>
      </SurfaceLedger>}
     </SurfaceSection>
    </div>
   </div>
   <footer className="canvas-foot"><Button dense variant="ghost">Back</Button><span className="surface-token">Saved</span></footer>
  </main>
 </div>;
}
createRoot(document.getElementById("root")!).render(<Canvas />);
