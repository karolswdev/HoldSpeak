import type { ReactNode } from "react";
import "./inspector-figures.css";
export type InspectorFigure = { value: ReactNode; label: string; tone?: "ask" | "info" | "ok" | "fail" };
type Figures = readonly [InspectorFigure, InspectorFigure] | readonly [InspectorFigure, InspectorFigure, InspectorFigure] | readonly [InspectorFigure, InspectorFigure, InspectorFigure, InspectorFigure];
/** Two to four recap figures; names below values in visual and reading order. */
export function InspectorFigures({ figures, label }: { figures: Figures; label: string }) {
  return <dl className="surface-inspector-figures" aria-label={label}>{figures.map(figure => <div key={figure.label} data-tone={figure.tone}><dt>{typeof figure.value === "number" && figure.value === 1 ? figure.label.replace(/questions/, "question") : figure.label}</dt><dd>{figure.value}</dd></div>)}</dl>;
}
