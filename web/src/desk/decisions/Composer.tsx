/* A new decision uses the same inspector form as other Desk list apps. */
import { useDeskWriteReceipt } from "../hooks/useWriteReceipt";
import { InspectorForm, PaneInspector, PadGadget, StringGadget } from "../surface";

export type NewDecisionAbout = { id: string; name: string };

export function DecisionComposer({ title, why, about, onTitle, onWhy, onCreate, onCancel, autoFocus = false, busy = false }: {
  title: string;
  why: string;
  about?: NewDecisionAbout | null;
  onTitle(next: string): void;
  onWhy(next: string): void;
  onCreate(): void;
  onCancel(): void;
  autoFocus?: boolean;
  busy?: boolean;
}) {
  return <PaneInspector label="New decision"><DecisionForm title={title} why={why} about={about}
    onTitle={onTitle} onWhy={onWhy} onCreate={onCreate} onCancel={onCancel} autoFocus={autoFocus} busy={busy} /></PaneInspector>;
}

function DecisionForm({ title, why, about, onTitle, onWhy, onCreate, onCancel, autoFocus, busy }: Parameters<typeof DecisionComposer>[0]) {
  const named = Boolean(title.trim());
  const { receipt, failure, clear } = useDeskWriteReceipt();
  const cancel = () => {
    if (failure?.verb === "CREATE DECISION") clear();
    onCancel();
  };
  return <div role="group" aria-label="New decision" data-testid="new-decision" onKeyDown={(event) => {
    if (event.key !== "Escape" || busy) return;
    event.preventDefault(); event.stopPropagation(); cancel();
  }}><InspectorForm notice={receipt} rows={[
    { label: "Decision", control: <StringGadget label="Decision title" value={title} autoFocus={autoFocus}
      disabled={busy} onChange={onTitle} placeholder="What you decided" micLabel="Speak the decision"
      inputProps={{ "data-testid": "palette-name" } as Record<string, string>}
      onKeyDown={(event) => {
        if (event.key !== "Enter" || event.nativeEvent.isComposing) return;
        event.preventDefault(); if (named && !busy) onCreate();
      }} /> },
    { label: "Why", control: <PadGadget label="Why" value={why} rows={3} disabled={busy}
      placeholder="Why (optional)" micLabel="Speak why" onChange={onWhy}
      inputProps={{ "data-testid": "decision-why" } as Record<string, string>} /> },
    ...(about ? [{ label: "Project", control: <span data-testid="decision-about-chip">{about.name}</span> }] : []),
  ]} completion={{ cancel, cancelDisabled: busy, cancelTestId: "new-decision-cancel",
    primary: { label: "Record", run: onCreate, disabled: !named || busy, busy, testId: "palette-name-save" } }} /></div>;
}
