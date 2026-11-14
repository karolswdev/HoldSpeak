import { CycleGadget, PadGadget, StringGadget } from "../../desk/surface";
import { roomWord } from "./RoomList";

export type RoomEditField = {
  key: string;
  label: string;
  kind: "text" | "number" | "choice";
  values?: (string | boolean | number)[];
  values_by_kind?: Record<string, string[]>;
  values_by_item_type?: Record<string, string[]>;
};

/** The hub declares the fields; the kit draws each control. */
export function roomEditRows(
  fields: readonly RoomEditField[],
  values: Record<string, unknown>,
  change: (key: string, value: unknown) => void,
  disabled = false,
) {
  return fields.map((field) => {
    const value = values[field.key];
    const choices =
      field.values_by_kind?.[String(values.kind)] ?? field.values_by_item_type?.[String(values.item_type)] ?? field.values ?? [];
    return {
      label: field.label,
      control: (
        <div className="surface-inspector-control" data-feedback-redact="true">
          {field.kind === "choice" ? (
            <CycleGadget
              disabled={disabled}
              label={field.label}
              value={String(value ?? "")}
              options={choices.map((choice) => ({
                value: String(choice),
                label: roomWord(String(choice)),
              }))}
              onChange={(next) => {
                change(
                  field.key,
                  choices.find((choice) => String(choice) === next) ?? next,
                );
                const states = fields.find((field) => field.key === "state")
                  ?.values_by_kind?.[next];
                if (
                  field.key === "kind" &&
                  states?.length &&
                  !states.includes(String(values.state))
                )
                  change("state", states[0]);
                const lifecycles = fields.find((field) => field.key === "lifecycle")
                  ?.values_by_item_type?.[next];
                if (field.key === "item_type" && lifecycles?.length && !lifecycles.includes(String(values.lifecycle)))
                  change("lifecycle", lifecycles[0]);
              }}
            />
          ) : field.key === "subject" ? (
            <PadGadget
              disabled={disabled}
              label={field.label}
              value={String(value ?? "")}
              rows={3}
              onChange={(next) => change(field.key, next)}
            />
          ) : (
            <StringGadget
              disabled={disabled}
              label={field.label}
              value={String(value ?? "")}
              type={field.kind === "number" ? "number" : "text"}
              mic={field.kind !== "number"}
              onChange={(next) =>
                change(field.key, field.kind === "number" ? Number(next) : next)
              }
            />
          )}
        </div>
      ),
    };
  });
}
