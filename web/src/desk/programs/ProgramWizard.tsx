/* New program (owner, live walk 2026-11-08: "I expected 'new program' to,
 * ideally, launch some kind of a wizard … add effects"): a wizard page
 * INSIDE the Programs window. The window's body is the wizard; the
 * toolbar stays; the title bar says "New program". No modal, no overlay.
 *
 * Four steps, one screen each:
 *   1 Where: the project rows (the desk's project rows), the scope's
 *     project or the only project preselected; "A folder on this machine"
 *     last, with its Folder field.
 *   2 What: the title and the brief (mic on both), the template tokens.
 *   3 How: what the Program may do on its own (the control level in his
 *     words), the agent and the reviewer, the check; spending is a fact
 *     line (HS-S24: a note, not a cap).
 *   4 Go: one summary sheet, then Create.
 * Bottom bar: Back · Next / Create, the progress dots. Escape returns to
 * the list, nothing saved. Create posts one captured body to POST
 * /api/programs (only the fields he set, beside title and template) and
 * opens the made Program in Drafting. Only the two refusals the hub
 * proves before a save (400 repository_required, 409 no_repository) say
 * "Not made"; any other failure is "not confirmed", never retried. */
import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { ApiError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { spriteUrl } from "../sprites";
import {
  ActionNotice, FilterTokens, GadgetGroup, GadgetRow, PadGadget, StringGadget, SurfaceState, useWindowBack, useWindowTitle,
} from "../surface";
import { ListRow, ListView } from "../surface/objects/ListView";
import { TEMPLATES, createProgram, readProjectChoices, type CreateBody, type ProjectChoice } from "./api";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { runsOnLabel } from "./StepRow";
import type { Control } from "./types";

export const DEFAULT_TITLE = "New program";
/** The "A folder on this machine" row's value. */
const FOLDER = "folder";
const STEPS = ["Where", "What", "How", "Go"] as const;

/** The control ladder in his words, hands-off first. */
const LEVELS: readonly { value: Control; word: string }[] = [
  { value: "yolo", word: "Runs by itself" },
  { value: "normal", word: "Asks before it merges or sends" },
  { value: "secure", word: "Asks at every step" },
];

type Choices = { state: "loading" } | { state: "failed" } | { state: "ready"; rows: ProjectChoice[] };
type Outcome =
  | { kind: "idle" }
  | { kind: "pending"; body: Readonly<CreateBody> }
  | { kind: "refused"; words: string }
  | { kind: "unknown" }
  | { kind: "made"; id: string };

function refusalWords(cause: unknown, placeName: string): string | null {
  if (!(cause instanceof ApiError)) return null;
  const code = cause.payload && typeof cause.payload === "object" ? (cause.payload as { code?: unknown }).code : undefined;
  if (cause.status === 409 && code === "no_repository") return `Not made · ${placeName} has no local repository · Add one in the project, or choose a different project`;
  if (cause.status === 400 && code === "repository_required") return "Not made · Choose a project";
  return null;
}

export function templateName(id: string): string {
  return TEMPLATES.find((template) => template.id === id)?.name ?? id;
}

const agentWord = (choice: RunsOnChoice | null) => (choice ? runsOnLabel(choice.profile, choice.engine ? { label: choice.engine } : null) : "");

export function ProgramWizard({ template: firstTemplate, scopeProjectId, onClose, onMade, onPending, reload }: {
  template: string;
  /** The project of the window's scope (opened from a Room or a project). */
  scopeProjectId?: string | null;
  onClose(): void;
  onMade(id: string): void;
  onPending(pending: boolean): void;
  reload(): Promise<void>;
}) {
  const [choices, setChoices] = useState<Choices>({ state: "loading" });
  const [readNonce, setReadNonce] = useState(0);
  const [step, setStep] = useState(0);
  const [dir, setDir] = useState<"on" | "back">("on");
  const [where, setWhere] = useState("");
  const [folder, setFolder] = useState("");
  const [template, setTemplate] = useState(firstTemplate);
  const [title, setTitle] = useState("");
  const [goal, setGoal] = useState("");
  const [control, setControl] = useState<Control | "">("");
  const [agent, setAgent] = useState<RunsOnChoice | null>(null);
  const [reviewer, setReviewer] = useState<RunsOnChoice | null>(null);
  const [check, setCheck] = useState("");
  const [outcome, setOutcome] = useState<Outcome>({ kind: "idle" });
  const inFlight = useRef(false);
  const alive = useRef(true);
  const stepRef = useRef<HTMLDivElement>(null);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const pending = outcome.kind === "pending";
  useEffect(() => { onPending(pending); }, [onPending, pending]);
  useEffect(() => () => onPending(false), [onPending]);
  // A template press in the toolbar while the wizard is open changes its template.
  useEffect(() => { setTemplate(firstTemplate); }, [firstTemplate]);

  useWindowTitle("New program", []);
  const leave = () => { if (!pending) onClose(); };
  useWindowBack({ onBack: leave, testId: "programs-wizard-back-frame" }, [pending]);

  useEffect(() => {
    let live = true;
    setChoices({ state: "loading" });
    readProjectChoices()
      .then((rows) => {
        if (!live || !alive.current) return;
        setChoices({ state: "ready", rows });
        // The scope's project, else the only project: chosen for him.
        setWhere((now) => now || (scopeProjectId && rows.some((row) => row.id === scopeProjectId) ? scopeProjectId : rows.length === 1 ? rows[0].id : ""));
      })
      .catch(() => { if (live && alive.current) setChoices({ state: "failed" }); });
    return () => { live = false; };
  }, [readNonce, scopeProjectId]);

  // Focus follows the step: its first control.
  useEffect(() => {
    if (choices.state === "loading") return;
    // On Go the one verb is Create, in the bar.
    const root = step === STEPS.length - 1 ? stepRef.current?.parentElement : stepRef.current;
    const order = step === STEPS.length - 1 ? ["[data-testid=programs-wizard-create]"] : step === 0 ? ["[aria-current] button", ".kit-listrow button"] : step === 1 ? ["input"] : ["button:not([disabled])", "input"];
    for (const selector of order) {
      const first = root?.querySelector<HTMLElement>(selector);
      if (first) { first.focus(); break; }
    }
  }, [step, choices.state]);

  const rows = choices.state === "ready" ? choices.rows : [];
  const project = rows.find((row) => row.id === where) ?? null;
  const placeName = where === FOLDER ? folder.trim() : project?.name ?? "";
  const made = outcome.kind === "made" ? outcome.id : "";
  const locked = pending || Boolean(made);
  const ready = [Boolean(project) || (where === FOLDER && Boolean(folder.trim())), true, true, true];
  const last = STEPS.length - 1;

  const go = (next: number) => {
    if (locked || next < 0 || next > last) return;
    if (next > step && !ready.slice(0, next).every(Boolean)) return;
    setDir(next > step ? "on" : "back");
    setStep(next);
  };

  const body = (): CreateBody => ({
    title: title.trim() || DEFAULT_TITLE,
    template,
    ...(where === FOLDER ? { repository: folder.trim() } : { project_id: where }),
    ...(goal.trim() ? { goal: goal.trim() } : {}),
    ...(control ? { control } : {}),
    ...(agent ? { default_profile: agent.profile, ...(agent.engine ? { default_engine: agent.engine } : {}) } : {}),
    ...(reviewer ? { reviewer_profile: reviewer.profile, ...(reviewer.engine ? { reviewer_engine: reviewer.engine } : {}) } : {}),
    ...(check.trim() ? { check_command: check.trim() } : {}),
  });

  const create = async () => {
    if (inFlight.current || made || !ready[0]) return;
    inFlight.current = true;
    const captured: Readonly<CreateBody> = Object.freeze(body());
    const name = placeName;
    setOutcome({ kind: "pending", body: captured });
    try {
      const answer = await createProgram({ ...captured });
      const id = answer && typeof answer === "object" ? (answer as { id?: unknown }).id : undefined;
      if (typeof id !== "string" || !id) {
        if (alive.current) setOutcome({ kind: "unknown" });
        return;
      }
      // The made Program is a fact from here on: keep its id before any reveal.
      if (!alive.current) { void reload(); return; }
      setOutcome({ kind: "made", id });
      onMade(id);
      void reload();
    } catch (cause) {
      if (!alive.current) return;
      const refused = refusalWords(cause, name);
      setOutcome(refused ? { kind: "refused", words: refused } : { kind: "unknown" });
    } finally {
      inFlight.current = false;
    }
  };

  const choose = (id: string) => {
    if (locked) return;
    setWhere(id);
    if (id !== where && (outcome.kind === "refused" || outcome.kind === "unknown")) setOutcome({ kind: "idle" });
  };

  let page: ReactNode;
  if (step === 0) {
    if (choices.state === "loading") {
      page = <div className="pg-wiz-state" data-testid="programs-wizard-reading"><SurfaceState loading /></div>;
    } else if (choices.state === "failed") {
      page = (
        <div className="pg-wiz-state" data-testid="programs-wizard-read-failed">
          <SurfaceState error="The projects did not load" onRetry={() => setReadNonce((value) => value + 1)} />
        </div>
      );
    } else {
      page = (
        <ListView label="Where" className="pg-wiz-where" data-testid="programs-wizard-where">
          <ul className="kit-listrows">
            {rows.map((row) => (
              <ListRow key={row.id} data-testid="programs-wizard-project" openTestId="programs-wizard-pick" nameTestId="programs-wizard-name"
                openLabel={row.name} glyph={spriteUrl("project", row.id, "rest", null, 20)} name={row.name}
                meta={row.line ? <span data-testid="programs-wizard-line">{row.line}</span> : undefined}
                selected={row.id === where} onOpen={locked ? undefined : () => choose(row.id)} />
            ))}
            <ListRow data-testid="programs-wizard-folder-row" openTestId="programs-wizard-folder" openLabel="A folder on this machine"
              glyph={spriteUrl("project", "folder", "rest", null, 20)} name="A folder on this machine"
              selected={where === FOLDER} onOpen={locked ? undefined : () => choose(FOLDER)} />
          </ul>
          {where === FOLDER ? (
            <div className="pg-wiz-folder" data-testid="programs-wizard-folder-field">
              <StringGadget label="Folder" caption value={folder} onChange={setFolder} placeholder="~/dev/my-repo" mic={false} />
            </div>
          ) : null}
        </ListView>
      );
    }
  } else if (step === 1) {
    page = (
      <div className="pg-wiz-what">
        <FilterTokens label="Template" className="pg-wiz-templates" value={template} onChange={setTemplate}
          options={TEMPLATES.map((row) => ({ value: row.id, label: row.name, ariaLabel: `${row.name} · ${row.line}` }))} />
        <StringGadget label="Title" caption value={title} onChange={setTitle} placeholder={DEFAULT_TITLE} />
        <PadGadget label="Brief" value={goal} onChange={setGoal} rows={6} placeholder="The goal, in your words" />
      </div>
    );
  } else if (step === 2) {
    page = (
      <GadgetGroup material="inset">
        <GadgetRow label="Control" controlWidth="full">
          <FilterTokens label="Control" className="pg-wiz-control" value={control} onChange={(next) => setControl(next as Control)}
            emptyLabel="Your desk's level" options={LEVELS.map((row) => ({ value: row.value, label: row.word }))} />
        </GadgetRow>
        <GadgetRow label="Agent">
          <RunsOnPicker label={agent ? `Agent: ${agentWord(agent)}` : "Agent: the template's"} value={agent}
            onPick={setAgent} data-testid="programs-wizard-agent" />
        </GadgetRow>
        <GadgetRow label="Review">
          <RunsOnPicker label={reviewer ? `Review: ${agentWord(reviewer)}` : "Review: the template's"} value={reviewer}
            onPick={setReviewer} data-testid="programs-wizard-reviewer" />
        </GadgetRow>
        <GadgetRow label="Check">
          <StringGadget label="Check" value={check} onChange={setCheck} placeholder="The repository's check" mic={false} />
        </GadgetRow>
        <GadgetRow label="Spending" fact={<span data-testid="programs-wizard-spending">Not capped</span>}>{null}</GadgetRow>
      </GadgetGroup>
    );
  } else {
    const how = [
      control ? LEVELS.find((row) => row.value === control)!.word : "Your desk's level",
      agent ? agentWord(agent) : "",
      reviewer ? `${agentWord(reviewer)} reviews` : "",
      check.trim() ? `check: ${check.trim()}` : "",
    ].filter(Boolean).join(" · ");
    page = (
      <GadgetGroup material="inset">
        <div className="pg-wiz-summary" data-testid="programs-wizard-summary">
          <GadgetRow label="Where" fact={<span data-testid="programs-wizard-sum-where">{placeName}</span>}>{null}</GadgetRow>
          <GadgetRow label="Title" fact={<span data-testid="programs-wizard-sum-title">{`${title.trim() || DEFAULT_TITLE} · ${templateName(template)}`}</span>}>{null}</GadgetRow>
          <GadgetRow label="How" fact={<span data-testid="programs-wizard-sum-how">{how}</span>}>{null}</GadgetRow>
        </div>
      </GadgetGroup>
    );
  }

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key !== "Escape" || event.defaultPrevented) return;
    event.preventDefault();
    event.stopPropagation();
    leave();
  };

  return (
    <section className="pg-wiz" aria-label="New program" data-testid="programs-wizard" data-template={template} data-step={step + 1}
      onKeyDown={onKeyDown}>
      <div key={step} ref={stepRef} className="pg-wiz-step" data-dir={dir} data-testid={`programs-wizard-step-${step + 1}`}>
        <h3 className="kit-listday-label pg-wiz-name">{STEPS[step]}</h3>
        {page}
      </div>
      {outcome.kind === "refused" ? (
        <ActionNotice tone="danger" role="alert"><span data-testid="programs-wizard-refused">{outcome.words}</span></ActionNotice>
      ) : null}
      {outcome.kind === "unknown" ? (
        <ActionNotice tone="warn" role="alert">
          <span data-testid="programs-wizard-unknown">Not confirmed · The program can exist · Look at the list before you try again</span>
        </ActionNotice>
      ) : null}
      {made ? (
        <ActionNotice tone="ok" role="status"><span data-testid="programs-wizard-made">Program made · Its window did not open</span></ActionNotice>
      ) : null}
      <div className="pg-wiz-bar">
        <span className="pg-wiz-dots" aria-label={`Step ${step + 1} of ${STEPS.length}`} role="img" data-testid="programs-wizard-dots">
          {STEPS.map((word, at) => (
            <span key={word} className="pg-wiz-dot" data-state={at === step ? "now" : at < step ? "done" : undefined} />
          ))}
        </span>
        <span className="pg-wiz-verbs">
          {outcome.kind === "unknown" ? (
            <Button dense variant="ghost" onClick={() => void reload()} data-testid="programs-wizard-look">Look at the list</Button>
          ) : null}
          {step === 0 ? (
            <Button dense variant="secondary" disabled={pending} onClick={leave} data-testid="programs-wizard-cancel">{made ? "Close" : "Cancel"}</Button>
          ) : (
            <Button dense variant="secondary" disabled={locked} onClick={() => go(step - 1)} data-testid="programs-wizard-back">Back</Button>
          )}
          {made ? (
            <Button dense variant="primary" onClick={() => onMade(made)} data-testid="programs-wizard-open">Open the program</Button>
          ) : step < last ? (
            <Button dense variant="primary" disabled={!ready[step] || locked} onClick={() => go(step + 1)} data-testid="programs-wizard-next">Next</Button>
          ) : (
            <Button dense variant="primary" loading={pending} disabled={pending} onClick={() => void create()} data-testid="programs-wizard-create">Create</Button>
          )}
        </span>
      </div>
    </section>
  );
}
