/** PHILO-14 B1 — TimelineRail and StationTrack: an agent's lane.
 *
 *  TimelineRail (board A-4): the vertical rail of what the agent did, one
 *  entry per event: the time, a tone square on the rail, the WORD (BRIEF,
 *  READ, SAYS, WRITE, RUN, COMMIT, PR, HELD, ASKS, MERGE), a text or a code
 *  line, a quoted line (what it SAYS), and the entry's own verbs (Brief;
 *  Deny / Approve). A `pending` entry is the next step that waits (MERGE ·
 *  Your press in GitHub): a hollow square, muted words.
 *
 *  StationTrack (board C-4, borrowed onto the A lane): the same life as
 *  stations on one horizontal track (BRIEF · WORK · COMMIT · PR · HELD ·
 *  ASKS · MERGE), a sub-line under each. Reached stations are filled with
 *  their tone, the current one is lit (`aria-current="step"`), the rest are
 *  hollow. In a narrow `surface` the sub-lines fold away.
 */
import type { ReactNode } from "react";
import type { ObjectTone } from "./kinds";
import { AgentWords } from "../../components/AgentWords";
import "./objects.css";

export type LaneWord =
  | "BRIEF"
  | "READ"
  | "SAYS"
  | "WRITE"
  | "RUN"
  | "COMMIT"
  | "PR"
  | "HELD"
  | "ASKS"
  | "MERGE"
  | (string & {});

export interface TimelineEntry {
  id?: string;
  /** `09:42`; empty for a pending entry. */
  time?: string;
  word: LaneWord;
  /** The square's tone; absent = the steel square (a plain event). */
  tone?: ObjectTone;
  /** A sentence (sans). */
  text?: string;
  /** A path, a command, a commit (mono). */
  code?: string;
  /** Words drawn as a quote (an answer, a re-brief: the owner's). */
  quote?: string;
  /** Phase 16: the agent's own words (SAYS, ASKS), drawn by AgentWords:
   *  whole under the line, or on the line when `wordsCompact`. */
  words?: string;
  wordsCompact?: boolean;
  /** The entry's verbs (library Buttons): Brief; Deny / Approve. */
  verbs?: ReactNode;
  /** The next step that waits (hollow square). */
  pending?: boolean;
}

export function TimelineRail({
  label,
  entries,
  "data-testid": testId,
}: {
  label: string;
  entries: TimelineEntry[];
  /** Pass-through data-testid for the root `ol`. */
  "data-testid"?: string;
}) {
  return (
    <ol className="lane-rail" aria-label={label} data-testid={testId}>
      {entries.map((entry, index) => (
        <li
          key={entry.id ?? `${entry.word}-${index}`}
          className="lane-rail-entry"
          data-tone={entry.tone}
          data-pending={entry.pending ? "true" : undefined}
        >
          <span className="lane-rail-time">{entry.time ?? ""}</span>
          <span className="lane-rail-node" aria-hidden="true">
            <span className="lane-square" data-tone={entry.tone} data-pending={entry.pending ? "true" : undefined} />
          </span>
          <span className="lane-rail-body">
            <span className="lane-rail-line">
              <span className="lane-word">{entry.word}</span>
              {entry.text ? <span className="lane-rail-text">{entry.text}</span> : null}
              {entry.code ? <code className="lane-rail-code">{entry.code}</code> : null}
              {entry.words && entry.wordsCompact ? (
                <AgentWords compact className="lane-rail-text lane-rail-words-line" text={entry.words} />
              ) : null}
            </span>
            {entry.words && !entry.wordsCompact ? <AgentWords className="lane-rail-says" text={entry.words} /> : null}
            {entry.quote ? <q className="lane-rail-quote">{entry.quote}</q> : null}
            {entry.verbs ? <span className="lane-verbs">{entry.verbs}</span> : null}
          </span>
        </li>
      ))}
    </ol>
  );
}

export interface Station {
  word: LaneWord;
  /** The line under the word (`09:42`, `14 calls`, `#413`, `yours`). */
  sub?: string;
  /** reached: filled; current: lit; ahead: hollow. */
  state: "reached" | "current" | "ahead";
  /** The fill of a reached or current station; default ok. */
  tone?: ObjectTone;
}

export function StationTrack({
  label,
  stations,
  "data-testid": testId,
}: {
  label: string;
  stations: Station[];
  /** Pass-through data-testid for the root `ol`. */
  "data-testid"?: string;
}) {
  return (
    <ol className="lane-track" aria-label={label} data-testid={testId}>
      {stations.map((station) => (
        <li
          key={station.word}
          className="lane-station"
          data-state={station.state}
          aria-current={station.state === "current" ? "step" : undefined}
        >
          <span
            className="lane-square"
            data-tone={station.state === "ahead" ? undefined : station.tone ?? "ok"}
            data-pending={station.state === "ahead" ? "true" : undefined}
            data-lit={station.state === "current" ? "true" : undefined}
            aria-hidden="true"
          />
          <span className="lane-word">{station.word}</span>
          {station.sub ? <span className="lane-station-sub">{station.sub}</span> : null}
        </li>
      ))}
    </ol>
  );
}
