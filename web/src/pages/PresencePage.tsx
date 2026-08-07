import { useRuntimeBus, useRuntimeFrame } from "../runtime/RuntimeBus";
import { LampGadget } from "../desk/surface/gadgets";

type Activity = {
  state?: string;
  label?: string;
  detail?: string;
  source?: string;
  window?: string;
};
export default function PresencePage() {
  const activity = useRuntimeFrame<Activity>("runtime_activity");
  const { state } = useRuntimeBus();
  const label =
    activity?.label ?? (state === "connected" ? "Ready" : "Connecting");
  const tone = activity?.state === "error" ? "fail" : state === "connected" ? "ok" : "warn";

  return (
    <div className="desk-next presence-body">
      <a href="/" className="desk-chip quiet presence-back">
        ← Desk
      </a>
      <section className="presence-card" role="status" aria-live="polite">
        <LampGadget on={state === "connected"} tone={tone} label={label} />
      </section>
    </div>
  );
}
