// HS-112-02 — the aim row: where a released TALK sends the words,
// and whether this one is only a rehearsal.
import {
  CheckGadget,
  CycleGadget,
  GadgetGroup,
  GadgetRow,
} from "../../../../desk/surface/gadgets";
import { AIM_FACT, AIM_OPTIONS } from "../shared";

export function AimRow({
  aim,
  onAimChange,
  rehearse,
  onRehearseChange,
}: {
  aim: string;
  onAimChange: (next: string) => void;
  rehearse: boolean;
  onRehearseChange: (next: boolean) => void;
}) {
  return (
    <div className="speak-aim">
      <GadgetGroup>
        <GadgetRow label="Aim" fact={AIM_FACT[aim] ?? aim}>
          <CycleGadget
            label="Aim"
            value={aim}
            options={AIM_OPTIONS}
            onChange={onAimChange}
          />
        </GadgetRow>
        <GadgetRow label="Rehearse" fact="DRY RUN">
          <CheckGadget
            label="Rehearse"
            checked={rehearse}
            onChange={onRehearseChange}
          />
        </GadgetRow>
      </GadgetGroup>
    </div>
  );
}
