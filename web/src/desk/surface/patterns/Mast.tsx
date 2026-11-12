/** The object, title, facts and figures in the shared window title band. */
import { createContext, useContext, useLayoutEffect, type ReactNode } from "react";
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

export type MastFigure = { value: string | number; label: string; tone?: "ask" };
export type MastDeclaration = { line?: string; figures?: readonly MastFigure[] };
export const MastSlotContext = createContext<((declaration: MastDeclaration | null) => void) | null>(null);

/** Publish already-read app facts into the one frame Mast. No host, no effect. */
export function useWindowMast(declaration: MastDeclaration) {
  const publish = useContext(MastSlotContext);
  const key = JSON.stringify(declaration);
  useLayoutEffect(() => {
    if (!publish) return;
    publish(JSON.parse(key) as MastDeclaration);
    return () => publish(null);
  }, [publish, key]);
}

export function Mast({ kind, title, facts, figures, object, framed = false, id, agent, glyph, children, className, ...data }: MastProps) {
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
          <h2 className={`surface-mast-title${framed ? " desk-pullout-title desk-window-title" : ""}`}>{title}</h2>
          {facts ? <p className="surface-mast-facts">{facts}</p> : null}
        </div>
        {framed ? <span className="surface-mast-stripes" aria-hidden="true" /> : null}
        {figures?.length ? <dl className="surface-mast-figures">{figures.filter(figure => figure.value !== 0).map(figure => <div key={figure.label} data-tone={figure.tone}><dt>{figure.label}</dt><dd>{figure.value}</dd></div>)}</dl> : null}
        {children ? <div className="surface-mast-verbs">{children}</div> : null}
      </div>
    </div>
  );
}
