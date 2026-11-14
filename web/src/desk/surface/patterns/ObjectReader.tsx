import { useRef, type ReactNode } from "react";
import { useWholeLines } from "../wholeLines";
import { ActionNotice } from "./ActionNotice";
import { InspectorFacts, type InspectorFact, type InspectorVerb } from "./PreferencePane";
import { Elapsed } from "../live/Elapsed";
import { LiveWell, type LiveLine } from "../live/LiveWell";
import { Lamp } from "../live/Lamp";
import "./object-reader.css";
/** One top-aligned reader for stored words, a running producer or its failure. */
export function ObjectReader({ label, facts = [], children, running, lines = [], failure, retry, testId, wholeLines = false }: {
  label: string; facts?: readonly InspectorFact[]; children?: ReactNode;
  running?: {start?: number | string; word?: string}; lines?: readonly LiveLine[];
  failure?: string; retry?: InspectorVerb; testId?: string; wholeLines?: boolean;
}) {
  const reading = useRef<HTMLDivElement>(null);
  useWholeLines(reading, wholeLines);
  return <section className="surface-object-reader" aria-label={label} data-testid={testId} data-feedback-redact="true">
    {facts.length ? <InspectorFacts name={label} header={false} rows={facts} /> : null}
    {running ? <div className="surface-object-running"><Lamp state="working" label={running.word ?? "Working"} /><span>{running.word ?? "Working"}</span>{running.start !== undefined ? <Elapsed start={running.start} /> : null}</div> : null}
    {running && lines.length ? <LiveWell label={label + " output"} lines={lines} working data-feedback-redact="true" /> : null}
    {failure ? <ActionNotice tone="danger" role="alert" action={retry ? {label:retry.label,onClick:retry.run,disabled:retry.disabled,busy:retry.busy} : undefined}>{failure}</ActionNotice> : null}
    {children ? <div ref={reading} className="surface-object-reading">{children}</div> : null}
  </section>;
}
