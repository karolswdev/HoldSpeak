/** W3 AGENT WINDOW (canvas docs/internal/betterment/canvases/agent-window-2026-10-27.html,
 *  direction A, the step log): the agent's steps as a dense list, one 30 px
 *  row per step: the time, a coloured glyph for its kind, the step in
 *  sentence-case words with the path or command in mono, the agent's own
 *  words in quotes. The newest step is lit while the agent works (the hub
 *  reports past events only: the light is on the newest one, never on a
 *  step it has not reported).
 *
 *  It draws the rail entries `laneEntries` builds (laneWire.ts) from the
 *  hub's real events, commits, held calls, instructions and the PR, so a
 *  lane with no hook events has no steps, and the window says so. */
import type { ReactNode } from "react";
import { AgentWords } from "../components/AgentWords";
import type { LaneEntry } from "./laneWire";

type StepKind = LaneEntry["kind"] | "asks";

/** The words a step starts with, by its kind. */
const VERB: Record<StepKind, string> = {
  brief: "Got the brief",
  read: "Read",
  says: "",
  write: "Wrote",
  run: "Ran",
  call: "Used",
  answer: "You answered",
  end: "The session ended",
  commit: "Committed",
  pr: "Pull request",
  held: "Held",
  asks: "Asked you",
  merge: "Merged",
  rebrief: "You told it",
};

/** The glyph's family (its colour) by kind. */
const FAMILY: Record<StepKind, string> = {
  brief: "brief", read: "read", says: "says", write: "write", run: "run", call: "read",
  answer: "answer", end: "brief", commit: "commit", pr: "commit", held: "held", asks: "answer",
  merge: "commit", rebrief: "answer",
};

const GLYPH: Record<string, ReactNode> = {
  brief: <path d="M2.5 1.5h5l2 2v7h-7Z M4 5.5h4M4 7.5h4" />,
  read: (
    <>
      <path d="M1 6s1.8-3.5 5-3.5S11 6 11 6 9.2 9.5 6 9.5 1 6 1 6Z" />
      <circle cx="6" cy="6" r="1.5" />
    </>
  ),
  write: <path d="M8 1.5l2.5 2.5L4.5 10H2V7.5Z" />,
  run: <path d="M3.5 2v8L10 6Z" />,
  says: <path d="M2 2.5h8v5.5H5.5L3 10V8H2Z" />,
  commit: (
    <>
      <circle cx="6" cy="6" r="2.2" />
      <path d="M0.5 6h3.3M8.2 6h3.3" />
    </>
  ),
  answer: <path d="M10 2.5H2v5.5h4.5L9 10V8h1Z" />,
  held: <path d="M3.5 5.5V4a2.5 2.5 0 0 1 5 0v1.5 M2.5 5.5h7v5h-7Z" />,
};

function StepGlyph({ family }: { family: string }) {
  return (
    <span className="lw-step-glyph" data-family={family} aria-hidden="true">
      <svg viewBox="0 0 12 12" width={12} height={12} fill="none" stroke="currentColor" strokeWidth={1.7}
        strokeLinecap="round" strokeLinejoin="round" focusable="false">
        {GLYPH[family] ?? GLYPH.brief}
      </svg>
    </span>
  );
}

/** `a`, `a, b`, `a, b and 2 more` (a call with no head counts, names nothing). */
function headsWords(heads: readonly string[]): { shown: string[]; more: number } {
  const named = heads.filter(Boolean);
  const shown = named.slice(0, 2);
  return { shown, more: heads.length - shown.length };
}

/** One step entry; `asks` is the wait, drawn after the reported steps. */
export type StepEntry = Omit<LaneEntry, "kind"> & { kind: StepKind; verbs?: ReactNode };

function StepWords({ entry }: { entry: StepEntry }) {
  const verb = VERB[entry.kind];
  if (entry.kind === "says" && entry.words) {
    return <AgentWords className="lane-rail-says lw-step-says" text={entry.words} />;
  }
  if ((entry.kind === "read" || entry.kind === "call") && entry.heads?.length) {
    const { shown, more } = headsWords(entry.heads);
    return (
      <span className="lw-step-line">
        {verb}{" "}
        {shown.map((head, i) => (
          <span key={`${head}:${i}`}>
            {i ? ", " : ""}
            <code className="lw-step-code">{head}</code>
          </span>
        ))}
        {more > 0 ? <span className="lw-step-muted">{shown.length ? ` and ${more} more` : `${more} ${more === 1 ? "file" : "files"}`}</span> : null}
      </span>
    );
  }
  if (entry.kind === "commit" && entry.code) {
    const [sha, ...subject] = entry.code.split(" ");
    return (
      <span className="lw-step-line">
        {verb} <code className="lw-step-code">{sha}</code>
        {subject.length ? <span className="lw-step-muted"> {subject.join(" ")}</span> : null}
      </span>
    );
  }
  return (
    <span className="lw-step-line">
      {verb}
      {entry.code ? <> <code className="lw-step-code">{entry.code}</code></> : null}
      {entry.text ? (
        <>
          {verb ? <span className="lw-step-muted" aria-hidden="true"> · </span> : null}
          <span className="lw-step-muted">{entry.text}</span>
        </>
      ) : null}
    </span>
  );
}

export function StepList({
  entries,
  lit,
  "data-testid": testId,
}: {
  entries: readonly StepEntry[];
  /** The id of the step to light (the newest one while the agent works). */
  lit?: string | null;
  "data-testid"?: string;
}) {
  return (
    <ol className="lw-steps" aria-label="Steps" data-testid={testId}>
      {entries.map((entry, index) => {
        const id = entry.id ?? `${entry.kind}-${index}`;
        const now = lit != null && id === lit;
        const tall = Boolean(entry.quote || (entry.kind === "says" && entry.words));
        return (
          <li
            key={id}
            className="lw-step"
            data-kind={entry.kind}
            data-tall={tall ? "true" : undefined}
            data-pending={entry.pending ? "true" : undefined}
            data-tone={entry.tone}
            aria-current={now ? "step" : undefined}
          >
            <span className="lw-step-time">{entry.time ?? ""}</span>
            <StepGlyph family={FAMILY[entry.kind] ?? "brief"} />
            <span className="lw-step-body">
              <StepWords entry={entry} />
              {entry.quote ? <q className="lw-step-quote">{entry.quote}</q> : null}
            </span>
            {entry.verbs ? <span className="lw-step-verbs">{entry.verbs}</span> : null}
          </li>
        );
      })}
    </ol>
  );
}
