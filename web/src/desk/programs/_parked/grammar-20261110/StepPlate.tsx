/* Parked: the live kit owns the Programs window grammar. */
/* The step plate (the language, 2026-11-08; ProgramsBold canvas): the one
 * raised thing of a Program. Under the mast and the step spine, the
 * current step: "03 · Merge" in the display face, when it was asked and
 * the agent in mono, the step's brief as body text, the evidence line in
 * mono (the PR, the check, the files, open the PR), and the verbs: the lead
 * verb is the brass Button (Merge, Decide, Start, Resume), then the other
 * choices, and Earlier steps at the right. What waits on him is the plate
 * (YourTurnWell: the hub's brief in his terms, #1684); the other items are
 * one line each under it. A drafting Program's plate is its plan row
 * (DraftHead: "planned · 4 steps", Start). With nothing that waits on him
 * the plate is the live step (CurrentPlate). */
import { useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { openRef } from "../openObject";
import { DotWord, EditInPlace, StringGadget, countWords } from "../surface";
import { ActionNotice } from "../surface/patterns/ActionNotice";
import { plainFail } from "../surface/plainFailure";
import { wireWords } from "../surface/words";
import { closeProgram, decide, decideProposal, decideRequirement, refreshProgram, type RequirementChoice } from "./api";
import { briefable, copyPageLink, pageWords, programRef, revokePage } from "../reach";
import { clock } from "./Ledger";
import { openShot } from "./Requirements";
import { PlanLine, type usePlanIt } from "./PlanDraft";
import { stepWord } from "./model";
import { rowWords } from "./StepRow";
import { stepNumber } from "./StepSpine";
import type { DecideBody, Program, ProgramStep, YourTurnItem } from "./types";

/** The plate's head: "03" (mono), the step's name (display 18), the facts (mono). */
export function PlateHead({ number, title, facts }: { number?: string; title: ReactNode; facts?: ReactNode }) {
  return (
    <header className="pg-plate-head" data-testid="programs-plate-head">
      {number ? <span className="pg-plate-number">{number}</span> : null}
      <h3 className="pg-plate-title">{title}</h3>
      {facts ? <span className="pg-plate-facts">{facts}</span> : null}
    </header>
  );
}

/** The evidence line (mono): "PR #1832 · Check green · 4 files · open the PR". */
export function Evidence({ pr, fact, step }: {
  pr?: { number: number | null; url: string | null } | null; fact?: string; step?: ProgramStep;
}) {
  const files = step?.owns?.length ? countWords(step.owns.length, "file") : "";
  const parts = [pr?.number ? `PR #${pr.number}` : "", fact ?? "", files ?? ""].filter(Boolean);
  if (!parts.length) return null;
  const green = step?.check?.verdict === "green" || step?.check?.verdict === "pass";
  const red = step?.state === "check_failed";
  return (
    <p className="pg-plate-evidence" data-testid="programs-plate-evidence">
      <span className="pg-plate-lamp" data-tone={red ? "coral" : green ? "moss" : undefined} aria-hidden="true" />
      <span>{parts.join(" · ")}</span>
      {pr?.url ? (
        <Button dense variant="ghost" className="pg-plate-open-pr" onClick={() => window.open(pr.url!, "_blank", "noopener,noreferrer")}
          data-testid="programs-open-pr">open the PR</Button>
      ) : null}
    </p>
  );
}

/** "planned · 4 steps", "planned · tonight 23:30 to 07:00", "no steps yet". */
function planWords(program: Program, steps: number): string {
  const fact = startFact(program);
  return steps || program.night ? `planned · ${fact}` : "no steps yet";
}

/** The head of an item's plate: its step's number and name, when it was asked and by whom. */
function itemHead(item: YourTurnItem, step: ProgramStep | undefined): { number: string; title: string; facts: string } {
  const ofStep = Boolean(item.ordinal) && !PROGRAM_KINDS.has(item.kind);
  return {
    number: ofStep ? stepNumber(item.ordinal) : "",
    title: ofStep ? item.step_title : "The program",
    facts: [item.since ? `asked ${clock(item.since)}` : "", ofStep ? step?.agent ?? "" : ""].filter(Boolean).join(" · "),
  };
}

const RUNNING = new Set(["briefed", "working", "checking", "review", "pr_open"]);

/** The step a plate shows when nothing waits on him: the live one, a red
 *  one, the next one ahead, else the last. */
export function currentStep(program: Program): ProgramStep | null {
  const steps = program.steps.filter((step) => !step.race_of);
  return steps.find((step) => RUNNING.has(step.state))
    ?? steps.find((step) => step.state === "check_failed" || step.state === "failed" || step.state === "limited")
    ?? steps.find((step) => step.state === "planned" || step.state === "ready" || step.state === "parked")
    ?? steps[steps.length - 1] ?? null;
}

/** The plate with nothing that waits on him: the live step (or the Done
 *  word), its line in his terms, its evidence, the lead verb, Earlier steps. */
export function CurrentPlate({ program, doneWord, lead, earlier, children }: {
  program: Program; doneWord: string; lead?: ReactNode; earlier?: ReactNode; children?: ReactNode;
}) {
  const step = program.state === "done" ? null : currentStep(program);
  const line = step ? rowWords(step) || step.brief.split("\n")[0] : "";
  const facts = step ? [stepWord(step), step.agent, step.elapsed].filter(Boolean).join(" · ") : "";
  return (
    <section className="pg-turn" aria-label={step ? `Step ${step.ordinal}` : doneWord} data-testid="programs-plate">
      <article className="pg-plate" data-state={step?.state ?? program.state}>
        {step ? <PlateHead number={stepNumber(step.ordinal)} title={step.title} facts={facts} />
          : <PlateHead title={doneWord} />}
        {line ? <p className="pg-plate-body">{line}</p> : null}
        {children}
        {step ? <Evidence pr={step.pr} step={step} /> : null}
        {lead || earlier ? (
          <div className="pg-plate-verbs">
            {lead ? <div className="pg-tray" data-testid="programs-tray">{lead}</div> : null}
            {earlier}
          </div>
        ) : null}
      </article>
    </section>
  );
}

/** The verbs of one your-turn item, in the canvas order. */
const VERBS: Record<string, { choice: string; word: string; primary?: boolean }[]> = {
  merge: [{ choice: "merge", word: "Merge", primary: true }, { choice: "not_yet", word: "Not yet" }],
  finding: [{ choice: "fix_now", word: "Fix now", primary: true }, { choice: "later", word: "Later" }, { choice: "skip", word: "Skip" }],
  parked: [{ choice: "resume", word: "Resume", primary: true }, { choice: "skip", word: "Skip" }],
  ask_review: [{ choice: "prepare", word: "Send…", primary: true }],
  core: [{ choice: "go_on", word: "Go on", primary: true }, { choice: "park", word: "Park" }],
  // 2026-10-31: the step's agent's commit, held by the gate or not made.
  commit: [{ choice: "allow", word: "Allow the commit", primary: true }, { choice: "not_now", word: "Not now" }],
  race: [{ choice: "pick", word: "Pick", primary: true }],
  add_step: [{ choice: "add", word: "Add", primary: true }, { choice: "skip", word: "Skip" }],
  close: [{ choice: "close", word: "Close", primary: true }],
  // PG19: the agent is at its usage limit (the first word names the next agent).
  limited: [{ choice: "continue", word: "Continue", primary: true }, { choice: "wait", word: "Wait" }],
  // PG-REQ §9: his word, a requirement left after the rounds, and what an agent proposes.
  requirement_word: [{ choice: "met", word: "Met", primary: true }, { choice: "unmet", word: "Unmet" }],
  // PG-IMPORT IMP2 (BroCrew's to-do): a thing the agent asks him to do by hand.
  todo: [{ choice: "done", word: "Done", primary: true }, { choice: "cant", word: "Can't do it" }],
  requirement_left: [{ choice: "send_back", word: "Send back", primary: true }, { choice: "waive", word: "Waive" }],
  requirement_proposed: [{ choice: "add", word: "Add", primary: true }, { choice: "skip", word: "Skip" }],
  step_change: [{ choice: "apply", word: "Apply", primary: true }, { choice: "skip", word: "Skip" }],
  step_amend: [{ choice: "send", word: "Send", primary: true }, { choice: "skip", word: "Skip" }],
  // LANG13, HS-S32: the hub's choices decide which; the first one offered is primary.
  delivery: [{ choice: "merge", word: "Merge" }, { choice: "retry", word: "Retry" }, { choice: "check", word: "Check" },
    { choice: "skip", word: "Skip" }],
  // PG-LANG JRN9 / JRN10: an audit's findings at Secure; its fix program.
  audit_file: [{ choice: "file", word: "File", primary: true }, { choice: "skip", word: "Skip" }],
  fix_program: [{ choice: "make", word: "Make", primary: true }, { choice: "skip", word: "Skip" }],
  // PG-LANG JRN11: a lesson.
  lesson: [{ choice: "keep_program", word: "Keep for this program", primary: true },
    { choice: "keep_repo", word: "Keep for HoldSpeak" }, { choice: "skip", word: "Skip" }],
};

/** The rows about the whole program, not one step (their place is "The program"). */
const PROGRAM_KINDS = new Set(["audit_file", "fix_program", "lesson"]);

/** The verbs an item offers: its kind's, kept to the choices the hub sent. */
function verbsFor(item: YourTurnItem): { choice: string; word: string; primary?: boolean }[] {
  const all = VERBS[item.kind] ?? [];
  if (item.kind !== "delivery") return all;
  return all.filter((verb) => item.choices.includes(verb.choice))
    .map((verb, index) => ({ ...verb, primary: index === 0 && verb.choice !== "skip" }));
}

const REQUIREMENT_KINDS = new Set(["requirement_word", "requirement_left", "todo"]);
const PROPOSAL_KINDS = new Set(["requirement_proposed", "step_change", "step_amend"]);

/** The requirement an item is about (its Program's or its step's). */
function requirementOf(program: Program, item: YourTurnItem) {
  if (!item.requirement_id) return undefined;
  return [...(program.requirements ?? []), ...program.steps.flatMap((step) => step.requirements ?? [])]
    .find((row) => row.id === item.requirement_id);
}

/** A verb's words on one item (`Continue in Codex`). */
function verbWord(item: YourTurnItem, verb: { choice: string; word: string }): string {
  if (item.kind === "limited" && verb.choice === "continue") return `Continue in ${item.next?.label ?? "the next agent"}`;
  return verb.word;
}

/** The quiet fact beside an item's verbs (`Check green · review passed`). */
function itemFact(item: YourTurnItem, step: ProgramStep | undefined, program: Program): string {
  if (item.kind === "merge") return step?.review.verdict === "pass" ? "Check green · review passed" : "Check green";
  if (item.kind === "finding") return [item.level ? wireWords(item.level) : "", step?.rounds ? `after ${step.rounds} rounds` : ""].filter(Boolean).join(" · ");
  if (item.kind === "answer") return "Asks you";
  if (item.kind === "parked") return step?.parked_reason ? "Parked" : "";
  if (item.kind === "core") return "A core question";
  if (item.kind === "limited") return item.warning ? "Near its limit" : "Limited";
  if (item.kind === "delivery") return item.delivery?.words ?? "The delivery";
  if (item.kind === "requirement_word") return step ? "Your word · holds the merge" : "Your word";
  if (item.kind === "todo") return item.head ?? "To do";
  if (item.kind === "requirement_left") return requirementOf(program, item)?.kind_word ?? "";
  return "";
}

/** `Step 3 · Projections off the loop: merge PR #1591?` */
function itemWords(item: YourTurnItem, step: ProgramStep | undefined): ReactNode {
  const head = `Step ${item.ordinal} · ${item.step_title}`;
  let tail = "";
  if (item.kind === "merge") tail = `merge ${item.pr?.number ? `PR #${item.pr.number}` : "the PR"}?`;
  else if (item.kind === "finding") tail = (step?.findings.find((finding) => finding.id === item.finding_id)?.text) ?? item.title;
  else if (item.kind === "parked") tail = step?.parked_reason ?? "it stopped";
  else if (item.kind === "answer") tail = `${step?.agent ?? "the agent"} asks you`;
  else if (item.kind === "core") tail = item.reason ?? item.title;
  else if (item.kind === "limited") tail = item.title;
  else {
    // PG-REQ: the hub composes the line (`Step 3 · Projections off the
    // loop: R4 · I tried it on my desk`); its place is bold.
    const at = item.title.indexOf(": ");
    if (at > 0 && /^(Step \d+|The program)/.test(item.title)) return <><b>{item.title.slice(0, at)}:</b> {item.title.slice(at + 2)}</>;
    return item.title;
  }
  return <><b>{head}:</b> {tail}</>;
}

/** The kind line's words when the hub sent no fact (`Waits on you`). */
function placeWords(item: YourTurnItem): string {
  return item.ordinal && !PROGRAM_KINDS.has(item.kind) ? `Step ${item.ordinal}, ${item.step_title}` : "The program";
}

/** PG-WINDOW W2: what waits on him, as the window's headline. The first
 *  item is the brief (canvas direction A, the briefing page's grammar,
 *  #1684): the kind line with its breathing lamp, the question, what the
 *  step was doing, what happened in plain words, what waits on this answer,
 *  then the tray: each choice a library Button with its consequence under
 *  it. No box around it; the tray is the one raised thing. The other items
 *  are one line each under it. The hub's words (`item.brief`); an item
 *  without them keeps its title. */
export function YourTurnWell({ program, onDecided, onOpenBrief, onOpenText, earlier }: {
  program: Program; onDecided(next: Program | null): void;
  /** The plate's right-hand verb: Earlier steps (opens the step list). */
  earlier?: ReactNode;
  /** The words row under the tray: Brief opens the held step's brief. */
  onOpenBrief?(stepId: string): void;
  /** … and Program text opens the Text view. */
  onOpenText?(): void;
}) {
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const [ask, setAsk] = useState<{ id: string; choice: string } | null>(null);
  const [line, setLine] = useState("");
  // PG-IMPORT IMP2: each to-do's optional note, kept until its press lands.
  const [notes, setNotes] = useState<Record<string, string>>({});
  const items = program.your_turn_items;
  if (!items.length) return null;
  // PG-DIRECTION DIR3: Copy page link makes the item's briefing page and
  // copies its link; Revoke ends it. The row's line says the page is open.
  const page = async (item: YourTurnItem, verb: "copy" | "revoke") => {
    setBusy(`${item.id}:${verb}`);
    setFailed(null);
    try {
      if (verb === "copy") await copyPageLink(programRef(program.id, item.id));
      else if (item.page) await revokePage(item.page.package_id);
      onDecided(await refreshProgram(program.id));
    } catch (error) {
      setFailed(plainFail(verb === "copy" ? "The page link was not made" : "The page was not revoked", error,
        "The item is unchanged", "Try again"));
    } finally {
      setBusy("");
    }
  };
  const press = async (item: YourTurnItem, choice: string, line?: string) => {
    if (item.kind === "answer") return;
    // Unmet and Waive ask one line, in place.
    if (REQUIREMENT_KINDS.has(item.kind) && (choice === "waive" || choice === "unmet") && line === undefined) {
      setAsk((now) => (now?.id === item.id && now.choice === choice ? null : { id: item.id, choice }));
      return;
    }
    if (item.kind === "todo" && line === undefined) line = (notes[item.id] ?? "").trim();
    setBusy(`${item.id}:${choice}`);
    setFailed(null);
    const body: DecideBody = { kind: item.kind as DecideBody["kind"], choice };
    if (item.finding_id) body.finding_id = item.finding_id;
    if (item.kind === "add_step" && item.proposal != null) body.finding_id = String(item.proposal);
    if (item.kind === "lesson" && item.lesson_id != null) body.lesson_id = item.lesson_id;
    if (item.kind === "delivery" && item.expected_delivery_checkpoint_id != null) {
      body.expected_delivery_checkpoint_id = item.expected_delivery_checkpoint_id;
    }
    try {
      if (item.kind === "close") onDecided(await closeProgram(program.id));
      else if (REQUIREMENT_KINDS.has(item.kind) && item.requirement_id) {
        onDecided(await decideRequirement(program.id, item.requirement_id, choice as RequirementChoice, line || undefined));
        if (item.kind === "todo") setNotes((now) => { const next = { ...now }; delete next[item.id]; return next; });
      } else if (PROPOSAL_KINDS.has(item.kind) && item.proposal_id != null) {
        onDecided(await decideProposal(program.id, item.proposal_id, choice));
      } else onDecided(await decide(program.id, item.step_id || "program", body));
      setAsk(null);
    } catch (error) {
      setFailed(plainFail("Your answer did not reach the program", error, "The step is unchanged", "Try again"));
    } finally {
      setBusy("");
    }
  };
  const verbsOf = (item: YourTurnItem, withCons: boolean) => {
    const choice = (key: string, button: ReactNode) => {
      const cons = withCons ? item.brief?.consequences?.[key] : undefined;
      return withCons ? (
        <span key={key} className="pg-choice" data-choice={key}>
          {button}
          {cons ? <span className="pg-choice-cons" data-testid="programs-turn-consequence">{cons}</span> : null}
        </span>
      ) : button;
    };
    return (
      <>
        {item.kind === "answer" ? choice("answer", (
          <Button dense={!withCons} variant={withCons ? "brass" : "primary"} onClick={() => item.launch_id && openRef(`launch:${item.launch_id}`)}
            disabled={!item.launch_id} data-testid="programs-turn-answer">Answer</Button>
        )) : verbsFor(item).map((verb) => choice(verb.choice, (
          <Button key={verb.choice} dense={!withCons} variant={verb.primary ? (withCons ? "brass" : "primary") : "secondary"}
            loading={busy === `${item.id}:${verb.choice}`} disabled={Boolean(busy)}
            onClick={() => void press(item, verb.choice)} data-testid={`programs-turn-${verb.choice.replace("_", "-")}`}>
            {verbWord(item, verb)}
          </Button>
        )))}
      </>
    );
  };
  /** The words row (the briefing page's evidence row): Brief · Program
   *  text · Open shot · Copy page link. Not choices: never in the tray. */
  const wordsOf = (item: YourTurnItem, headline: boolean) => {
    const step = program.steps.find((row) => row.id === item.step_id);
    const shot = item.kind === "requirement_word"
      ? (step?.requirements ?? []).find((row) => row.kind === "shot" && row.evidence?.url) : undefined;
    return (
      <>
          {headline && step && onOpenBrief ? (
            <Button dense variant="ghost" onClick={() => onOpenBrief(step.id)} data-testid="programs-turn-brief">Brief</Button>
          ) : null}
          {headline && onOpenText ? (
            <Button dense variant="ghost" onClick={onOpenText} data-testid="programs-turn-text">Program text</Button>
          ) : null}
          {shot ? (
            <Button dense variant="secondary" onClick={() => openShot(program.id, shot.id)} data-testid="programs-turn-open-shot">Open shot</Button>
          ) : null}
          {briefable(item.kind) ? (
            <Button dense variant="ghost" loading={busy === `${item.id}:${item.page ? "revoke" : "copy"}`}
              disabled={Boolean(busy)} onClick={() => void page(item, item.page ? "revoke" : "copy")}
              data-testid={item.page ? "programs-turn-revoke" : "programs-turn-copy-link"}>
              {item.page ? "Revoke" : "Copy page link"}
            </Button>
          ) : null}
      </>
    );
  };
  /** PG-IMPORT IMP2: a to-do's walk lines and its optional note. */
  const todoWell = (item: YourTurnItem) => item.kind !== "todo" ? null : (
    <div className="pg-todo" data-testid="programs-todo">
      {/* The hub's brief says the walk in its "what happened" line; a row
          with no brief lists it here. */}
      {item.walk?.length && !item.brief?.happened ? (
        <ol className="pg-todo-walk" data-testid="programs-todo-walk">
          {item.walk.map((row, index) => <li key={`${index}-${row}`}>{row}</li>)}
        </ol>
      ) : null}
      <span className="pg-todo-note">
        <StringGadget label="Add a note (optional)" placeholder="Add a note (optional)" value={notes[item.id] ?? ""}
          onChange={(value) => setNotes((now) => ({ ...now, [item.id]: value }))} />
      </span>
    </div>
  );
  /** J5: a race parked as one step names each contender's red log. */
  const raceLogs = (item: YourTurnItem) => item.kind !== "parked" || !item.race || !item.logs?.length ? null : (
    <ul className="pg-race-logs" data-testid="programs-race-logs">
      {item.logs.map((row) => (
        <li key={row.step_id} className="pg-race-log" data-step={row.step_id}>
          <span className="pg-race-agent">{row.agent}</span>
          <Button dense variant="secondary" aria-label={`Open ${row.agent}'s log`}
            onClick={() => openRef(row.log.startsWith("note:") ? row.log : `note:${row.log}`)} data-testid="programs-race-open-log">
            Open log
          </Button>
        </li>
      ))}
    </ul>
  );
  const askWell = (item: YourTurnItem) => {
    const asking = ask?.id === item.id ? ask : null;
    if (!asking) return null;
    return (
      <span className="pg-turn-ask" data-testid="programs-turn-ask">
        <StringGadget label={asking.choice === "waive" ? "Why you waive it" : "What is missing"} value={line} onChange={setLine}
          placeholder={asking.choice === "waive" ? "Why you waive it" : "What is missing"} autoFocus />
        <Button dense variant="primary" loading={busy === `${item.id}:${asking.choice}`}
          disabled={Boolean(busy) || (asking.choice === "waive" && !line.trim())}
          onClick={() => { void press(item, asking.choice, line.trim()); setLine(""); }} data-testid="programs-turn-ask-send">
          {asking.choice === "waive" ? "Waive" : "Unmet"}
        </Button>
      </span>
    );
  };
  const [first, ...rest] = items;
  const firstStep = program.steps.find((row) => row.id === first.step_id);
  const brief = first.brief;
  const fact = itemFact(first, firstStep, program);
  const head = itemHead(first, firstStep);
  return (
    <section className="pg-turn" aria-label="Waits on you" data-testid="programs-your-turn">
      <article className="pg-plate pg-brief" data-kind={first.kind} data-testid="programs-turn-item" data-item={first.id}
        data-asking={ask?.id === first.id ? "" : undefined}>
        <PlateHead number={head.number} title={head.title} facts={head.facts} />
        <h3 className="pg-brief-question" data-testid="programs-brief-question">
          {brief?.question ?? itemWords(first, firstStep)}
        </h3>
        {brief ? (
          <>
            {brief.doing ? <p className="pg-brief-say">{brief.doing}</p> : null}
            {brief.happened ? <p className="pg-brief-say pg-brief-happened" data-testid="programs-brief-happened">{brief.happened}</p> : null}
            {brief.blocked_words ? <p className="pg-brief-blocked" data-testid="programs-brief-blocked">{brief.blocked_words}</p> : null}
          </>
        ) : null}
        <Evidence pr={first.pr?.number ? first.pr : firstStep?.pr} fact={fact} step={firstStep} />
        {first.page ? <p className="pg-turn-page" data-testid="programs-turn-page">{pageWords(first.page)}</p> : null}
        {todoWell(first)}
        {raceLogs(first)}
        {askWell(first)}
        <div className="pg-plate-verbs">
          <div className="pg-tray" data-testid="programs-tray">{verbsOf(first, true)}</div>
          {earlier}
        </div>
        <p className="pg-brief-ev" data-testid="programs-turn-words">{wordsOf(first, true)}</p>
      </article>
      {rest.length ? (
        <ul className="pg-turn-items" aria-label={rest.length === 1 ? "One more waits on you" : `${rest.length} more wait on you`}>
          {rest.map((item) => {
            const step = program.steps.find((row) => row.id === item.step_id);
            return (
              <li key={item.id} className="pg-turn-item" data-kind={item.kind} data-testid="programs-turn-item" data-item={item.id}
                data-asking={ask?.id === item.id ? "" : undefined}>
                <span className="pg-turn-words">
                  <span className="kit-dot" data-tone="ask" aria-hidden="true" />
                  {item.brief ? <><b>{`${placeWords(item)}:`}</b> {[item.brief.happened, item.brief.question].filter(Boolean).join(" ")}</> : itemWords(item, step)}
                </span>
                {item.page ? <span className="pg-turn-page" data-testid="programs-turn-page">{pageWords(item.page)}</span> : null}
                {todoWell(item)}
                {raceLogs(item)}
                {askWell(item)}
                <span className="pg-turn-verbs">{verbsOf(item, false)}{wordsOf(item, false)}</span>
              </li>
            );
          })}
        </ul>
      ) : null}
      {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="programs-turn-failure">{failed.words}</p> : null}
    </section>
  );
}

/** The quiet fact beside Start (no sentence under a verb): a Program split
 *  from a draft waits on the one before it (JRN1); else its step count; a
 *  night program with no steps names its window (#1697). */
export function startFact(program: Program): string {
  const origin = program.place?.origin;
  if (origin?.kind === "after") return `After ${origin.title || "the program before it"}`;
  const count = countWords(program.steps.filter((step) => !step.race_of).length, "step");
  if (count) return count;
  const night = program.night;
  return night ? `Tonight ${night.start} to ${night.end}` : "";
}

/** PG-WINDOW, Drafting (the definition phase): the headline is the goal,
 *  in his words and edited in place, and the tray shows ONE thing from the
 *  Program's state (Create plans itself, #1878): while the engine plans the
 *  goal, the working row with the ledger's line and no verb; with steps (or
 *  a night), Start and the step count; when the engine did not plan, the
 *  ledger's line as a notice and Plan it; with no goal plan yet, Plan it
 *  (and Ask me first). No sentence under a verb. */
export function DraftHead({ program, goal, busy, planner, canAsk, askBusy, anyRoundBusy, onGoal, onStart, onPlan, onAskFirst, onOpenText }: {
  program: Program; goal: string; busy: string; planner: ReturnType<typeof usePlanIt>;
  canAsk: boolean; askBusy: boolean; anyRoundBusy: boolean;
  onGoal(next: string): void; onStart(): void; onPlan(): void; onAskFirst(): void; onOpenText(): void;
}) {
  const steps = program.steps.filter((step) => !step.race_of);
  const held = Boolean(busy) || planner.busy || anyRoundBusy;
  const claim = program.checkpoints.find((row) => row.kind === "plan_goal");
  const ready = Boolean(steps.length || program.night);
  const planning = !ready && claim?.choice === "pending";
  const refused = !ready && claim?.choice === "not_planned";
  const fact = ready ? startFact(program) : "";
  return (
    <section className="pg-turn pg-draft-top" aria-label="Drafting" data-testid="programs-draft-head">
      <article className="pg-plate pg-brief">
        <PlateHead title="Drafting" facts={planWords(program, steps.length)} />
        <div className="pg-draft-goal" data-testid="programs-draft-goal">
          <EditInPlace label="Goal" multiline value={goal} placeholder="Say what the program is for" onCommit={onGoal} />
        </div>
        <PlanLine planner={planner} onOpenText={onOpenText} />
        {refused && !planner.busy && !planner.refusal ? (
          <div className="pg-plan-line" data-testid="programs-plan-claim">
            <ActionNotice tone="warn">{claim!.line}</ActionNotice>
          </div>
        ) : null}
        <div className="pg-plate-verbs">
          <div className="pg-tray" data-testid="programs-tray" data-tray={planning ? "planning" : ready ? "start" : "plan"}>
            {planning ? (
              <DotWord tone="info" live className="pg-plan-line" data-testid="programs-planning">{claim!.line}</DotWord>
            ) : ready ? (
              <span className="pg-choice" data-choice="start">
                <Button variant="brass" loading={busy === "start"} disabled={held} onClick={onStart} data-testid="program-start">Start</Button>
                {fact ? <span className="pg-choice-cons" data-testid="programs-start-words">{fact}</span> : null}
              </span>
            ) : (
              <>
                <Button variant="brass" loading={planner.busy} disabled={held} onClick={onPlan} data-testid="program-plan-it">Plan it</Button>
                {canAsk && !refused ? (
                  <Button variant="secondary" loading={askBusy} disabled={held} onClick={onAskFirst} data-testid="program-ask-first">Ask me first</Button>
                ) : null}
              </>
            )}
          </div>
        </div>
      </article>
    </section>
  );
}
