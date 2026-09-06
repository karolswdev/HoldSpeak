import "./session-pullout.css";
import { Button } from "../../components/signal/Signal";
import { StringGadget, PadGadget } from "../surface";
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
}: DeskComposerProps) {
  const input = multiline ? (
    <PadGadget
      label={placeholder || actionLabel}
      value={value}
      rows={rows}
      onChange={onChange}
    />
  ) : (
    <StringGadget
      label={placeholder || actionLabel}
      value={value}
      onChange={onChange}
    />
  );

  return (
    <div className={["desk-chat-composer", className].filter(Boolean).join(" ")}>
      {input}
      <MicButton draftScope={micDraftScope} onText={onChange} />
      <Button
        dense
        disabled={actionDisabled || actionBusy}
        onClick={onAction}
      >
        {actionBusy ? `${actionLabel}…` : actionLabel}
      </Button>
    </div>
  );
}
