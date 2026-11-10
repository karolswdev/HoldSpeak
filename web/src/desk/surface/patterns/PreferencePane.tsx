import { Children, Fragment, cloneElement, isValidElement, useId, useRef, type ReactNode, type ReactElement, type HTMLAttributes } from "react";
import { Button } from "../../../components/signal/Signal";
import { CycleGadget, GadgetRow } from "../gadgets";
import { useRovingRows } from "../roving";
import "./preferences.css";
import { useGroupHeading } from "../groupHeading";

/** A window-sized column. Only its list wells scroll. */
export function PreferencePane({
  children,
  label,
  testId,
  ...props
}: HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  label: string;
  testId?: string;
}) {
  return (
    <div
      {...props}
      className="surface-preference-pane"
      aria-label={label}
      data-testid={testId}
    >
      {children}
    </div>
  );
}
export function PaneGroup({
  label,
  children,
  grow = true,
}: {
  label: string;
  children: ReactNode;
  grow?: boolean;
}) {
  const ref = useRef<HTMLElement>(null);
  const heading = useGroupHeading(ref, label);
  return (
    <section
      ref={ref}
      className="surface-pane-group"
      data-grow={grow || undefined}
      aria-label={label}
    >
      {heading ? <h3>{label}</h3> : null}
      {children}
    </section>
  );
}
export interface InspectorRow {
  label: string;
  control: ReactNode;
  key?: string;
}
export interface InspectorVerb {
  label: string;
  run(): void;
  disabled?: boolean;
  busy?: boolean;
  testId?: string;
}
export type InspectorCompletion =
  | { done: () => void }
  | { cancel: () => void; primary: InspectorVerb; cancelDisabled?: boolean; cancelTestId?: string };

/** The inspector owns its name, aligned form grid and single final action row.
 * Stateful editors use InspectorForm inside the inspector, never their own layout. */
type PaneInspectorProps = { label: string; onClose?(): void } & (
  | { rows: readonly InspectorRow[]; completion?: InspectorCompletion; children?: never }
  | { children: ReactElement | null; rows?: never; completion?: never }
);
export function PaneInspector({ label, children, rows, completion, onClose }: PaneInspectorProps) {
  if (children && typeof children.type === "string") throw new Error("An inspector accepts a form, not app layout");
  const content = children?.type === GadgetRow || children?.type === Fragment ? <InspectorForm>{children}</InspectorForm> : children;
  return <section className="surface-pane-inspector" aria-label={label}>
    <div className="surface-pane-inspector-head"><strong>{label}</strong></div>
    {rows ? <InspectorForm rows={rows} completion={completion ?? (onClose ? { done: onClose } : undefined)} />
      : <>{content}{onClose ? <InspectorActions completion={{ done: onClose }} /> : null}</>}
  </section>;
}
export function InspectorActions({ completion }: { completion?: InspectorCompletion }) {
  if (!completion) return null;
  return <div className="surface-pane-actions surface-inspector-actions">
    {"done" in completion ? <Button dense variant="ghost" onClick={completion.done}>Done</Button> : <>
      <Button dense variant="ghost" disabled={completion.cancelDisabled} data-testid={completion.cancelTestId} onClick={completion.cancel}>Cancel</Button>
      <Button dense variant="primary" disabled={completion.primary.disabled} loading={completion.primary.busy} data-testid={completion.primary.testId} onClick={completion.primary.run}>{completion.primary.label}</Button>
    </>}
  </div>;
}
function inspectorRows(children: ReactNode, prefix = ""): ReactNode[] {
  return Children.toArray(children).flatMap((child) => {
    if (!isValidElement<{ children?: ReactNode }>(child)) throw new Error("An inspector form accepts only GadgetRow children");
    if (child.type === Fragment) return inspectorRows(child.props.children, `${prefix}${child.key}/`);
    if (child.type !== GadgetRow) throw new Error("An inspector form accepts only GadgetRow children");
    return [cloneElement(child, { key: `${prefix}${child.key}` }, <div className="surface-inspector-control">{child.props.children}</div>)];
  });
}
export function InspectorForm({ rows = [], children, completion, notice, testId }: {
  rows?: readonly InspectorRow[];
  /** Only GadgetRow children and conditional fragments of GadgetRow are accepted. */
  children?: ReactNode;
  completion?: InspectorCompletion;
  notice?: ReactNode;
  testId?: string;
}) {
  return <div className="surface-inspector-form" data-testid={testId}>
    <div className="surface-inspector-rows">{rows.map((row) => <GadgetRow key={row.key ?? row.label} label={row.label} controlWidth="standard"><div className="surface-inspector-control">{row.control}</div></GadgetRow>)}{inspectorRows(children)}</div>
    {notice ? <div className="surface-inspector-notice">{notice}</div> : null}
    <InspectorActions completion={completion} />
  </div>;
}
export function PaneActions({ children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div {...props} className="surface-pane-actions">{children}</div>;
}
export function SegmentedTabs({
  label,
  value,
  onChange,
  tabs,
  children,
}: {
  label: string;
  value: string;
  onChange(id: string): void;
  tabs: readonly { id: string; label: string }[];
  children: ReactNode;
}) {
  const id = useId();
  const ref = useRef<HTMLDivElement>(null);
  useRovingRows(ref, { selector: "[role=tab]" });
  return (
    <>
      <div
        className="surface-segmented-tabs"
        data-many={tabs.length > 4 || undefined}
        role="tablist"
        data-joined-controls
        aria-label={label}
        ref={ref}
        onKeyDown={(event) => {
          if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
          event.preventDefault();
          const at = tabs.findIndex((tab) => tab.id === value);
          const next =
            tabs[
              (at + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) %
                tabs.length
            ];
          onChange(next.id);
          ref.current
            ?.querySelector<HTMLElement>(`[data-tab="${next.id}"]`)
            ?.focus();
        }}
      >
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant="chrome"
            role="tab"
            id={`${id}-${tab.id}`}
            data-tab={tab.id}
            aria-selected={value === tab.id}
            aria-controls={`${id}-panel`}
            tabIndex={value === tab.id ? 0 : -1}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </Button>
        ))}
      </div>
      {tabs.length > 4 ? <div className="surface-tab-choice"><CycleGadget label={`${label} tab`} value={value} onChange={onChange} options={tabs.map((tab) => ({value: tab.id, label: tab.label}))} /></div> : null}
      <div
        className="surface-tab-panel"
        id={`${id}-panel`}
        role="tabpanel"
        aria-labelledby={`${id}-${value}`}
      >
        {children}
      </div>
    </>
  );
}

/** Long form groups scroll inside their tab, never the preference window. */
export function PreferenceWell({ children }: { children: ReactNode }) { return <div className="surface-preference-well">{children}</div>; }
