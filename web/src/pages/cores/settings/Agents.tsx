// Settings > Agents: how many work at once, Agents act and People access. Moved out of SettingsCore.tsx.
import { useState } from "react";
import type { AuthorityPolicyResponse } from "../core-types";
import { apiFetch, readableError } from "../../../lib/api";
import { CONTROL_MODES, controlModeLabel } from "../../../lib/productLanguage";
import { CycleGadget, GadgetGroup, GadgetRow } from "../../../desk/surface/gadgets";
import { PeopleAccessModule } from "./People";
import type { SettingsBindings } from "./bindings";
import type { SettingsWriter } from "./writer";

/** Agents act: the authority control mode. The face holds the busy flag. */
export function useControlMode(
  authority: { data: AuthorityPolicyResponse; setData: (next: AuthorityPolicyResponse) => void },
  writer: SettingsWriter,
  onWritten: () => void,
) {
  const [authorityBusy, setAuthorityBusy] = useState(false);
  const setControlMode = async (controlMode: string) => {
    setAuthorityBusy(true);
    writer.restoreRefusal();
    try {
      const result = await apiFetch<Record<string, unknown>>(
        "/api/authority/control-mode",
        {
          method: "PUT",
          json: { control_mode: controlMode },
        },
      );
      authority.setData({ ...authority.data, ...result });
      writer.restoreRefusal();
      onWritten();
    } catch (error) {
      writer.setRefusal(readableError(error));
    } finally {
      setAuthorityBusy(false);
    }
  };
  return { authorityBusy, setControlMode };
}

export type ControlMode = ReturnType<typeof useControlMode>;

export function AgentsSection({ b, focusHighlight, posture, authority, control }: {
  b: SettingsBindings;
  focusHighlight: string;
  posture: string | undefined;
  authority: { data: AuthorityPolicyResponse; loading: boolean; error: string };
  control: ControlMode;
}) {
  const { num } = b;
  return <>
          {/* ── Agents: how many work at once (Betterment AG5) ── */}
          <GadgetGroup material="inset" label="Working at once">
            {num(["agents", "working_at_once"], "Working at once", { min: 1, max: 20, step: 1 })}
          </GadgetGroup>
          <GadgetGroup material="inset" label="Agents act">
            <GadgetRow label="Agents act" highlight={focusHighlight === "agents-act"}>
              <CycleGadget
                label="Agents act"
                value={String(posture || authority.data.control_mode || "neutral")}
                disabled={control.authorityBusy || authority.loading || Boolean(authority.error)}
                options={CONTROL_MODES.map((mode) => ({ value: mode, label: controlModeLabel(mode) }))}
                onChange={(mode) => void control.setControlMode(mode)}
              />
            </GadgetRow>
          </GadgetGroup>
          <PeopleAccessModule highlight={focusHighlight} />
        </>;
}
