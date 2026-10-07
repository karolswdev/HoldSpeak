/** PHILO-14 C2 — the lane's parts, LOCAL to the agent's window.
 *
 * Lane B1 ports the object species (TimelineRail, StationTrack, AskWell,
 * PRCard, FilesChanged) into `web/src/desk/surface/objects/` in parallel.
 * These are the same names with the same props as B1's (as read on its
 * branch, 2026-10-07), drawn from the canvas rules (`p14.css`) on the
 * Workbench tokens, so the swap to the library species is one import line
 * per part. One addition, named: AskWell's `listenSignal` (the Speak answer
 * press of Conductor F2 starts its mic, through StringGadget's own mic) and
 * `inputRef`.
 */
import { useRef, type ReactNode, type Ref } from "react";
import { Button } from "../../components/signal/Signal";
import { EgressChip, LampGadget, StringGadget, SurfaceSection } from "../surface";
import { countLabel } from "../surface/count";
import { spriteUrl } from "../sprites";
import "./lane.css";

/** The tones an object wears (B1 `kinds.ts`). */
export type ObjectTone = "ok" | "warn" | "fail" | "info" | "ask";

export type LaneWord =
  | "BRIEF" | "READ" | "SAYS" | "WRITE" | "RUN" | "COMMIT" | "PR" | "HELD" | "ASKS" | "MERGE"
  | (string & {});

export interface TimelineEntry {
  id?: string;
  /** `09:42`; empty for a pending entry. */
  time?: string;
  word: LaneWord;
  tone?: ObjectTone;
  /** A sentence (sans). */
  text?: string;
  /** A path, a command, a commit (mono). */
  code?: string;
  /** The agent's own words (SAYS), drawn as a quote. */
  quote?: string;
  /** The entry's verbs (library Buttons): Brief; Deny / Approve. */
  verbs?: ReactNode;
  /** The next step that waits (hollow square). */
  pending?: boolean;
}

/** TimelineRail: the vertical rail of what the agent did (board A-4). */
export function TimelineRail({ label, entries }: { label: string; entries: TimelineEntry[] }) {
  return (
    <ol className="lw-rail" aria-label={label} data-testid="lane-rail">
      {entries.map((entry, index) => (
        <li
          key={entry.id ?? `${entry.word}-${index}`}
          className="lw-ev"
          data-tone={entry.tone}
          data-pending={entry.pending ? "true" : undefined}
          data-word={entry.word}
        >
          <span className="lw-ev-time">{entry.time ?? ""}</span>
          <span className="lw-ev-node" aria-hidden="true">
            <span className="lw-square" data-tone={entry.tone} data-pending={entry.pending ? "true" : undefined} />
          </span>
          <span className="lw-ev-body">
            <span className="lw-ev-line">
              <span className="lw-word">{entry.word}</span>
              {entry.text ? <span className="lw-ev-text">{entry.text}</span> : null}
              {entry.code ? <code className="lw-ev-code">{entry.code}</code> : null}
            </span>
            {entry.quote ? <q className="lw-ev-quote">{entry.quote}</q> : null}
            {entry.verbs ? <span className="lw-verbs">{entry.verbs}</span> : null}
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
  tone?: ObjectTone;
}

/** StationTrack: the lane's life as stations on one track (board C-4). */
export function StationTrack({ label, stations }: { label: string; stations: Station[] }) {
  return (
    <ol className="lw-track" aria-label={label} data-testid="lane-track">
      {stations.map((station) => (
        <li
          key={station.word}
          className="lw-station"
          data-state={station.state}
          data-word={station.word}
          aria-current={station.state === "current" ? "step" : undefined}
        >
          <span
            className="lw-square"
            data-tone={station.state === "ahead" ? undefined : station.tone ?? "ok"}
            data-pending={station.state === "ahead" ? "true" : undefined}
            aria-hidden="true"
          />
          <span className="lw-word">{station.word}</span>
          {station.sub ? <span className="lw-station-sub">{station.sub}</span> : null}
        </li>
      ))}
    </ol>
  );
}

export interface AskWellProps {
  /** `Claude Code` → the caption `CLAUDE CODE ASKS`. */
  agent: string;
  /** `6 min`. */
  age?: string;
  question: string;
  value: string;
  onChange(next: string): void;
  onAnswer(answer: string): void;
  draft?: string;
  onUseDraft?(draft: string): void;
  draftEgress?: { label: string; scope?: "local" | "mixed" | "cloud" | "remote" };
  busy?: boolean;
  /** C2: each new value starts the mic (Conductor F2's Speak answer). */
  listenSignal?: number;
  /** C2: the mic's draft scope (the steer composer's). */
  draftScope?: string;
  inputRef?: Ref<HTMLInputElement>;
}

/** AskWell: the agent's question, the answer field with its mic, Answer;
 * the DRAFT line with Use draft and the drafting host. */
export function AskWell({
  agent, age, question, value, onChange, onAnswer, draft, onUseDraft, draftEgress, busy,
  listenSignal = 0, draftScope, inputRef,
}: AskWellProps) {
  const caption = [`${agent.toUpperCase()} ASKS`, age?.toUpperCase()].filter(Boolean).join(" · ");
  const field = useRef<HTMLInputElement | null>(null);
  // An empty answer is never sent: the press takes you to the field (B1).
  const send = () => {
    if (busy) return;
    if (value.trim()) onAnswer(value.trim());
    else field.current?.focus();
  };
  return (
    <section className="lw-ask" aria-label={`${agent} asks`} data-testid="lane-ask">
      <p className="lw-caption">{caption}</p>
      <p className="lw-ask-q" data-testid="lane-question">{question}</p>
      <div className="lw-ask-row">
        <StringGadget
          label="Answer"
          value={value}
          onChange={onChange}
          placeholder="Say or type the answer"
          micLabel="Speak the answer"
          micStartSignal={listenSignal}
          micDraftScope={draftScope}
          inputRef={(el) => {
            field.current = el;
            if (typeof inputRef === "function") inputRef(el);
            else if (inputRef) (inputRef as { current: HTMLInputElement | null }).current = el;
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.nativeEvent.isComposing) {
              event.preventDefault();
              send();
            }
          }}
        />
        <Button variant="primary" onClick={send} disabled={busy} data-testid="lane-answer">
          Answer
        </Button>
      </div>
      {draft ? (
        <div className="lw-draft" data-testid="lane-draft">
          <span className="lw-caption">Draft</span>
          <span className="lw-draft-text">{draft}</span>
          {onUseDraft ? (
            <Button dense variant="ghost" onClick={() => onUseDraft(draft)} data-testid="lane-use-draft">
              Use draft
            </Button>
          ) : null}
          {draftEgress ? <EgressChip label={draftEgress.label} scope={draftEgress.scope} /> : null}
        </div>
      ) : null}
    </section>
  );
}

export interface PRCardProps {
  number: number;
  title: string;
  checks?: { passed: number; total: number; failed?: number; running?: number };
  review?: string;
  branch?: string;
  base?: string;
  sprite?: string;
}

/** PRCard: the PR inline (its checks, its review, branch → base). */
export function PRCard({ number, title, checks, review, branch, base, sprite }: PRCardProps) {
  const failed = checks?.failed ?? 0;
  const running = checks?.running ?? 0;
  return (
    <article className="lw-pr" aria-label={`Pull request #${number}: ${title}`} data-testid="lane-pr">
      <div className="lw-pr-line">
        <img className="lw-pr-icon" src={sprite ?? spriteUrl("artifact", `pr-${number}`)} alt="" draggable={false} />
        <span className="lw-pr-title">#{number} {title}</span>
      </div>
      {checks || review ? (
        <div className="lw-pr-line">
          {checks && checks.total > 0 ? (
            <LampGadget label={`CHECKS ${checks.passed} OF ${checks.total}`} on tone={failed > 0 ? "fail" : "ok"} />
          ) : null}
          {failed > 0 ? <LampGadget label={`${failed} FAILED`} on tone="fail" /> : null}
          {running > 0 ? <LampGadget label={`${running} RUNNING`} on={false} /> : null}
          {review ? <span className="lw-fact">REVIEW <b>{review.toUpperCase()}</b></span> : null}
        </div>
      ) : null}
      {branch ? (
        <div className="lw-pr-line">
          <code className="lw-mono">{branch}{base ? ` → ${base}` : ""}</code>
        </div>
      ) : null}
    </article>
  );
}

export interface ChangedFile {
  path: string;
  added?: number;
  removed?: number;
}

/** FilesChanged: one line per file the agent changed. */
export function FilesChanged({ files, label = "Files changed" }: { files: ChangedFile[]; label?: string }) {
  if (!files.length) return null;
  return (
    <SurfaceSection label={countLabel(`${label} ·`, files.length)}>
      <ul className="lw-files" data-testid="lane-files">
        {files.map((file) => {
          const counts = [file.added ? `+${file.added}` : "", file.removed ? `−${file.removed}` : ""].filter(Boolean);
          return (
            <li key={file.path} className="lw-file">
              <code>{file.path}</code>
              {counts.length ? <span className="lw-file-counts">{counts.join(" ")}</span> : <span />}
            </li>
          );
        })}
      </ul>
    </SurfaceSection>
  );
}
