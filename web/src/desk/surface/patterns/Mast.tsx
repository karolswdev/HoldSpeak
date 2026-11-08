/** Mast (the language, 2026-11-08): the head of an object face. The
 *  desk's illustrated sprite for the object kind (32 px, never a coloured
 *  block), the title in the display face, one facts line in mono and a
 *  slot for the face's verbs (library Buttons). The title steps from 24/28
 *  to 20/24 when the mast is narrow: a container query on the mast, never a
 *  viewport media query, so a narrow window at 1440 steps down too. */
import type { ReactNode } from "react";
import { spriteUrl } from "../../sprites";
import "./mast.css";

export type MastProps = {
  /** The object kind ("project", "program", "meeting", ...): picks the sprite. */
  kind: string;
  title: ReactNode;
  /** The facts line: counts, times, owners. Mono, 12 px, secondary ink. */
  facts?: ReactNode;
  /** The object id, for a kind whose sprite varies by id (a zone's hue). */
  id?: string;
  /** The agent name of a coder or agent object (picks its sprite). */
  agent?: string | null;
  /** The verbs: library Buttons. */
  children?: ReactNode;
  className?: string;
  "data-testid"?: string;
  [data: `data-${string}`]: string | undefined;
};

export function Mast({ kind, title, facts, id, agent, children, className, ...data }: MastProps) {
  return (
    <header {...data} className={className ? `surface-mast ${className}` : "surface-mast"} data-kind={kind}>
      <div className="surface-mast-row">
        <img
          className="surface-mast-glyph"
          src={spriteUrl(kind, id ?? kind, "rest", agent, 32)}
          width={32}
          height={32}
          alt=""
          draggable={false}
        />
        <div className="surface-mast-words">
          <h2 className="surface-mast-title">{title}</h2>
          {facts ? <p className="surface-mast-facts">{facts}</p> : null}
        </div>
        {children ? <div className="surface-mast-verbs">{children}</div> : null}
      </div>
    </header>
  );
}
