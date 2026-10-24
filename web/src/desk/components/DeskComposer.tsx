import "./session-pullout.css";
import { Button } from "../../components/signal/Signal";
import { ComposerWell, StringGadget, PadGadget } from "../surface";
import { MicButton } from "./MicButton";

interface DeskComposerProps {
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
  multiline?: boolean;
  rows?: number;
  actionLabel: string;
  onAction: () => void;
  actionDisabled?: boolean;
  actionBusy?: boolean;
  className?: string;
  /** Durable scope for a retained voice capture. */
  micDraftScope?: string;
  /** A local specimen has no speech capture IO. Live editors default on. */
  mic?: boolean;
}

/** A speak-to-fill text well with its primary action. */
export function DeskComposer({
  value,
  onChange,
  placeholder,
  multiline,
  rows = 3,
  actionLabel,
  onAction,
  actionDisabled,
  actionBusy,
  className,
  micDraftScope,
  mic = true,
}: DeskComposerProps) {
  const input = multiline ? (
    <PadGadget
      label={placeholder || actionLabel}
      value={value}
      rows={rows}
      mic={false}
      onChange={onChange}
    />
  ) : (
    <StringGadget
      label={placeholder || actionLabel}
      value={value}
      mic={false}
      onChange={onChange}
    />
  );
  // Legacy receipt-row hooks belong to the editor slot. Keeping them off the
  // shared species root lets ComposerWell own the action-row layout.
  const editor = className ? <div className={className}>{input}</div> : input;

  return (
    <ComposerWell
      capture={mic ? <MicButton draftScope={micDraftScope} onText={onChange} /> : undefined}
      actions={(
        <Button
          dense
          variant="primary"
          disabled={actionDisabled || actionBusy}
          onClick={onAction}
        >
          {actionBusy ? `${actionLabel}…` : actionLabel}
        </Button>
      )}
    >
      {editor}
    </ComposerWell>
  );
}
