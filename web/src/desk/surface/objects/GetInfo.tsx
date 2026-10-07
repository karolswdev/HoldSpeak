/** PHILO-14 B1 — GetInfo: the Get Info window body (board A-2, right).
 *
 *  The object's identity (its sprite at 64 px, its name at the primary
 *  step, its KIND word as a caption), then its facts as a two-column grid
 *  (WHERE, FROM, MADE, DUE, OWNER, STATE, BRANCH). Every fact is optional:
 *  an absent fact is no row (no counters of zero, no "None" filler). The
 *  verbs are the caller's, in the window's footer (SurfaceFooter).
 */
import type { ReactNode } from "react";
import { LampGadget } from "../gadgets";
import { SurfaceFooter } from "../SurfaceFooter";
import { lampGadgetTone, objectKindWord, objectSprite, type ObjectTone } from "./kinds";
import "./objects.css";

export interface GetInfoFacts {
  where?: string;
  from?: string;
  made?: string;
  due?: string;
  owner?: string;
  state?: { label: string; tone: ObjectTone };
  branch?: string;
}

export interface GetInfoProps {
  id: string;
  kind: string;
  name: string;
  kindWord?: string;
  sprite?: string;
  facts: GetInfoFacts;
  /** The object's verbs (library Buttons), drawn in the window's footer. */
  verbs?: ReactNode;
}

const ORDER: { key: keyof GetInfoFacts; word: string }[] = [
  { key: "where", word: "Where" },
  { key: "from", word: "From" },
  { key: "made", word: "Made" },
  { key: "due", word: "Due" },
  { key: "owner", word: "Owner" },
  { key: "state", word: "State" },
  { key: "branch", word: "Branch" },
];

export function GetInfo({ id, kind, name, kindWord, sprite, facts, verbs }: GetInfoProps) {
  const rows = ORDER.filter(({ key }) => {
    const value = facts[key];
    return typeof value === "string" ? value.trim() !== "" : Boolean(value);
  });
  return (
    <div className="object-info" data-object-id={id}>
      <div className="object-info-head">
        <img src={sprite ?? objectSprite(kind, id)} alt="" draggable={false} />
        <div className="object-info-id">
          <h2 className="object-info-name">{name}</h2>
          <p className="object-info-kind">{kindWord ?? objectKindWord(kind)}</p>
        </div>
      </div>
      {rows.length ? (
        <dl className="object-info-facts">
          {rows.map(({ key, word }) => (
            <div key={key} className="object-info-fact" data-fact={key}>
              <dt>{word}</dt>
              <dd>
                {key === "state" && facts.state ? (
                  <LampGadget label={facts.state.label} on tone={lampGadgetTone(facts.state.tone)} />
                ) : key === "branch" ? (
                  <code>{facts.branch}</code>
                ) : (
                  (facts[key] as string)
                )}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
      {verbs ? <SurfaceFooter verbs={verbs} /> : null}
    </div>
  );
}
