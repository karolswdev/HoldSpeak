import type { ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { InspectorFacts, type InspectorFact, type InspectorVerb } from "./PreferencePane";
import { DotWord } from "../kit";
import { Elapsed } from "../live/Elapsed";
import { LiveWell, type LiveLine } from "../live/LiveWell";
import { Lamp } from "../live/Lamp";
import "./object-reader.css";
/** One top-aligned reader for stored words, a running producer or its failure. */
export function ObjectReader({ label, facts = [], children, running, lines = [], failure, retry, testId }: {
  label: string; facts?: readonly InspectorFact[]; children?: ReactNode;
  running?: {start?: number | string; word?: string}; lines?: readonly LiveLine[];
  failure?: string; retry?: InspectorVerb; testId?: string;
}) {
  return <section className="surface-object-reader" aria-label={label} data-testid={testId} data-feedback-redact="true">
    {facts.length ? <InspectorFacts name={label} header={false} rows={facts} /> : null}
    {running ? <div className="surface-object-running"><Lamp state="working" label={running.word ?? "Working"} /><span>{running.word ?? "Working"}</span>{running.start !== undefined ? <Elapsed start={running.start} /> : null}</div> : null}
    {running && lines.length ? <LiveWell label={label + " output"} lines={lines} working data-feedback-redact="true" /> : null}
    {failure ? <div className="surface-object-failure" role="alert"><DotWord tone="fail">{failure}</DotWord>{retry ? <Button dense variant="secondary" loading={retry.busy} disabled={retry.disabled} data-testid={retry.testId} onClick={retry.run}>{retry.label}</Button> : null}</div> : null}
    {children ? <div className="surface-object-reading">{children}</div> : null}
  </section>;
}
