import type { InferenceTarget } from "../api";
import { humanizeWireValue } from "../../lib/productLanguage";
import { CycleGadget } from "../surface/gadgets";
import { openSurfaceOr } from "../shell";

const KIND_LABEL: Record<string, string> = {
  this_device: "This device",
  paired_device: "Paired device",
  private_endpoint: "Private endpoint",
  mesh_node: "Mesh node",
  external_service: "External service",
  unsupported: "Unsupported destination",
};

/** The one Runs-on control/view model used by Ask, Persona, Sequence, and
 * Workflow. HS-111-05: the naked select died — the destination is a
 * CycleGadget and the caption is mono tokens, never a sentence. */
export function RunsOnPicker(props: {
  targets: InferenceTarget[];
  selectedId: string;
  onChange: (id: string) => void;
  disabled?: boolean;
}) {
  const availableTargets = props.targets.filter(
    (target) => target.readiness.available,
  );
  const selected =
    props.targets.find((target) => target.id === props.selectedId) ||
    props.targets[0];
  const sent = selected?.data_scope?.sent || [];
  const noDestinations = availableTargets.length === 0;
  return (
    <div className="runs-on-picker">
      <CycleGadget
        label="Runs on"
        value={
          noDestinations ? "no_destinations" : selected?.id || "this_machine"
        }
        disabled={props.disabled || noDestinations}
        onChange={props.onChange}
        options={
          noDestinations
            ? [
                {
                  value: "no_destinations",
                  label: "NO DESTINATIONS",
                  disabled: true,
                },
              ]
            : props.targets.map((target) => ({
                value: target.id,
                disabled: !target.readiness.available,
                label:
                  target.name +
                  ((KIND_LABEL[target.kind] || target.kind) !== target.name
                    ? ` · ${KIND_LABEL[target.kind] || target.kind}`
                    : "") +
                  (!target.readiness.available
                    ? ` · unavailable: ${target.readiness.reason}`
                    : ""),
              }))
        }
      />
      {noDestinations ? (
        <button
          type="button"
          className="gadget-table-add"
          onClick={() => openSurfaceOr("configure-runs-on", "/profiles")}
        >
          + ADD IN SETTINGS &gt; MODELS
        </button>
      ) : null}
      {selected && !noDestinations && (
        <p
          className={
            (selected.readiness.available ? "quiet" : "desk-run-warning") +
            " runs-on-facts"
          }
        >
          {KIND_LABEL[selected.kind] || selected.kind} ·{" "}
          {humanizeWireValue(selected.boundary)}
          {sent.length
            ? ` · SENDS: ${sent
                .map((value) => humanizeWireValue(value))
                .join("+")}`
            : ""}
          {!selected.readiness.available
            ? ` · ${selected.readiness.reason}`
            : ""}
        </p>
      )}
    </div>
  );
}
