import "./session-pullout.css";
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
    <textarea
      aria-label={placeholder || actionLabel}
      value={value}
      placeholder={placeholder}
      rows={rows}
      onChange={(event) => onChange(event.target.value)}
    />
  ) : (
    <input
      aria-label={placeholder || actionLabel}
      value={value}
      placeholder={placeholder}
      onChange={(event) => onChange(event.target.value)}
    />
  );

  return (
    <div className={["desk-chat-composer", className].filter(Boolean).join(" ")}>
      {input}
      <MicButton draftScope={micDraftScope} onText={onChange} />
      <button
        type="button"
        className="desk-chip"
        disabled={actionDisabled || actionBusy}
        onClick={onAction}
      >
        {actionBusy ? `${actionLabel}…` : actionLabel}
      </button>
    </div>
  );
}
