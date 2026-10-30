/* Programs (design §9 "The Program window", §9b; canvas direction C, "the
 * ledger"): `pullout:program:<id>`.
 *
 * Window grammar: title bar (the title) → Toolbar (Start / Park / Resume,
 * Add step, Race on the selected step; at the right Runs on ▾, When idle,
 * Control: YOLO ▾, the desk's ladder Secure · Normal · YOLO) → the Your
 * turn well (only what the hub sends: core questions and the level's asks)
 * → the board (one 32 px row per step) → the Gate fold of the selected
 * step → the Decided for you fold (each engine decision, its rule,
 * Overturn) → the Checkpoints fold → the StatusBar (`Running · 2 of 6 done
 * · 1 waits on you · check: quick_check.sh · control YOLO`, then the place line:
 * Project ▸ HoldSpeak · From the meeting · For Alice, or a No project
 * Token that files it).
 *
 * Drafting: steps are rows of fields; the selected step opens its brief in
 * a PadGadget; the goal is a PadGadget; Start is the primary verb. Done:
 * Open note in place of Start / Park / Resume. */
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu } from "../components/DeskMenu";
import { openRef } from "../openObject";
import { openProjectRoom } from "../shell";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { useCompactViewport } from "../useCompactViewport";
import {
  CheckGadget, DotWord, FoldGadget, ListView, PadGadget, StatusBar, SurfaceState, SurfaceWell, Toolbar, countWords,
  type StatusBarItem,
} from "../surface";
import { useWindowInterior } from "../surface/interior";
import { Token } from "../surface/Token";
import { plainFail } from "../surface/plainFailure";
import { useWindowTitle } from "../surface/title";
import { stateWords } from "../surface/words";
import { closeProgram, decide, overturn, planProgram, programVerb, race, updateProgram, useProgram } from "./api";
import { GateFold } from "./GateFold";
import { CONTROLS, agentKey, controlValue, controlWord, durationWords, programTone } from "./model";
import { runsOnLabel, DraftStepRow, StepRow } from "./StepRow";
import { RunsOnPicker } from "./RunsOn";
import type {
  Control, DecidedRow, DecideBody, PlanStep, Program, ProgramCheckpoint, ProgramStep, RunsOnEntry, StepHandoff, YourTurnItem,
} from "./types";
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
};

/** A verb's words on one item (`Continue in Codex`). */
function verbWord(item: YourTurnItem, verb: { choice: string; word: string }): string {
  if (item.kind === "limited" && verb.choice === "continue") return `Continue in ${item.next?.label ?? "the next agent"}`;
  return verb.word;
}

/** The quiet fact beside an item's verbs (`Check green · review passed`). */
function itemFact(item: YourTurnItem, step: ProgramStep | undefined): string {
  if (item.kind === "merge") return step?.review.verdict === "pass" ? "Check green · review passed" : "Check green";
  if (item.kind === "finding") return [item.level ? stateWords(item.level.toUpperCase()) : "", step?.rounds ? `after ${step.rounds} rounds` : ""].filter(Boolean).join(" · ");
  if (item.kind === "answer") return "Asks you";
  if (item.kind === "parked") return step?.parked_reason ? "Parked" : "";
  if (item.kind === "core") return "A core question";
  if (item.kind === "limited") return item.warning ? "Near its limit" : "Limited";
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
  else return item.title;
  return <><b>{head}:</b> {tail}</>;
}

export function YourTurnWell({ program, onDecided }: { program: Program; onDecided(next: Program | null): void }) {
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const items = program.your_turn_items;
  if (!items.length) return null;
  const press = async (item: YourTurnItem, choice: string) => {
    if (item.kind === "answer") return;
    setBusy(`${item.id}:${choice}`);
    setFailed(null);
    const body: DecideBody = { kind: item.kind, choice };
    if (item.finding_id) body.finding_id = item.finding_id;
    if (item.kind === "add_step" && item.proposal != null) body.finding_id = String(item.proposal);
    try {
      onDecided(item.kind === "close" ? await closeProgram(program.id) : await decide(program.id, item.step_id, body));
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
          const fact = itemFact(item, step);
          return (
            <li key={item.id} className="pg-turn-item" data-kind={item.kind} data-testid="programs-turn-item" data-item={item.id}>
              <span className="pg-turn-words">{itemWords(item, step)}</span>
              {fact ? <span className="pg-turn-fact">{fact}</span> : null}
              <span className="pg-turn-verbs">
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

function byWords(row: ProgramCheckpoint, program: Program): { who: string; sprite: string | null } {
  if (row.by === "owner") return { who: "You", sprite: null };
  if (row.by === "engine") return { who: "HoldSpeak · engine", sprite: spriteUrl("program", program.id, "rest", null, 20) };
  const step = program.steps.find((candidate) => candidate.id === row.step_id);
  const agent = agentKey(step?.profile, step?.agent);
  return { who: `${step?.agent ?? "Agent"} · step ${step?.ordinal ?? ""}`.trim(), sprite: spriteUrl("coder", agent, "rest", agent, 20) };
}

function clock(at: string): string {
  const ms = Date.parse(at);
  if (!Number.isFinite(ms)) return "";
  return new Date(ms).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
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
function HandoffLine({ row, step, entry }: { row: ProgramCheckpoint; step: ProgramStep; entry: StepHandoff }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="pg-handoff-row" data-testid="programs-handoff" data-checkpoint={row.id}>
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
          </p>
          <SurfaceWell>
            <pre className="pg-handoff-brief">{entry.brief}</pre>
          </SurfaceWell>
        </div>
      ) : null}
    </li>
  );
}

function Checkpoints({ program, open, onToggle }: { program: Program; open: boolean; onToggle(open: boolean): void }) {
  const rows = program.checkpoints;
  const handoffs = useMemo(() => handoffsOf(program), [program]);
  if (!rows.length) return null;
  return (
    <FoldGadget className="pg-checkpoints" title="Checkpoints" token={open ? "newest first" : String(rows.length)} open={open} onToggle={onToggle}>
      <ul className="pg-ledger" data-testid="programs-checkpoints">
        {rows.slice(0, 50).map((row) => {
          const handed = handoffs.get(String(row.id));
          if (handed) return <HandoffLine key={row.id} row={row} step={handed.step} entry={handed.entry} />;
          const by = byWords(row, program);
          return (
            <li key={row.id} className="pg-ledger-row">
              <span className="pg-ledger-by">
                {by.sprite ? <img src={by.sprite} alt="" width={20} height={20} /> : <span className="pg-ledger-you" aria-hidden="true">You</span>}
                <span>{by.who}</span>
              </span>
              <span className="pg-ledger-line">{row.line}</span>
              <span className="pg-ledger-at">{clock(row.at)}</span>
            </li>
          );
        })}
      </ul>
    </FoldGadget>
  );
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

export function ProgramBody({ programId }: { programId: string }) {
  const { loading, error, program, reload, apply } = useProgram(programId);
  const [selected, setSelected] = useState<string | null>(null);
  const [gateOpen, setGateOpen] = useState(true);
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

  const status: StatusBarItem[] = [
    { key: "state", lamp: lampOf(programTone(program.state)), live: program.state === "running", text: program.state === "done" && program.done_in ? `Done in ${program.done_in}` : program.state_word, testId: "programs-status-state" },
    { key: "done", text: program.done ? `${program.done} of ${program.total} done` : countWords(program.total, "step"), tick: program.done || null, testId: "programs-status-done" },
    program.your_turn ? { key: "turn", text: `${program.your_turn} ${program.your_turn === 1 ? "waits" : "wait"} on you`, tick: program.your_turn, testId: "programs-status-turn" } : null,
    program.check_command ? { key: "check", text: <span>{`check: ${checkName(program)}`}</span> } : null,
    // The ladder's own word (`YOLO` keeps its capitals: an element, not a wire token).
    { key: "control", text: <span>{`control ${program.control_word || controlWord(program.control)}`}</span>, testId: "programs-status-control" },
    ...placeItems(program, fileTo, compact),
  ].filter(Boolean) as StatusBarItem[];

  const idle = program.prefer_idle;
  const thenRows = (program.default.runs_on ?? []).slice(1);
  const defaultLabel = `Agent: ${listWords(runsOnLabel(program.default.profile, program.default.engine), thenRows)}`;
  const firstChoice = { profile: program.default.profile ?? "claude-default", engine: program.default.engine?.id ?? null };

  return (
    <div className="pg-window" data-testid="program-window" data-state={program.state} data-program={program.id}>
      <Toolbar label="Program" data-testid="program-toolbar" trailing={
        <span className="pg-toolbar-trailing">
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
      </Toolbar>
      <div className="pg-body">
        {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="program-failure">{failed.words}</p> : null}
        <YourTurnWell program={program} onDecided={apply} />
        {drafting ? (
          <>
            <div className="pg-goal">
              <PadGadget label="Goal" value={goal ?? program.goal} rows={2} onChange={setGoal}
                inputProps={{ onBlur: () => { if (goal != null && goal !== program.goal) void run("goal", () => updateProgram(program.id, { goal }), "The goal was not saved"); } }} />
            </div>
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
          <ListView label="Steps" className="pg-board" data-testid="programs-board">
            <h3 className="pg-board-caption">Steps</h3>
            <ul className="kit-listrows">
              {steps.map((step) => (
                <StepGroup key={step.id} step={step} selected={chosen?.id === step.id} onSelect={() => setSelected(step.id)} />
              ))}
            </ul>
          </ListView>
        ) : (
          <SurfaceState empty emptyKind="program" emptyImage={spriteUrl("program", program.id)} emptyLabel="No steps yet"
            emptyHint="Add a step for each brief." actionLabel="Add step" onAction={addStep} />
        )}
        {!drafting && chosen && (chosen.check.verdict || chosen.check.running || chosen.station >= 2) ? (
          <GateFold step={chosen} open={gateOpen} onToggle={setGateOpen} />
        ) : null}
        {!drafting ? <DecidedFold program={program} open={decidedOpen} onToggle={setDecidedOpen} onOverturned={apply} /> : null}
        {!drafting ? <ReachLine program={program} /> : null}
        {!drafting ? <Checkpoints program={program} open={checksOpen} onToggle={setChecksOpen} /> : null}
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
function StepGroup({ step, selected, onSelect }: { step: ProgramStep; selected: boolean; onSelect(): void }) {
  return (
    <>
      <StepRow step={step} selected={selected} onSelect={onSelect} />
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
