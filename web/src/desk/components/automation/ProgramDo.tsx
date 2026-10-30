/** Programs PG14 — the Do sentence "Run a program": the template, the
 *  control level and the Agent (Runs on). The template and the level are
 *  choice rows (one press each, the one in use pressed); the Agent is the
 *  Programs window's own picker (`programs/RunsOn.tsx`). */
import { Button } from "../../../components/signal/Signal";
import { TEMPLATES } from "../../programs/api";
import { CONTROLS } from "../../programs/model";
import { RunsOnPicker, type RunsOnChoice } from "../../programs/RunsOn";
import type { AutomationDetail } from "./model";

export interface ProgramDraft {
  template: string;
  /** "" = the template's level (or the desk's Control mode). */
  control: string;
  runsOn: RunsOnChoice[];
}

/** The template whose steps come from the Project, not from the goal. */
export const FROM_THE_DESK = "from-the-desk";

export function programDraft(detail: AutomationDetail): ProgramDraft {
  return {
    template: detail.program_template ?? "",
    control: detail.program_control ?? "",
    runsOn: (detail.program_runs_on ?? []).map((row) => ({ profile: row.profile, engine: row.engine ?? null })),
  };
}

export function sameProgram(a: ProgramDraft, b: ProgramDraft): boolean {
  return a.template === b.template && a.control === b.control
    && JSON.stringify(a.runsOn) === JSON.stringify(b.runsOn);
}

/** The fields one Save writes. */
export function programFields(draft: ProgramDraft): Record<string, unknown> {
  return {
    program_template: draft.template,
    program_control: draft.control,
    program_runs_on: draft.runsOn,
  };
}

const AGENT_WORDS: Record<string, string> = {
  "claude-default": "Claude Code", "codex-default": "Codex", "pi-default": "pi",
};

/** `Agent: Claude Code` — the picker's words for the first agent. */
export function agentWords(runsOn: readonly RunsOnChoice[], fallback?: string | null): string {
  const first = runsOn[0];
  if (!first) return fallback ? `Agent: ${fallback}` : "Agent: the template's";
  const name = AGENT_WORDS[first.profile] ?? first.profile;
  if (first.profile !== "pi-default") return `Agent: ${name}`;
  return first.engine ? "Agent: pi on an engine" : "Agent: pi · the desk's assignment";
}

export function ProgramAgent({
  draft,
  fallback,
  onChange,
}: {
  draft: ProgramDraft;
  fallback?: string | null;
  onChange: (draft: ProgramDraft) => void;
}) {
  return (
    <RunsOnPicker
      label={agentWords(draft.runsOn, fallback)}
      value={draft.runsOn[0] ?? null}
      then={draft.runsOn.slice(1)}
      onThen={(next) => draft.runsOn[0] && onChange({ ...draft, runsOn: [draft.runsOn[0], ...next] })}
      onPick={(choice) => onChange({ ...draft, runsOn: [choice, ...draft.runsOn.slice(1).filter((row) =>
        row.profile !== choice.profile || (row.engine ?? null) !== (choice.engine ?? null))] })}
      data-testid="automation-program-agent"
    />
  );
}

export function ProgramDo({
  draft,
  fallbackAgent,
  onChange,
}: {
  draft: ProgramDraft;
  /** The agent the automation runs on now (its wire words). */
  fallbackAgent?: string | null;
  onChange: (draft: ProgramDraft) => void;
}) {
  return (
    <div className="automation-program-do" data-testid="automation-program-do">
      <div className="automation-editor-verbs" role="group" aria-label="Template">
        {TEMPLATES.map((template) => (
          <Button key={template.id} dense variant={draft.template === template.id ? "secondary" : "ghost"}
            aria-pressed={draft.template === template.id} title={template.line}
            onClick={() => onChange({ ...draft, template: template.id })}
            data-testid={`automation-program-template-${template.id}`}>
            {template.name}
          </Button>
        ))}
      </div>
      <div className="automation-editor-verbs" role="group" aria-label="Control">
        {CONTROLS.map((row) => (
          <Button key={row.value} dense variant={draft.control === row.value ? "secondary" : "ghost"}
            aria-pressed={draft.control === row.value} title={row.line}
            onClick={() => onChange({ ...draft, control: draft.control === row.value ? "" : row.value })}
            data-testid={`automation-program-control-${row.value}`}>
            {row.word}
          </Button>
        ))}
        <ProgramAgent draft={draft} fallback={fallbackAgent} onChange={onChange} />
      </div>
    </div>
  );
}
