/* Programs (canvas direction C, "the ledger"): one 32 px row per step.
 * Number · title (with "after 4, 5" in muted words) · the six station dots
 * and one state word · the agent's sprite and name (with the engine for pi)
 * · the time in this state · the last checkpoint · Open (the step's lane).
 * At 393 (the window's container is 520 px or less) the row is two lines:
 * the title with a StateChip, then the agent, the time and the checkpoint.
 * A race's contenders are indented rows under the step.
 *
 * In Drafting the row is fields: the title (StringGadget, with its mic),
 * the files it owns as Tokens, Runs on, effort, after, When idle. */
import { Button } from "../../components/signal/Signal";
import { CheckGadget, CycleGadget, DotWord, StateChip, StringGadget } from "../surface";
import { Token } from "../surface/Token";
import { openRef } from "../openObject";
import { spriteUrl } from "../sprites";
import { afterWords, agentKey, runsOnWords, stationsOf, stepChip, stepTone, stepWord } from "./model";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { StationTrack } from "./StationTrack";
import { stateWords } from "../surface/words";
import type { PlanStep, ProgramStep } from "./types";

function quote(line: string | undefined | null): string {
  return line ? `“${line}”` : "";
}

export function StepRow({
  step,
  selected,
  onSelect,
  contender = false,
}: {
  step: ProgramStep;
  selected?: boolean;
  onSelect?: () => void;
  contender?: boolean;
}) {
  const word = stepWord(step);
  const agent = agentKey(step.profile, step.agent);
  const started = step.state !== "planned" && step.state !== "ready";
  // A step held for its engine names the engine it waits for.
  const shown = started || Boolean(step.held_reason);
  const runsOn = runsOnWords(step.agent, step.engine);
  const when = step.elapsed;
  const after = afterWords(step.after);
  const line = quote(step.last_checkpoint?.line);
  return (
    <li
      className="kit-listrow pg-step"
      data-state={step.state}
      data-selected={selected ? "" : undefined}
      data-contender={contender ? "" : undefined}
      data-testid={contender ? "programs-contender" : "programs-step"}
      data-step={step.id}
    >
      <Button variant="chrome" className="pg-step-main" aria-pressed={selected} onClick={onSelect}
        aria-label={`Step ${step.ordinal}: ${step.title}, ${word}`} data-testid="programs-step-select">
        <span className="pg-step-n" aria-hidden="true">{contender ? "" : step.ordinal}</span>
        <span className="pg-step-title">
          {contender ? <img className="pg-step-sprite" src={spriteUrl("coder", agent, "rest", agent, 20)} alt="" width={20} height={20} /> : null}
          <span className="pg-step-name">{contender ? runsOn : step.title}</span>
          {!contender && after ? <span className="pg-step-after">{after}</span> : null}
        </span>
      </Button>
      <span className="pg-step-track">
        <StationTrack stations={stationsOf(step)} />
        <DotWord tone={stepTone(step.state)} className="pg-step-word" data-testid="programs-step-word"
          title={step.state === "limited" ? stateWords(step.state_word) : undefined}>{word}</DotWord>
      </span>
      <span className="pg-step-chip"><StateChip state={stepChip(step.state)} label={word} wordless={false} /></span>
      <span className="pg-step-agent">
        {shown && !contender ? (
          <>
            {step.gate.review === "person" && step.for_person && (step.state === "pr_open" || step.state === "review") ? null : (
              <img className="pg-step-sprite" src={spriteUrl("coder", agent, "rest", agent, 20)} alt="" width={20} height={20} />
            )}
            <span className="pg-step-agent-name">{runsOn}</span>
          </>
        ) : null}
      </span>
      <span className="pg-step-meta">
        {[shown ? runsOn : "", when, after].filter(Boolean).join(" · ")}
        {line ? <span className="pg-step-meta-line"> · {line}</span> : null}
      </span>
      <span className="pg-step-when">{started ? when : ""}</span>
      <span className="pg-step-line" title={step.last_checkpoint?.line ?? undefined}>{line}</span>
      <span className="pg-step-verbs">
        {step.launch_id ? (
          <Button dense variant="secondary" onClick={() => openRef(`launch:${step.launch_id}`)} data-testid="programs-step-open">Open lane</Button>
        ) : null}
      </span>
    </li>
  );
}

const EFFORTS = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

export function runsOnLabel(profile: string | null | undefined, engine: { short?: string; label?: string } | null | undefined): string {
  const agent = profile === "codex-default" ? "Codex" : profile === "pi-default" ? "pi" : "Claude Code";
  if (profile !== "pi-default") return agent;
  return engine ? `pi · ${engine.short || engine.label}` : "pi · the desk's assignment";
}

/** One step in Drafting: every field writes back through `onChange`. */
export function DraftStepRow({
  index,
  step,
  count,
  selected,
  engineLabel,
  onSelect,
  onChange,
}: {
  index: number;
  step: PlanStep;
  count: number;
  selected?: boolean;
  /** The engine's name for a pi step (from the Program's wire). */
  engineLabel?: string;
  onSelect(): void;
  onChange(next: PlanStep, commit?: boolean): void;
}) {
  const ordinal = index + 1;
  const afterOptions = [
    { value: "", label: "None" },
    ...Array.from({ length: count }, (_, i) => i + 1).filter((n) => n !== ordinal).map((n) => ({ value: String(n), label: `After ${n}` })),
  ];
  const choice: RunsOnChoice = { profile: step.profile || "claude-default", engine: step.engine ?? null };
  return (
    <li className="kit-listrow pg-step pg-draft" data-selected={selected ? "" : undefined} data-testid="programs-draft-step"
      onFocusCapture={onSelect}>
      <span className="pg-step-n" aria-hidden="true">{ordinal}</span>
      <span className="pg-draft-title">
        <StringGadget label={`Step ${ordinal} title`} value={step.title}
          onChange={(title) => onChange({ ...step, title })}
          inputProps={{ onBlur: () => onChange(step, true) }} />
      </span>
      <span className="pg-draft-owns">
        {(step.owns ?? []).slice(0, 2).map((path) => <Token key={path} code>{path}</Token>)}
      </span>
      <span className="pg-draft-runs">
        <RunsOnPicker label={choice.profile === "pi-default" && engineLabel ? `pi · ${engineLabel}` : runsOnLabel(choice.profile, null)}
          value={choice} idle={Boolean(step.prefer_idle)} idleLabel="When idle, for this step"
          onPick={(next) => onChange({ ...step, profile: next.profile, engine: next.engine }, true)}
          onIdle={(next) => onChange({ ...step, prefer_idle: next }, true)} data-testid="programs-draft-runs-on" />
      </span>
      <span className="pg-draft-effort">
        <CycleGadget label={`Step ${ordinal} effort`} value={step.effort ?? "medium"} options={EFFORTS}
          onChange={(effort) => onChange({ ...step, effort: effort as PlanStep["effort"] }, true)} />
      </span>
      <span className="pg-draft-after">
        <CycleGadget label={`Step ${ordinal} after`} value={step.after?.length === 1 ? String(step.after[0]) : step.after?.length ? String(step.after[0]) : ""}
          options={afterOptions} onChange={(value) => onChange({ ...step, after: value ? [Number(value)] : [] }, true)} />
      </span>
      <span className="pg-draft-idle">
        <CheckGadget label="When idle" checked={Boolean(step.prefer_idle)} onChange={(next) => onChange({ ...step, prefer_idle: next }, true)} />
        <span className="pg-draft-idle-word">When idle</span>
      </span>
    </li>
  );
}
