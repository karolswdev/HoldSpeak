/** TaskResume (HS-200-41) — the ratified `UNFINISHED 1` row: one piece of
 *  work the owner walked away from, drawn so he can pick it back up.
 *
 *  The row states, in order: the purpose (primary step), the state chip,
 *  `SAVED HH:MM`, the recipe when it HAS one, the custody token, why it is
 *  stopped, the Project button, and ONE verb. `Discard` is a `ConfirmVerb`
 *  inside a `MORE` `Disclosure` — never a bare destructive verb.
 *
 *  Three rules the species enforces so no face has to remember them:
 *
 *  - **No token for an absent fact** (UX-CANON A.8). An ask with no recipe
 *    draws no recipe chip; it never draws `RECIPE · NONE`.
 *  - **Custody is `SAVED HERE` / `SAVED ON <host>`** (ruling B7). `THIS
 *    DEVICE` is the egress vocabulary (`desk/surface/egress.ts:16,25`) and
 *    egress is a hard boundary; two facts never wear one token.
 *  - **Every verb is the library `Button`** (UX-CANON A.1). A refused verb
 *    is native `disabled`, not an invented "unavailable" variant.
 *
 *  The state vocabulary is the full union of the six work states the product
 *  must distinguish (design D2(f)) PLUS `discarded`, because story 15 draws
 *  the whole wing from three different owners. A Room ask reaches only
 *  `saved`, `failed`, `accepted` and `discarded` (ruling B8): it is one
 *  blocking POST with no job row, so no caller may hand this species a
 *  running clock for an ask.
 */
import { Children, useRef, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { countLabel } from "../count";
import { streamTime } from "../format";
import { useRovingRows } from "../roving";
import { ConfirmVerb } from "../Surface";
import { Disclosure } from "./Disclosure";
import { StateChip, type ChipState } from "./StateChip";
import "./task-resume.css";

/** The closed work-state vocabulary. */
export type TaskResumeState =
  | "saved"
  | "running"
  | "waiting"
  | "failed"
  | "incomplete"
  | "accepted"
  | "discarded";

/** state → the chip's tone, its word, and the ONE verb that state owns. */
const STATE_GRAMMAR: Record<
  TaskResumeState,
  { chip: ChipState; word: string; verb: string | null }
> = {
  saved: { chip: "idle", word: "SAVED", verb: "Resume" },
  running: { chip: "working", word: "RUNNING", verb: "Stop" },
  waiting: { chip: "active", word: "WAITING ON YOU", verb: "Answer" },
  failed: { chip: "failure", word: "FAILED", verb: "Check" },
  incomplete: { chip: "warning", word: "INCOMPLETE", verb: "Re-read" },
  accepted: { chip: "success", word: "ACCEPTED", verb: "Open" },
  discarded: { chip: "unreachable", word: "DISCARDED", verb: null },
};

/** `HH:MM` for a token, or "" when the value is not a time. */
function clock(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "";
  const date =
    typeof value === "number"
      ? new Date(value < 1e12 ? value * 1000 : value)
      : new Date(
          /^\d{4}-\d{2}-\d{2} /.test(String(value))
            ? String(value).replace(" ", "T")
            : String(value),
        );
  if (Number.isNaN(date.getTime())) return "";
  return streamTime(date);
}

/** `MM-DD` — the day a settled row names (`ACCEPTED 09-02`). */
function day(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "";
  const date =
    typeof value === "number"
      ? new Date(value < 1e12 ? value * 1000 : value)
      : new Date(
          /^\d{4}-\d{2}-\d{2} /.test(String(value))
            ? String(value).replace(" ", "T")
            : String(value),
        );
  if (Number.isNaN(date.getTime())) return "";
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${mm}-${dd}`;
}

export interface TaskResumeProps {
  /** The work itself, at the primary type step. Said once. */
  purpose: string;
  state: TaskResumeState;
  /** When the record was written. Drawn as `SAVED HH:MM`. */
  savedAt?: string | number | null;
  /** When a settled row settled. Drawn as `ACCEPTED MM-DD`. */
  settledAt?: string | number | null;
  /** The recipe this work runs. ABSENT draws NOTHING (never `· NONE`). */
  recipe?: string;
  /** The originating Project — the way back (design D2(g)). */
  projectName?: string;
  onOpenProject?: () => void;
  /** The target's OWN words for why it stopped (ruling B5: quoted, never
   *  composed here). Drawn inside the chip on `failed`, as its own token
   *  otherwise, and never twice. */
  stoppedReason?: string;
  /** The bounded refusal TOKEN the record always carries. The store quotes
   *  the destination only while it still observes the state the code names,
   *  so a row can hold a code and no words. The face falls back to the code
   *  rather than composing a sentence out of it — and when BOTH are empty it
   *  draws no token at all (A.8). */
  stoppedCode?: string;
  /** Custody (ruling B7, corrected by F1). `here` → `SAVED HERE`;
   *  `elsewhere` → `SAVED ON ANOTHER DESK`. Absent → no custody token.
   *
   *  There is deliberately no host prop. The hub's machine identity is an
   *  opaque token and a face does not print opaque tokens (canon `raw-ids`);
   *  the wire carries the VERDICT, and the words are the species'. */
  custody?: "here" | "elsewhere";
  /** The state chip's own trailing fact, when the OWNER of that state can
   *  supply one (`00:52`, `3 OF 4 SOURCES`). An ask cannot (ruling B8). */
  detail?: string;
  /** Override the state's default verb label. */
  verbLabel?: string;
  /** The verb's accessible name; defaults to `<label> — <purpose>`. */
  verbAriaLabel?: string;
  onVerb?: () => void;
  /** A refused verb is native `disabled`, and says why in its name. */
  verbDisabledReason?: string;
  /** The face's ONE filled primary (design D2(f): `Resume` is it). */
  primary?: boolean;
  busy?: boolean;
  /** `Discard` — a state, never a delete (ruling B6). Behind `MORE`. */
  onDiscard?: () => void;
  discardBusy?: boolean;
  className?: string;
  "data-testid"?: string;
}

export function TaskResume({
  purpose,
  state,
  savedAt,
  settledAt,
  recipe,
  projectName,
  onOpenProject,
  stoppedReason,
  stoppedCode,
  custody,
  detail,
  verbLabel,
  verbAriaLabel,
  onVerb,
  verbDisabledReason,
  primary = false,
  busy = false,
  onDiscard,
  discardBusy = false,
  className,
  "data-testid": dataTestId,
}: TaskResumeProps) {
  const grammar = STATE_GRAMMAR[state] ?? STATE_GRAMMAR.saved;
  const savedClock = clock(savedAt);
  const settledDay = day(settledAt ?? savedAt);

  // The chip carries the state's word plus the ONE fact that state owns.
  // `saved` owns the clock, `accepted` owns the day, `failed` owns the
  // quoted reason — so none of them is drawn twice below.
  // Why it stopped: the destination's own words when the store HAS them, the
  // bounded code when it does not, and nothing at all when it has neither.
  // Never a sentence composed out of either (ruling B5).
  //
  // F3: it does NOT ride the chip. Ruling B5 quotes the engine verbatim and
  // a filesystem path is the ORDINARY case, not an edge — a `FAILED · <path>`
  // chip ran 534px inside a 341px row and was sliced off-glass mid-token,
  // because `StateChip` neither wraps nor truncates. The engine's words are
  // not truncated to fit a chip; they get their own row that wraps.
  const stopped = stoppedReason || stoppedCode || "";
  let chipLabel = grammar.word;
  if (state === "saved" && savedClock) chipLabel = `SAVED ${savedClock}`;
  else if (state === "accepted" && settledDay) chipLabel = `ACCEPTED ${settledDay}`;
  else if (detail) chipLabel = `${grammar.word} · ${detail}`;

  // Every token below is drawn ONLY when its fact exists (A.8).
  const tokens: Array<{ key: string; text: string }> = [];
  if (state !== "saved" && savedClock)
    tokens.push({ key: "saved", text: `SAVED ${savedClock}` });
  if (recipe) tokens.push({ key: "recipe", text: `RECIPE · ${recipe}` });
  if (custody === "here") tokens.push({ key: "custody", text: "SAVED HERE" });
  else if (custody === "elsewhere")
    tokens.push({ key: "custody", text: "SAVED ON ANOTHER DESK" });

  const label = verbLabel ?? grammar.verb;
  const cx = ["surface-task-resume", className].filter(Boolean).join(" ");

  return (
    <li className={cx} data-state={state} data-testid={dataTestId}>
      <p className="surface-task-resume-purpose">{purpose}</p>
      <div className="surface-task-resume-tokens">
        <StateChip state={grammar.chip} label={chipLabel} />
        {tokens.map((token) => (
          <span
            key={token.key}
            className="surface-token"
            data-chip=""
            data-task-resume-token={token.key}
          >
            {token.text}
          </span>
        ))}
        {projectName && onOpenProject ? (
          <Button
            dense
            variant="ghost"
            className="surface-task-resume-project"
            aria-label={`Open the Project: ${projectName}`}
            onClick={onOpenProject}
          >
            {projectName}
          </Button>
        ) : null}
      </div>
      {stopped ? (
        <p className="surface-task-resume-reason" data-task-resume-reason="">
          {stopped}
        </p>
      ) : null}
      <div className="surface-task-resume-verbs">
        {label && onVerb ? (
          <Button
            dense
            variant={primary ? "primary" : "secondary"}
            loading={busy}
            disabled={Boolean(verbDisabledReason)}
            aria-disabled={verbDisabledReason ? true : undefined}
            aria-label={
              verbAriaLabel ??
              (verbDisabledReason
                ? `${label}: ${verbDisabledReason}`
                : `${label}: ${purpose}`)
            }
            onClick={onVerb}
          >
            {label}
          </Button>
        ) : null}
        {onDiscard ? (
          <Disclosure label="MORE">
            <ConfirmVerb
              label="Discard"
              ariaLabel="Discard the unfinished ask"
              busy={discardBusy}
              onConfirm={onDiscard}
            />
          </Disclosure>
        ) : null}
      </div>
    </li>
  );
}

/** The list the rows live in: ONE Tab stop, Up/Down rove rows, Left/Right
 *  walk a row's own verbs (`useRovingRows` — kit law, never re-implemented
 *  in a consumer). Renders NOTHING when there is nothing unfinished, so no
 *  face can draw a caption of zero (A.8). */
export function TaskResumeList({
  label,
  children,
  className,
  "data-testid": dataTestId,
}: {
  /** The section caption; the count rides `countLabel` (`UNFINISHED 1`). */
  label?: string;
  children: ReactNode;
  className?: string;
  "data-testid"?: string;
}) {
  const rootRef = useRef<HTMLDivElement>(null);
  useRovingRows(rootRef, {
    selector: ".surface-task-resume button",
    rowSelector: ".surface-task-resume",
  });
  const count = Children.toArray(children).length;
  if (count === 0) return null;
  const cx = ["surface-task-resume-list", className].filter(Boolean).join(" ");
  return (
    <div ref={rootRef} className={cx} data-testid={dataTestId}>
      {label ? (
        <span className="surface-task-resume-caption">
          {countLabel(label, count)}
        </span>
      ) : null}
      <ul
        className="surface-task-resume-rows"
        aria-label={label ? countLabel(label, count) : undefined}
      >
        {children}
      </ul>
    </div>
  );
}
