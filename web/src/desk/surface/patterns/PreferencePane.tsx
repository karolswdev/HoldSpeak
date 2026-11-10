import { Children, Fragment, cloneElement, isValidElement, useId, useLayoutEffect, useRef, useState, type ReactNode, type ReactElement, type HTMLAttributes } from "react";
import { Button } from "../../../components/signal/Signal";
import { GadgetRow } from "../gadgets";
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
  const ref = useRef<HTMLDivElement>(null);
  useFormLabels(ref);
  return (
    <div
      ref={ref}
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
type PaneInspectorProps = { label: string; onClose?(): void; pendingChoice?: boolean } & (
  | { rows: readonly InspectorRow[]; completion?: InspectorCompletion; children?: never }
  | { children: ReactElement | null; rows?: never; completion?: never }
);
export function PaneInspector({ label, children, rows, completion, onClose, pendingChoice }: PaneInspectorProps) {
  const ref = useRef<HTMLElement>(null);
  const hasFields = useInspectorFields(ref);
  if (children && typeof children.type === "string") throw new Error("An inspector accepts a form, not app layout");
  const content = children?.type === GadgetRow || children?.type === Fragment ? <InspectorForm>{children}</InspectorForm> : children;
  return <section ref={ref} className="surface-pane-inspector" aria-label={label} data-pending-choice={pendingChoice || undefined}>
    <div className="surface-pane-inspector-head"><strong>{label}</strong></div>
    {rows ? <InspectorForm pendingChoice={pendingChoice} rows={rows} completion={completion ?? (onClose && (hasFields || pendingChoice) ? { done: onClose } : undefined)} />
      : <>{content}{onClose && (hasFields || pendingChoice) ? <InspectorActions completion={{ done: onClose }} /> : null}</>}
  </section>;
}
export function InspectorActions({ completion, danger = false }: { completion?: InspectorCompletion; danger?: boolean }) {
  if (!completion) return null;
  return <div className="surface-pane-actions surface-inspector-actions">
    {"done" in completion ? <Button dense variant="ghost" onClick={completion.done}>Done</Button> : <>
      <Button dense variant="ghost" autoFocus={danger} disabled={completion.cancelDisabled} data-testid={completion.cancelTestId} onClick={completion.cancel}>Cancel</Button>
      <Button dense variant={danger ? "danger" : "primary"} disabled={completion.primary.disabled} loading={completion.primary.busy} data-testid={completion.primary.testId} onClick={completion.primary.run}>{completion.primary.label}</Button>
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
export function InspectorForm({ rows = [], children, completion, notice, testId, pendingChoice }: {
  pendingChoice?: boolean;
  rows?: readonly InspectorRow[];
  /** Only GadgetRow children and conditional fragments of GadgetRow are accepted. */
  children?: ReactNode;
  completion?: InspectorCompletion;
  notice?: ReactNode;
  testId?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useFormLabels(ref);
  const hasFields = useInspectorFields(ref);
  const actions = completion && "done" in completion && !hasFields && !pendingChoice ? undefined : completion;
  return <div ref={ref} className="surface-inspector-form" data-testid={testId}>
    <div className="surface-inspector-rows">{rows.map((row) => <GadgetRow key={row.key ?? row.label} label={row.label} controlWidth="standard"><div className="surface-inspector-control">{row.control}</div></GadgetRow>)}{inspectorRows(children)}</div>
    {notice ? <div className="surface-inspector-notice">{notice}</div> : null}
    <InspectorActions completion={actions} />
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

/** Measure the form's own labels, not the viewport. Long labels stack instead
 * of wrapping; ordinary rows share the longest label's seat. */
function useFormLabels(ref: { current: HTMLDivElement | null }) {
  useLayoutEffect(() => {
    const form = ref.current;
    if (!form) return;
    const update = () => {
      const labels = [...form.querySelectorAll<HTMLElement>(".gadget-row-label")]
        .filter(label => label.closest(".surface-inspector-form, .surface-preference-pane") === form);
      const limit = Math.min(240, form.clientWidth * .55);
      let longest = 80;
      for (const label of labels) {
        const width = Math.ceil(label.scrollWidth);
        const row = label.closest<HTMLElement>(".gadget-row");
        if (width > limit) row?.setAttribute("data-label-stacked", "");
        else { row?.removeAttribute("data-label-stacked"); longest = Math.max(longest, width); }
      }
      form.style.setProperty("--surface-label-seat", `${longest}px`);
    };
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(update);
    const changes = new MutationObserver(update);
    observer?.observe(form);
    changes.observe(form, { childList: true, subtree: true, characterData: true });
    update();
    void document.fonts?.ready.then(update);
    return () => { observer?.disconnect(); changes.disconnect(); };
  }, [ref]);
}

export interface InspectorFact { label: string; value: ReactNode; key?: string }
/** Read-only values use the form's grid, without a completion row. */
export function InspectorFacts({ rows, testId, notice }: { rows: readonly InspectorFact[]; testId?: string; notice?: ReactNode }) {
  return <InspectorForm testId={testId} notice={notice} rows={rows.filter(row => hasWords(row.value)).map(row => ({ ...row, control: row.value }))} />;
}
function hasWords(value: ReactNode): boolean {
  if (value == null || typeof value === "boolean") return false;
  if (typeof value === "string") return Boolean(value.trim());
  if (Array.isArray(value)) return value.some(hasWords);
  if (isValidElement<{ children?: ReactNode }>(value) && typeof value.type === "string") return ["video", "audio", "img", "canvas"].includes(value.type) || hasWords(value.props.children);
  return true;
}

/** One in-window destructive question. Cancel owns the initial focus. */
export function InspectorQuestion({ question, keeps, consequence, cancel, verb, notice, testId, cancelTestId }: {
  question: string; keeps?: ReactNode; consequence?: ReactNode; cancel(): void;
  verb: InspectorVerb; notice?: ReactNode; testId?: string; cancelTestId?: string;
}) {
  const ref = useRef<HTMLElement>(null);
  useLayoutEffect(() => { ref.current?.querySelector<HTMLButtonElement>(".surface-inspector-actions button")?.focus(); }, []);
  return <section ref={ref} className="surface-pane-inspector" aria-label={question} data-question data-testid={testId}>
    <div className="surface-pane-inspector-head"><strong>{question}</strong></div>
    {consequence ? <div className="surface-question-consequence">{consequence}</div> : null}
    {keeps ? <div className="surface-question-keeps">Keeps · {keeps}</div> : null}
    {notice ? <div className="surface-inspector-notice">{notice}</div> : null}
    <InspectorActions danger completion={{ cancel, cancelDisabled: verb.busy, cancelTestId, primary: verb }} />
  </section>;
}

function useInspectorFields(ref: {current: HTMLElement | null}) {
  const [fields, setFields] = useState(false);
  useLayoutEffect(() => {
    const seat = ref.current;
    if (!seat) return;
    const update = () => setFields(Boolean(seat.querySelector("input,select,textarea,[role=checkbox],[role=radio],.object-list--selection")));
    update();
    const observer = new MutationObserver(update);
    observer.observe(seat, {childList:true,subtree:true});
    return () => observer.disconnect();
  }, [ref]);
  return fields;
}
