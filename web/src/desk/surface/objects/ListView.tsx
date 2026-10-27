/** Window Program W1 (2026-10-27) — ListView: the plain list view of a
 *  window that lists happenings or plumbing (Room ▸ History, the gear wings
 *  of Meetings, Activity and Live), where ObjectList's sortable columns are
 *  more than the job needs.
 *
 *  One row: a 20 px glyph · the name (sans 13, ink) · the meta (sans 12,
 *  muted: who, where, what kind) · a state as a dot and a word · the age or
 *  the time at the right (sans 12, muted, tabular) · the row's verbs. Rows
 *  are 32 px on the desktop and fold the meta under the name at 520 px or
 *  less (44 px). `onOpen` makes the row's body one library Button.
 *  `ListDay` groups rows under a quiet sentence-case day caption (Today,
 *  Yesterday, Mon 20 Oct).
 *
 *  `useWaitWord` is the honest face of a read that may never answer: a
 *  state word with an age ("Checking… 12 s"), then "No answer" after the
 *  limit, never a spinner that turns forever. */
import { useEffect, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { DotWord } from "../kit";
import type { ObjectTone } from "./kinds";
import "./list-view.css";

export function ListView({
  label,
  children,
  className,
  "data-testid": testId,
}: {
  /** The list's accessible name. */
  label: string;
  children: ReactNode;
  className?: string;
  "data-testid"?: string;
}) {
  return (
    <div className={className ? `kit-listview ${className}` : "kit-listview"} role="group" aria-label={label} data-testid={testId}>
      {children}
    </div>
  );
}

/** A day (or any group) of rows under a quiet caption. */
export function ListDay({ label, children, "data-testid": testId }: { label: string; children: ReactNode; "data-testid"?: string }) {
  return (
    <section className="kit-listday" aria-label={label} data-testid={testId}>
      <h3 className="kit-listday-label">{label}</h3>
      <ul className="kit-listrows">{children}</ul>
    </section>
  );
}

/** Rows with no group caption. */
export function ListRows({ children }: { children: ReactNode }) {
  return <ul className="kit-listrows">{children}</ul>;
}

export type ListRowState = { word: string; tone?: ObjectTone | "idle"; testId?: string };

export function ListRow({
  glyph,
  name,
  meta,
  state,
  age,
  verbs,
  onOpen,
  openLabel,
  openTestId,
  nameTestId,
  "data-testid": testId,
}: {
  /** A 20 px sprite URL, or a node. */
  glyph?: string | ReactNode;
  name: ReactNode;
  meta?: ReactNode;
  state?: ListRowState | null;
  /** The age or the time (`14:02`, `2 h ago`). */
  age?: ReactNode;
  verbs?: ReactNode;
  onOpen?: () => void;
  /** The open Button's accessible name (`Open: Added risk · …`). */
  openLabel?: string;
  openTestId?: string;
  nameTestId?: string;
  "data-testid"?: string;
}) {
  const lead = glyph == null ? null : typeof glyph === "string" ? (
    <img className="kit-listrow-glyph" src={glyph} alt="" width={20} height={20} draggable={false} />
  ) : (
    <span className="kit-listrow-glyph" aria-hidden="true">{glyph}</span>
  );
  const body = (
    <>
      {lead}
      <span className="kit-listrow-text">
        <span className="kit-listrow-name" data-testid={nameTestId}>{name}</span>
        {meta ? <span className="kit-listrow-meta">{meta}</span> : null}
      </span>
    </>
  );
  return (
    <li className="kit-listrow" data-open={onOpen ? "" : undefined} data-testid={testId}>
      {onOpen ? (
        <Button variant="chrome" className="kit-listrow-main" aria-label={openLabel} data-testid={openTestId} onClick={onOpen}>
          {body}
        </Button>
      ) : (
        <span className="kit-listrow-main">{body}</span>
      )}
      {state ? (
        <span className="kit-listrow-state">
          <DotWord tone={state.tone} data-testid={state.testId}>{state.word}</DotWord>
        </span>
      ) : null}
      {age ? <span className="kit-listrow-age">{age}</span> : null}
      {verbs ? <span className="kit-listrow-verbs">{verbs}</span> : null}
    </li>
  );
}

/** A read that may never answer: "Checking… 12 s" while it waits, then
 *  "No answer" once `limitMs` passes. Null when it is not waiting. */
export function useWaitWord(waiting: boolean, limitMs = 30_000): ListRowState | null {
  const [since, setSince] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!waiting) {
      setSince(null);
      return;
    }
    const start = Date.now();
    setSince(start);
    setNow(start);
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [waiting]);
  if (!waiting || since == null) return null;
  const elapsed = now - since;
  if (elapsed >= limitMs) return { word: "No answer", tone: "warn" };
  return { word: `Checking… ${Math.max(1, Math.round(elapsed / 1000))} s`, tone: "idle" };
}

/** A quiet age from a wire time: `just now`, `12 min ago`, `3 h ago`,
 *  `2 d ago`; empty for junk. */
export function ageWords(value: unknown, now: number = Date.now()): string {
  const at = typeof value === "number" ? (value < 1e12 ? value * 1000 : value) : Date.parse(String(value ?? ""));
  if (!Number.isFinite(at)) return "";
  const s = Math.max(0, Math.round((now - at) / 1000));
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86_400) return `${Math.round(s / 3600)} h ago`;
  return `${Math.round(s / 86_400)} d ago`;
}
