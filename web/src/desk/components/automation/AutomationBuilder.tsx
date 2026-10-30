/** Guided Automation setup — the five step builder for a blank automation or
 * an existing automation opened through Edit setup. Each step composes the
 * editor that already owns its real API and admission rules. */
import { useEffect, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { PadGadget } from "../../surface";
import { spriteUrl } from "../../sprites";
import { AboutEditor } from "./AboutEditor";
import { PutEditor } from "./PutEditor";
import { WhenEditor } from "./WhenEditor";
import { readNativeAgentOptions, WithEditor, type NativeAgentOption } from "./WithEditor";
import { eventSubjectWords, type AutomationDetail } from "./model";
import { FROM_THE_DESK, ProgramAgent, ProgramDo, programDraft, sameProgram, type ProgramDraft } from "./ProgramDo";
import type { AutomationWhenChoice } from "../../api";

type Step = "do" | "about" | "with" | "when" | "put";
type DoKind = "run" | "hand_to_agent" | "run_program";

const STEPS: Array<{ key: Step; label: string; kind: string; id: string }> = [
  { key: "do", label: "Do", kind: "artifact", id: "guided-do" },
  { key: "about", label: "About", kind: "directory", id: "guided-about" },
  { key: "with", label: "With", kind: "workbench", id: "guided-with" },
  { key: "when", label: "When", kind: "meeting", id: "guided-when" },
  { key: "put", label: "Put it in", kind: "repository", id: "guided-put" },
];

function StepSprite({ kind, id }: { kind: string; id: string }) {
  return <img src={spriteUrl(kind, id, "rest", undefined, 32)} alt="" draggable={false} />;
}

function StepRail({
  current,
  disabled,
  onChoose,
}: {
  current: Step;
  disabled: boolean;
  onChoose: (step: Step) => void;
}) {
  return (
    <nav className="automation-setup-rail" aria-label="Automation setup">
      {STEPS.map((step, index) => (
        <Button
          key={step.key}
          variant={step.key === current ? "primary" : "ghost"}
          className="automation-setup-step"
          aria-current={step.key === current ? "step" : undefined}
          aria-label={`${index + 1}. ${step.label}`}
          disabled={disabled && step.key !== current}
          onClick={() => onChoose(step.key)}
          data-testid={`automation-setup-step-${step.key}`}
        >
          <span className="automation-setup-step-sprite" aria-hidden="true">
            <StepSprite kind={step.kind} id={step.id} />
          </span>
          <span className="automation-setup-step-number">{index + 1}</span>
          <span className="automation-setup-step-label">{step.label}</span>
        </Button>
      ))}
    </nav>
  );
}

function SetupHeading({ step, children }: { step: Step; children?: ReactNode }) {
  const spec = STEPS.find((candidate) => candidate.key === step) ?? STEPS[0];
  return (
    <header className="automation-setup-heading">
      <span className="automation-setup-heading-sprite" aria-hidden="true">
        <StepSprite kind={spec.kind} id={spec.id} />
      </span>
      <span>
        <span className="automation-setup-kicker">Step {STEPS.indexOf(spec) + 1} of 5</span>
        <h2>{spec.label}</h2>
        {children}
      </span>
    </header>
  );
}

function DoStep({
  kind,
  draft,
  program,
  agent,
  onKind,
  onDraft,
  onProgram,
}: {
  kind: DoKind;
  draft: string;
  program: ProgramDraft;
  agent: string | null;
  onKind: (kind: DoKind) => void;
  onDraft: (draft: string) => void;
  onProgram: (program: ProgramDraft) => void;
}) {
  const label = kind === "hand_to_agent" ? "Agent brief" : kind === "run_program" ? "Goal" : "What it does";
  return (
    <div className="automation-setup-step-body" data-testid="automation-setup-do">
      <SetupHeading step="do" />
      <div className="automation-setup-choice-row" aria-label="Do kind">
        <Button dense variant={kind === "run" ? "secondary" : "ghost"} aria-pressed={kind === "run"}
          onClick={() => onKind("run")}>Make a result</Button>
        <Button dense variant={kind === "hand_to_agent" ? "secondary" : "ghost"}
          aria-pressed={kind === "hand_to_agent"} onClick={() => onKind("hand_to_agent")}>
          Hand to an agent
        </Button>
        <Button dense variant={kind === "run_program" ? "secondary" : "ghost"}
          aria-pressed={kind === "run_program"} onClick={() => onKind("run_program")}
          data-testid="automation-do-run-program">
          Run a program
        </Button>
      </div>
      {kind === "run_program" ? <ProgramDo draft={program} fallbackAgent={agent} onChange={onProgram} /> : null}
      <PadGadget
        label={label}
        value={draft}
        onChange={onDraft}
        rows={5}
        autoGrow
        autoFocus
        placeholder={kind === "hand_to_agent" ? "Say what the agent should do"
          : kind === "run_program" ? "Say what the program should do" : "Say what it should do each time"}
      />
    </div>
  );
}

function ReviewStep({
  value,
  onChoose,
}: {
  value: string;
  onChoose: (value: string) => Promise<boolean>;
}) {
  const [agents, setAgents] = useState<NativeAgentOption[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { void readNativeAgentOptions().then(setAgents).catch(() => setAgents([])); }, []);
  const choices = [
    ["none", "None"],
    ...(agents ?? []).filter((agent) => agent.ready).map((agent) => [
      agent.agentId,
      agent.agentId === "codex" ? "Codex" : agent.label,
    ] as const),
  ] as ReadonlyArray<readonly [string, string]>;
  const choose = async (key: string) => {
    setError(null);
    if (!(await onChoose(key))) setError("Review choice not saved. Automation stays open. Choose again.");
  };
  return (
    <section className="automation-setup-subsection" aria-label="Review by">
      <span className="automation-setup-subheading">Review by</span>
      <div className="automation-setup-choice-row">
        {choices.map(([key, label]) => (
          <Button key={key} dense variant={value === key ? "secondary" : "ghost"}
            aria-pressed={value === key} onClick={() => void choose(key)}>
            {label}
          </Button>
        ))}
      </div>
      {error ? <p className="automation-setup-error" role="alert">{error}</p> : null}
    </section>
  );
}

export function AutomationBuilder({
  detail,
  pending,
  whenSaving,
  saveError,
  onSaveDo,
  onSaveSources,
  onChooseEngine,
  onSpendLimit,
  onChooseWhen,
  onChoosePut,
  onChooseReview,
  onPending,
  onDone,
}: {
  detail: AutomationDetail;
  pending: boolean;
  whenSaving: string | null;
  saveError: string | null;
  onSaveDo: (kind: DoKind, instruction: string, program?: ProgramDraft) => Promise<boolean>;
  onSaveSources: (sources: string[]) => Promise<boolean>;
  onChooseEngine: (profileId: string) => Promise<boolean>;
  onSpendLimit: (limit: number | null) => Promise<boolean>;
  onChooseWhen: (choice: AutomationWhenChoice, key: string) => Promise<boolean>;
  onChoosePut: (target: string) => Promise<boolean>;
  onChooseReview: (reviewBy: string) => Promise<boolean>;
  onPending: (pending: Promise<unknown>) => void;
  onDone: () => void;
}) {
  const initialKind: DoKind = detail.do_kind === "hand_to_agent" || detail.do_kind === "run_program" ? detail.do_kind : "run";
  const initialProgram = programDraft(detail);
  const initialInstruction = detail.instruction ?? detail.instruction_shown ?? "";
  const [step, setStep] = useState<Step>("do");
  const [savedKind, setSavedKind] = useState<DoKind>(initialKind);
  const [savedInstruction, setSavedInstruction] = useState(initialInstruction);
  const [draftKind, setDraftKind] = useState<DoKind>(initialKind);
  const [draft, setDraft] = useState(initialInstruction);
  const [savedProgram, setSavedProgram] = useState(initialProgram);
  const [program, setProgram] = useState(initialProgram);
  const [navigationError, setNavigationError] = useState<string | null>(null);
  const doDirty = draftKind !== savedKind || draft.trim() !== savedInstruction.trim()
    || (draftKind === "run_program" && !sameProgram(program, savedProgram));
  // PG14: From the desk takes its steps from the Project, so its goal may be empty.
  const doReady = draftKind === "run_program"
    ? Boolean(program.template) && (program.template === FROM_THE_DESK || Boolean(draft.trim()))
    : Boolean(draft.trim());
  const blocked = pending || Boolean(whenSaving);

  const chooseStep = (next: Step) => {
    if (next === step || blocked || (saveError && step !== "do")) return;
    if (step === "do" && (doDirty || !doReady)) {
      setNavigationError("Save Do before you go to another step.");
      return;
    }
    setNavigationError(null);
    setStep(next);
  };

  const next = async () => {
    setNavigationError(null);
    if (blocked || (saveError && step !== "do")) return;
    if (step === "do") {
      if (!doReady) {
        setNavigationError(draftKind === "run_program" && !program.template
          ? "Choose a template before Next." : "Add what it should do before Next.");
        return;
      }
      if (doDirty) {
        const saved = draftKind === "run_program"
          ? await onSaveDo(draftKind, draft.trim(), program)
          : await onSaveDo(draftKind, draft.trim());
        if (!saved) return;
        setSavedKind(draftKind);
        setSavedInstruction(draft.trim());
        setSavedProgram(program);
      }
      setStep("about");
      return;
    }
    if (step === "about") setStep("with");
    else if (step === "with") setStep("when");
    else if (step === "when") setStep("put");
    else onDone();
  };

  const back = () => {
    if (blocked) return;
    setNavigationError(null);
    const index = STEPS.findIndex((candidate) => candidate.key === step);
    if (index > 0) setStep(STEPS[index - 1].key);
  };

  const vendor = detail.assignment_summary?.vendor || null;
  const sources = detail.sources_shown ?? [];
  const happened = eventSubjectWords(detail);
  return (
    <div className="automation-setup" data-testid="automation-setup">
      <StepRail current={step}
        disabled={blocked || Boolean(saveError && step !== "do") || (step === "do" && (doDirty || !doReady))}
        onChoose={chooseStep} />
      <div className="automation-setup-well surface-group-well">
        {step === "do" ? (
          <DoStep kind={draftKind} draft={draft} program={program} agent={detail.program?.runs_on_words ?? null}
            onKind={setDraftKind} onDraft={setDraft} onProgram={setProgram} />
        ) : null}
        {step === "about" ? (
          <div className="automation-setup-step-body" data-testid="automation-setup-about">
            <SetupHeading step="about" />
            {happened ? (
              <div className="automation-setup-about-event">
                <p>{happened}</p>
                <AboutEditor sources={sources} busy={pending} folders foldersOnly
                  onChange={(refs) => void onSaveSources(refs)} />
              </div>
            ) : (
              <AboutEditor sources={sources} busy={pending} folders={Boolean(vendor)}
                onChange={(refs) => void onSaveSources(refs)} />
            )}
          </div>
        ) : null}
        {step === "with" ? (
          <div className="automation-setup-step-body" data-testid="automation-setup-with">
            <SetupHeading step="with" />
            {detail.do_kind === "run_program" ? (
              // PG14: a Program runs on agents, not on an engine assignment.
              <div className="automation-setup-choice-row">
                <ProgramAgent draft={savedProgram} fallback={detail.program?.runs_on_words}
                  onChange={(next) => {
                    void onSaveDo("run_program", savedInstruction.trim(), next).then((saved) => {
                      if (saved) { setSavedProgram(next); setProgram(next); }
                    });
                  }} />
              </div>
            ) : (
            <WithEditor detail={detail} handMode={detail.do_kind === "hand_to_agent"}
              onUse={async (profileId) => {
                if (!(await onChooseEngine(profileId))) throw new Error("Engine choice not saved. Automation stays open. Choose again.");
              }}
              onSpendLimit={async (limit) => {
                if (!(await onSpendLimit(limit))) throw new Error("Spend limit not saved. Automation stays open. Try again.");
              }}
              onPending={onPending} />
            )}
            {detail.do_kind === "hand_to_agent" ? (
              <ReviewStep value={detail.review_by || "none"} onChoose={onChooseReview} />
            ) : null}
          </div>
        ) : null}
        {step === "when" ? (
          <div className="automation-setup-step-body" data-testid="automation-setup-when">
            <SetupHeading step="when" />
            <WhenEditor detail={detail} saving={whenSaving}
              onChoose={(choice, key) => void onChooseWhen(choice, key)} />
          </div>
        ) : null}
        {step === "put" ? (
          <div className="automation-setup-step-body" data-testid="automation-setup-put">
            <SetupHeading step="put" />
            <PutEditor target={detail.output_target}
              onChoose={async (target) => {
                if (!(await onChoosePut(target))) throw new Error("Destination not saved. Automation stays open. Choose again.");
              }} />
          </div>
        ) : null}
        {navigationError ? <p className="automation-setup-error" role="alert">{navigationError}</p> : null}
        {saveError ? <p className="automation-setup-error" role="alert">{saveError}</p> : null}
        <div className="automation-setup-footer">
          <Button variant="ghost" disabled={blocked || step === "do"} onClick={back} data-testid="automation-setup-back">
            Back
          </Button>
          <Button variant="primary" disabled={blocked} loading={pending} onClick={() => void next()}
            data-testid={step === "put" ? "automation-setup-done" : "automation-setup-next"}>
            {step === "put" ? "Done" : "Next"}
          </Button>
        </div>
      </div>
    </div>
  );
}
