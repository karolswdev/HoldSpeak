/** PHILO-14 B1 — NeedsRow, DropTarget, DragGhost.
 *
 *  NeedsRow (board A-5): a Needs-you row IS the object: its sprite (the
 *  32 px set drawn at 32, PHILO-14 A0c, in the 40 px cell),
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
import { AgentWords } from "../../components/AgentWords";
import { ProjectButton } from "../patterns/ProjectButton";
import { DotWord, KindPlate } from "../kit";
import { listSprite } from "../../sprites";
import { lampGadgetTone, objectSprite, type ObjectTone } from "./kinds";
import "./objects.css";

export interface NeedsRowProps {
  id: string;
  kind: string;
  name: string;
  /** The one fact (the question, the held call, `Sam Rivera · 1:1`). */
  fact?: string;
  /** W6-H words: the raw reason behind a failure fact, for the hover only. */
  factTitle?: string;
  /** The fact is a command (a held call): lines kept, mono, wraps. */
  factCode?: boolean;
  /** Phase 16: the fact is an agent's words: AgentWords, compact, two
   *  lines, cut at a whole word. */
  factWords?: boolean;
  lamp: { label: string; tone: ObjectTone };
  /** The object's verbs (library Buttons; one primary at most). */
  verbs?: ReactNode;
  sprite?: string;
  /** PHILO-14 A5b: the Project the object belongs to, as the library
   *  ProjectButton at the end of the fact line (`Open the Project: <name>`; a generic
   *  open, so the caller opens the Project's drawer). The caller leaves it
   *  out when the desk holds one Project (UX-CANON A.7). */
  project?: { name: string; onOpen: () => void };
  /** PHILO-15-09 (B12): what the object is, in one word at the head of
   *  the fact line (`DECISION`, `ACTION`, `PROPOSAL`, `MEETING`, `AGENT`). */
  kindWord?: string;
  /** Phase 16 (the interior kit, the Ledger's kind plate): the row's kind
   *  as a raised Steel plate (`CC`, `DEC`, `ACT`) in place of the sprite.
   *  The kind word moves into the plate's title; the fact line keeps it. */
  plate?: string;
  /** Window grammar (2026-10-24): with no plate the row leads with its
   *  glyph; this word names what the glyph shows (its alt and title). */
  glyphLabel?: string;
  /** Window grammar (2026-10-24): the state is a DotWord (an 8 px dot and
   *  a sentence-case word) in place of the lamp gadget, the Project's name
   *  keeps its own case, and in a narrow surface the state and the fact
   *  fold under the name so the row stays one 44 px line pair. */
  dotState?: boolean;
}

export const KEEP_CAPS = new Set(["PR", "CI", "AI", "ID", "OK", "LAN", "MCP", "API", "CLI", "URL", "PDF", "ADR", "UI"]);

/** A wire state word in sentence case, per ` · ` part: the part's first
 *  word keeps a capital, every later ALL-CAPS word of three letters or
 *  more is lower case; mixed-case words (names), acronyms (`PR`, `CI`,
 *  `LAN`), numbers, times and ids stay as they are (`OVERDUE · 23 DAYS` →
 *  `Overdue · 23 days`, `PR OPEN` → `PR open`, `PROPOSED · Standup` →
 *  `Proposed · Standup`). */
export function stateWords(label: string): string {
  return label
    .split(" · ")
    .map((part) => {
      let first = true;
      let afterLink = false;
      return part.replace(/[^\s]+/g, (word) => {
        const lead = first;
        const named = afterLink && !COMMON_AFTER_LINK.has(word);
        first = false;
        afterLink = LINK_WORDS.has(word);
        if (!/^[A-Z][A-Z'’-]+$/.test(word) || KEEP_CAPS.has(word)) return word;
        // `WAITING ON PRIYA`: the word after a link word is a name; it keeps
        // its capital (`Waiting on Priya`, `Waiting on your review`).
        return lead || named ? word.charAt(0) + word.slice(1).toLowerCase() : word.toLowerCase();
      });
    })
    .join(" · ");
}
const LINK_WORDS = new Set(["ON", "FOR", "WITH", "BY", "FROM"]);
const COMMON_AFTER_LINK = new Set(["YOUR", "YOU", "THE", "A", "AN", "IT", "THIS", "THAT", "ME", "HIM", "HER", "THEM", "REVIEW", "TRACK", "HOLD", "TIME"]);

export function NeedsRow({ id, kind, name, fact, factTitle, factCode, factWords, lamp, verbs, sprite, project, kindWord, plate, glyphLabel, dotState }: NeedsRowProps) {
  const factClass = factCode ? "needs-row-fact is-code" : "needs-row-fact";
  const factNode = !fact ? null : factWords && !factCode ? (
    <AgentWords compact lines={2} className="needs-row-fact needs-row-words" text={fact} />
  ) : (
    <span className={factClass} title={factTitle || undefined}>{fact}</span>
  );
  return (
    <li className="needs-row" data-object-id={id} data-kind={kind} data-plate={plate ? "true" : undefined}
      data-dot={dotState ? "true" : undefined}>
      {plate ? (
        <KindPlate kind={plate} title={kindWord} />
      ) : (
        <img src={listSprite(sprite ?? objectSprite(kind, id))} alt={glyphLabel ?? ""} title={glyphLabel} draggable={false} />
      )}
      <span className="needs-row-what">
        <span className="needs-row-name">{name}</span>
        {project || kindWord ? (
          // The canvas names the Project on the fact line (README, Phase 14):
          // here it is the Project's own Button at the line's end. The kind
          // word leads the line (PHILO-15-09).
          <span className="needs-row-factline">
            {kindWord ? (
              <span className="surface-token needs-row-kind" data-testid="needs-row-kind">{kindWord}</span>
            ) : null}
            {factNode}
            {project ? (
              <ProjectButton name={project.name} onOpen={project.onOpen} plain={dotState}
                className="needs-row-project" data-testid="needs-row-project" />
            ) : null}
          </span>
        ) : factNode}
      </span>
      <span className="needs-row-lamp">
        {dotState ? (
          <DotWord tone={lamp.tone} data-testid="needs-row-state">{stateWords(lamp.label)}</DotWord>
        ) : (
          <LampGadget label={lamp.label} on tone={lampGadgetTone(lamp.tone)} />
        )}
      </span>
      {verbs ? <span className="object-verbs needs-row-verbs">{verbs}</span> : <span />}
    </li>
  );
}

/** The list the rows sit in (an `ul` with its accessible name). Phase 16:
 *  the kit's Ledger well (sunken paper; objects.css). */
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
