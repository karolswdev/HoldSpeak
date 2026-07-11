import { useRuntimeBus, useRuntimeFrame } from "../runtime/RuntimeBus";
import { StatusPill } from "../components/signal/Signal";

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
  const tone =
    activity?.state === "error"
      ? "error"
      : activity?.state === "complete"
        ? "complete"
        : ["recording", "listening"].includes(activity?.state ?? "")
          ? "recording"
          : activity
            ? "working"
            : "idle";
  return (
    <div className="presence-body">
      <section
        className={`presence-card tone-${tone}`}
        role="status"
        aria-live="polite"
      >
        <span className="presence-orb" aria-hidden="true" />
        <div>
          <strong>
            {activity?.label ??
              (state === "connected" ? "Ready" : "Connecting")}
          </strong>
          <p>{activity?.detail ?? "Waiting for activity."}</p>
          <small>
            {activity?.source ?? "HoldSpeak"}
            {activity?.window ? ` · ${activity.window}` : ""}
          </small>
        </div>
        <StatusPill tone={state === "connected" ? "success" : "warning"}>
          {state}
        </StatusPill>
      </section>
    </div>
  );
}
