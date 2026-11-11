import { useGuideView } from "../../walk/viewState";
import { Children, Fragment, createContext, useContext, cloneElement, isValidElement, useId, useLayoutEffect, useRef, useState, type ReactNode, type ReactElement, type HTMLAttributes } from "react";
import { Button } from "../../../components/signal/Signal";
import { GadgetRow } from "../gadgets";
import { useRovingRows } from "../roving";
import "./preferences.css";
import { useGroupHeading } from "../groupHeading";
import { hasWords } from "../content";

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
const InspectorNameContext = createContext<string | null>(null);
const InspectorCompletionContext = createContext<{ completion?: InspectorCompletion; pendingChoice?: boolean }>({});
type PaneInspectorProps = { label: string; trailing?: ReactNode; nameTestId?: string; testId?: string; onClose?(): void; pendingChoice?: boolean } & (
  | { rows: readonly InspectorRow[]; completion?: InspectorCompletion; children?: never }
  | { children: ReactElement | null; rows?: never; completion?: never }
);
export function PaneInspector({ label, children, rows, completion, onClose, pendingChoice, nameTestId, testId, trailing }: PaneInspectorProps) {
  if (children && typeof children.type === "string") throw new Error("An inspector accepts a form, not app layout");
  const content = children?.type === GadgetRow || children?.type === Fragment ? <InspectorForm>{children}</InspectorForm> : children;
  return <InspectorNameContext.Provider value={label}><InspectorCompletionContext.Provider value={{ completion: onClose ? { done: onClose } : undefined, pendingChoice }}><section className="surface-pane-inspector" data-testid={testId} aria-label={label} data-pending-choice={pendingChoice || undefined}>
    <div className="surface-pane-inspector-head"><strong data-testid={nameTestId}>{label}</strong>{trailing ? <span className="surface-inspector-trailing">{trailing}</span> : null}</div>
    {rows ? <InspectorForm pendingChoice={pendingChoice} rows={rows} completion={completion} /> : content}
  </section></InspectorCompletionContext.Provider></InspectorNameContext.Provider>;
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
  const inherited = useContext(InspectorCompletionContext);
  const chosen = completion ?? inherited.completion;
  const actions = chosen && "done" in chosen && !hasFields && !pendingChoice && !inherited.pendingChoice ? undefined : chosen;
  return <div ref={ref} className="surface-inspector-form" data-testid={testId} data-completion={Boolean(actions) || undefined}>
    <div className="surface-inspector-fields">
    <div className="surface-inspector-rows">{rows.map((row) => <GadgetRow key={row.key ?? row.label} label={row.label} controlWidth="standard"><div className="surface-inspector-control">{row.control}</div></GadgetRow>)}{inspectorRows(children)}</div>
    </div>
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
  useGuideView(() => value, saved => {if(saved !== value)onChange(saved);});
  const ref = useRef<HTMLDivElement>(null);
  useRovingRows(ref, { selector: "[role=tab]" });
  useLayoutEffect(() => {
    const strip = ref.current;
    if (!strip) return;
    const showSelected = () => {
      const selected = strip.querySelector<HTMLElement>('[aria-selected="true"]');
      if (!selected) return;
      const seat = strip.getBoundingClientRect(), tab = selected.getBoundingClientRect();
      if (tab.left < seat.left) strip.scrollLeft -= seat.left - tab.left;
      else if (tab.right > seat.right) strip.scrollLeft += tab.right - seat.right;
    };
    showSelected();
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(showSelected);
    observer?.observe(strip);
    return () => observer?.disconnect();
  }, [value, tabs]);
  return (
    <>
      {tabs.length > 1 ? <div
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
      </div> : null}

      <div
        className="surface-tab-panel"
        id={`${id}-panel`}
        role="tabpanel"
        aria-labelledby={tabs.length > 1 ? `${id}-${value}` : undefined}
        aria-label={tabs.length <= 1 ? tabs[0]?.label ?? label : undefined}
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
export function InspectorFacts({ name, nameTestId, rows, testId, notice, trailing }: { name: string; trailing?: ReactNode; nameTestId?: string; rows: readonly InspectorFact[]; testId?: string; notice?: ReactNode }) {
  const heading = useContext(InspectorNameContext);
  if (heading !== name) return <PaneInspector label={name} nameTestId={nameTestId} testId={testId} trailing={trailing}><InspectorFacts name={name} rows={rows} notice={notice} /></PaneInspector>;
  return <div className="surface-inspector-facts" data-facts-name={name} data-testid={testId}><InspectorForm notice={notice}
    rows={rows.filter(row => hasWords(row.value) && factText(row.value).trim() !== name.trim()).map(row => ({ ...row, control: row.value }))} /></div>;
}
function factText(value: ReactNode): string {
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(factText).join("");
  if (isValidElement<{children?:ReactNode}>(value)) return factText(value.props.children);
  return "";
}

/** One in-window destructive question. Cancel owns the initial focus. */
export function InspectorQuestion({ question, keeps, clears, restores, keepsTestId, consequenceTestId, consequence, cancel, verb, notice, testId, cancelTestId, targetId }: {
  question: string; keeps?: readonly string[]; clears?: string; restores?: string; keepsTestId?: string; consequenceTestId?: string; consequence?: ReactNode; cancel(): void;
  verb: InspectorVerb; notice?: ReactNode; testId?: string; cancelTestId?: string;
  targetId: string | number;
}) {
  const [answer] = useState(() => ({ target: targetId, run: verb.run }));
  const current = answer.target === targetId;
  useLayoutEffect(() => { if (!current) cancel(); }, [current, cancel]);
  const ref = useRef<HTMLElement>(null);
  useLayoutEffect(() => { ref.current?.querySelector<HTMLButtonElement>(".surface-inspector-actions button")?.focus(); }, []);
  if (!current) return null;
  return <section ref={ref} className="surface-pane-inspector" aria-label={question} data-question data-testid={testId}>
    <div className="surface-pane-inspector-head"><strong>{question}</strong></div>
    {clears ? <div className="surface-question-consequence" data-testid={consequenceTestId}>Clears {clears}{restores ? ` and puts back ${restores}` : ""}.</div> : consequence ? <div className="surface-question-consequence">{consequence}</div> : null}
    {keeps?.length ? <div className="surface-question-keeps" data-testid={keepsTestId}>{new Intl.ListFormat("en", {style:"long",type:"conjunction"}).format(keeps)} {keeps.length > 1 || /s$/i.test(keeps[0]) ? "stay" : "stays"}.</div> : null}
    {notice ? <div className="surface-inspector-notice">{notice}</div> : null}
    <InspectorActions danger completion={{ cancel, cancelDisabled: verb.busy, cancelTestId, primary: { ...verb, run: answer.run } }} />
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
