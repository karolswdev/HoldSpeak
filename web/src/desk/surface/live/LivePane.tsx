import type { ReactNode } from "react";
import {
  PaneInspector,
  PreferenceWell,
  InspectorFacts,
  type InspectorFact,
} from "../patterns/PreferencePane";
import "./live-pane.css";

/** A running object's reading well, facts and answer share one bounded seat.
 * Facts and the question keep their intrinsic height; only the well yields. */
type LiveContentProps = { label: string; well?: ReactNode; figures?: ReactNode; facts: readonly InspectorFact[]; question?: ReactNode };
export function LivePane({ label, trailing, ...content }: LiveContentProps & { trailing?: ReactNode }) {
  return <PaneInspector label={label} trailing={trailing}><LiveContent label={label} {...content} /></PaneInspector>;
}
function LiveContent({ label, well, figures, facts, question }: LiveContentProps) {
  return (
    <div className="surface-live-content">
      {figures}
      <PreferenceWell fit="reading">
        {well ? <div className="surface-live-reading">{well}</div> : null}
        <InspectorFacts data-feedback-redact="true" name={label} rows={facts} />
      </PreferenceWell>
      {question ? <div className="surface-live-answer">{question}</div> : null}
    </div>
  );
}
