/** PHILO-14 B1 — NeedsRow, DropTarget, DragGhost.
 *
 *  NeedsRow (board A-5): a Needs-you row IS the object: its sprite (40 px),
 *  its name (primary step), one fact line, ONE lamp and its word, and the
 *  object's own verbs at the right. In a narrow `surface` the lamp falls
 *  under the name and the verbs under the row, left-aligned.
 *
 *  DropTarget and DragGhost (board A-3, for lane C3): presentation only,
 *  no drag logic. DropTarget wraps any target (a drawer's body, a bay) and
 *  lights it (`lit`: the dashed paper ring) while a drag hovers it.
 *  DragGhost is the dragged object's sprite under the pointer (fixed,
 *  aria-hidden, no pointer events). A DeskIcon lights itself with `drop`.
 */
import type { ReactNode } from "react";
import { LampGadget } from "../gadgets";
import { ProjectButton } from "../patterns/ProjectButton";
import { lampGadgetTone, objectSprite, type ObjectTone } from "./kinds";
import "./objects.css";

export interface NeedsRowProps {
  id: string;
  kind: string;
  name: string;
  /** The one fact (the question, the held call, `Sam Rivera · 1:1`). */
  fact?: string;
  lamp: { label: string; tone: ObjectTone };
  /** The object's verbs (library Buttons; one primary at most). */
  verbs?: ReactNode;
  sprite?: string;
  /** PHILO-14 A5b: the Project the object belongs to, as the library
   *  ProjectButton at the end of the fact line (`Open the Project: <name>`; a generic
   *  open, so the caller opens the Project's drawer). The caller leaves it
   *  out when the desk holds one Project (UX-CANON A.7). */
  project?: { name: string; onOpen: () => void };
}

export function NeedsRow({ id, kind, name, fact, lamp, verbs, sprite, project }: NeedsRowProps) {
  return (
    <li className="needs-row" data-object-id={id} data-kind={kind}>
      <img src={sprite ?? objectSprite(kind, id)} alt="" draggable={false} />
      <span className="needs-row-what">
        <span className="needs-row-name">{name}</span>
        {project ? (
          // The canvas names the Project on the fact line (README, Phase 14):
          // here it is the Project's own Button at the line's end.
          <span className="needs-row-factline">
            {fact ? <span className="needs-row-fact">{fact}</span> : null}
            <ProjectButton name={project.name} onOpen={project.onOpen}
              className="needs-row-project" data-testid="needs-row-project" />
          </span>
        ) : fact ? <span className="needs-row-fact">{fact}</span> : null}
      </span>
      <span className="needs-row-lamp">
        <LampGadget label={lamp.label} on tone={lampGadgetTone(lamp.tone)} />
      </span>
      {verbs ? <span className="object-verbs needs-row-verbs">{verbs}</span> : <span />}
    </li>
  );
}

/** The list the rows sit in (an `ul` with its accessible name). */
export function NeedsList({ label, children }: { label: string; children: ReactNode }) {
  return (
    <ul className="needs-list" aria-label={label}>
      {children}
    </ul>
  );
}

export function DropTarget({
  lit,
  children,
  className,
}: {
  lit: boolean;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`drop-target${className ? ` ${className}` : ""}`} data-lit={lit ? "true" : undefined}>
      {children}
    </div>
  );
}

export function DragGhost({
  kind,
  id,
  sprite,
  x,
  y,
  from,
}: {
  kind: string;
  id: string;
  sprite?: string;
  /** Viewport coordinates of the sprite's top-left corner. */
  x: number;
  y: number;
  /** PHILO-14 C3: where the drag began (viewport). Given, a dotted path is
   *  drawn from it to the ghost's centre (board A-3). */
  from?: { x: number; y: number };
}) {
  const ghost = (
    <img
      className="drag-ghost"
      src={sprite ?? objectSprite(kind, id)}
      alt=""
      aria-hidden="true"
      draggable={false}
      style={{ left: x, top: y }}
    />
  );
  if (!from) return ghost;
  return (
    <>
      <svg className="drag-path" aria-hidden="true" data-testid="drag-path">
        <line x1={from.x} y1={from.y} x2={x + 32} y2={y + 32} />
      </svg>
      {ghost}
    </>
  );
}
