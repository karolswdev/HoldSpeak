/* Programs: the ledger (design §9 "Checkpoints"; PG-REQ §7 "The ledger,
 * folded per step"; canvas programs-requirements-2026-10-31 "The ledger,
 * folded per step").
 *
 * The window's Ledger fold: the Program's own lines first (start, park,
 * plan, the end check), then one sub-fold per step, the newest step
 * activity on top: "Step 3 · Projections off the loop · 14 lines · last
 * 18:40". A step's sub-fold opens to the rows the step fold's Ledger token
 * shows (by, line, the pinned commit and Start from here, time); a handoff
 * is its divider line with View brief. */
import { useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { spriteUrl } from "../sprites";
import { DotWord, FoldGadget, SurfaceWell, countWords } from "../surface";
import { plainFail } from "../surface/plainFailure";
import { startFrom } from "./api";
import { agentKey } from "./model";
import type { Program, ProgramCheckpoint, ProgramStep, StepHandoff } from "./types";

export function clock(at: string): string {
  const ms = Date.parse(at);
  if (!Number.isFinite(ms)) return "";
  return new Date(ms).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** `18:40` today, `yesterday 19:20`, `29 Oct 14:02` before. */
function whenWords(at: string): string {
  const ms = Date.parse(at);
  if (!Number.isFinite(ms)) return "";
  const then = new Date(ms);
  const now = new Date();
  const day = (value: Date) => new Date(value.getFullYear(), value.getMonth(), value.getDate()).getTime();
  const days = Math.round((day(now) - day(then)) / 86_400_000);
  if (days <= 0) return clock(at);
  if (days === 1) return `yesterday ${clock(at)}`;
  return `${then.toLocaleDateString("en-GB", { day: "numeric", month: "short" })} ${clock(at)}`;
}

function byWords(row: ProgramCheckpoint, program: Program): { who: string; sprite: string | null } {
  if (row.by === "owner") return { who: "You", sprite: null };
  if (row.by === "engine") return { who: "HoldSpeak · engine", sprite: spriteUrl("program", program.id, "rest", null, 20) };
  const step = program.steps.find((candidate) => candidate.id === row.step_id);
  const agent = agentKey(step?.profile, step?.agent);
  return { who: `${step?.agent ?? "Agent"} · step ${step?.ordinal ?? ""}`.trim(), sprite: spriteUrl("coder", agent, "rest", agent, 20) };
}

/** PG19: each handoff checkpoint's entry on its step (the nth handoff line
 *  of a step is its nth handoff). */
function handoffsOf(program: Program): Map<string, { step: ProgramStep; entry: StepHandoff }> {
  const out = new Map<string, { step: ProgramStep; entry: StepHandoff }>();
  const seen = new Map<string, number>();
  for (const row of [...program.checkpoints].reverse()) {
    if (row.kind !== "handoff") continue;
    const step = program.steps.find((candidate) => candidate.id === row.step_id);
    const index = seen.get(row.step_id) ?? 0;
    seen.set(row.step_id, index + 1);
    const entry = step?.handoffs?.[index];
    if (step && entry) out.set(String(row.id), { step, entry });
  }
  return out;
}

const REASON_WORDS: Record<string, string> = { usage_limit: "usage limit", usage_warning: "usage warning", by_hand: "by hand" };

/** The divider line of one handoff, and its brief in a sunken well under
 *  View brief (what was sent, what was redacted, the earlier turns). */
export function HandoffLine({ id, step, entry }: { id: string | number; step: ProgramStep; entry: StepHandoff }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="pg-handoff-row" data-testid="programs-handoff" data-checkpoint={id}>
      <div className="pg-handoff">
        <span className="kit-dot" data-tone="warn" aria-hidden="true" />
        <span className="pg-handoff-words">
          <b>Step {step.ordinal} · Handed to {entry.to}</b> · {REASON_WORDS[entry.reason] ?? entry.reason} · {clock(entry.at)}
        </span>
        <Button dense variant="secondary" aria-expanded={open} onClick={() => setOpen((now) => !now)} data-testid="programs-view-brief">
          {open ? "Hide brief" : "View brief"}
        </Button>
      </div>
      {open ? (
        <div className="pg-handoff-sheet" data-testid="programs-handoff-brief">
          <p className="pg-handoff-head">
            <b>Handoff brief</b>
            <span>{entry.from} to {entry.to}</span>
            <span data-testid="programs-handoff-redacted">{entry.redacted_words ? `Redacted: ${entry.redacted_words}` : "Nothing redacted"}</span>
            {entry.earlier_turns ? <span>{`${entry.earlier_turns} earlier ${entry.earlier_turns === 1 ? "turn" : "turns"}, not included`}</span> : null}
            {entry.continues_from ? (
              <span data-testid="programs-handoff-ref">Continues from <code className="pg-ref">{entry.continues_from}</code></span>
            ) : null}
          </p>
          <SurfaceWell>
            <pre className="pg-handoff-brief">{entry.brief}</pre>
          </SurfaceWell>
        </div>
      ) : null}
    </li>
  );
}

/** PG16: a Skip or a merge by rule became a proposed decision record (he
 *  accepts it in the Decisions window). A row word, never a chip of zero. */
export function ProposedWord() {
  return <DotWord tone="ask" className="pg-proposed" data-testid="programs-proposed-decision">Proposed as a decision</DotWord>;
}

/** PG20: the commit a checkpoint pinned (the short hash git users read; the
 *  full ref in its title) and Start from here. */
function PinCell({ row, busy, onStart }: { row: ProgramCheckpoint; busy: string; onStart(row: ProgramCheckpoint): void }) {
  if (!row.ref) return <span className="pg-ledger-pin" />;
  return (
    <span className="pg-ledger-pin" data-testid="programs-checkpoint-ref" data-ref={row.ref}>
      <code className="pg-ref" title={row.ref}>{(row.ref_commit ?? "").slice(0, 7) || row.ref.split("/").pop()}</code>
      <Button dense variant="ghost" loading={busy === String(row.id)} disabled={Boolean(busy)} title={`A new step from ${row.ref}`}
        onClick={() => onStart(row)} data-testid="programs-start-from">Start from here</Button>
    </span>
  );
}

/** Start from here, for every ledger list of one window. */
function useStartFrom(program: Program, onStarted: (next: Program | null) => void) {
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const start = async (row: ProgramCheckpoint) => {
    setBusy(String(row.id));
    setFailed(null);
    try {
      onStarted(await startFrom(program.id, String(row.id)));
    } catch (cause) {
      setFailed(plainFail("The step was not started", cause, "The program is unchanged", "Try again"));
    } finally {
      setBusy("");
    }
  };
  return { busy, failed, start };
}

/** The rows of one ledger list (newest first). */
export function LedgerRows({ program, rows, busy, onStart, "data-testid": testId }: {
  program: Program; rows: readonly ProgramCheckpoint[]; busy: string; onStart(row: ProgramCheckpoint): void; "data-testid"?: string;
}) {
  const handoffs = useMemo(() => handoffsOf(program), [program]);
  return (
    <ul className="pg-ledger" data-testid={testId}>
      {rows.slice(0, 50).map((row) => {
        const handed = handoffs.get(String(row.id));
        if (handed) return <HandoffLine key={row.id} id={row.id} step={handed.step} entry={handed.entry} />;
        const by = byWords(row, program);
        return (
          <li key={row.id} className="pg-ledger-row">
            <span className="pg-ledger-by">
              {by.sprite ? <img src={by.sprite} alt="" width={20} height={20} /> : <span className="pg-ledger-you" aria-hidden="true" />}
              <span>{by.who}</span>
            </span>
            <span className="pg-ledger-line" data-proposed={row.decision_record_id && !row.overturned_at ? "" : undefined}>
              <span className="pg-ledger-text">{row.line}</span>
              {row.decision_record_id && !row.overturned_at ? <ProposedWord /> : null}
            </span>
            <PinCell row={row} busy={busy} onStart={onStart} />
            <span className="pg-ledger-at">{clock(row.at)}</span>
          </li>
        );
      })}
    </ul>
  );
}

/** A step's own ledger (the step fold's Ledger token). */
export function StepLedger({ program, step, onStarted }: { program: Program; step: ProgramStep; onStarted(next: Program | null): void }) {
  const { busy, failed, start } = useStartFrom(program, onStarted);
  const rows = program.checkpoints.filter((row) => row.step_id === step.id);
  return (
    <>
      <LedgerRows program={program} rows={rows} busy={busy} onStart={(row) => void start(row)} data-testid="programs-step-ledger" />
      {failed ? <p className="pg-failure" role="status" title={failed.title}>{failed.words}</p> : null}
    </>
  );
}

function linesWords(rows: readonly ProgramCheckpoint[]): string {
  return [rows.length ? countWords(rows.length, "line") : "", rows[0] ? `last ${whenWords(rows[0].at)}` : ""].filter(Boolean).join(" · ");
}

/** The window's Ledger fold, one sub-fold per step. */
export function LedgerFold({ program, open, onToggle, onStarted }: {
  program: Program; open: boolean; onToggle(open: boolean): void; onStarted(next: Program | null): void;
}) {
  const { busy, failed, start } = useStartFrom(program, onStarted);
  const [openSteps, setOpenSteps] = useState<Record<string, boolean>>({});
  const rows = program.checkpoints;
  if (!rows.length) return null;
  const stepIds = new Set(program.steps.map((step) => step.id));
  const own = rows.filter((row) => !stepIds.has(row.step_id));
  // Newest step activity on top (the checkpoints are newest first).
  const order: ProgramStep[] = [];
  for (const row of rows) {
    const step = program.steps.find((candidate) => candidate.id === row.step_id);
    if (step && !order.includes(step)) order.push(step);
  }
  const onStart = (row: ProgramCheckpoint) => void start(row);
  return (
    <FoldGadget className="pg-checkpoints" title="Ledger" token={open ? "newest first" : `${rows.length} ${rows.length === 1 ? "line" : "lines"}`}
      open={open} onToggle={onToggle}>
      <div className="pg-ledger-folds" data-testid="programs-checkpoints">
        {own.length ? (
          <FoldGadget className="pg-ledger-sub" title={<>The program<span className="pg-fold-sub">{` · ${linesWords(own)}`}</span></>} open>
            <LedgerRows program={program} rows={own} busy={busy} onStart={onStart} />
          </FoldGadget>
        ) : null}
        {order.map((step, index) => {
          const mine = rows.filter((row) => row.step_id === step.id);
          // The newest step's lines are open; the rest open on a press.
          const isOpen = openSteps[step.id] ?? index === 0;
          return (
            <FoldGadget key={step.id} className="pg-ledger-sub" open={isOpen}
              onToggle={(next) => setOpenSteps((now) => ({ ...now, [step.id]: next }))}
              title={<>{`Step ${step.ordinal} · ${step.title}`}<span className="pg-fold-sub">{` · ${linesWords(mine)}`}</span></>}>
              <LedgerRows program={program} rows={mine} busy={busy} onStart={onStart} />
            </FoldGadget>
          );
        })}
      </div>
      {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="programs-start-from-failure">{failed.words}</p> : null}
    </FoldGadget>
  );
}
