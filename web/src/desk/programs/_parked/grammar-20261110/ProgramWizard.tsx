/* Parked: the live kit owns the Programs window grammar. */
/* New program (owner, live walk 2026-11-08: "I expected 'new program' to,
 * ideally, launch some kind of a wizard … add effects"): a wizard page
 * INSIDE the Programs window. The window's body is the wizard; the
 * toolbar stays. No modal, no overlay.
 *
 * Direction W2, "the object leads" (owner pick 2026-11-08): four screens,
 * each about one object, never a label.
 *   1 The project rows; a picked row grows into the project card (its
 *     sprite at 44, its name, one quiet line, Change). The only project or
 *     the scope's project opens on the card, so Next is one press.
 *   2 The card, then Title and the Brief pad (the pad fills the screen).
 *     The template chips sit above the title only when the template is
 *     not the default; else the card's quiet line holds Template · Fast cycle.
 *   3 The card, then the control level as one segmented control of three
 *     (the desk's level pressed), its meaning in one fact line, Agent,
 *     Review, Person (who reviews the person-gated steps; "Nobody yet"
 *     until he picks one), Check, and the Spending note (HS-S24, D20/G24
 *     disclosure-only: an amount he reads on the Program, never a cap).
 *   4 The card, then the summary rows; the bar's primary is Create.
 * Under each screen the next screen's first row peeks (dead, muted).
 * The title bar reads "New program · <project>" and carries the progress
 * dots; the frame's narrow Back says Cancel; the frame's close and Escape
 * cancel on the desk (back to the list; the window stays).
 * At phone width (the surface container under 480) the levels say their
 * short words and Check and Spending fold into one quiet row; a press on
 * it opens Check.
 * The bar: Back · Next / Create. Create posts one captured body to POST
 * /api/programs (only the fields he set, beside title and template) and
 * opens the made Program in Drafting. Only the two refusals the hub
 * proves before a save (400 repository_required, 409 no_repository) say
 * "Not made"; any other failure is "not confirmed", never retried. */
import { Fragment, useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { ApiError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { spriteUrl } from "../sprites";
import {
  ActionNotice, FilterTokens, GadgetGroup, GadgetRow, PadGadget, ProgressDots, StringGadget, SurfaceState, useWindowBack, useWindowTitle, useWindowWings,
} from "../surface";
import { readControlMode } from "../hand/begin";
import { ListRow, ListView } from "../surface/objects/ListView";
import { TEMPLATES, createProgram, defaultProjectId, readProjectChoices, type CreateBody, type ProjectChoice } from "./api";
import type { NewProgramPrefill } from "./newProgram";
import { PersonPicker, type PersonChoice } from "./PersonPicker";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { runsOnLabel } from "./StepRow";
import { CONTROLS, controlValue } from "./model";
import type { Control } from "./types";

export const DEFAULT_TITLE = "New program";
/** The "A folder on this machine" row's value. */
const FOLDER = "folder";
// The steps have no names on the face (owner, 2026-11-08: "still uses the
// super unprofessional what where how and why"); the keys order the dots.
const STEPS = ["project", "goal", "runs", "create"] as const;
/** The wizard always has its four steps (never a count of zero). */
const STEP_TOTAL = STEPS.length;

/** The template a New program starts on (the toolbar's New program). */
const DEFAULT_TEMPLATE = "fast-cycle";

/** The control ladder in his words, hands-off first. */
const LEVELS: readonly { value: Control; word: string; short: string }[] = [
  { value: "yolo", word: "Runs by itself", short: "By itself" },
  { value: "normal", word: "Asks before it merges or sends", short: "Asks to merge" },
  { value: "secure", word: "Asks at every step", short: "Asks each step" },
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

/** What each level means, in his words (the Program window's ladder lines). */
const levelLine = (value: Control) => CONTROLS.find((row) => row.value === value)?.line ?? "";

/** The next screen's first row, dead: it names what comes and shows its
 *  first control's outline. Next is the press, never this. */
function Peek({ step }: { step: number }) {
  if (step >= STEPS.length - 1) return null;
  const words = ["Next · the goal", "Next · how it runs", "Next · create"][step];
  const preview = step === 0 ? <span className="pg-wiz-peek-field">Title</span>
    : step === 1 ? <span className="pg-wiz-peek-levels">{LEVELS.map((row) => <span key={row.value}>{row.word}</span>)}</span>
      : <span className="pg-wiz-peek-plate">Create</span>;
  return (
    <div className="pg-wiz-peek" aria-hidden="true" inert data-testid="programs-wizard-peek">
      <span className="pg-wiz-peek-words">{words}</span>
      {preview}
    </div>
  );
}

export function ProgramWizard({ template: firstTemplate, prefill, scopeProjectId, programsOf, onClose, onMade, onPending, reload }: {
  template: string;
  /** Filled in by the window that opened it (an old queue automation's tasks as steps). */
  prefill?: NewProgramPrefill;
  /** The project of the window's scope (opened from a Room or a project). */
  scopeProjectId?: string | null;
  /** How many Programs each project has (the card's quiet line; no zero). */
  programsOf?: Readonly<Record<string, number>>;
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
  // The rows are open again (Change), or the card a press just grew.
  const [changing, setChanging] = useState(false);
  const [grown, setGrown] = useState(false);
  const [folder, setFolder] = useState("");
  const [template, setTemplate] = useState(firstTemplate);
  const [chips, setChips] = useState(false);
  const [title, setTitle] = useState(prefill?.title ?? "");
  const [goal, setGoal] = useState(prefill?.goal ?? "");
  const [control, setControl] = useState<Control | "">("");
  const [deskLevel, setDeskLevel] = useState<Control | null>(null);
  const [agent, setAgent] = useState<RunsOnChoice | null>(null);
  const [reviewer, setReviewer] = useState<RunsOnChoice | null>(null);
  const [person, setPerson] = useState<PersonChoice | null>(null);
  const [check, setCheck] = useState("");
  const [spend, setSpend] = useState("");
  // At phone width Check and Spending fold into one row; a press opens Check.
  const [checkOpen, setCheckOpen] = useState(false);
  const [outcome, setOutcome] = useState<Outcome>({ kind: "idle" });
  const inFlight = useRef(false);
  const alive = useRef(true);
  const rootRef = useRef<HTMLElement>(null);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const pending = outcome.kind === "pending";
  useEffect(() => { onPending(pending); }, [onPending, pending]);
  useEffect(() => () => onPending(false), [onPending]);
  // A template press in the toolbar while the wizard is open changes its template.
  useEffect(() => { setTemplate(firstTemplate); }, [firstTemplate]);
  // The desk's level, pressed on the runs screen until he presses another.
  useEffect(() => {
    let live = true;
    void readControlMode().then((mode) => { if (live && mode) setDeskLevel(controlValue(mode)); });
    return () => { live = false; };
  }, []);

  const rows = choices.state === "ready" ? choices.rows : [];
  const project = rows.find((row) => row.id === where) ?? null;
  const placeName = where === FOLDER ? folder.trim() : project?.name ?? "";
  const made = outcome.kind === "made" ? outcome.id : "";
  const locked = pending || Boolean(made);
  const ready = [Boolean(project) || (where === FOLDER && Boolean(folder.trim())), true, true, true];
  const last = STEPS.length - 1;
  const picked = Boolean(project) || where === FOLDER;
  const carded = picked && !changing;

  // The title bar reads the picked object.
  useWindowTitle(placeName ? `${DEFAULT_TITLE} · ${placeName}` : DEFAULT_TITLE, [placeName]);
  const leave = () => { if (!pending) onClose(); };
  // The frame's close is Cancel too: back to the list, the window stays.
  useWindowBack({
    onBack: leave, testId: "programs-wizard-back-frame", label: "Cancel",
    onCloseRequest: () => { leave(); return true; },
  }, [pending]);
  // The progress dots ride the title bar's right end.
  useWindowWings(
    <ProgressDots className="pg-wiz-progress" data-keeps-title="" data-testid="programs-wizard-dots"
      count={STEP_TOTAL} at={step} done={(at) => at < step} label={`Step ${step + 1} of ${STEP_TOTAL}`} />,
    [step],
  );

  useEffect(() => {
    let live = true;
    setChoices({ state: "loading" });
    readProjectChoices()
      .then((rows) => {
        if (!live || !alive.current) return;
        setChoices({ state: "ready", rows });
        // The scope's project, else the only project: chosen for him.
        setWhere((now) => now || defaultProjectId(rows, scopeProjectId));
      })
      .catch(() => { if (live && alive.current) setChoices({ state: "failed" }); });
    return () => { live = false; };
  }, [readNonce, scopeProjectId]);

  // Focus follows the screen: its first control; with the card up on the
  // first screen (or on the last), the bar's primary.
  useEffect(() => {
    if (choices.state === "loading") return;
    const root = rootRef.current;
    const screen = root?.querySelector<HTMLElement>(".pg-wiz-step");
    const primary = "[data-testid=programs-wizard-next], [data-testid=programs-wizard-create]";
    const order: [HTMLElement | null | undefined, string][] = step === last ? [[root, primary]]
      : step === 0 ? (carded ? [[screen, "input"], [root, primary]] : [[screen, "[aria-current] button"], [screen, ".kit-listrow button"]])
        : step === 1 ? [[screen, "input"]] : [[screen, "button:not([disabled])"], [screen, "input"]];
    for (const [scope, selector] of order) {
      const first = scope?.querySelector<HTMLElement>(selector);
      if (first) { first.focus(); break; }
    }
  }, [step, choices.state, carded, last]);

  useEffect(() => {
    if (checkOpen) rootRef.current?.querySelector<HTMLElement>(".pg-wiz-check input")?.focus();
  }, [checkOpen]);

  const go = (next: number) => {
    if (locked || next < 0 || next > last) return;
    if (next > step && !ready.slice(0, next).every(Boolean)) return;
    setDir(next > step ? "on" : "back");
    setGrown(false);
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
    ...(person ? { for_person_id: person.id } : {}),
    ...(check.trim() ? { check_command: check.trim() } : {}),
    ...(spendAmount(spend) !== null ? { spend_limit_usd: spendAmount(spend)! } : {}),
    ...(prefill?.steps?.length ? { steps: prefill.steps } : {}),
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
    setChanging(false);
    setGrown(true);
    if (id !== where && (outcome.kind === "refused" || outcome.kind === "unknown")) setOutcome({ kind: "idle" });
  };

  // The card: the picked object at the top of every screen.
  const level = control || deskLevel;
  const count = where && where !== FOLDER ? programsOf?.[where] ?? 0 : 0;
  const showChips = template !== DEFAULT_TEMPLATE || chips;
  const quiet: ReactNode[] = [];
  if (count) quiet.push(count === 1 ? "1 program" : `${count} programs`);
  if (step === 1 && !showChips) {
    quiet.push(
      <Button key="template" dense variant="ghost" className="pg-wiz-card-template" disabled={locked}
        onClick={() => setChips(true)} data-testid="programs-wizard-template">
        {`Template · ${templateName(template)}`}
      </Button>,
    );
  } else if (step !== 1) {
    quiet.push(templateName(template));
  }
  const card = carded ? (
    <div className="pg-wiz-card" data-grow={grown ? "" : undefined} data-testid="programs-wizard-card">
      <img className="pg-wiz-card-glyph" src={spriteUrl("project", where === FOLDER ? "folder" : where, "rest", null, 64)}
        alt="" width={44} height={44} draggable={false} />
      <span className="pg-wiz-card-text">
        <span className="pg-wiz-card-name" data-testid={step === last ? "programs-wizard-sum-where" : "programs-wizard-card-name"}>
          {placeName || "A folder on this machine"}
        </span>
        {quiet.length ? (
          <span className="pg-wiz-card-line" data-testid="programs-wizard-card-line">
            {quiet.map((part, at) => (
              <Fragment key={at}>{at ? <span aria-hidden="true">{" · "}</span> : null}{part}</Fragment>
            ))}
          </span>
        ) : null}
      </span>
      {step === 0 ? (
        <Button dense variant="secondary" disabled={locked} onClick={() => setChanging(true)} data-testid="programs-wizard-change">Change</Button>
      ) : null}
    </div>
  ) : null;

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
    } else if (carded) {
      page = where === FOLDER ? (
        <div className="pg-wiz-folder" data-testid="programs-wizard-folder-field">
          <StringGadget label="Folder" caption value={folder} onChange={setFolder} placeholder="~/dev/my-repo" mic={false} />
        </div>
      ) : null;
    } else {
      page = (
        <ListView label="Project" className="pg-wiz-where" data-testid="programs-wizard-where">
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
        </ListView>
      );
    }
  } else if (step === 1) {
    page = (
      <div className="pg-wiz-goal">
        {showChips ? (
          <FilterTokens label="Template" className="pg-wiz-templates" value={template} onChange={setTemplate}
            options={TEMPLATES.map((row) => ({ value: row.id, label: row.name, ariaLabel: `${row.name} · ${row.line}` }))} />
        ) : null}
        <span className="pg-wiz-title">
          <StringGadget label="Title" value={title} onChange={setTitle} placeholder="Title" />
        </span>
        <PadGadget label="Brief" value={goal} onChange={setGoal} rows={6} placeholder="Brief" />
      </div>
    );
  } else if (step === 2) {
    page = (
      <div className="pg-wiz-runs" data-check-open={checkOpen ? "" : undefined}>
        <span className="pg-wiz-levels" role="group" aria-label="Runs" data-testid="programs-wizard-levels">
          {LEVELS.map((row) => (
            <Button key={row.value} variant={row.value === level ? "secondary" : "ghost"} aria-pressed={row.value === level}
              aria-label={row.word} className="pg-wiz-level" disabled={locked} onClick={() => setControl(row.value)} data-testid={`programs-wizard-level-${row.value}`}>
              <span className="pg-wiz-level-word">{row.word}</span>
              <span className="pg-wiz-level-short" aria-hidden="true">{row.short}</span>
            </Button>
          ))}
        </span>
        {level ? <span className="pg-wiz-fact" data-testid="programs-wizard-level-line">{levelLine(level)}</span> : null}
        <GadgetGroup material="inset">
          <GadgetRow label="Agent">
            <RunsOnPicker label={agent ? agentWord(agent) : "The template's"} value={agent}
              onPick={setAgent} data-testid="programs-wizard-agent" />
          </GadgetRow>
          <GadgetRow label="Review">
            <RunsOnPicker label={reviewer ? agentWord(reviewer) : "The template's"} value={reviewer}
              onPick={setReviewer} data-testid="programs-wizard-reviewer" />
          </GadgetRow>
          <GadgetRow label="Person">
            <PersonPicker value={person} onPick={setPerson} disabled={locked} data-testid="programs-wizard-person" />
          </GadgetRow>
          <GadgetRow label="Check">
            <span className="pg-wiz-check">
              <StringGadget label="Check" value={check} onChange={setCheck} placeholder="The repository's check" mic={false} />
            </span>
          </GadgetRow>
          <GadgetRow label="Spending">
            <span className="pg-wiz-spending" data-testid="programs-wizard-spending">
              <StringGadget label="Spending note" value={spend} onChange={setSpend} placeholder="No note · USD"
                inputProps={{ inputMode: "decimal" }} />
            </span>
          </GadgetRow>
        </GadgetGroup>
        <Button dense variant="ghost" className="pg-wiz-fold" disabled={locked} onClick={() => setCheckOpen(true)} data-testid="programs-wizard-fold">
          {`Check · ${check.trim() || "The repository's"} · ${spendWords(spend) ?? "No spend note"}`}
        </Button>
      </div>
    );
  } else {
    const how = [
      level ? LEVELS.find((row) => row.value === level)!.word : "Your desk's level",
      agent ? agentWord(agent) : "",
      reviewer && !person ? `${agentWord(reviewer)} reviews` : "",
      check.trim() ? `check: ${check.trim()}` : "",
      spendWords(spend) ?? "",
    ].filter(Boolean).join(" · ");
    // A person reviews the person-gated steps: the Review row names both.
    const review = person ? `${reviewer ? agentWord(reviewer) : "The template's"} · ${person.name} reviews` : "";
    page = (
      <GadgetGroup material="inset">
        <div className="pg-wiz-summary" data-testid="programs-wizard-summary">
          <GadgetRow label="Title" fact={<span data-testid="programs-wizard-sum-title">{`${title.trim() || DEFAULT_TITLE} · ${templateName(template)}`}</span>}>{null}</GadgetRow>
          <GadgetRow label="Runs" fact={<span data-testid="programs-wizard-sum-how">{how}</span>}>{null}</GadgetRow>
          {review ? (
            <GadgetRow label="Review" fact={<span data-testid="programs-wizard-sum-review">{review}</span>}>{null}</GadgetRow>
          ) : null}
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
    <section ref={rootRef} className="pg-wiz" aria-label="New program" data-testid="programs-wizard" data-template={template} data-step={step + 1}
      onKeyDown={onKeyDown}>
      {card}
      <div key={step} className="pg-wiz-step" data-dir={dir} data-testid={`programs-wizard-step-${step + 1}`}>
        {page}
        {choices.state === "ready" ? <Peek step={step} /> : null}
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
        {outcome.kind === "unknown" ? (
          <Button dense variant="ghost" onClick={() => void reload()} data-testid="programs-wizard-look">Look at the list</Button>
        ) : null}
        {step > 0 ? (
          <Button variant="secondary" className="pg-wiz-back" disabled={locked} onClick={() => go(step - 1)} data-testid="programs-wizard-back">Back</Button>
        ) : null}
        {made ? (
          <Button variant="primary" className="pg-wiz-go" onClick={() => onMade(made)} data-testid="programs-wizard-open">Open the program</Button>
        ) : step < last ? (
          <Button variant="primary" className="pg-wiz-go" disabled={!ready[step] || locked} onClick={() => go(step + 1)} data-testid="programs-wizard-next">Next</Button>
        ) : (
          <Button variant="primary" className="pg-wiz-go" loading={pending} disabled={pending} onClick={() => void create()} data-testid="programs-wizard-create">Create</Button>
        )}
      </div>
    </section>
  );
}

/** HS-S24: the amount he typed, or null (empty, not a number, below zero). */
function spendAmount(text: string): number | null {
  const words = text.trim().replace(/^\$/, "").replace(/\s*usd$/i, "");
  if (!words) return null;
  const value = Number(words);
  return Number.isFinite(value) && value >= 0 ? value : null;
}

/** The hub's own words (program_reads.spend_note): "spend note · 40 USD". */
function spendWords(text: string): string | null {
  const value = spendAmount(text);
  if (value === null) return null;
  return `spend note · ${Number.isInteger(value) ? String(value) : value.toFixed(2)} USD`;
}
