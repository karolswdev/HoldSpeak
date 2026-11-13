import { MiddleText } from "../MiddleText";
import { VerbRow } from "../VerbRow";
import { useWholeLines } from "../wholeLines";
import { InspectorFigures } from "../live/InspectorFigures";
import { useGuideView } from "../../walk/viewState";
import { Children, Fragment, createContext, useContext, cloneElement, isValidElement, useId, useLayoutEffect, useRef, useState, type ReactNode, type ReactElement, type HTMLAttributes } from "react";
import { WorkMenu } from "../../components/DeskMenu";
import { fitStrip } from "../fitStrip";
import { Button } from "../../../components/signal/Signal";
import { GadgetRow } from "../gadgets";
import { useRovingRows } from "../roving";
import "./preferences.css";
import { useGroupHeading } from "../groupHeading";
import { hasWords, labelCaption } from "../content";

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
  dispatching?: boolean;
  testId?: string;
}
export type InspectorCompletion = ({ leading?: ReactNode; state?: ReactNode } & (
  | { done: () => void }
  | { cancel: () => void; primary: InspectorVerb; cancelDisabled?: boolean; cancelTestId?: string }));

/** The inspector owns its name, aligned form grid and single final action row.
 * Stateful editors use InspectorForm inside the inspector, never their own layout. */
const InspectorNameContext = createContext<string | null>(null);
const InspectorCompletionContext = createContext<{ completion?: InspectorCompletion; pendingChoice?: boolean }>({});
type PaneInspectorProps = { subtitle?: string; object?: ReactNode; label: string; trailing?: ReactNode; nameTestId?: string; testId?: string; onClose?(): void; pendingChoice?: boolean } & (
  | { rows: readonly InspectorRow[]; completion?: InspectorCompletion; children?: never }
  | { children: ReactElement | null; rows?: never; completion?: never }
);
export function PaneInspector({ label, children, rows, completion, onClose, pendingChoice, nameTestId, testId, trailing, object, subtitle }: PaneInspectorProps) {
  if (children && typeof children.type === "string") throw new Error("An inspector accepts a form, not app layout");
  const content = children?.type === GadgetRow || children?.type === Fragment ? <InspectorForm>{children}</InspectorForm> : children;
  return <InspectorNameContext.Provider value={label}><InspectorCompletionContext.Provider value={{ completion: onClose ? { done: onClose } : undefined, pendingChoice }}><section className="surface-pane-inspector" data-testid={testId} aria-label={label} data-pending-choice={pendingChoice || undefined}>
    <div className="surface-pane-inspector-head">{object ? <span className="surface-inspector-object" aria-hidden="true">{object}</span> : null}<div className="surface-inspector-heading"><strong data-testid={nameTestId}><MiddleText className="surface-inspector-name" value={label} lines={2} cut="end" /></strong>{subtitle ? <span className="surface-inspector-subtitle" data-caption={labelCaption(subtitle)}>{subtitle}</span> : null}</div>{trailing ? <span className="surface-inspector-trailing">{trailing}</span> : null}</div>
    {rows ? <InspectorForm pendingChoice={pendingChoice} rows={rows} completion={completion} /> : content}
  </section></InspectorCompletionContext.Provider></InspectorNameContext.Provider>;
}
export function InspectorActions({ completion, danger = false, cancelLabel = "Cancel", variant, focusSafe = danger }: { focusSafe?: boolean; completion?: InspectorCompletion; danger?: boolean; cancelLabel?: string; variant?: "brass" | "danger" | "primary" | "secondary" }) {
  const ref = useRef<HTMLDivElement>(null);
  useLayoutEffect(()=>{
    const safe=ref.current?.querySelector<HTMLButtonElement>("button[data-safe-answer]:not(:disabled)");
    if(!focusSafe || !safe)return;
    const focus=()=>{safe.dataset.questionFocus="";safe.focus({preventScroll:true});};
    focus(); const frame=requestAnimationFrame(focus);
    const clear=()=>safe.removeAttribute("data-question-focus");safe.addEventListener("blur",clear);
    return()=>{cancelAnimationFrame(frame);clear();safe.removeEventListener("blur",clear);};
  },[focusSafe, completion && "cancel" in completion ? completion.cancelDisabled : false]);
  if (!completion) return null;
  return <VerbRow as="div" nodeRef={ref} className="surface-pane-actions surface-inspector-actions" data-cancel-label={cancelLabel}>
    {completion.state ? <span className="surface-completion-state">{completion.state}</span> : null}
    {completion.leading ? <span className="surface-completion-leading">{completion.leading}</span> : null}
    {"done" in completion ? <Button dense variant="secondary" onClick={completion.done}>Done</Button> : <>
      <Button dense variant="secondary" data-safe-answer autoFocus={focusSafe} disabled={completion.cancelDisabled} data-testid={completion.cancelTestId} onClick={completion.cancel}>{cancelLabel}</Button>
      <Button dense variant={variant ?? (danger ? "danger" : "primary")} dispatching={completion.primary.dispatching} disabled={completion.primary.disabled} loading={completion.primary.busy} data-testid={completion.primary.testId} onClick={completion.primary.run}>{completion.primary.label}</Button>
    </>}
  </VerbRow>;
}
function inspectorRows(children: ReactNode, prefix = ""): ReactNode[] {
  return Children.toArray(children).flatMap((child) => {
    if (!isValidElement<{ children?: ReactNode }>(child)) throw new Error("An inspector form accepts only GadgetRow children");
    if (child.type === Fragment) return inspectorRows(child.props.children, `${prefix}${child.key}/`);
    if (child.type !== GadgetRow) throw new Error("An inspector form accepts only GadgetRow children");
    return [cloneElement(child, { key: `${prefix}${child.key}` }, <div className="surface-inspector-control">{child.props.children}</div>)];
  });
}
export function InspectorForm({ rows = [], children, completion, notice, testId, pendingChoice, facts, fit, wholeRows = false }: {
  /** A bounded row editor ends its field well at a complete row. */
  wholeRows?: boolean;
  /** Short standalone forms keep completion directly after their rows. */
  fit?: "rows";
  /** Stored values share the editor's scroll well and completion seat. */
  facts?: { name: string; rows: readonly InspectorFact[]; testId?: string; "data-feedback-redact"?: boolean };
  pendingChoice?: boolean;
  rows?: readonly InspectorRow[];
  /** Only GadgetRow children and conditional fragments of GadgetRow are accepted. */
  children?: ReactNode;
  completion?: InspectorCompletion;
  notice?: ReactNode;
  testId?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const fieldsRef = useRef<HTMLDivElement>(null);
  useWholeLines(fieldsRef, wholeRows, ":scope > .surface-inspector-rows > .gadget-row");
  useFormLabels(ref);
  const hasFields = useInspectorFields(ref);
  const layout = [...rows.map(row => row.key ?? row.label), ...(facts?.rows.map(row => row.key ?? row.label) ?? [])].join("\0");
  useLayoutEffect(() => {
    const fields = ref.current?.querySelector<HTMLElement>(":scope > .surface-inspector-fields");
    if (fields) fields.scrollTop = 0;
  }, [layout]);
  const inherited = useContext(InspectorCompletionContext);
  const chosen = completion ?? inherited.completion;
  const actions = chosen && "done" in chosen && !hasFields && !pendingChoice && !inherited.pendingChoice ? undefined : chosen;
  return <div ref={ref} className="surface-inspector-form" data-testid={testId} data-fit={fit} data-completion={Boolean(actions) || undefined} onKeyDown={event=>{if(event.key!=="Escape" || event.defaultPrevented || !actions || !("cancel" in actions))return;event.preventDefault();event.stopPropagation();if(!actions.cancelDisabled && !actions.primary.busy)actions.cancel();}}>
    <div ref={fieldsRef} className="surface-inspector-fields">
    {facts ? <InspectorFacts {...facts} header={false} /> : null}
    <div className="surface-inspector-rows">{rows.map((row) => <GadgetRow key={row.key ?? row.label} label={row.label} controlWidth="standard"><div className="surface-inspector-control">{row.control}</div></GadgetRow>)}{inspectorRows(children)}</div>
    </div>
    {notice ? <div className="surface-inspector-notice">{notice}</div> : null}
    <InspectorActions completion={actions} />
  </div>;
}
export function PaneActions({ children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <VerbRow {...props} as="div" className="surface-pane-actions">{children}</VerbRow>;
}
export function SegmentedTabs({label, value, onChange, tabs, children, showSingle = false}: {
  label: string; value: string; onChange(id: string): void;
  tabs: readonly { id: string; label: string }[]; children: ReactNode; showSingle?: boolean;
}) {
  const id = useId(), ref = useRef<HTMLDivElement>(null), probe = useRef<HTMLSpanElement>(null), anchor = useRef<HTMLButtonElement>(null);
  const signature = tabs.map(tab=>tab.id+tab.label).join("|");
  const [fitting, setFitting] = useState({signature, shown:tabs.map((_,i)=>i)}), [open, setOpen] = useState(false);
  const shown = fitting.signature === signature ? fitting.shown : tabs.map((_,i)=>i);
  const keyFocus = useRef(false);
  useGuideView(()=>value,saved=>{if(saved!==value)onChange(saved);});
  useLayoutEffect(()=>{
    const strip=ref.current, measure=probe.current;
    if(!strip||!measure)return;
    const fit=()=>{
      if(!strip.isConnected || !strip.parentElement)return;
      const sizes=Array.from(measure.children).map(node=>node.getBoundingClientRect().width);
      const more=sizes.pop()||0;
      const host = strip.parentElement!, style = getComputedStyle(host), own = getComputedStyle(strip);
      const inset = [style.paddingLeft,style.paddingRight,own.marginLeft,own.marginRight,own.paddingLeft,own.paddingRight,own.borderLeftWidth,own.borderRightWidth].reduce((sum,value)=>sum+(parseFloat(value)||0),0);
      setFitting({signature,shown:fitStrip(host.getBoundingClientRect().width-inset,sizes,more,parseFloat(own.gap)||0,tabs.findIndex(tab=>tab.id===value))});
    };
    fit(); const observer=typeof ResizeObserver === "undefined"?null:new ResizeObserver(fit);
    observer?.observe(strip.parentElement!); void document.fonts?.ready.then(fit); return ()=>observer?.disconnect();
  },[value,signature]);
  useLayoutEffect(()=>{if(keyFocus.current){const tab=ref.current?.querySelector<HTMLElement>('[aria-selected="true"]');if(tab){tab.focus();keyFocus.current=false;}}},[shown,value]);
  const folded=tabs.filter((_,i)=>!shown.includes(i)), rect=open?anchor.current?.getBoundingClientRect():null;
  return <>
    {tabs.length>1||showSingle ? <div className="surface-segmented-tabs" role="tablist" data-joined-controls aria-label={label} ref={ref} onKeyDown={event=>{
      if(!["ArrowLeft","ArrowRight","Home","End"].includes(event.key))return;
      event.preventDefault(); const at=tabs.findIndex(tab=>tab.id===value);
      const next=event.key==="Home"?0:event.key==="End"?tabs.length-1:(at+(event.key==="ArrowRight"?1:-1)+tabs.length)%tabs.length;
      keyFocus.current=true;onChange(tabs[next].id);
    }}>
      {tabs.filter((_,i)=>shown.includes(i)).map(tab=><Button key={tab.id} variant="chrome" role="tab" id={`${id}-${tab.id}`} data-tab={tab.id} aria-selected={value===tab.id} aria-controls={`${id}-panel`} tabIndex={value===tab.id?0:-1} onClick={()=>onChange(tab.id)}>{tab.label}</Button>)}
      {folded.length ? <Button variant="chrome" ref={anchor} aria-label={`${label} more`} aria-haspopup="menu" aria-expanded={open} onClick={()=>setOpen(!open)}>More ▾</Button>:null}
      <span ref={probe} className="surface-tabs-measure" aria-hidden="true" inert>{tabs.map(tab=><Button key={tab.id} variant="chrome" tabIndex={-1}>{tab.label}</Button>)}<Button variant="chrome" tabIndex={-1}>More ▾</Button></span>
      {rect?<WorkMenu label={`${label} more`} x={rect.left} y={rect.bottom} opener={anchor.current} autoFocus onClose={()=>setOpen(false)} returnFocus={()=>ref.current?.querySelector<HTMLElement>('[aria-selected="true"]')?.focus()}
        entries={folded.map(tab=>({type:"item",id:tab.id,label:tab.label,onSelect:()=>onChange(tab.id)}))}/>:null}
    </div>:null}
    <div className="surface-tab-panel" id={`${id}-panel`} role="tabpanel" aria-label={tabs.find(tab=>tab.id===value)?.label}>{children}</div>
  </>;
}

/** A reading well follows short text, yields for long text and ends on a whole line. */
export function PreferenceWell({ children, fit }: { children: ReactNode; fit?: "reading" }) {
  const ref = useRef<HTMLDivElement>(null), content = useRef<HTMLDivElement>(null);
  useWholeLines(ref, fit === "reading");
  useLayoutEffect(() => {
    const well = ref.current, words = content.current, host = well?.parentElement;
    if (!well || !words || !host || fit !== "reading") return;
    const size = () => {
      const style = getComputedStyle(host), gap = parseFloat(style.rowGap) || 0;
      const siblings = [...host.children].filter(child => child !== well && getComputedStyle(child).display !== "none");
      const inset = (parseFloat(style.paddingTop) || 0) + (parseFloat(style.paddingBottom) || 0);
      const available = Math.max(0, host.clientHeight - inset - siblings.reduce((sum, child) => sum + child.getBoundingClientRect().height, 0) - gap * siblings.length);
      const natural = words.scrollHeight;
      let height = Math.min(natural, available);
      const top = well.getBoundingClientRect().top;
      for (const row of words.querySelectorAll<HTMLElement>(".gadget-row")) {
        const box = row.getBoundingClientRect();
        if (box.top < top + height && box.bottom > top + height) height = Math.max(0, box.top - top);
      }
      well.style.height = `${Math.max(0, height)}px`;
    };
    size();
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(size);
    observer?.observe(host); observer?.observe(words);
    for (const child of host.children) if (child !== well) observer?.observe(child);
    void document.fonts?.ready.then(size);
    return () => observer?.disconnect();
  }, [fit, children]);
  return <div ref={ref} className="surface-preference-well" data-fit={fit}>{fit ? <div ref={content} className="surface-reading-content">{children}</div> : children}</div>;
}

/** Measure the form's own labels, not the viewport. Long labels stack instead
 * of wrapping; ordinary rows share the longest label's seat. */
function useFormLabels(ref: { current: HTMLDivElement | null }) {
  useLayoutEffect(() => {
    const form = ref.current;
    if (!form) return;
    form.setAttribute("data-label-seat", "");
    const update = () => {
      const labels = [...form.querySelectorAll<HTMLElement>(".gadget-row-label")]
        .filter(label => label.closest("[data-label-seat]") === form);
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
    changes.observe(form, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["hidden"] });
    update();
    void document.fonts?.ready.then(update);
    return () => { observer?.disconnect(); changes.disconnect(); form.removeAttribute("data-label-seat"); };
  }, [ref]);
}

export interface InspectorFact { label: string; value: ReactNode; key?: string }
/** Read-only values use the form's grid, without a completion row. */
export function InspectorFacts({ name, nameTestId, rows, testId, notice, trailing, header = true, figures, subtitle, "data-feedback-redact": redact }: { figures?: Parameters<typeof InspectorFigures>[0]["figures"]; subtitle?: string; "data-feedback-redact"?: boolean | "true" | "false"; header?: boolean; name: string; trailing?: ReactNode; nameTestId?: string; rows: readonly InspectorFact[]; testId?: string; notice?: ReactNode }) {
  const heading = useContext(InspectorNameContext);
  if (header && heading !== name) return <PaneInspector object={name.trim().split(/\s+/).slice(0,2).map(word => word[0]).join("")} label={name} subtitle={subtitle} nameTestId={nameTestId} testId={testId} trailing={trailing}><InspectorFacts name={name} rows={rows} figures={figures} notice={notice} data-feedback-redact={redact} /></PaneInspector>;
  return <div className="surface-inspector-facts" data-feedback-redact={redact} role={header ? undefined : "region"} aria-label={header ? undefined : name} data-headerless={!header || undefined} data-facts-name={name} data-testid={testId}>{figures ? <InspectorFigures figures={figures} label={name} /> : null}<InspectorForm notice={notice}
    rows={rows.filter(row => hasWords(row.value) && (row.label === "Name" || factText(row.value).trim() !== name.trim())).map(row => ({ ...row, control: row.value }))} /></div>;
}
function factText(value: ReactNode): string {
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(factText).join("");
  if (isValidElement<{children?:ReactNode}>(value)) return factText(value.props.children);
  return "";
}

/** One in-window destructive question. Cancel owns the initial focus. */
export function InspectorQuestion({ question, keeps, clears, restores, keepsTestId, consequenceTestId, consequence, cancel, verb, notice, testId, cancelTestId, targetId, cancelLabel, variant, onDisarm, rows, leading, actionId }: {
  question: string; keeps?: readonly string[]; clears?: string; restores?: string; keepsTestId?: string; consequenceTestId?: string; consequence?: ReactNode; cancel(): void;
  verb: InspectorVerb; notice?: ReactNode; testId?: string; cancelTestId?: string;
  targetId: string | number;
  leading?: ReactNode; actionId: string;
  rows?: readonly InspectorRow[]; onDisarm?(): void; cancelLabel?: string; variant?: "brass" | "danger" | "primary";
}) {
  const [answer] = useState(() => ({ target: targetId, action: actionId, run: verb.run }));
  const current = answer.target === targetId && answer.action === actionId;
  useLayoutEffect(() => { if (!current) (onDisarm ?? cancel)(); }, [current, cancel, onDisarm]);
  const ref = useRef<HTMLElement>(null);
  if (!current) return null;
  return <section ref={ref} className="surface-pane-inspector" aria-label={question} data-question data-testid={testId}>
    <div className="surface-pane-inspector-head"><strong>{question}</strong></div>
    {clears ? <div className="surface-question-consequence" data-testid={consequenceTestId}>Clears {clears}{restores ? ` and puts back ${restores}` : ""}.</div> : consequence ? <div className="surface-question-consequence">{consequence}</div> : null}
    {keeps?.length ? <div className="surface-question-keeps" data-testid={keepsTestId}>{new Intl.ListFormat("en", {style:"long",type:"conjunction"}).format(keeps)} {keeps.length > 1 || /s$/i.test(keeps[0]) ? "stay" : "stays"}.</div> : null}
    {rows?.length ? <InspectorForm rows={rows} /> : null}
    {notice ? <div className="surface-inspector-notice">{notice}</div> : null}
    <InspectorActions danger cancelLabel={cancelLabel} variant={variant} completion={{ leading, cancel, cancelDisabled: verb.busy, cancelTestId, primary: { ...verb, run: answer.run } }} />
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

/** A plain in-pane state or refusal; the window status keeps its counts. */
export const PaneNoticeContext = createContext<ReactNode>(null);
export function PaneNotice({children}: {children: ReactNode}) { return <div className="surface-pane-notice" role="status">{children}</div>; }

/** A bounded composition of kit facts, figures, forms and notices. */
export function InspectorBody({children, fit}:{children:ReactNode; fit?: "rows" | "reading"}) { return <div className="surface-inspector-body" data-fit={fit}>{children}</div>; }
