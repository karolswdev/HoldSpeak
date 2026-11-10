import type { ReactNode } from "react";
import "./list-pane.css";

/** A bounded list with a plain reading well below it, at every width. */
export function ListPane({ list, children, label, listTestId, previewTestId }: { list: ReactNode; children: ReactNode; label: string; listTestId?: string; previewTestId?: string }) {
  return <div className="surface-list-pane"><div className="surface-list-pane-list" data-testid={listTestId}>{list}</div>
    <section className="surface-list-pane-preview" data-testid={previewTestId} aria-label={label}>{children}</section></div>;
}
