import type { ReactNode } from "react";
import {
  PaneInspector,
  InspectorFacts,
  type InspectorFact,
} from "../patterns/PreferencePane";
import "./live-pane.css";

/** A running object's reading well, facts and answer share one bounded seat.
 * Facts and the question keep their intrinsic height; only the well yields. */
export function LivePane({
  label,
  trailing,
  well,
  figures,
  facts,
  question,
}: {
  label: string;
  trailing?: ReactNode;
  well?: ReactNode;
  figures?: ReactNode;
  facts: readonly InspectorFact[];
  question?: ReactNode;
}) {
  return (
    <PaneInspector label={label} trailing={trailing}>
      <LiveContent
        label={label}
        well={well}
        figures={figures}
        facts={facts}
        question={question}
      />
    </PaneInspector>
  );
}
function LiveContent({
  label,
  well,
  figures,
  facts,
  question,
}: {
  label: string;
  well?: ReactNode;
  figures?: ReactNode;
  facts: readonly InspectorFact[];
  question?: ReactNode;
}) {
  return (
    <div className="surface-live-content">
      {figures}
      {well ? <div className="surface-live-reading">{well}</div> : null}
      <InspectorFacts data-feedback-redact="true" name={label} rows={facts} />
      {question ? <div className="surface-live-answer">{question}</div> : null}
    </div>
  );
}
