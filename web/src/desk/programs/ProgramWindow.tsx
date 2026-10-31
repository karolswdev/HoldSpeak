/* Programs (design §9 "The Program window", §9b; canvas direction C, "the
 * ledger"): `pullout:program:<id>`.
 *
 * Window grammar: title bar (the title) → Toolbar (Start / Park / Resume,
 * Add step, Race on the selected step; at the right Runs on ▾, When idle,
 * Control: YOLO ▾, the desk's ladder Secure · Normal · YOLO) → the Your
 * turn well (only what the hub sends: core questions and the level's asks)
 * → the Requirements board (PG-REQ, direction A: the checklist) → the
 * board (one 32 px row per step, with its Met column) → the step fold of
 * the selected step (FilterTokens: Brief · Requirements · Gate · Findings ·
 * Handoffs · Ledger; Move up, Move down, Insert before, Alt+↑ / Alt+↓;
 * Amend brief, Hand off) → the Decided for you fold (each engine decision,
 * its rule, Overturn) → the Ledger fold (one sub-fold per step) → the
 * StatusBar (`Running · 2 of 6 done
 * · 1 waits on you · check: quick_check.sh · control YOLO`, then the place line:
 * Project ▸ HoldSpeak · From the meeting · For Alice, or a No project
 * Token that files it).
 *
 * Drafting: steps are rows of fields; the selected step opens its brief in
 * a PadGadget; the goal is a PadGadget; Start is the primary verb. Done:
 * Open note in place of Start / Park / Resume. */
import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu } from "../components/DeskMenu";
import { openRef } from "../openObject";
import { openProjectRoom } from "../shell";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { keepPlace } from "../deskMemory";
import { useCompactViewport } from "../useCompactViewport";
import {
  CheckGadget, DotWord, FilterTokens, FoldGadget, ListView, PadGadget, StatusBar, StringGadget, SurfaceState, Toolbar, countWords,
  type StatusBarItem,
} from "../surface";
import { useWindowInterior } from "../surface/interior";
import { Token } from "../surface/Token";
import { plainFail } from "../surface/plainFailure";
import { useWindowTitle } from "../surface/title";
import { stateWords, wireWords } from "../surface/words";
import { closeProgram, decide, decideProposal, decideRequirement, overturn, planProgram, programVerb, race, updateProgram, useProgram,
  type RequirementChoice } from "./api";
import { LedgerFold, ProposedWord, clock } from "./Ledger";
import { RequirementsBoard, openShot } from "./Requirements";
import { StepFold, isPlanned, moveStep } from "./StepFold";
import { CONTROLS, agentKey, controlValue, controlWord, durationWords, programTone } from "./model";
import { runsOnLabel, DraftStepRow, StepRow } from "./StepRow";
import { RunsOnPicker } from "./RunsOn";
import { ProgramChangeWell, ProgramTextPane, landedSteps, useProgramText, type TextProposal } from "./ProgramText";
import { ShapeBar, ShapedWell, engineFact } from "./ShapeBar";
import type {
  Control, DecidedRow, DecideBody, PlanStep, Program, ProgramStep, RunsOnEntry, TextApplyAnswer, YourTurnItem, ShapeAnswer } from "./types";
import "./programs.css";
import { openPhoneWing } from "../calls/phoneFocus";

/** The verbs of one your-turn item, in the canvas order. */
const VERBS: Record<string, { choice: string; word: string; primary?: boolean }[]> = {
  merge: [{ choice: "merge", word: "Merge", primary: true }, { choice: "not_yet", word: "Not yet" }],
  finding: [{ choice: "fix_now", word: "Fix now", primary: true }, { choice: "later", word: "Later" }, { choice: "skip", word: "Skip" }],
  parked: [{ choice: "resume", word: "Resume", primary: true }, { choice: "skip", word: "Skip" }],
  ask_review: [{ choice: "prepare", word: "Send…", primary: true }],
  core: [{ choice: "go_on", word: "Go on", primary: true }, { choice: "park", word: "Park" }],
  race: [{ choice: "pick", word: "Pick", primary: true }],
  add_step: [{ choice: "add", word: "Add", primary: true }, { choice: "skip", word: "Skip" }],
  close: [{ choice: "close", word: "Close", primary: true }],
  // PG19: the agent is at its usage limit (the first word names the next agent).
  limited: [{ choice: "continue", word: "Continue", primary: true }, { choice: "wait", word: "Wait" }],
  // PG-REQ §9: his word, a requirement left after the rounds, and what an agent proposes.
  requirement_word: [{ choice: "met", word: "Met", primary: true }, { choice: "unmet", word: "Unmet" }],
  requirement_left: [{ choice: "send_back", word: "Send back", primary: true }, { choice: "waive", word: "Waive" }],
  requirement_proposed: [{ choice: "add", word: "Add", primary: true }, { choice: "skip", word: "Skip" }],
  step_change: [{ choice: "apply", word: "Apply", primary: true }, { choice: "skip", word: "Skip" }],
  step_amend: [{ choice: "send", word: "Send", primary: true }, { choice: "skip", word: "Skip" }],
};

const REQUIREMENT_KINDS = new Set(["requirement_word", "requirement_left"]);
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
  if (item.kind === "requirement_word") return step ? "Your word · holds the merge" : "Your word";
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

export function YourTurnWell({ program, onDecided }: { program: Program; onDecided(next: Program | null): void }) {
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const [ask, setAsk] = useState<{ id: string; choice: string } | null>(null);
  const [line, setLine] = useState("");
  const items = program.your_turn_items;
  if (!items.length) return null;
  const press = async (item: YourTurnItem, choice: string, line?: string) => {
    if (item.kind === "answer") return;
    // Unmet and Waive ask one line, in place.
    if (REQUIREMENT_KINDS.has(item.kind) && (choice === "waive" || choice === "unmet") && line === undefined) {
      setAsk((now) => (now?.id === item.id && now.choice === choice ? null : { id: item.id, choice }));
      return;
    }
    setBusy(`${item.id}:${choice}`);
    setFailed(null);
    const body: DecideBody = { kind: item.kind as DecideBody["kind"], choice };
    if (item.finding_id) body.finding_id = item.finding_id;
    if (item.kind === "add_step" && item.proposal != null) body.finding_id = String(item.proposal);
    try {
      if (item.kind === "close") onDecided(await closeProgram(program.id));
      else if (REQUIREMENT_KINDS.has(item.kind) && item.requirement_id) {
        onDecided(await decideRequirement(program.id, item.requirement_id, choice as RequirementChoice, line || undefined));
      } else if (PROPOSAL_KINDS.has(item.kind) && item.proposal_id != null) {
        onDecided(await decideProposal(program.id, item.proposal_id, choice));
      } else onDecided(await decide(program.id, item.step_id, body));
      setAsk(null);
    } catch (error) {
      setFailed(plainFail("Your answer did not reach the program", error, "The step is unchanged", "Try again"));
    } finally {
      setBusy("");
    }
  };
  return (
    <section className="pg-turn" aria-label="Your turn" data-testid="programs-your-turn">
      <h3 className="pg-turn-head"><DotWord tone="ask">Your turn</DotWord></h3>
      <ul className="pg-turn-items">
        {items.map((item) => {
          const step = program.steps.find((row) => row.id === item.step_id);
          const fact = itemFact(item, step, program);
          // His word on a step that has a shot: Open shot beside Met.
          const shot = item.kind === "requirement_word"
            ? (step?.requirements ?? []).find((row) => row.kind === "shot" && row.evidence?.url) : undefined;
          const asking = ask?.id === item.id ? ask : null;
          return (
            <li key={item.id} className="pg-turn-item" data-kind={item.kind} data-testid="programs-turn-item" data-item={item.id}
              data-asking={asking ? "" : undefined}>
              <span className="pg-turn-words">{itemWords(item, step)}</span>
              {fact ? <span className="pg-turn-fact">{fact}</span> : null}
              {asking ? (
                <span className="pg-turn-ask" data-testid="programs-turn-ask">
                  <StringGadget label={asking.choice === "waive" ? "Why you waive it" : "What is missing"} value={line} onChange={setLine}
                    placeholder={asking.choice === "waive" ? "Why you waive it" : "What is missing"} autoFocus />
                  <Button dense variant="primary" loading={busy === `${item.id}:${asking.choice}`}
                    disabled={Boolean(busy) || (asking.choice === "waive" && !line.trim())}
                    onClick={() => { void press(item, asking.choice, line.trim()); setLine(""); }} data-testid="programs-turn-ask-send">
                    {asking.choice === "waive" ? "Waive" : "Unmet"}
                  </Button>
                </span>
              ) : null}
              <span className="pg-turn-verbs">
                {shot ? (
                  <Button dense variant="secondary" onClick={() => openShot(program.id, shot.id)} data-testid="programs-turn-open-shot">Open shot</Button>
                ) : null}
                {item.kind === "answer" ? (
                  <Button dense variant="primary" onClick={() => item.launch_id && openRef(`launch:${item.launch_id}`)}
                    disabled={!item.launch_id} data-testid="programs-turn-answer">Answer</Button>
                ) : (VERBS[item.kind] ?? []).map((verb) => (
                  <Button key={verb.choice} dense variant={verb.primary ? "primary" : "secondary"}
                    loading={busy === `${item.id}:${verb.choice}`} disabled={Boolean(busy)}
                    onClick={() => void press(item, verb.choice)} data-testid={`programs-turn-${verb.choice.replace("_", "-")}`}>
                    {verbWord(item, verb)}
                  </Button>
                ))}
              </span>
            </li>
          );
        })}
      </ul>
      {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="programs-turn-failure">{failed.words}</p> : null}
    </section>
  );
}

/** The check's name as the hub's status line says it (`quick_check.sh`). */
function checkName(program: Program): string {
  const said = /check: ([^·]+)/.exec(program.status_line ?? "")?.[1]?.trim();
  if (said) return said;
  const words = String(program.check_command ?? "").split(/\s+/).filter((word) => !word.includes("="));
  return (words.find((word) => /\.(sh|py)$/.test(word)) ?? words[0] ?? "").split("/").pop() ?? "";
}

function lampOf(tone: ReturnType<typeof programTone>): StatusBarItem["lamp"] {
  return tone === "idle" ? undefined : tone;
}

/** Control: YOLO ▾ — the desk's ladder (Secure · Normal · YOLO). */
function ControlPicker({ value, onPick, disabled }: { value: Control | string; onPick(next: Control): void; disabled?: boolean }) {
  const opener = useRef<HTMLButtonElement | null>(null);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const current = controlValue(value);
  return (
    <>
      <Button ref={opener} dense variant="ghost" className="pg-control" aria-haspopup="menu" aria-expanded={Boolean(rect)} disabled={disabled}
        title={CONTROLS.find((row) => row.value === current)?.line}
        onClick={() => setRect((now) => (now ? null : opener.current?.getBoundingClientRect() ?? null))} data-testid="program-control">
        Control: {controlWord(current)}
        <svg className="kit-toolbar-more-caret" width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor"
          strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
          <path d="M2.5 3.75L5 6.25l2.5-2.5" />
        </svg>
      </Button>
      {rect ? (
        <WorkMenu label="Control" x={rect.left} y={rect.bottom} opener={opener.current} autoFocus
          returnFocus={() => opener.current?.focus()} onClose={() => setRect(null)}
          entries={CONTROLS.map((row) => ({
            type: "item" as const, id: row.value, label: `${row.word} · ${row.line}`,
            checked: row.value === current ? "exclusive" as const : undefined,
            onSelect: () => { if (row.value !== current) onPick(row.value); },
          }))} />
      ) : null}
    </>
  );
}

/** Phone (PHONE-DESIGN §9): one line under Decided for you when the engine
 *  messaged or called him for this Program — the newest reach (a Decided
 *  for you row of kind `reach`: its line and its rule). Open thread opens
 *  the Calls window on its Phone wing. */
export function ReachLine({ program }: { program: Program }) {
  const reaches = (program.decided_for_you ?? []).filter((row) => row.kind === "reach");
  const reach = reaches[reaches.length - 1];
  if (!reach) return null;
  return (
    <div className="pg-reach" data-testid="programs-reach" data-channel={reach.choice ?? undefined}>
      <span className="pg-reach-at">{clock(reach.at)}</span>
      <span className="pg-reach-line">
        {reach.line}
        {reach.rule ? <span className="pg-decided-rule"> · {reach.rule}</span> : null}
        {program.may_call ? <span className="pg-decided-rule"> · it may call you</span> : null}
      </span>
      <span className="pg-reach-verb">
        <Button dense variant="secondary" onClick={() => openPhoneWing()} data-testid="programs-reach-open">Open thread</Button>
      </span>
    </div>
  );
}

/** Decided for you (§6, §9 item 3): every engine decision, its rule in
 *  muted words, and Overturn while it can still be undone. */
function DecidedFold({ program, open, onToggle, onOverturned }: {
  program: Program; open: boolean; onToggle(open: boolean): void; onOverturned(next: Program | null): void;
}) {
  const rows = program.decided_for_you ?? [];
  const [busy, setBusy] = useState("");
  const [done, setDone] = useState<Record<string, true>>({});
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  if (!rows.length) return null;
  const press = async (row: DecidedRow) => {
    setBusy(String(row.id));
    setFailed(null);
    try {
      const next = await overturn(program.id, String(row.id));
      setDone((now) => ({ ...now, [String(row.id)]: true }));
      onOverturned(next);
    } catch (cause) {
      setFailed(plainFail("The decision was not overturned", cause, "It stands", "Try again"));
    } finally {
      setBusy("");
    }
  };
  return (
    <FoldGadget className="pg-decided" title="Decided for you" token={String(rows.length)} open={open} onToggle={onToggle}>
      <ul className="pg-ledger" data-testid="programs-decided">
        {rows.map((row) => {
          const overturned = Boolean(row.overturned_at) || done[String(row.id)];
          const step = row.step_id ? program.steps.find((candidate) => candidate.id === row.step_id) : undefined;
          const ordinal = step?.ordinal;
          return (
            <li key={row.id} className="pg-ledger-row pg-decided-row" data-overturned={overturned ? "" : undefined} data-testid="programs-decided-row" data-decision={row.id}>
              <span className="pg-ledger-at pg-decided-at">{clock(row.at)}</span>
              <span className="pg-ledger-line">
                {ordinal ? <b>Step {ordinal} · </b> : null}{row.line}
                {row.rule ? <span className="pg-decided-rule"> · {row.rule}</span> : null}
              </span>
              <span className="pg-decided-verb">
                {row.decision_record_id && !overturned ? <ProposedWord /> : null}
                {overturned ? <DotWord data-testid="programs-decided-overturned">Overturned</DotWord>
                  : row.overturnable ? (
                    <Button dense variant="secondary" loading={busy === String(row.id)} disabled={Boolean(busy)} onClick={() => void press(row)}
                      data-testid="programs-overturn">Overturn</Button>
                  ) : null}
              </span>
            </li>
          );
        })}
      </ul>
      {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="programs-decided-failure">{failed.words}</p> : null}
    </FoldGadget>
  );
}

const AGENTS: readonly { profile: string; word: string }[] = [
  { profile: "claude-default", word: "Claude Code" },
  { profile: "codex-default", word: "Codex" },
  { profile: "pi-default", word: "pi" },
];

/** PG19, Drafting: which agents may read this repository, and whether the
 *  program hands off on its own at Normal. */
function AllowedFold({ program, open, onToggle, onChange, busy }: {
  program: Program; open: boolean; onToggle(open: boolean): void; busy: boolean;
  onChange(body: { allowed_profiles?: string[]; may_handoff?: boolean }): void;
}) {
  const allowed = program.allowed_profiles ?? [];
  const on = (profile: string) => !allowed.length || allowed.includes(profile);
  const toggle = (profile: string, next: boolean) => {
    const now = AGENTS.map((row) => row.profile).filter((candidate) => (candidate === profile ? next : on(candidate)));
    if (!now.length) return;
    onChange({ allowed_profiles: now.length === AGENTS.length ? [] : now });
  };
  const count = AGENTS.filter((row) => on(row.profile)).length;
  return (
    <FoldGadget className="pg-allowed-fold" title="Allowed agents" token={count === AGENTS.length ? "every agent" : `${count} of ${AGENTS.length}`}
      open={open} onToggle={onToggle}>
      <div className="pg-allowed" data-testid="programs-allowed">
        {AGENTS.map((row) => (
          <CheckGadget key={row.profile} variant="token" label={row.word} checked={on(row.profile)} disabled={busy}
            onChange={(next) => toggle(row.profile, next)} />
        ))}
        <CheckGadget variant="token" label="May hand off on its own" checked={Boolean(program.may_handoff)} disabled={busy}
          onChange={(next) => onChange({ may_handoff: next })} />
        <span className="pg-allowed-note">At Normal, after 10 minutes at a limit</span>
      </div>
    </FoldGadget>
  );
}

/** `Claude Code, then Codex` (the toolbar's Agent words). */
function listWords(first: string, then: readonly RunsOnEntry[]): string {
  return [first, ...then.map((row) => `then ${row.label}`)].join(", ");
}

function toPlan(step: ProgramStep): PlanStep {
  return {
    id: step.id, title: step.title, brief: step.brief, owns: step.owns, after: step.after,
    profile: step.profile, engine: step.engine?.id ?? null, prefer_idle: step.prefer_idle,
    effort: step.effort ?? undefined, race: step.race || undefined,
  };
}

/** The Program's place line (§9b): Project ▸ name · From … · For …, or the
 *  No project Token that files it. */
function placeItems(program: Program, fileTo: (anchor: HTMLElement) => void, compact = false): StatusBarItem[] {
  const place = program.place;
  const items: StatusBarItem[] = [];
  // At 393 the 24 px bar holds no 44 px target: the place line is words
  // (the project and the person open from the Programs list and the Room).
  if (compact) {
    if (place.project) items.push({ key: "project", testId: "programs-place-project", text: <span>{`Project ▸ ${place.project.name}`}</span> });
    if (place.person) items.push({ key: "person", testId: "programs-place-person", text: <span>{`For ${place.person.name}`}</span> });
    return items;
  }
  if (place.project) {
    items.push({
      key: "project", testId: "programs-place-project",
      text: <Button dense variant="ghost" className="pg-place" onClick={() => openProjectRoom(place.project!.id)}>
        <img src={spriteUrl("project", place.project.id, "rest", null, 20)} alt="" width={14} height={14} />
        <span>Project ▸ {place.project.name}</span>
      </Button>,
    });
  } else {
    items.push({
      key: "no-project", testId: "programs-place-no-project",
      text: <Button dense variant="ghost" className="pg-place" onClick={(event) => fileTo(event.currentTarget)} title="File it in a project">
        <Token>No project</Token>
      </Button>,
    });
  }
  if (place.origin) {
    const kind = place.origin.kind === "meeting" ? "the meeting" : place.origin.kind === "note" ? "the note" : place.origin.kind === "decision" ? "the decision" : place.origin.kind === "automation" ? "the automation" : "";
    // PG14: an automation names itself: "From the automation Nightly fixes".
    const words = place.origin.kind === "automation"
      ? `From the automation${place.origin.title ? ` ${place.origin.title}` : ""}`
      : place.origin.title ? `From ${place.origin.title}` : `From ${kind || "its origin"}`;
    items.push({
      key: "origin", testId: "programs-place-origin",
      text: <Button dense variant="ghost" className="pg-place" onClick={() => openRef(place.origin!.ref)}>
        <img src={spriteUrl(place.origin.kind === "automation" ? "workbench" : place.origin.kind, place.origin.id, "rest", null, 20)} alt="" width={14} height={14} />
        <span>{words}</span>
      </Button>,
    });
  }
  if (place.person) {
    items.push({
      key: "person", testId: "programs-place-person",
      text: <Button dense variant="ghost" className="pg-place" onClick={() => openRef(`people:${place.person!.id}`)}>
        <span>For {place.person.name}</span>
      </Button>,
    });
  }
  return items;
}

/** PG-LANG §9.1: one window, two views, one truth. */
type ProgramView = "board" | "text";
const VIEWS = [{ value: "board", label: "Board" }, { value: "text", label: "Text" }];

/** At 393 the view switch folds into More ▾ (the toolbar's right side does
 *  not fit the phone). */
function ViewMore({ view, onView }: { view: ProgramView; onView(next: ProgramView): void }) {
  const opener = useRef<HTMLButtonElement | null>(null);
  const [rect, setRect] = useState<DOMRect | null>(null);
  return (
    <>
      <Button ref={opener} dense variant="ghost" className="pg-narrow kit-toolbar-more" aria-haspopup="menu" aria-expanded={Boolean(rect)}
        onClick={() => setRect((now) => (now ? null : opener.current?.getBoundingClientRect() ?? null))} data-testid="program-more">
        More
        <svg className="kit-toolbar-more-caret" width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor"
          strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
          <path d="M2.5 3.75L5 6.25l2.5-2.5" />
        </svg>
      </Button>
      {rect ? (
        <WorkMenu label="More" x={rect.left} y={rect.bottom} opener={opener.current} autoFocus
          returnFocus={() => opener.current?.focus()} onClose={() => setRect(null)}
          entries={VIEWS.map((row) => ({
            type: "item" as const, id: row.value, label: row.label,
            checked: row.value === view ? "exclusive" as const : undefined,
            onSelect: () => onView(row.value as ProgramView),
          }))} />
      ) : null}
    </>
  );
}

export function ProgramBody({ programId }: { programId: string }) {
  const { loading, error, program, reload, apply } = useProgram(programId);
  const [selected, setSelected] = useState<string | null>(null);
  const [stepOpen, setStepOpen] = useState(true);
  const [checksOpen, setChecksOpen] = useState(false);
  const [decidedOpen, setDecidedOpen] = useState(true);
  const [allowedOpen, setAllowedOpen] = useState(false);
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const [draft, setDraft] = useState<PlanStep[] | null>(null);
  const [goal, setGoal] = useState<string | null>(null);
  const [filing, setFiling] = useState<DOMRect | null>(null);
  const fileOpener = useRef<HTMLElement | null>(null);
  const projects = useDesk((s) => s.items.project ?? []);
  useWindowInterior("list");
  useWindowTitle(program?.title ?? null, [program?.title]);
  const compact = useCompactViewport();
  // The view he picked, remembered per window (the desk's places).
  const viewKey = `program/view/${programId}`;
  const view: ProgramView = useDesk((s) => s.places[viewKey]) === "text" ? "text" : "board";
  const setView = (next: ProgramView) => keepPlace(viewKey, next === "text" ? "text" : "");
  const text = useProgramText(programId, program, view === "text");
  const [proposal, setProposal] = useState<TextProposal | null>(null);
  const [settling, setSettling] = useState(false);
  const [landed, setLanded] = useState<Record<string, "born" | "changed">>({});
  const [shaped, setShaped] = useState<ShapeAnswer | null>(null);
  useEffect(() => {
    if (!Object.keys(landed).length) return;
    const timer = window.setTimeout(() => setLanded({}), 2600);
    return () => window.clearTimeout(timer);
  }, [landed]);

  const drafting = program?.state === "drafting";
  useEffect(() => {
    if (!program) return;
    if (program.state === "drafting") setDraft(program.steps.map(toPlan));
    else setDraft(null);
  }, [program?.revision, program?.state]); // eslint-disable-line react-hooks/exhaustive-deps

  const steps = program?.steps ?? [];
  const chosen = useMemo(() => {
    if (!program) return null;
    const pick = steps.find((step) => step.id === selected);
    if (pick) return pick;
    // The step his eye goes to first: the one that waits on him, else a red, else a live one.
    return steps.find((step) => ["merge_ask", "findings", "waiting"].includes(step.state))
      ?? steps.find((step) => step.state === "check_failed")
      ?? steps.find((step) => step.check.verdict) ?? null;
  }, [program, steps, selected]);

  const run = async (kind: string, act: () => Promise<Program | null>, failedWords: string) => {
    setBusy(kind);
    setFailed(null);
    try { apply(await act()); } catch (cause) {
      setFailed(plainFail(failedWords, cause, "The program is unchanged", "Try again"));
    } finally { setBusy(""); }
  };

  const preview = async () => {
    const next = await text.preview();
    if (next) setProposal(next);
  };
  const applied = (answer: TextApplyAnswer) => {
    const before = program;
    if (answer.program) apply(answer.program);
    text.reset(answer.text);
    if (before && answer.program) setLanded(landedSteps(before, answer.program, answer.changes));
    // Apply settles: the well fades up and closes; the rows land on the board.
    setSettling(true);
    window.setTimeout(() => { setProposal(null); setSettling(false); }, 200);
    setView("board");
  };
  // LANG4: a shaped sentence. At YOLO the hub landed the allowed rows (the
  // ShapedWell says so, with Overturn); the rows that wait for his press
  // open in the change well against the text as it is now.
  const onShaped = (answer: ShapeAnswer) => {
    const before = program;
    if (answer.applied && answer.program) {
      apply(answer.program);
      text.reset(answer.text);
      if (before) setLanded(landedSteps(before, answer.program, answer.applied_rows));
      setShaped(answer);
    } else {
      setShaped(null);
    }
    setProposal(answer.changes.length ? {
      source: "sentence", text: answer.proposed_text, base: answer.base, answer, say: answer.say, fact: engineFact(answer),
    } : null);
  };
  const notThis = () => {
    if (proposal?.source === "text") text.revert();
    setProposal(null);
  };

  // A new answer is a new well (his presses on the old rows do not carry).
  const wellKey = proposal ? [proposal.source, proposal.answer.revision, proposal.text, proposal.answer.changes.map((row) => row.id + row.verdict).join()].join(":") : "";

  if (loading || (error && !program) || !program) {
    return <SurfaceState loading={loading} error={error ? "The program did not load. Nothing on it changed. Try again." : undefined} onRetry={() => void reload()} />;
  }

  const savePlan = (next: PlanStep[]) => {
    setDraft(next);
    void run("plan", () => planProgram(program.id, next.map((step) => ({ ...step, id: undefined })), true), "The steps were not saved");
  };
  const addStep = () => {
    const step: PlanStep = { title: `Step ${steps.length + 1}`, brief: "", profile: program.default.profile, engine: program.default.engine?.id ?? null };
    if (drafting) savePlan([...(draft ?? []), step]);
    else void run("add", () => planProgram(program.id, [step], false), "The step was not added");
  };
  const verb = program.state === "parked" || program.state === "failed" ? "resume" : program.state === "drafting" ? "start" : program.state === "done" ? null : "park";
  const raceTarget = chosen && !chosen.race_of && ["planned", "ready"].includes(chosen.state) ? chosen : null;
  const fileTo = (anchor: HTMLElement) => { fileOpener.current = anchor; setFiling(anchor.getBoundingClientRect()); };

  // PG-REQ §9 Delight: a Program whose every requirement is met says so in its Done word.
  const met = program.requirements_met;
  const allMet = Boolean(met?.total && met.met >= met.total);
  const doneWord = program.state === "done" && allMet ? `Done · ${met!.met} of ${met!.total} met`
    : program.state === "done" && program.history ? `Done · ${program.history.words}`
    : program.state === "done" && program.done_in ? `Done in ${program.done_in}` : program.state_word;
  const status: StatusBarItem[] = [
    { key: "state", lamp: lampOf(programTone(program.state)), live: program.state === "running", text: doneWord, testId: "programs-status-state" },
    program.state === "done" && allMet && program.done_in ? { key: "took", text: `in ${program.done_in}` } : null,
    { key: "done", text: program.done ? `${program.done} of ${program.total} done` : countWords(program.total, "step"), tick: program.done || null, testId: "programs-status-done" },
    program.your_turn ? { key: "turn", text: `${program.your_turn} ${program.your_turn === 1 ? "waits" : "wait"} on you`, tick: program.your_turn, testId: "programs-status-turn" } : null,
    met?.total && !(program.state === "done" && allMet) ? {
      key: "met", text: met.met || met.unmet ? `${met.met} of ${met.total} met` : countWords(met.total, "requirement"), tick: met.met || null,
      lamp: allMet ? "ok" as const : undefined, pulse: allMet ? met.met : undefined, testId: "programs-status-met",
    } : null,
    program.check_command ? { key: "check", text: <span>{`check: ${checkName(program)}`}</span> } : null,
    // The ladder's own word (`YOLO` keeps its capitals: an element, not a wire token).
    { key: "control", text: <span>{`control ${program.control_word || controlWord(program.control)}`}</span>, testId: "programs-status-control" },
    ...placeItems(program, fileTo, compact),
  ].filter(Boolean) as StatusBarItem[];

  const idle = program.prefer_idle;
  const thenRows = (program.default.runs_on ?? []).slice(1);
  const defaultLabel = `Agent: ${listWords(runsOnLabel(program.default.profile, program.default.engine), thenRows)}`;
  const firstChoice = { profile: program.default.profile ?? "claude-default", engine: program.default.engine?.id ?? null };

  // Alt+↑ / Alt+↓ moves the selected Planned step (never from a text well).
  const onKeys = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!event.altKey || (event.key !== "ArrowUp" && event.key !== "ArrowDown") || !chosen || drafting) return;
    const target = event.target as HTMLElement;
    if (target.closest("input, textarea, select, [contenteditable=true]")) return;
    if (!isPlanned(chosen) || !chosen.editable?.includes("position")) return;
    event.preventDefault();
    const step = chosen;
    void (async () => {
      setBusy("move");
      setFailed(null);
      try {
        const answer = await moveStep(program, step, event.key === "ArrowUp" ? -1 : 1);
        if ("refused" in answer) setFailed({ words: `${answer.refused} · It keeps its place`, title: answer.refused });
        else { apply(answer.program); setSelected(step.id); }
      } catch (cause) {
        setFailed(plainFail(`Step ${step.ordinal} did not move`, cause, "The order is as it was", "Try again"));
      } finally {
        setBusy("");
      }
    })();
  };

  return (
    <div className="pg-window" data-testid="program-window" data-state={program.state} data-program={program.id} onKeyDown={onKeys}>
      <Toolbar label="Program" data-testid="program-toolbar" trailing={
        <span className="pg-toolbar-trailing">
          <FilterTokens label="View" options={VIEWS} value={view} onChange={(next) => setView(next as ProgramView)} className="pg-views" />
          <RunsOnPicker label={defaultLabel} value={firstChoice}
            idle={idle} idleLabel="When idle, for every pi step" disabled={!drafting}
            then={thenRows.map((row) => ({ profile: row.profile, engine: row.engine }))}
            onThen={(next) => void run("agents", () => updateProgram(program.id, { runs_on: [firstChoice, ...next] }), "The agents were not saved")}
            onPick={(choice) => drafting && savePlan((draft ?? []).map((step) => ({ ...step, profile: choice.profile, engine: choice.engine })))}
            onIdle={(next) => void run("idle", () => updateProgram(program.id, { prefer_idle: next }), "When idle was not changed")}
            data-testid="program-runs-on" />
          <CheckGadget variant="token" label="When idle" checked={idle}
            onChange={(next) => void run("idle", () => updateProgram(program.id, { prefer_idle: next }), "When idle was not changed")} />
          <ControlPicker value={program.control} disabled={Boolean(busy)}
            onPick={(control) => void run("control", () => updateProgram(program.id, { control }), "The control was not changed")} />
        </span>
      }>
        {verb ? (
          <Button dense variant={verb === "start" ? "primary" : "secondary"} loading={busy === verb} disabled={Boolean(busy) || (verb === "start" && !steps.length && !(draft ?? []).length)}
            onClick={() => void run(verb, () => programVerb(program.id, verb), verb === "start" ? "The program did not start" : verb === "park" ? "The program was not parked" : "The program did not resume")}
            data-testid={`program-${verb}`}>
            {verb === "start" ? "Start" : verb === "park" ? "Park" : "Resume"}
          </Button>
        ) : program.note_window || program.note_id ? (
          <Button dense variant="secondary" onClick={() => openRef(`note:${program.note_id}`)} data-testid="program-open-note">Open note</Button>
        ) : null}
        {program.state !== "done" ? (
          <Button dense variant="ghost" loading={busy === "add" || busy === "plan"} disabled={Boolean(busy)} onClick={addStep} data-testid="program-add-step">Add step</Button>
        ) : null}
        {raceTarget ? (
          <Button dense variant="ghost" disabled={Boolean(busy)} onClick={() => void run("race", () => race(program.id, raceTarget.id, 2), "The race did not start")}
            data-testid="program-race">Race</Button>
        ) : null}
        {view === "text" && text.edited && !proposal ? (
          <>
            <Button dense variant={verb === "start" ? "secondary" : "primary"} loading={text.busy === "preview"} disabled={Boolean(text.busy)}
              onClick={() => void preview()} data-testid="program-text-preview">Preview</Button>
            <Button dense variant="ghost" disabled={Boolean(text.busy)} onClick={text.revert} data-testid="program-text-revert">Revert</Button>
          </>
        ) : null}
        <ViewMore view={view} onView={setView} />
      </Toolbar>
      {program.state !== "done" ? <ShapeBar program={program} onAnswer={onShaped} onOpenText={() => setView("text")} /> : null}
      <div className="pg-body">
        {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="program-failure">{failed.words}</p> : null}
        <YourTurnWell program={program} onDecided={apply} />
        {shaped ? (
          <ShapedWell key={String(shaped.decision?.id ?? shaped.revision)} program={program} answer={shaped}
            onOverturned={(next) => { apply(next); setShaped(null); setProposal(null); if (next) void text.read(); }}
            onKeep={() => setShaped(null)} />
        ) : null}
        {proposal ? (
          <ProgramChangeWell key={wellKey}
            programId={program.id} proposal={proposal} settling={settling}
            onApplied={applied} onAnswer={setProposal} onDismiss={notThis} />
        ) : null}
        {view === "text" ? (
          <ProgramTextPane text={text} proposal={proposal}
            scrollTo={chosen ? text.lines.findIndex((line) => line.text.startsWith(`step ${chosen.ordinal} `)) : null}
            onLines={(next) => { text.setLines(next); if (proposal?.source === "text") setProposal(null); }} />
        ) : drafting ? (
          <>
            <div className="pg-goal">
              <PadGadget label="Goal" value={goal ?? program.goal} rows={2} onChange={setGoal}
                inputProps={{ onBlur: () => { if (goal != null && goal !== program.goal) void run("goal", () => updateProgram(program.id, { goal }), "The goal was not saved"); } }} />
            </div>
            <RequirementsBoard program={program} onApplied={apply} />
            <ListView label="Steps" className="pg-board" data-testid="programs-board">
              <div className="pg-board-head pg-draft-head" aria-hidden="true">
                <span>Step</span><span>Owns</span><span>Agent</span><span>Effort</span><span>After</span><span>Down time</span>
              </div>
              <ul className="kit-listrows">
                {(draft ?? []).map((step, index) => (
                  <DraftStepRow key={`${index}-${step.id ?? ""}`} index={index} step={step} count={(draft ?? []).length}
                    selected={selected === String(index)} onSelect={() => setSelected(String(index))}
                    engineLabel={steps[index]?.engine?.short || steps[index]?.engine?.label}
                    onChange={(next, commit) => {
                      const rows = [...(draft ?? [])];
                      rows[index] = next;
                      if (commit) savePlan(rows); else setDraft(rows);
                    }} />
                ))}
              </ul>
              {selected != null && draft?.[Number(selected)] ? (
                <div className="pg-draft-brief">
                  <PadGadget label={`Step ${Number(selected) + 1} brief`} rows={3} value={draft[Number(selected)].brief ?? ""}
                    onChange={(brief) => { const rows = [...draft]; rows[Number(selected)] = { ...rows[Number(selected)], brief }; setDraft(rows); }}
                    inputProps={{ onBlur: () => savePlan(draft) }} />
                </div>
              ) : null}
            </ListView>
            <AllowedFold program={program} open={allowedOpen} onToggle={setAllowedOpen} busy={Boolean(busy)}
              onChange={(body) => void run("allowed", () => updateProgram(program.id, body), "The allowed agents were not saved")} />
          </>
        ) : steps.length ? (
          <>
            <RequirementsBoard program={program} onApplied={apply} />
            <ListView label="Steps" className="pg-board" data-testid="programs-board">
              <h3 className="pg-board-caption">Steps</h3>
              <ul className="kit-listrows">
                {steps.map((step) => (
                  <StepGroup key={step.id} step={step} selected={chosen?.id === step.id} onSelect={() => setSelected(step.id)} landed={landed[step.id]}
                    his={program.your_turn_items.some((item) => item.kind === "requirement_word" && item.step_id === step.id)} />
                ))}
              </ul>
            </ListView>
          </>
        ) : (
          <SurfaceState empty emptyKind="program" emptyImage={spriteUrl("program", program.id)} emptyLabel="No steps yet"
            emptyHint="Add a step for each brief." actionLabel="Add step" onAction={addStep} />
        )}
        {view === "board" && !drafting && chosen ? (
          <StepFold key={chosen.id} program={program} step={chosen} onApplied={apply} open={stepOpen} onToggle={setStepOpen} />
        ) : null}
        {view === "board" && !drafting ? <DecidedFold program={program} open={decidedOpen} onToggle={setDecidedOpen} onOverturned={apply} /> : null}
        {view === "board" && !drafting ? <ReachLine program={program} /> : null}
        {view === "board" && !drafting ? <LedgerFold program={program} open={checksOpen} onToggle={setChecksOpen} onStarted={apply} /> : null}
      </div>
      <StatusBar data-testid="program-status" items={status} />
      {filing ? (
        <WorkMenu label="File in a project" x={filing.left} y={filing.top} anchor="above" opener={fileOpener.current} autoFocus
          entries={projects.length ? projects.map((project) => ({
            type: "item" as const, id: project.id, label: String((project as { title?: string; name?: string }).name ?? (project as { title?: string }).title ?? project.id),
            onSelect: () => void run("file", () => updateProgram(program.id, { project_id: project.id }), "The program was not filed"),
          })) : [{ type: "note" as const, id: "none", label: "No project yet" }]}
          onClose={() => setFiling(null)} />
      ) : null}
    </div>
  );
}

/** A step with its race's contenders indented under it. */
function StepGroup({ step, selected, onSelect, his, landed }: {
  step: ProgramStep; selected: boolean; onSelect(): void; his?: boolean; landed?: "born" | "changed";
}) {
  return (
    <>
      <StepRow step={step} selected={selected} onSelect={onSelect} his={his} landed={landed} />
      {(step.contenders ?? []).map((contender) => (
        <StepRow key={contender.id} step={contender} contender onSelect={onSelect} />
      ))}
    </>
  );
}

/** The pullout content: `pullout:program:<id>`. */
export function ProgramPullout({ object }: { object: { id: string } }) {
  return <ProgramBody programId={object.id} />;
}

export { durationWords };
export default ProgramPullout;
