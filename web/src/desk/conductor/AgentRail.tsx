/* The rail of agents (the language, 2026-11-08; the Programs rail is the
 * pattern): the left edge of the Agents window. "Start an agent" at the
 * top, then one tile per agent in its group: Needs you, Running, Ended
 * today, On this Mac. A tile is the provider's sprite, what the agent
 * works on (the item, the Program step), its state in a word and a 4 px
 * spine in the meaning colours (brass waits on you, steel works, moss
 * done, coral at risk, graphite ended). The picked tile is ringed. ↑ and ↓
 * (← and → on the phone strip) move the focus; Enter picks. At 393 the
 * rail is a strip of sprite tiles at the window's foot (conductor.css). */
import { useRef, type CSSProperties, type KeyboardEvent } from "react";
import { Button } from "../../components/signal/Signal";
import { ToolGlyph } from "../surface";
import { Spine } from "../surface/patterns/Spine";
import { listSprite } from "../sprites";
import { agentWord, memberTitle, spineTone } from "./AgentPane";
import type { ConductorMember } from "./members";

export interface RailSection {
  id: "asks" | "running" | "ended" | "installed";
  word: string;
  rows: Array<{ member: ConductorMember; group: string; helperOf?: string }>;
}

function Tile({ member, group, helperOf, picked, pill, onPick }: {
  member: ConductorMember; group: string; helperOf?: string; picked: boolean;
  pill: { word: string }; onPick(id: string): void;
}) {
  const title = memberTitle(member);
  const tone = spineTone(member);
  const sub = helperOf ? `Helper of ${helperOf}` : member.role === "ready" ? "" : agentWord(member);
  return (
    <li className="aw-tile" data-object-id={member.id} data-testid="conductor-row" data-group={group}
      data-picked={picked ? "" : undefined} data-tone={tone} data-helper={helperOf ? "" : undefined}>
      <Button variant="chrome" className="aw-tile-open" aria-current={picked ? "true" : undefined}
        aria-label={title} title={`${title}, ${pill.word}`} tabIndex={picked ? 0 : -1} onClick={() => onPick(member.id)}>
        <img className="aw-tile-sprite" src={listSprite(member.sprite ?? "")} alt="" width={32} height={32} draggable={false} />
        <span className="aw-tile-words">
          <span className="aw-tile-title">{title}</span>
          <span className="aw-tile-meta">
            <span data-testid="conductor-pill">{pill.word}</span>
            {sub ? <span className="aw-tile-sub">{sub}</span> : null}
            {member.deskAnswer?.state === "answered" && member.deskAnswer.isNew ? (
              <span className="aw-tile-sub" data-testid="agents-tile-new">The desk answered · New</span>
            ) : null}
          </span>
        </span>
      </Button>
      <Spine className="aw-tile-spine" tone={tone} />
    </li>
  );
}

export function AgentRail({ sections, picked, starting, pillOf, onPick, onStart }: {
  sections: readonly RailSection[];
  picked: string | null;
  starting: boolean;
  pillOf(member: ConductorMember): { word: string };
  onPick(id: string): void;
  onStart(): void;
}) {
  const ref = useRef<HTMLElement | null>(null);
  const onKeys = (event: KeyboardEvent<HTMLElement>) => {
    const step = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : event.key === "ArrowUp" || event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    const tiles = [...(ref.current?.querySelectorAll<HTMLButtonElement>(".aw-tile-open") ?? [])];
    if (!tiles.length) return;
    const at = tiles.indexOf(document.activeElement as HTMLButtonElement);
    event.preventDefault();
    tiles[Math.min(tiles.length - 1, Math.max(0, at < 0 ? 0 : at + step))]?.focus();
  };
  return (
    <nav ref={ref} className="aw-rail" aria-label="Agents" onKeyDown={onKeys} data-testid="agents-rail">
      <Button dense variant={starting ? "secondary" : "primary"} className="aw-rail-start" aria-expanded={starting}
        aria-label="Start an agent" onClick={onStart} data-testid="conductor-start">
        <ToolGlyph kind="new" />
        <span className="aw-rail-start-word">Start an agent</span>
      </Button>
      {sections.map((section) => (
        <div key={section.id} className="aw-rail-group" role="group" aria-label={section.word}
          data-section={section.id} data-testid="conductor-list">
          <h3 className="aw-cap" data-testid="conductor-section">{section.word}</h3>
          <ul className="aw-rail-tiles" style={{ "--aw-cols": Math.min(4, section.rows.length) } as CSSProperties}>
            {section.rows.map(({ member, group, helperOf }) => (
              <Tile key={member.id} member={member} group={group} helperOf={helperOf} picked={member.id === picked}
                pill={pillOf(member)} onPick={onPick} />
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}
