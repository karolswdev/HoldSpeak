// Actual library components, declared samples. No runtime producer claim.
import { createRoot } from "react-dom/client";
import { BrowserRouter, useNavigate } from "react-router-dom";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import { Button } from "@w/components/signal/Signal";
import { SurfaceSection } from "@w/desk/surface/Surface";
import { LampGadget } from "@w/desk/surface/gadgets";
import "./canvas.css";

const samples = {
  ready: { connection: "connected", activity: null },
  long: { connection: "connected", activity: { state: "working", label: "Reading architecture migration decisions and release readiness across every platform and integration" } },
  connecting: { connection: "offline", activity: null },
  error: { connection: "connected", activity: { state: "error", label: "Task failed" } },
} as const;
const face = new URLSearchParams(location.search).get("face") || "ready";
const sample = samples[face as keyof typeof samples] || samples.ready;

function Direction() {
  const navigate = useNavigate();
  const label = sample.activity?.label ?? (sample.connection === "connected" ? "Ready" : "Connecting");
  const tone = sample.activity?.state === "error" ? "fail" : sample.connection === "connected" ? "ok" : "warn";
  return <main className="desk-next presence-body">
    <div className="presence-card">
      <SurfaceSection label="Runtime" actions={<Button dense variant="ghost" className="presence-back" onClick={() => navigate({ pathname: "/", search: window.location.search })}>Desk</Button>}>
        <div className="presence-activity" role="status" aria-live="polite">
          <LampGadget on={sample.connection === "connected"} tone={tone} label={label} block />
        </div>
      </SurfaceSection>
    </div>
  </main>;
}
createRoot(document.getElementById("root")!).render(<BrowserRouter><Direction/></BrowserRouter>);
