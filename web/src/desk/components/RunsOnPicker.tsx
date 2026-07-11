import type { InferenceTarget } from "../api";

const KIND_LABEL: Record<string, string> = {
  this_device: "This device",
  paired_device: "Paired device",
  private_endpoint: "Private endpoint",
  mesh_node: "Mesh node",
  external_service: "External service",
  unsupported: "Unsupported destination",
};

/** The one Runs-on control/view model used by Ask, Persona, Sequence, and Workflow. */
export function RunsOnPicker(props: {
  targets: InferenceTarget[];
  selectedId: string;
  onChange: (id: string) => void;
  disabled?: boolean;
}) {
  const selected = props.targets.find((target) => target.id === props.selectedId)
    || props.targets[0];
  const sent = selected?.data_scope?.sent || [];
  return (
    <div className="runs-on-picker">
      <label>
        <span>Runs on</span>
        <select
          aria-label="Runs on"
          value={selected?.id || "this_machine"}
          onChange={(event) => props.onChange(event.target.value)}
          disabled={props.disabled}
        >
          {props.targets.map((target) => (
            <option key={target.id} value={target.id} disabled={!target.readiness.available}>
              {target.name} · {KIND_LABEL[target.kind] || target.kind}
              {!target.readiness.available ? ` · unavailable: ${target.readiness.reason}` : ""}
            </option>
          ))}
        </select>
      </label>
      {selected && (
        <p className={selected.readiness.available ? "quiet" : "desk-run-warning"}>
          {KIND_LABEL[selected.kind] || selected.kind} · {selected.boundary}
          {sent.length ? ` · sends ${sent.join(", ")}` : ""}
          {!selected.readiness.available ? ` · ${selected.readiness.reason}` : ""}
        </p>
      )}
    </div>
  );
}
