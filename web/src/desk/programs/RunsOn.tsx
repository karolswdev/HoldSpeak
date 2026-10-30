/* Programs "Runs on" (design, the section before §7; canvas "Runs on, from
 * the toolbar" and "on a step"): one picker for every role. Claude Code,
 * Codex, then "pi on an engine" with the library's engines and their
 * readiness word (the Engines window's five words, `stateWord`), the
 * desk's assignment, When idle at its foot and Engines… (opens the Engines
 * window). The engines are read when the picker opens (the Engines
 * window's own detection), never on the first paint. */
import { useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { conciergeDetect, type Engine } from "../../features/concierge/api";
import { stateWord } from "../../features/runson/stateWord";
import { openSurfaceOr } from "../shell";
import { spriteUrl } from "../sprites";
import { stateWords } from "../surface/words";

export interface RunsOnChoice {
  profile: string;
  /** pi only: an engine profile id; null = the desk's assignment. */
  engine: string | null;
}

export interface PickerEngine {
  id: string;
  label: string;
  word: string;
}

export function pickerEngines(engines: readonly Engine[]): PickerEngine[] {
  return engines
    .filter((engine) => engine.kind !== "agent" && engine.kind !== "preset")
    .map((engine) => ({
      id: engine.profileId || engine.id,
      label: engine.host ? `${engine.name} on ${engine.host}` : engine.name,
      word: stateWords(stateWord(engine.state)),
    }));
}

const sprite = (agent: string) => <img src={spriteUrl("coder", agent, "rest", agent, 20)} alt="" width={20} height={20} />;

const same = (a: RunsOnChoice, b: RunsOnChoice) => a.profile === b.profile && (a.engine ?? null) === (b.engine ?? null);

/** The "Then, at a limit" rows: each agent other than the first, checked
 *  when it is in the order; a press adds it at the end or takes it out. */
function thenEntries(first: RunsOnChoice | null, then: readonly RunsOnChoice[], engines: PickerEngine[],
  onThen: (next: RunsOnChoice[]) => void): WorkMenuEntry[] {
  const options: { choice: RunsOnChoice; label: string; agent: string }[] = [
    { choice: { profile: "claude-default", engine: null }, label: "Claude Code", agent: "claude" },
    { choice: { profile: "codex-default", engine: null }, label: "Codex", agent: "codex" },
    ...engines.map((engine) => ({ choice: { profile: "pi-default", engine: engine.id }, label: `pi · ${engine.label}`, agent: "pi" })),
  ].filter((row) => !first || !same(row.choice, first));
  const order = (choice: RunsOnChoice) => then.findIndex((row) => same(row, choice));
  return [
    { type: "sep", id: "then" },
    { type: "note", id: "then-note", label: "Then, at a limit" },
    ...options.map((row): WorkMenuEntry => {
      const at = order(row.choice);
      return {
        type: "item", id: `then:${row.choice.profile}:${row.choice.engine ?? ""}`,
        label: at >= 0 ? `then ${row.label} · ${at + 1}` : `then ${row.label}`, glyph: sprite(row.agent),
        checked: at >= 0,
        onSelect: () => onThen(at >= 0 ? then.filter((_, index) => index !== at) : [...then, row.choice]),
      };
    }),
  ];
}

export function RunsOnPicker({
  label,
  value,
  idle,
  idleLabel,
  onPick,
  onIdle,
  disabled,
  then,
  onThen,
  "data-testid": testId,
}: {
  /** The Button's words (`Runs on: Claude Code`). */
  label: string;
  value: RunsOnChoice | null;
  idle?: boolean;
  /** `When idle, for every pi step` / `When idle, for this step`. */
  idleLabel?: string;
  onPick(choice: RunsOnChoice): void;
  /** Absent: the picker has no When idle row (an automation's Program
   *  takes its template's). */
  onIdle?(next: boolean): void;
  disabled?: boolean;
  /** PG19: the agents that take over at a usage limit, in order ("then"
   *  rows under the first choice). Absent: the picker has no then rows. */
  then?: readonly RunsOnChoice[];
  onThen?(next: RunsOnChoice[]): void;
  "data-testid"?: string;
}) {
  const opener = useRef<HTMLButtonElement | null>(null);
  const [open, setOpen] = useState(false);
  const [engines, setEngines] = useState<PickerEngine[] | null>(null);
  const toggle = () => {
    setOpen((now) => !now);
    if (engines == null) {
      void conciergeDetect().then((answer) => setEngines(pickerEngines(answer.engines))).catch(() => setEngines([]));
    }
  };
  const rect = open ? opener.current?.getBoundingClientRect() : null;
  const is = (profile: string, engine: string | null = null) =>
    value?.profile === profile && (profile !== "pi-default" || (value?.engine ?? null) === engine);
  const entries: WorkMenuEntry[] = [
    { type: "item", id: "claude", label: "Claude Code · Ready", glyph: sprite("claude"), checked: is("claude-default") ? "exclusive" : undefined, onSelect: () => onPick({ profile: "claude-default", engine: null }) },
    { type: "item", id: "codex", label: "Codex · Ready", glyph: sprite("codex"), checked: is("codex-default") ? "exclusive" : undefined, onSelect: () => onPick({ profile: "codex-default", engine: null }) },
    { type: "sep", id: "pi" },
    { type: "note", id: "pi-note", label: "pi on an engine" },
    ...(engines ?? []).map((engine): WorkMenuEntry => ({
      type: "item", id: `engine:${engine.id}`, label: `pi · ${engine.label} · ${engine.word}`, glyph: sprite("pi"),
      checked: is("pi-default", engine.id) ? "exclusive" : undefined,
      onSelect: () => onPick({ profile: "pi-default", engine: engine.id }),
    })),
    ...(engines == null ? [{ type: "note" as const, id: "reading", label: "Reading the engines…" }] : []),
    { type: "item", id: "assignment", label: "pi · the desk's assignment", glyph: sprite("pi"), checked: is("pi-default", null) ? "exclusive" : undefined, onSelect: () => onPick({ profile: "pi-default", engine: null }) },
    ...(onThen ? thenEntries(value, then ?? [], engines ?? [], onThen) : []),
    { type: "sep", id: "foot" },
    ...(onIdle ? [{ type: "item" as const, id: "idle", label: idleLabel ?? "When idle", checked: Boolean(idle), onSelect: () => onIdle(!idle) }] : []),
    { type: "item", id: "engines", label: "Engines…", onSelect: () => openSurfaceOr("configure-runs-on", "/models") },
  ];
  return (
    <>
      <Button ref={opener} dense variant="ghost" className="pg-runs-on" aria-haspopup="menu" aria-expanded={open}
        disabled={disabled} onClick={toggle} data-testid={testId}>
        {label}
        <svg className="kit-toolbar-more-caret" width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor"
          strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
          <path d="M2.5 3.75L5 6.25l2.5-2.5" />
        </svg>
      </Button>
      {open && rect ? (
        <WorkMenu label="Agent" x={rect.left} y={rect.bottom} opener={opener.current} autoFocus
          returnFocus={() => opener.current?.focus()} entries={entries} onClose={() => setOpen(false)} />
      ) : null}
    </>
  );
}
