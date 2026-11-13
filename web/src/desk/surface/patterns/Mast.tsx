/** The object, title, facts and figures in the shared window title band. */
import { createContext, isValidElement, useContext, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { contentText, labelCaption } from "../content";
import { fitName, textMeasure } from "../objects/fitName";
import { spriteUrl } from "../../sprites";
import "./mast.css";

export type MastProps = {
  /** The object kind ("project", "program", "meeting", ...): picks the sprite. */
  kind: string;
  title: ReactNode;
  /** Quiet short facts already read by the app. */
  facts?: ReactNode;
  figures?: readonly MastFigure[];
  /** The frame supplies its resolved object; the Mast owns its seat. */
  object?: ReactNode;
  framed?: boolean;
  /** A changing object name or greeting belongs in the frame state line. */
  stateTitle?: boolean;
  compact?: boolean;
  /** The object id, for a kind whose sprite varies by id (a zone's hue). */
  id?: string;
  /** The agent name of a coder or agent object (picks its sprite). */
  agent?: string | null;
  /** A system sprite's URL in place of the kind's (a window that is not an
   *  object kind, e.g. Needs you wears the Dock's lamp). */
  glyph?: string;
  /** The verbs: library Buttons. */
  children?: ReactNode;
  className?: string;
  "data-testid"?: string;
  [data: `data-${string}`]: string | undefined;
};

export type MastFigure = { value: ReactNode; label: string; tone?: "ask" | "stop" };
export type MastDeclaration = { glyph?: string; line?: ReactNode; figures?: readonly MastFigure[] };
export const MastSlotContext = createContext<((declaration: MastDeclaration | null) => void) | null>(null);

/** Publish already-read app facts into the one frame Mast. No host, no effect. */
export function useWindowMast(declaration: MastDeclaration, enabled = true) {
  const publish = useContext(MastSlotContext);
  const key = JSON.stringify([declaration.glyph, contentText(declaration.line), declaration.figures?.map(figure => ({...figure, value: isValidElement(figure.value) ? figure.value.props : figure.value}))]);
  useLayoutEffect(() => {
    if (!publish || !enabled) return;
    publish(declaration);
    return () => publish(null);
  }, [publish, key, enabled]);
}


export function Mast({ kind, title, facts, figures, object, framed = false, stateTitle = false, compact = false, id, agent, glyph, children, className, ...data }: MastProps) {
  const publish = useContext(MastSlotContext);
  const hosted = Boolean(publish) && !framed;
  const frameGlyph = glyph ?? spriteUrl(kind, id ?? kind, "rest", agent, 32);
  useWindowMast({line: stateTitle ? <>{title}{facts ? <> · {facts}</> : null}</> : facts, figures, glyph: frameGlyph}, hosted);
  if (hosted) return children ? <div {...data} className={`surface-mast-verbs surface-mast-inline-verbs${className ? ` ${className}` : ""}`}>{children}</div> : null;
  const visibleFigures = figures?.filter(figure => figure.value !== 0);
  return (
    <div {...data} className={`surface-mast${framed ? " surface-mast--framed" : ""}${className ? ` ${className}` : ""}`} data-kind={kind}>
      <div className="surface-mast-row">
        {object ? <span className="surface-mast-object desk-window-icon">{object}</span> : <img
          className="surface-mast-glyph"
          src={glyph ?? spriteUrl(kind, id ?? kind, "rest", agent, 32)}
          width={32}
          height={32}
          alt=""
          draggable={false}
        />}
        <div className="surface-mast-words">
          <MastText heading framed={framed} compact={compact} stateKey={contentText(facts)}>{title}</MastText>
          {facts ? <MastText framed={framed} compact={compact}>{facts}</MastText> : null}
        </div>
        {framed ? <span className="surface-mast-stripes" aria-hidden="true" /> : null}
        {visibleFigures?.length ? <dl className="surface-mast-figures">{visibleFigures.map(figure => <div key={figure.label} data-tone={figure.tone}><dt data-caption={labelCaption(figure.label)}>{figure.label}</dt><dd>{figure.value}</dd></div>)}</dl> : null}
        {children ? <div className="surface-mast-verbs">{children}</div> : null}
      </div>
    </div>
  );
}

/** The Mast keeps whole title words; the full name stays available on hover. */
function MastText({children,compact,framed,heading=false,stateKey}:{children:ReactNode;compact:boolean;framed:boolean;heading?:boolean;stateKey?:string}) {
  const ref=useRef<HTMLElement|null>(null);
  const Tag=heading ? "h2" : "p";
  const [shown,setShown]=useState<string|null>(null);
  const text = contentText(children);
  useLayoutEffect(()=>{
    const el=ref.current;
    if(!el||!text) {setShown(null);return;}
    let live=true;
    const fit=()=>{
      if(!live)return;
      const measure=textMeasure(getComputedStyle(el)),room=el.clientWidth;
      if (!measure || room <= 0) { setShown(null); return; }
      const tracking = parseFloat(getComputedStyle(el).letterSpacing) || 0;
      const fits = (text: string) => measure.width(text) + Math.max(0, text.length - 1) * tracking <= room - 1;
      if (!heading) {
        const parts = text.split(/\s*·\s*/);
        while (parts.length && !fits(parts.join(" · "))) parts.pop();
        setShown(parts.length === text.split(/\s*·\s*/).length ? null : parts.join(" · "));
        return;
      }
      // Retain the full title's natural seat while fitting its visible words.
      // The state line must not steal that width or make the fit oscillate.
      if (el.parentElement) {
        const state = el.parentElement.querySelector<HTMLElement>(".surface-mast-facts"), stateStyle = state && getComputedStyle(state);
        const stateText = state?.getAttribute("aria-label") ?? "";
        const stateWidth = stateStyle ? (textMeasure(stateStyle)?.width(stateText) ?? 0) + Math.max(0,stateText.length-1)*(parseFloat(stateStyle.letterSpacing)||0) : 0;
        el.parentElement.style.flexBasis = `${Math.ceil(Math.max(stateWidth,measure.width(text) + Math.max(0,text.length-1)*tracking))+2}px`;
      }
      setShown(fitName(text, Math.max(4, Math.floor(room / measure.average)), 1, fits, "end")[0]);
    };
    const observer=typeof ResizeObserver!=="undefined"?new ResizeObserver(fit):null;
    observer?.observe(el);fit();void document.fonts?.ready.then(fit);
    return()=>{live=false;observer?.disconnect();};
  },[text,compact,heading,stateKey]);
  return <Tag ref={(el:HTMLElement|null)=>{ref.current=el;}} className={heading ? `surface-mast-title${framed ? " desk-pullout-title desk-window-title" : ""}` : "surface-mast-facts"} title={text || undefined} aria-label={text || undefined} data-feedback-redact={typeof children !== "string" ? "true" : undefined}>{shown??children}</Tag>;
}
