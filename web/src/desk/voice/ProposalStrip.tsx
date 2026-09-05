import { useEffect } from "react";
import { Button } from "../../components/signal/Signal";
import { EgressChip } from "../surface/gadgets";
import type { VoiceProposal } from "./grammar";

interface ProposalStripProps {
  proposal: VoiceProposal | null;
  onConfirm: () => void;
  onCancel: () => void;
  pending: boolean;
  receipt?: { text: string; scope: string } | null;
}

const INTENT_LABELS: Record<string, string> = {
  bold: "Bold selection",
  italic: "Italicize selection",
  heading: "Make heading",
  list: "Make bullet list",
  rewrite: "Rewrite selection",
  expand: "Expand selection",
  continue: "Continue writing",
  readback: "Read selection",
  open: "Open item",
  "create-note": "Create note",
  attention: "Show attention",
};

function egressScope(scope: string): "local" | "mixed" | "cloud" {
  return scope === "cloud" || scope === "mixed" ? scope : "local";
}

/** An in-world arm/fire receipt. Enter is explicit consent; Escape disarms. */
export function VoiceProposalStrip({
  proposal,
  onConfirm,
  onCancel,
  pending,
  receipt,
}: ProposalStripProps) {
  useEffect(() => {
    if (!proposal || pending) return;
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) return;
      if (event.key === "Enter") {
        event.preventDefault();
        onConfirm();
      }
      if (event.key === "Escape") {
        event.preventDefault();
        onCancel();
      }
    };
    document.addEventListener("keydown", onKeyDown, true);
    return () => document.removeEventListener("keydown", onKeyDown, true);
  }, [proposal, pending, onConfirm, onCancel]);

  useEffect(() => {
    if (!receipt) return;
    const timer = window.setTimeout(onCancel, 3000);
    return () => window.clearTimeout(timer);
  }, [receipt, onCancel]);

  if (!proposal) return null;
  const label = pending
    ? "CLASSIFYING"
    : INTENT_LABELS[proposal.intentId] ?? proposal.intentId;

  return (
    <div className="desk-voice-proposal" role="status" aria-live="polite">
      {pending ? <span className="desk-voice-scan" aria-hidden="true" /> : null}
      <span className="desk-voice-proposal-heard">“{proposal.transcript}”</span>
      <strong className="desk-voice-proposal-action">{label}</strong>
      {proposal.requiresLLM ? (
        <EgressChip label="AI" scope="cloud" title="Intent classification used Ask AI." />
      ) : null}
      {receipt ? (
        <span className="desk-voice-proposal-action">{receipt.text}</span>
      ) : pending ? null : (
        <>
          <Button dense variant="ghost" onClick={onConfirm}>Confirm</Button>
          <Button dense variant="ghost" onClick={onCancel}>Cancel</Button>
        </>
      )}
      {receipt ? <EgressChip label={receipt.scope} scope={egressScope(receipt.scope)} /> : null}
    </div>
  );
}
