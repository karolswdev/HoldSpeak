/* The agent (the language, 2026-11-08; owner: "the agent window is too
 * somber, basic and weak … a product differentiator"): the right pane of
 * the Agents window for the picked agent. The window grammar is the one
 * the Programs window ratified: the MAST (the provider sprite, what the
 * agent works on in the display face, one mono facts line, the verbs), the
 * SPINE (steel works, brass waits on you, moss done, coral at risk,
 * graphite ended), the PLATE (the one thing that matters now, with its one
 * verb: the question with Answer, the finished report with Open the PR and
 * Done, a failure with Resume, else the latest tool activity with Stop) and
 * the LEDGER (the agent's reports and tool activity, newest first; the
 * lane's events for a launch, the session's last words for a plain one).
 *
 * Every verb is an existing call: the ask row's answer and allow
 * (`agents/AgentRow.tsx`), the lane's kill, Resume, Done, Remove, Cancel,
 * Hand again, Allow helper (`open.ts`), Connect (the store). The terminal is
 * behind one verb (Terminal); Details opens the agent's Get Info. */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { CONTROL_MODE_LABELS } from "../../lib/productLanguage";
import { madeWord } from "../drawer/members";
import { AgentWords } from "../components/AgentWords";
import { useAgentFlights, type CoderSessionRow } from "../agentFlights";
import { handRefOf, openHand } from "../agentHand";
import { AgentRow as AskPlate, DeskAnswerLine } from "../agents/AgentRow";
import { WhyThisState } from "../agents/WhyThisState";
import { AGENT_INSTALL, AGENT_NAME, needsHooks, type AgentId } from "../firstrun/agentsStep";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { laneEntries, isNotRead, turnEndWord, turnWord, type LaneEntry, type LaneEvent, type LaneWire } from "../lane/laneWire";
import { useLane } from "../lane/laneStore";
import { CheckLog, FilesFold, LaneReceipts, PrRow, RawPane, RebriefWell, UnreadLines, heldNow, spokeWord, useLaneOf } from "./AgentLane";
import { ResultBlock } from "../lane/ResultBlock";
import { ProgramStepLine } from "../programs/StepLine";
import { openAgentLane } from "../shell";
import { DotWord, FoldGadget, SurfaceLedger, SurfaceLedgerRow } from "../surface";
import { SurfaceFacts } from "../surface/Surface";
import { Mast } from "../surface/patterns/Mast";
import { Spine, type SpineTone } from "../surface/patterns/Spine";
import { reviewResult } from "../agentFlights";
import { ReviewResult } from "./ReviewResult";
import { canRun, fleetRank, reviewWords, type ConductorMember } from "./members";
import {
  allowHelper, answerMember, cancelQueuedHand, doneMember, openMember, removeLaunch, resumeAll, stopMember, stops,
} from "./open";
import { useConductor } from "./store";
import { ShowMe } from "../walk/ShowMe";

/** The stopped agents whose item takes Hand again (a new agent in the
 *  same worktree; the hub checks it). */
const HAND_AGAIN = new Set(["resume_failed", "stopped_by_restart", "ended", "expired"]);

/** The tone of an agent's spine (and its rail tile): one colour per meaning. */
export function spineTone(member: ConductorMember): SpineTone {
  if (member.role === "ready") return member.detect && canRun(member.detect) ? "moss" : "idle";
  if (member.role === "stale") {
    if (member.flightState === "resume_failed" || member.flightState === "stopped_by_restart") return "coral";
    if (member.flightState === "checked" || member.flightState === "merged") return "moss";
    return "graphite";
  }
  switch (member.live) {
    case "ask":
    case "held":
    case "needs_you":
      return "brass";
    case "done":
    case "pr":
    case "idle":
      return "moss";
    case "no_signal":
      return "coral";
    case "queued":
      return "idle";
    default:
      return "steel";
  }
}

/** The title of an agent: the item (or Program step) it works on, else its name. */
export function memberTitle(member: ConductorMember): string {
  return member.role === "ready" ? member.name : String(member.facts.from || member.name);
}

export function agentWord(member: ConductorMember): string {
  return AGENT_NAME[member.agent as AgentId] ?? member.agent;
}

/** `6 MIN` → `6 min ago`; `OCT 5` → `Oct 5`. */
export function agoWord(when: string | undefined): string {
  if (!when) return "";
  if (/^\d+ (MIN|H)$/.test(when)) return `${when.toLowerCase()} ago`;
  return when.charAt(0) + when.slice(1).toLowerCase();
}

/** `PR #413 MERGED · ITEM CLOSED` → `PR #413 merged · item closed`. */
export function plainReceipt(receipt: string): string {
  const lower = receipt.toLowerCase().replace(/\bpr #/g, "PR #");
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** `41,200 tokens` from the lane's usage (the gate's session row), else "". */
export function tokenWords(usage: unknown): string {
  if (!usage || typeof usage !== "object" || isNotRead(usage)) return "";
  const row = usage as Record<string, unknown>;
  const total = ["input_tokens", "output_tokens"].reduce((sum, key) => sum + (Number(row[key]) || 0), 0);
  if (!total) return "";
  return total >= 1000 ? `${(total / 1000).toFixed(total >= 10_000 ? 0 : 1)}k tokens` : `${total} tokens`;
}

/* ── the ledger ─────────────────────────────────────────────────────── */

/** The ledger shows this many activity rows; Terminal holds the rest. */
const LEDGER_ROWS = 40;

/** The ledger's words for a lane entry: sentence case, never a caps chip. */
const ENTRY_WORD: Record<LaneEntry["kind"], string> = {
  brief: "Brief", read: "Read", says: "Says", write: "Wrote", run: "Ran", call: "Called", answer: "Your answer",
  end: "Ended", commit: "Commit", pr: "PR", held: "Held", asks: "Asks", merge: "Merged", rebrief: "Re-brief",
};

export interface LedgerLine {
  id: string;
  time: string;
  word: string;
  text: string;
  tone?: "ask" | "ok" | "fail";
  /** The agent's own words (a report): drawn as its words, at reading size. */
  report?: boolean;
  /** Read opens this in the row (a report section, the brief). */
  body?: string;
}

/** A report's sections: a heading line (`# …`, `**…**`, `Words:`) starts
 *  one; without headings, each paragraph is one. Each is `{title, body}`. */
export function reportSections(text: string): Array<{ title: string; body: string }> {
  const lines = String(text ?? "").replace(/\r/g, "").split("\n");
  const heading = (line: string) => {
    const t = line.trim();
    const m = /^#{1,6}\s+(.+)$/.exec(t) ?? /^\*\*(.+?)\*\*:?$/.exec(t) ?? /^([A-Z][^.!?]{0,48}):$/.exec(t);
    return m ? m[1].replace(/\*\*/g, "").trim() : null;
  };
  const out: Array<{ title: string; body: string }> = [];
  let current: { title: string; body: string[] } | null = null;
  const flush = () => {
    if (current && (current.title || current.body.join("").trim())) {
      const body = current.body.join("\n").trim();
      out.push({ title: current.title || firstWords(body), body });
    }
  };
  const headed = lines.some((line) => heading(line));
  if (!headed) {
    return String(text ?? "").split(/\n\s*\n/).map((part) => part.trim()).filter(Boolean)
      .map((part) => ({ title: firstWords(part), body: part }));
  }
  for (const line of lines) {
    const h = heading(line);
    if (h) {
      flush();
      current = { title: h, body: [] };
    } else {
      if (!current) current = { title: "", body: [] };
      current.body.push(line);
    }
  }
  flush();
  return out;
}

function firstWords(text: string, max = 72): string {
  const flat = String(text ?? "").replace(/\s+/g, " ").replace(/[#*`>]/g, "").trim();
  if (flat.length <= max) return flat;
  const cut = flat.slice(0, max);
  return `${cut.slice(0, Math.max(cut.lastIndexOf(" "), 24)).trim()} …`;
}

/** The pane's ledger: the report's sections first (Read opens each), then
 *  the tool activity by time, newest first; a launch with only its brief
 *  shows the brief as one row. */
export function ledgerLines(lane: LaneWire | null, events: readonly LaneEvent[], report: string, row?: CoderSessionRow): LedgerLine[] {
  const sections = report ? reportSections(report).map((section, i): LedgerLine => ({
    id: `report-${i}`, time: "", word: "Report", text: section.title, body: section.body, report: true,
  })) : [];
  const said = report.trim();
  const activity = (lane ? laneLines(lane, events) : sessionLines(row).filter((line) => !line.report))
    .filter((line) => !said || line.text.trim() !== said);
  if (lane && !activity.length && !sections.length && lane.launch?.brief_text) {
    return [{ id: "brief", time: "", word: "Brief", text: "The brief", body: String(lane.launch.brief_text) }];
  }
  return [...sections, ...activity];
}

/** The lane's timeline, newest first, as ledger lines. */
export function laneLines(lane: LaneWire, events: readonly LaneEvent[] = Array.isArray(lane.events) ? lane.events : []): LedgerLine[] {
  // An older hub (or a partial answer) leaves a part out: it is not read.
  const whole: LaneWire = {
    ...lane,
    launch: lane.launch ?? ({} as LaneWire["launch"]),
    worktree: lane.worktree ?? { not_read: "absent" },
    follow_through: lane.follow_through ?? { pr: null },
    gated: lane.gated ?? [],
  };
  return laneEntries(whole, events)
    .slice()
    .reverse()
    .slice(0, LEDGER_ROWS)
    .map((entry, index): LedgerLine => ({
      id: String(entry.id ?? `entry-${index}`),
      time: String(entry.time ?? ""),
      word: ENTRY_WORD[entry.kind] ?? String(entry.word ?? ""),
      text: String(entry.words ?? entry.quote ?? entry.code ?? entry.text ?? entry.result ?? ""),
      tone: entry.tone === "fail" ? "fail" : entry.tone === "warn" ? "ask" : entry.tone === "ok" ? "ok" : undefined,
    }))
    // The brief is its own row (the only one, when nothing else is
    // reported); the PR and its merge are the PR row above the ledger.
    .filter((line) => line.text.trim() && !["Brief", "PR", "Merged"].includes(line.word));
}

/** A plain session's ledger: what the session row holds (its last words, its
 *  last tool, the command on its screen). */
export function sessionLines(row: CoderSessionRow | undefined): LedgerLine[] {
  if (!row) return [];
  const raw = ((row.raw as Record<string, unknown>)?.session ?? row.raw ?? {}) as Record<string, unknown>;
  const lines: LedgerLine[] = [];
  const said = String(raw.last_assistant_text ?? "").trim() || String(row.screen?.said ?? "").trim();
  const tool = String(raw.last_tool_name ?? "").trim();
  const command = String(row.screen?.command ?? "").trim();
  if (said) lines.push({ id: "said", time: "", word: "Says", text: said, report: true });
  if (tool) lines.push({ id: "tool", time: "", word: "Tool", text: tool });
  if (command) lines.push({ id: "command", time: "", word: "Command", text: command });
  return lines;
}

function AgentLedger({ lines, failed, onRetry }: { lines: LedgerLine[]; failed: boolean; onRetry(): void }) {
  const [open, setOpen] = useState<string | null>(null);
  if (failed) {
    // A quiet line: the plate above keeps the one alert of the pane.
    return (
      <div className="aw-ledger" role="group" aria-label="Activity" data-testid="agents-ledger">
        <p className="aw-ledger-failed" data-testid="agents-ledger-failed">
          <DotWord tone="fail">Activity not read</DotWord>
          <Button dense variant="ghost" onClick={onRetry}>Read again</Button>
        </p>
      </div>
    );
  }
  if (!lines.length) return null;
  return (
    <div className="aw-ledger" role="group" aria-label="Activity" data-testid="agents-ledger">
      <h3 className="aw-cap">Activity</h3>
      <SurfaceLedger cols="agent" label="Activity">
        <ul className="surface-ledger-rows">
          {lines.map((line) => (
            <SurfaceLedgerRow
              key={line.id}
              time={line.time}
              primary={<span className="aw-ledger-text" title={line.text}>{line.text}</span>}
              meta={line.word}
              metaTone={line.tone}
              expands={false}
              open={open === line.id}
              trailing={line.body ? (
                <Button dense variant="ghost" aria-expanded={open === line.id} data-testid="agents-ledger-read"
                  onClick={() => setOpen((now) => (now === line.id ? null : line.id))}>
                  {open === line.id ? "Close" : "Read"}
                </Button>
              ) : undefined}
              data-testid="agents-ledger-row"
            >
              {line.body ? <AgentWords className="aw-ledger-body" text={line.body} /> : null}
            </SurfaceLedgerRow>
          ))}
        </ul>
      </SurfaceLedger>
    </div>
  );
}

/* ── the plate ──────────────────────────────────────────────────────── */

function Plate({ tone, head, children, testId = "agents-plate" }: {
  tone: SpineTone; head: ReactNode; children?: ReactNode; testId?: string;
}) {
  return (
    <div className="aw-plate" data-tone={tone} data-testid={testId}>
      <header className="aw-plate-head">{head}</header>
      {children}
    </div>
  );
}

function PlateVerbs({ children }: { children: ReactNode }) {
  return <div className="aw-plate-verbs">{children}</div>;
}

/** The receipt of the picked agent: its Stop, a hooks install the hub
 *  refused (with Retry) or did, a stale launch's close. */
export function MemberReceipt({ member }: { member: ConductorMember | null }) {
  const stop = useConductor((s) => (member ? s.stops[member.ref] : undefined));
  const failure = useConductor((s) => s.installFailure);
  const failedFor = useConductor((s) => s.installFailedAgent);
  const installing = useConductor((s) => s.installing);
  const done = useConductor((s) => s.installDone);
  if (failure && failedFor && (member?.detect ? failedFor === member.detect.id : !member)) {
    const agent = failedFor;
    return (
      <span className="drawer-receipt cw-receipt" data-tone="fail" role="status" data-testid="conductor-install-failed">
        <span className="kit-dot" data-tone="fail" aria-hidden="true" />
        {plainReceipt(`Not connected · ${failure}`)}
        <Button dense variant="ghost" loading={installing === agent} onClick={() => void useConductor.getState().installHooks(agent)}>
          Retry
        </Button>
      </span>
    );
  }
  if (stop) {
    return (
      <span className="drawer-receipt cw-receipt" data-tone={stop.tone === "ok" ? undefined : "fail"} role="status" data-testid="conductor-stop-receipt">
        <span className="kit-dot" data-tone={stop.tone === "ok" ? "ok" : "fail"} aria-hidden="true" />
        {stopWords(stop.word, stop.text)}
      </span>
    );
  }
  if (member?.receipt) {
    return <span className="drawer-receipt cw-receipt" data-testid="conductor-receipt">{plainReceipt(member.receipt)}</span>;
  }
  if (done && (!member || member.detect?.id === done.agent)) {
    return (
      <span className="drawer-receipt cw-receipt" role="status" data-testid="conductor-install-done">
        <span className="kit-dot" data-tone="ok" aria-hidden="true" />
        {`Connected · ${AGENT_NAME[done.agent]} · ${done.at}`}
      </span>
    );
  }
  return null;
}

/** W5-WORDS: a Stop's receipt in sentence case (`Stopped by you`). */
export function stopWords(word: string, text: string): string {
  if (word === "STOPPED" && text === "BY YOU") return "Stopped by you";
  return plainReceipt([word, text].filter(Boolean).join(" · "));
}

/** Stop, in place: the confirmation replaces the verb, bound to the agent
 *  pressed whatever is picked after. */
export function StopVerb({ member, quiet = false }: { member: ConductorMember; quiet?: boolean }) {
  const [confirmFor, setConfirmFor] = useState<ConductorMember | null>(null);
  const [stopping, setStopping] = useState(false);
  useEffect(() => {
    if (!stopping) setConfirmFor((now) => (now && now.id !== member.id ? null : now));
  }, [member.id, stopping]);
  if (!stops(member)) return null;
  if (confirmFor) {
    const pressed = confirmFor;
    return (
      <>
        <Button dense variant="ghost" disabled={stopping} onClick={() => setConfirmFor(null)}>
          Back
        </Button>
        <Button
          dense
          variant="danger"
          loading={stopping}
          data-testid="conductor-stop-confirm"
          onClick={() => {
            setStopping(true);
            void stopMember(pressed).finally(() => {
              setStopping(false);
              setConfirmFor(null);
            });
          }}
        >
          Stop · sure? (ends the agent's session)
        </Button>
      </>
    );
  }
  return (
    <Button dense variant={quiet ? "ghost" : "danger"} data-testid="conductor-stop" onClick={() => setConfirmFor(member)}>
      Stop
    </Button>
  );
}

function handAgain(member: ConductorMember): void {
  const o = member.origin;
  const kind = handRefOf(`${o?.kind}:${o?.id}`)?.kind;
  if (!o || !kind) return;
  openHand({ kind, id: o.id, title: o.title, projectId: o.projectId, agent: o.agent as AgentId });
}

/** The verb that fixes an agent on this Mac (Connect, Copy install), or none. */
function ReadyVerbs({ member, onStart }: { member: ConductorMember; onStart(): void }) {
  const installing = useConductor((s) => s.installing);
  const { copy, receipt } = useCopyReceipt();
  const row = member.detect;
  if (!row) return null;
  if (!row.installed) {
    return (
      <>
        {receipt}
        <Button dense variant="secondary" aria-label={`Copy install: ${member.name}`} onClick={() => void copy(AGENT_INSTALL[row.id])}>
          Copy install
        </Button>
      </>
    );
  }
  if (needsHooks(row)) {
    return (
      <Button
        dense
        variant="secondary"
        aria-label={`Connect ${member.name}`}
        data-testid="conductor-install-hooks"
        loading={installing === row.id}
        disabled={Boolean(installing) && installing !== row.id}
        onClick={() => void useConductor.getState().installHooks(row.id)}
      >
        {`Connect ${AGENT_NAME[row.id]}`}
      </Button>
    );
  }
  return canRun(row) ? (
    <Button dense variant="secondary" onClick={onStart} data-testid="agents-plate-start">
      Start an agent
    </Button>
  ) : null;
}

/** The Control mode in the registry's words (Secure, Normal, Open throttle). */
const CONTROL_WORD: Record<string, string> = {
  ...CONTROL_MODE_LABELS, secure: CONTROL_MODE_LABELS.safe, normal: CONTROL_MODE_LABELS.neutral,
};

/** The lane's own wait asks him now (a question or a permission prompt,
 *  not a turn end): the plate is the ask row whatever the flight says. */
function laneAsks(lane: LaneWire | null): boolean {
  const wait = lane && !isNotRead(lane.wait) ? lane.wait : null;
  if (!wait?.question || (wait.kind !== "TO ANSWER" && wait.kind !== "TO APPROVE")) return false;
  return !turnEndWord(wait) && turnWord(wait).word === "ASKS";
}

/** The technical facts (Details): the item, the Project, the branch, the
 *  session and launch ids, the agent's own facts (version, hooks, control). */
export function detailFacts(member: ConductorMember, lane: LaneWire | null): Record<string, string> {
  const facts: Record<string, string> = {};
  const put = (word: string, value: unknown) => {
    const text = String(value ?? "").trim();
    if (text) facts[word] = text;
  };
  put("Agent", agentWord(member));
  put("From", member.role === "ready" ? "" : member.facts.from);
  put("Project", member.facts.where);
  put("Branch", lane?.launch?.branch || member.facts.branch);
  put("Launched", lane?.launch?.launched_at ? madeWord(lane.launch.launched_at, new Date()) : "");
  const control = String(lane?.launch?.control_mode ?? "").toLowerCase();
  put("Control", CONTROL_WORD[control] ?? control);
  put("Session", member.sessionKey);
  put("Launch", member.launchId);
  for (const more of member.facts.more ?? []) put(more.word, more.value);
  return facts;
}

export interface PaneProps {
  member: ConductorMember;
  /** The word of the agent's state (memberPill) and its tone. */
  pill: { word: string; tone: string; live?: boolean };
  /** The session row of the agent (its question, its last words). */
  row: CoderSessionRow | undefined;
  onStart(): void;
  /** He picked this agent (a press, a hand, an open): its done turn is seen.
   *  False for the agent Agents shows first by itself. */
  opened?: boolean;
}

/** What the plate says the agent did last: its tool, else the screen's command. */
function activityOf(row: CoderSessionRow | undefined, lines: LedgerLine[]): string {
  const latest = lines.find((line) => !line.report && !["Brief", "Says"].includes(line.word));
  if (latest) return `${latest.word} · ${latest.text}`;
  const raw = ((row?.raw as Record<string, unknown>)?.session ?? row?.raw ?? {}) as Record<string, unknown>;
  const tool = String(raw.last_tool_name ?? "").trim();
  const command = String(row?.screen?.command ?? "").trim();
  return [tool, command].filter(Boolean).join(" · ");
}

/** The agent's last report: the lane's last words, the hook's, the screen's. */
function reportOf(lane: LaneWire | null, row: CoderSessionRow | undefined, lines: LedgerLine[]): string {
  const raw = ((row?.raw as Record<string, unknown>)?.session ?? row?.raw ?? {}) as Record<string, unknown>;
  const lastWords = lane && typeof (lane as unknown as Record<string, unknown>).last_words === "string"
    ? String((lane as unknown as Record<string, unknown>).last_words).trim() : "";
  return lastWords || lines.find((line) => line.report)?.text || String(raw.last_assistant_text ?? "").trim()
    || String(row?.screen?.said ?? "").trim();
}

export function AgentPane({ member, pill, row, onStart, opened = true }: PaneProps) {
  // One face per agent: a launched agent's lane is bound to the one lane
  // store while the pane shows it (lane/laneStore.ts).
  const { lane, events, error, raw, rebrief } = useLaneOf(member.launchId, opened);
  const failed = Boolean(error) && !lane;
  const read = () => void useLane.getState().load();
  const flights = useAgentFlights((s) => s.flights);
  const flight = useMemo(() => flights.find((f) => f.launchId && f.launchId === member.launchId) ?? null, [flights, member.launchId]);
  const activity = useMemo(() => (lane ? laneLines(lane, events) : sessionLines(row)), [lane, events, row]);
  const report = reportOf(lane, row, activity);
  const lines = useMemo(() => ledgerLines(lane, events, report, row), [lane, events, report, row]);
  const held = lane ? heldNow(lane) : undefined;
  const launched = Boolean(member.launchId && lane);
  const tellIt = launched && Boolean(lane?.launch.session_key) && !lane?.launch.stopped && member.role === "live";
  const tone = spineTone(member);
  const [busy, setBusy] = useState<string | null>(null);
  const run = (key: string, work: () => Promise<unknown>) => {
    setBusy(key);
    void work().finally(() => setBusy(null));
  };

  const question = row?.question ?? "";
  const rawSession = ((row?.raw as Record<string, unknown>)?.session ?? row?.raw ?? {}) as Record<string, unknown>;
  const waitId = rawSession.wait_id ? String(rawSession.wait_id) : null;
  const tokens = tokenWords(lane?.usage);
  const facts = [
    agentWord(member),
    agoWord(member.when),
    member.role !== "ready" ? String(member.facts.where || "") : member.detect?.version ? String(member.detect.version) : "",
    tokens,
  ].filter(Boolean).join(" · ");
  // Terminal: a launched agent's own pane in the pane; a plain session's window.
  const terminal = member.role !== "ready" && !member.ownAgent && member.live !== "queued"
    && (launched ? Boolean(lane?.launch.session_key) : fleetRank(member) !== 0 && Boolean(member.sessionKey));

  // Stop is the working plate's verb; any other agent that runs has it in the mast.
  const working = member.role === "live" && !member.helperRequest && fleetRank(member) !== 0
    && !["queued", "done", "pr", "idle"].includes(String(member.live));
  const mast = (
    <Mast kind="agent" id={member.id} agent={member.agent} title={memberTitle(member)} facts={facts}
      className="aw-mast" data-testid="agents-mast">
      {working ? null : <StopVerb member={member} quiet />}
      {tellIt ? (
        <Button dense variant="ghost" aria-pressed={rebrief} data-testid="lane-rebrief"
          onClick={() => useLane.getState().setRebrief(!rebrief)}>
          Tell it
        </Button>
      ) : null}
      {terminal ? (
        <Button dense variant="ghost" aria-pressed={raw} data-testid="agents-terminal" onClick={() => {
          if (launched) useLane.getState().setRaw(!raw);
          else openMember(member);
        }}>
          {raw ? "Back to the agent" : "Terminal"}
        </Button>
      ) : null}
      <ShowMe app="open-conductor" />
    </Mast>
  );

  const stateWord = (
    <DotWord className="aw-plate-state" tone={pill.tone === "danger" ? "fail" : pill.tone === "idle" ? "idle" : (pill.tone as "ok" | "warn" | "info")}
      data-testid="conductor-pill">
      {pill.word}
    </DotWord>
  );
  const programLine = <ProgramStepLine program={member.program} />;
  const head = (
    <>
      {stateWord}
      {reviewWords(member.review) ? <span className="aw-plate-fact" data-testid="conductor-review">{reviewWords(member.review)}</span> : null}
      {programLine}
    </>
  );

  const askPlate = (
    <div className="aw-plate aw-plate--ask" data-tone="brass" data-testid="conductor-asks" role="group" aria-label="Needs you">
      <AskPlate
        bare
        member={member}
        question={question}
        waitId={waitId}
        lead={false}
        selected={false}
        onSelect={() => undefined}
        onTerminal={() => {
          if (launched) useLane.getState().setRaw(true);
          else if (member.launchId) openAgentLane(member.launchId, { sessionKey: member.sessionKey, raw: true });
          else openMember(member);
        }}
        onOpenAnswer={() => answerMember(member)}
        onOpen={() => openMember(member)}
      />
    </div>
  );
  // The Result of a done turn (AG10): its words, what changed, what it used.
  const result = (word: string) => lane ? (
    <ResultBlock lane={lane} screenSaid={flight?.screen?.said ?? null}
      done={{ word, age: flight?.doneAt ? spokeWord(new Date(flight.doneAt)) : null }} />
  ) : null;

  let plate: ReactNode;
  if (launched && (held || laneAsks(lane)) && !member.helperRequest) {
    // The call the gate holds now is the plate (Allow / Deny on the ask row;
    // a cut call: Terminal shows it whole, with its own Allow / Deny).
    plate = askPlate;
  } else if (member.helperRequest) {
    plate = (
      <Plate tone="brass" head={<>{stateWord}<span className="aw-plate-fact">Asks for a helper</span></>}>
        <p className="aw-plate-words" data-testid="conductor-helper-request">{member.helperRequest.instruction}</p>
        <PlateVerbs>
          <Button dense variant="brass" loading={busy === "helper"} disabled={busy !== null} data-testid="conductor-allow-helper"
            onClick={() => run("helper", () => allowHelper(member))}>
            Allow helper
          </Button>
        </PlateVerbs>
      </Plate>
    );
  } else if (fleetRank(member) === 0) {
    plate = askPlate;
  } else if (member.role === "ready") {
    plate = (
      <Plate tone={tone} head={head}>
        <p className="aw-plate-words">
          {member.detect?.installed ? (member.detect.path ? String(member.detect.path) : "On this Mac") : "Not on this Mac"}
        </p>
        <PlateVerbs><ReadyVerbs member={member} onStart={onStart} /></PlateVerbs>
      </Plate>
    );
  } else if (member.role === "stale") {
    const restart = member.flightState === "stopped_by_restart" && member.launchId;
    plate = (
      <Plate tone={tone} head={head}>
        {member.flightState === "checked" && lane ? result("Done · checked by you")
          : report ? <AgentWords className="aw-plate-report" text={report} /> : null}
        <PlateVerbs>
          {restart ? (
            <Button dense variant="brass" loading={busy === "resume"} disabled={busy !== null} data-testid="conductor-resume"
              onClick={() => run("resume", () => resumeAll([member]))}>
              Resume
            </Button>
          ) : null}
          {HAND_AGAIN.has(String(member.flightState)) && member.origin ? (
            <Button dense variant="secondary" onClick={() => handAgain(member)} data-testid="conductor-hand-again">
              Hand again
            </Button>
          ) : null}
          {!restart && member.launchId ? (
            <Button dense variant="ghost" loading={busy === "remove"} disabled={busy !== null} data-testid="conductor-remove"
              onClick={() => run("remove", () => removeLaunch(member))}>
              Remove
            </Button>
          ) : null}
        </PlateVerbs>
      </Plate>
    );
  } else if (member.live === "queued") {
    plate = (
      <Plate tone={tone} head={head}>
        <p className="aw-plate-words">Waits for a free agent</p>
        <PlateVerbs>
          <Button dense variant="secondary" loading={busy === "cancel"} disabled={busy !== null} data-testid="conductor-cancel-queued"
            onClick={() => run("cancel", () => cancelQueuedHand(member))}>
            Cancel
          </Button>
        </PlateVerbs>
      </Plate>
    );
  } else if (member.live === "done" || member.live === "pr" || member.live === "idle") {
    // The PR row in the ledger carries Open the PR once the lane is read.
    const pr = flight?.pr?.url && !lane?.follow_through?.pr?.url ? flight.pr : null;
    const done = member.live === "done" && member.launchId;
    plate = (
      <Plate tone={tone} head={head}>
        {lane && member.live === "done" ? result("Done") : report ? <AgentWords className="aw-plate-report" text={report} data-testid="agents-report" /> : (
          <p className="aw-plate-words">{member.live === "idle" ? "Waits for your next words" : "No report yet"}</p>
        )}
        {reviewResult(member.review) ? <ReviewResult review={member.review} /> : null}
        <DeskAnswerLine answer={member.deskAnswer} />
        <PlateVerbs>
          {pr ? (
            <Button dense variant={done ? "secondary" : "brass"} data-testid="agents-open-pr"
              onClick={() => window.open(pr.url, "_blank", "noopener,noreferrer")}>
              {`Open the PR #${pr.number ?? ""}`.trim()}
            </Button>
          ) : null}
          {done ? (
            <Button dense variant="brass" loading={busy === "done"} disabled={busy !== null} data-testid="conductor-done"
              onClick={() => run("done", () => doneMember(member))}>
              Done
            </Button>
          ) : null}
          {member.ownAgent || member.launchId ? null : (
            <Button dense variant="ghost" onClick={() => openMember(member)} data-testid="conductor-open">
              Read
            </Button>
          )}
        </PlateVerbs>
      </Plate>
    );
  } else {
    const latest = activityOf(row, activity);
    plate = (
      <Plate tone={tone} head={head}>
        <p className="aw-plate-words" data-testid="agents-activity">
          {latest ? <span className="aw-plate-label">Latest activity</span> : null}
          {latest || "Working"}
        </p>
        <DeskAnswerLine answer={member.deskAnswer} />
        <PlateVerbs>
          <StopVerb member={member} />
          {member.ownAgent || member.launchId ? null : (
            <Button dense variant="ghost" onClick={() => openMember(member)} data-testid="conductor-open">
              Open
            </Button>
          )}
        </PlateVerbs>
      </Plate>
    );
  }

  return (
    <div className="aw-agent" data-testid="agents-agent" data-member={member.id}>
      {mast}
      <Spine className="aw-spine" tone={tone} label={pill.word} data-testid="agents-spine" data-tone={tone} />
      {launched && raw ? <div className="aw-terminal"><RawPane /></div>
        : launched && rebrief ? <div className="aw-plate aw-plate--tell" data-tone="steel"><RebriefWell /></div> : plate}
      <div className="aw-receipt-line">
        <MemberReceipt member={member} />
        {launched && lane ? <LaneReceipts lane={lane} /> : null}
      </div>
      {launched && raw ? null : <>
        {launched && lane ? <div className="aw-made"><PrRow lane={lane} itemTitle={String(member.facts.from || "")} /><FilesFold lane={lane} /></div> : null}
        <AgentLedger lines={lines} failed={failed && Boolean(member.launchId)} onRetry={read} />
        {launched && lane ? <UnreadLines lane={lane} /> : null}
      </>}
      <div className="aw-details" data-testid="agents-details">
        <FoldGadget title="Details">
          <SurfaceFacts value={detailFacts(member, lane)} />
          {lane ? <CheckLog lane={lane} /> : null}
          {member.launchId && !raw ? <WhyThisState launchId={member.launchId} /> : null}
        </FoldGadget>
      </div>
    </div>
  );
}
