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
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { CONTROL_MODE_LABELS } from "../../lib/productLanguage";
import { madeWord } from "../drawer/members";
import { AgentWords } from "../components/AgentWords";
import { useAgentFlights, type CoderSessionRow } from "../agentFlights";
import { handRefOf, openHand } from "../agentHand";
import { AgentRow as AskPlate, DeskAnswerLine } from "../agents/AgentRow";
import { WhyThisState } from "../agents/WhyThisState";
import { AGENT_INSTALL, AGENT_NAME, needsHooks, type AgentId } from "../firstrun/agentsStep";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { laneEntries, isNotRead, type LaneEntry, type LaneEvent, type LaneWire } from "../lane/laneWire";
import { ProgramStepLine } from "../programs/StepLine";
import { openAgentLane } from "../shell";
import { DotWord, FoldGadget, SurfaceLedger, SurfaceLedgerRow } from "../surface";
import { SurfaceFacts } from "../surface/Surface";
import { Mast } from "../surface/patterns/Mast";
import { Spine, type SpineTone } from "../surface/patterns/Spine";
import { useOnCoderFrame } from "../useDeskChangedRefresh";
import { reviewResult } from "../agentFlights";
import { ReviewResult } from "./ReviewResult";
import { canRun, fleetRank, reviewWords, type ConductorMember } from "./members";
import {
  allowHelper, answerMember, cancelQueuedHand, doneMember, openMember, removeLaunch, resumeAll, stopMember, stops,
} from "./open";
import { useConductor } from "./store";

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

/* ── the lane read (one launch) ─────────────────────────────────────── */

/** The newest events the ledger reads (the lane pages oldest first). */
const LEDGER_LIMIT = 1000;
/** The ledger shows this many rows; Terminal and the agent's window hold the rest. */
const LEDGER_ROWS = 40;

export function useAgentLane(launchId: string | null | undefined, live: string | undefined) {
  const [lane, setLane] = useState<LaneWire | null>(null);
  const [failed, setFailed] = useState(false);
  const asked = useRef(0);
  const read = useCallback(() => {
    if (!launchId) return;
    const seq = ++asked.current;
    apiFetch<LaneWire | null>(`/api/agent/launches/${encodeURIComponent(launchId)}/lane?after=0&limit=${LEDGER_LIMIT}`)
      .then((body) => {
        if (seq !== asked.current) return;
        setLane(body && typeof body === "object" && body.launch ? body : null);
        setFailed(false);
      })
      .catch(() => {
        if (seq === asked.current) setFailed(true);
      });
  }, [launchId]);
  useEffect(() => {
    setLane(null);
    setFailed(false);
  }, [launchId]);
  // A state change (works → asks → done) reads the lane again.
  useEffect(() => read(), [read, live]);
  useOnCoderFrame(read);
  return { lane, failed, read };
}

/* ── the ledger ─────────────────────────────────────────────────────── */

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
}

/** The lane's timeline, newest first, as ledger lines. */
export function laneLines(lane: LaneWire): LedgerLine[] {
  const events = Array.isArray(lane.events) ? (lane.events as LaneEvent[]) : [];
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
      report: entry.kind === "says",
    }))
    .filter((line) => line.text.trim());
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
      <SurfaceLedger cols="kit" label="Activity">
        <ul className="surface-ledger-rows">
          {lines.map((line) => (
            <SurfaceLedgerRow
              key={line.id}
              time={line.time || undefined}
              primary={<span className="aw-ledger-text" title={line.text}>{line.text}</span>}
              meta={line.word}
              metaTone={line.tone}
              expands={false}
              data-testid="agents-ledger-row"
            />
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
}

/** What the plate says the agent did last: its tool, else the screen's command. */
function activityOf(row: CoderSessionRow | undefined, lines: LedgerLine[]): string {
  const latest = lines.find((line) => !line.report && line.word !== "Brief");
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

export function AgentPane({ member, pill, row, onStart }: PaneProps) {
  const { lane, failed, read } = useAgentLane(member.launchId, member.live);
  const flights = useAgentFlights((s) => s.flights);
  const flight = useMemo(() => flights.find((f) => f.launchId && f.launchId === member.launchId) ?? null, [flights, member.launchId]);
  const lines = useMemo(() => (lane ? laneLines(lane) : sessionLines(row)), [lane, row]);
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
  // An ask's plate carries its own Terminal where it matters (a held call).
  const terminal = member.role !== "ready" && !member.ownAgent && member.live !== "queued" && fleetRank(member) !== 0
    && (member.launchId || member.sessionKey);

  // Stop is the working plate's verb; any other agent that runs has it in the mast.
  const working = member.role === "live" && !member.helperRequest && fleetRank(member) !== 0
    && !["queued", "done", "pr", "idle"].includes(String(member.live));
  const mast = (
    <Mast kind="agent" id={member.id} agent={member.agent} title={memberTitle(member)} facts={facts}
      className="aw-mast" data-testid="agents-mast">
      {working ? null : <StopVerb member={member} quiet />}
      {terminal ? (
        <Button dense variant="ghost" data-testid="agents-terminal" onClick={() => {
          if (member.launchId) openAgentLane(member.launchId, { sessionKey: member.sessionKey, raw: true });
          else openMember(member);
        }}>
          Terminal
        </Button>
      ) : null}
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

  let plate: ReactNode;
  if (member.helperRequest) {
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
    plate = (
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
            if (member.launchId) openAgentLane(member.launchId, { sessionKey: member.sessionKey, raw: true });
            else openMember(member);
          }}
          onOpenAnswer={() => answerMember(member)}
          onOpen={() => openMember(member)}
        />
      </div>
    );
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
        {reportOf(lane, row, lines) ? <AgentWords className="aw-plate-report" text={reportOf(lane, row, lines)} /> : null}
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
          <Button dense variant="ghost" onClick={() => openMember(member)} data-testid="conductor-open">
            Read
          </Button>
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
    const report = reportOf(lane, row, lines);
    const pr = flight?.pr?.url ? flight.pr : null;
    const done = member.live === "done" && member.launchId;
    plate = (
      <Plate tone={tone} head={head}>
        {report ? <AgentWords className="aw-plate-report" text={report} data-testid="agents-report" /> : (
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
          {member.ownAgent ? null : (
            <Button dense variant="ghost" onClick={() => openMember(member)} data-testid="conductor-open">
              Read
            </Button>
          )}
        </PlateVerbs>
      </Plate>
    );
  } else {
    const activity = activityOf(row, lines);
    plate = (
      <Plate tone={tone} head={head}>
        <p className="aw-plate-words" data-testid="agents-activity">
          {activity ? <span className="aw-plate-label">Latest activity</span> : null}
          {activity || "Working"}
        </p>
        <DeskAnswerLine answer={member.deskAnswer} />
        <PlateVerbs>
          <StopVerb member={member} />
          {member.ownAgent ? null : (
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
      {plate}
      <div className="aw-receipt-line"><MemberReceipt member={member} /></div>
      <AgentLedger lines={lines} failed={failed && Boolean(member.launchId)} onRetry={read} />
      <div className="aw-details" data-testid="agents-details">
        <FoldGadget title="Details">
          <SurfaceFacts value={detailFacts(member, lane)} />
          {member.launchId ? <WhyThisState launchId={member.launchId} /> : null}
        </FoldGadget>
      </div>
    </div>
  );
}
