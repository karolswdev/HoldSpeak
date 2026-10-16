import { useRuntimeBus, useRuntimeFrame } from "../runtime/RuntimeBus";
import { LampGadget } from "../desk/surface/gadgets";
import { SurfaceSection } from "../desk/surface/Surface";
import { Button } from "../components/signal/Signal";
import { useNavigate } from "react-router-dom";

type Activity = {
  state?: string;
  label?: string;
  detail?: string;
  source?: string;
  window?: string;
};
export default function PresencePage() {
  const navigate = useNavigate();
  const activity = useRuntimeFrame<Activity>("runtime_activity");
  const { state } = useRuntimeBus();
  const label =
    activity?.label ?? (state === "connected" ? "Ready" : "Connecting");
  const tone = activity?.state === "error" ? "fail" : state === "connected" ? "ok" : "warn";

  return (
    <div className="desk-next presence-body">
      <div className="presence-card">
        <SurfaceSection label="Runtime" actions={
          <Button dense variant="ghost" className="presence-back" onClick={() => navigate({ pathname: "/", search: window.location.search })}>
            Desk
          </Button>
        }>
          <div className="presence-activity" role="status" aria-live="polite">
            <LampGadget on={state === "connected"} tone={tone} label={label} block />
          </div>
        </SurfaceSection>
      </div>
    </div>
  );
}
