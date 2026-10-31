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
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { afterWords, agentKey, mergedWords, runsOnWords, stationsOf, stepChip, stepMetWords, stepTone, stepWord } from "./model";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { StationTrack } from "./StationTrack";
import { stateWords } from "../surface/words";
import type { PlanSize, PlanStep, ProgramStep } from "./types";

function quote(line: string | undefined | null): string {
  return line ? `“${line}”` : "";
}

/** PG-REQ §9 Delight: the step's Met cell. When its last required
 *  requirement goes Met the count draws in ok ink and the dot breathes
 *  once (the 2.4 s ring, once; none under reduced motion). */
function MetCell({ step, his }: { step: ProgramStep; his?: boolean }) {
  const met = stepMetWords(step.requirements_met, his);
  const was = useRef(met?.all ?? false);
  const [settled, setSettled] = useState(false);
  useEffect(() => {
    const all = met?.all ?? false;
    if (all && !was.current) {
      setSettled(true);
      const timer = window.setTimeout(() => setSettled(false), 2600);
      was.current = all;
      return () => window.clearTimeout(timer);
    }
    was.current = all;
    return undefined;
  }, [met?.all]);
  return (
    <span className="pg-step-met" data-testid="programs-step-met" data-all={met?.all ? "" : undefined} data-tone={met?.tone ?? undefined}
      data-settled={settled ? "" : undefined}>
      {met?.tone ? <span className="kit-dot pg-step-met-dot" data-tone={met.tone} aria-hidden="true" /> : null}
      {met?.text ?? ""}
    </span>
  );
}

export function StepRow({
  step,
  selected,
  onSelect,
  contender = false,
  his = false,
  landed,
}: {
  step: ProgramStep;
  selected?: boolean;
  onSelect?: () => void;
  contender?: boolean;
  /** A requirement of this step waits on his word. */
  his?: boolean;
  /** PG-LANG §9.7: the step an applied text added (born) or changed. */
  landed?: "born" | "changed";
}) {
  const word = stepWord(step);
  const agent = agentKey(step.profile, step.agent);
  const started = step.state !== "planned" && step.state !== "ready";
  // PG17: an imported step names its PR and its merge time; no agent ran it.
  const history = step.history ?? null;
  // A step held for its engine names the engine it waits for.
  const shown = !history && (started || Boolean(step.held_reason));
  const runsOn = runsOnWords(step.agent, step.engine);
  const when = history ? mergedWords(history.merged_at) : step.elapsed;
  const after = afterWords(step.after);
  const line = history ? `PR #${history.pr_number}` : quote(step.last_checkpoint?.line);
  return (
    <li
      className="kit-listrow pg-step"
      data-state={step.state}
      data-selected={selected ? "" : undefined}
      data-contender={contender ? "" : undefined}
      data-testid={contender ? "programs-contender" : "programs-step"}
      data-step={step.id}
      data-history={history ? "" : undefined}
      data-landed={landed}
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
      {contender ? <span className="pg-step-met" /> : <MetCell step={step} his={his} />}
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
        {[shown ? runsOn : "", stepMetWords(step.requirements_met, his)?.text ?? "", when, after].filter(Boolean).join(" · ")}
        {line ? <span className="pg-step-meta-line"> · {line}</span> : null}
      </span>
      <span className="pg-step-when">{started ? when : ""}</span>
      <span className="pg-step-line" title={history ? history.pr_url ?? undefined : step.last_checkpoint?.line ?? undefined}
        data-testid={history ? "programs-step-pr" : undefined}>{line}</span>
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
  size,
  landed,
  onSelect,
  onChange,
}: {
  index: number;
  step: PlanStep;
  count: number;
  selected?: boolean;
  /** PG-LANG §5.4 (LANG7): the step's size by rule (`7k of 32k`). */
  size?: PlanSize | null;
  /** PG-LANG §9.7: a step the applied draft added (born) or changed. */
  landed?: "born" | "changed";
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
      data-landed={landed} style={landed ? ({ "--i": index } as CSSProperties) : undefined}
      onFocusCapture={onSelect}>
      <span className="pg-step-n" aria-hidden="true">{ordinal}</span>
      <span className="pg-draft-title">
        <StringGadget label={`Step ${ordinal} title`} value={step.title}
          onChange={(title) => onChange({ ...step, title })}
          inputProps={{ onBlur: () => onChange(step, true) }} />
      </span>
      <span className="pg-draft-owns">
        {size ? (
          <span className="pg-size" data-fits={size.fits === false ? "no" : size.fits ? "yes" : undefined}
            title={size.fits === false ? size.words : undefined} data-testid="programs-draft-size">
            {size.fits === false ? size.words.replace(/^Too big for .* · /, "") : size.words}
          </span>
        ) : null}
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
