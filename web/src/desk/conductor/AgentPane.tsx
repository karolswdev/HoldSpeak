/** The selected agent on the shared list and inspector grammar. */
import { useEffect, useMemo, useState, useRef } from "react";
import { Button } from "../../components/signal/Signal";
import { CONTROL_MODE_LABELS } from "../../lib/productLanguage";
import { AgentWords } from "../components/AgentWords";
import { useAgentFlights, type CoderSessionRow } from "../agentFlights";
import { handRefOf, openHand } from "../agentHand";
import { AgentRow as AskPlate, DeskAnswerLine } from "../agents/AgentRow";
import { WhyThisState } from "../agents/WhyThisState";
import { AGENT_INSTALL, AGENT_NAME, needsHooks, type AgentId } from "../firstrun/agentsStep";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import {
  laneEntries,
  isNotRead,
  branchFace,
  turnEndWord,
  turnWord,
  type LaneEntry,
  type LaneEvent,
  type LaneWire,
} from "../lane/laneWire";
import { useLane } from "../lane/laneStore";
import {
  CheckLog,
  FilesFold,
  LaneReceipts,
  PrRow,
  RawPane,
  RebriefWell,
  UnreadLines,
  heldNow,
  spokeWord,
  useLaneOf,
} from "./AgentLane";
import { ResultBlock } from "../lane/ResultBlock";
import { ProgramLink } from "../programs/ProgramLink";
import { openAgentLane } from "../shell";
import {
  DotWord,
  PaneInspector,
  InspectorBody,
  InspectorFacts,
  PaneActions,
  wireDayClock,
  PreferenceWell,
  ListView,
  StepTrack,
  LiveWell,
  InspectorFigures,
  SegmentedTabs,
  InspectorQuestion,
  PaneNotice,
  type ListVerb,
} from "../surface";

import { reviewResult } from "../agentFlights";
import { ReviewResult } from "./ReviewResult";
import { canRun, fleetRank, reviewWords, type ConductorMember } from "./members";
import {
  allowHelper,
  answerMember,
  cancelQueuedHand,
  doneMember,
  openMember,
  removeLaunch,
  resumeAll,
  stopMember,
  stops,
} from "./open";
import { useConductor } from "./store";
import { listSprite } from "../sprites";
import { nameIsFile } from "../surface/objects/fitName";
import { objectSprite } from "../surface";

/** The stopped agents whose item takes Hand again (a new agent in the
 *  same worktree; the hub checks it). */
const HAND_AGAIN = new Set(["resume_failed", "stopped_by_restart", "ended", "expired"]);

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
  brief: "Brief",
  read: "Read",
  says: "Says",
  write: "Wrote",
  run: "Ran",
  call: "Called",
  answer: "Your answer",
  end: "Ended",
  commit: "Commit",
  pr: "PR",
  held: "Held",
  asks: "Asks",
  merge: "Merged",
  rebrief: "Re-brief",
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
  const lines = String(text ?? "")
    .replace(/\r/g, "")
    .split("\n");
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
    return String(text ?? "")
      .split(/\n\s*\n/)
      .map((part) => part.trim())
      .filter(Boolean)
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
  const flat = String(text ?? "")
    .replace(/\s+/g, " ")
    .replace(/[#*`>]/g, "")
    .trim();
  if (flat.length <= max) return flat;
  const cut = flat.slice(0, max);
  return `${cut.slice(0, Math.max(cut.lastIndexOf(" "), 24)).trim()} …`;
}

/** The pane's ledger: the report's sections first (Read opens each), then
 *  the tool activity by time, newest first; a launch with only its brief
 *  shows the brief as one row. */
export function ledgerLines(
  lane: LaneWire | null,
  events: readonly LaneEvent[],
  report: string,
  row?: CoderSessionRow,
): LedgerLine[] {
  const sections = report
    ? reportSections(report).map((section, i): LedgerLine => ({
        id: `report-${i}`,
        time: "",
        word: "Report",
        text: section.title,
        body: section.body,
        report: true,
      }))
    : [];
  const said = report.trim();
  const activity = (lane ? laneLines(lane, events) : sessionLines(row).filter((line) => !line.report)).filter(
    (line) => !said || line.text.trim() !== said,
  );
  if (lane && !activity.length && !sections.length && lane.launch?.brief_text) {
    return [
      {
        id: "brief",
        time: "",
        word: "Brief",
        text: "The brief",
        body: String(lane.launch.brief_text),
      },
    ];
  }
  return [...sections, ...activity];
}

/** The lane's timeline, newest first, as ledger lines. */
export function laneLines(
  lane: LaneWire,
  events: readonly LaneEvent[] = Array.isArray(lane.events) ? lane.events : [],
): LedgerLine[] {
  // An older hub (or a partial answer) leaves a part out: it is not read.
  const whole: LaneWire = {
    ...lane,
    launch: lane.launch ?? ({} as LaneWire["launch"]),
    worktree: lane.worktree ?? { not_read: "absent" },
    follow_through: lane.follow_through ?? { pr: null },
    gated: lane.gated ?? [],
  };
  return (
    laneEntries(whole, events)
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
      .filter((line) => line.text.trim() && !["Brief", "PR", "Merged"].includes(line.word))
  );
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
  if (said)
    lines.push({
      id: "said",
      time: "",
      word: "Says",
      text: said,
      report: true,
    });
  if (tool) lines.push({ id: "tool", time: "", word: "Tool", text: tool });
  if (command) lines.push({ id: "command", time: "", word: "Command", text: command });
  return lines;
}

function AgentLedger({ lines, failed, onRetry }: { lines: LedgerLine[]; failed: boolean; onRetry(): void }) {
  const [picked, setPicked] = useState<string | null>(null);
  const [reading, setReading] = useState<string | null>(null);
  if (failed)
    return (
      <PaneActions>
        <DotWord tone="fail" data-testid="agents-ledger-failed">
          Activity not read
        </DotWord>
        <Button dense onClick={onRetry}>
          Read again
        </Button>
      </PaneActions>
    );
  if (!lines.length) return <PaneNotice>No activity yet.</PaneNotice>;
  const line = lines.find((line) => line.id === reading);
  return (
    <InspectorBody>
      <ListView
        label="Activity"
        selection
        ordered
        headerless
        rows={lines.map((line) => ({
          id: line.id,
          kind: "report",
          name: line.text,
          detail: line.word,
          when: line.time,
        }))}
        columns={[
          { key: "name", word: "Activity" },
          { key: "when", word: "When", minWidth: 80 },
        ]}
        selectedId={picked}
        onSelect={setPicked}
        onOpen={setReading}
        verbs={[
          {
            id: "read",
            label: reading ? "Close" : "Read",
            testId: "agents-ledger-read",
            enabled: (row) => Boolean(lines.find((line) => line.id === row?.id)?.body),
            run: (row) => setReading(reading ? null : (row?.id ?? null)),
          },
        ]}
        rowProps={() => ({ "data-testid": "agents-ledger-row" })}
      />
      {line?.body ? (
        <PreferenceWell>
          <AgentWords text={line.body} />
        </PreferenceWell>
      ) : null}
    </InspectorBody>
  );
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
        <Button
          dense
          variant="ghost"
          loading={installing === agent}
          onClick={() => void useConductor.getState().installHooks(agent)}
        >
          Retry
        </Button>
      </span>
    );
  }
  if (stop) {
    return (
      <span
        className="drawer-receipt cw-receipt"
        data-tone={stop.tone === "ok" ? undefined : "fail"}
        role="status"
        data-testid="conductor-stop-receipt"
      >
        <span className="kit-dot" data-tone={stop.tone === "ok" ? "ok" : "fail"} aria-hidden="true" />
        {stopWords(stop.word, stop.text)}
      </span>
    );
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
  if (word === "NOT RESUMED") return text;
  if (word === "STOPPED" && text === "BY YOU") return "Stopped by you";
  return plainReceipt([word, text].filter(Boolean).join(" · "));
}

function handAgain(member: ConductorMember): void {
  const o = member.origin;
  const kind = handRefOf(`${o?.kind}:${o?.id}`)?.kind;
  if (!o || !kind) return;
  openHand({
    kind,
    id: o.id,
    title: o.title,
    projectId: o.projectId,
    agent: o.agent as AgentId,
  });
}

/** The Control mode in the registry's words (Secure, Normal, Open throttle). */
const CONTROL_WORD: Record<string, string> = {
  ...CONTROL_MODE_LABELS,
  secure: CONTROL_MODE_LABELS.safe,
  normal: CONTROL_MODE_LABELS.neutral,
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
  put("Review", reviewWords(member.review));
  put("From", member.role === "ready" ? "" : member.facts.from);
  put("Project", member.facts.where);
  put("Branch", branchFace(lane?.launch?.branch || member.facts.branch));
  put("Launched", lane?.launch?.launched_at ? wireDayClock(lane.launch.launched_at) : "");
  const control = String(lane?.launch?.control_mode ?? "").toLowerCase();
  put("Control", CONTROL_WORD[control] ?? control);
  put("Usage", tokenWords(lane?.usage));
  put("Status", member.receipt ? plainReceipt(member.receipt) : "");
  const pr = lane?.follow_through?.pr;
  put("PR", pr?.number ? `#${pr.number}` : "");
  for (const more of member.facts.more ?? []) put(more.word.replace(/-/g, " "), more.value);
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
  onVerbs?(verbs: readonly ListVerb[]): void;
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
  const lastWords =
    lane && typeof (lane as unknown as Record<string, unknown>).last_words === "string"
      ? String((lane as unknown as Record<string, unknown>).last_words).trim()
      : "";
  return (
    lastWords ||
    lines.find((line) => line.report)?.text ||
    String(raw.last_assistant_text ?? "").trim() ||
    String(row?.screen?.said ?? "").trim()
  );
}

/** The selected session: one inspector, with the existing hub actions. */
export function AgentPane({ member, pill, row, onStart, opened = true, onVerbs }: PaneProps) {
  const { lane, events, error, raw, rebrief } = useLaneOf(member.launchId, opened && Boolean(member.isNew || (member.deskAnswer?.state === "answered" && member.deskAnswer.isNew)));
  const flights = useAgentFlights((s) => s.flights);
  const flight = flights.find((f) => f.launchId && f.launchId === member.launchId);
  const activity = useMemo(() => (lane ? laneLines(lane, events) : sessionLines(row)), [lane, events, row]);
  const report = reportOf(lane, row, activity);
  const lines = useMemo(() => ledgerLines(lane, events, report, row), [lane, events, report, row]);
  const [view, setView] = useState("now");
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const installing = useConductor((state) => state.installing);
  const [busy, setBusy] = useState<string | null>(null);
  const [question, setQuestion] = useState<"stop" | "remove" | "cancel" | null>(null);
  const answerSeat = useRef<HTMLDivElement>(null);
  const answerAction = useRef<(() => void) | null>(null);
  const launched = Boolean(member.launchId && lane);
  const asks = Boolean((lane && (heldNow(lane) || laneAsks(lane))) || fleetRank(member) === 0);
  const tellIt = launched && Boolean(lane?.launch.session_key) && !lane?.launch.stopped && member.role === "live";
  const terminal =
    member.role !== "ready" &&
    !member.ownAgent &&
    member.live !== "queued" &&
    Boolean(member.sessionKey || lane?.launch.session_key);
  const pr = lane?.follow_through?.pr ?? flight?.pr;
  const run = (key: string, work: () => Promise<unknown>) => {
    setBusy(key);
    void work().finally(() => setBusy(null));
  };
  const verbs: ListVerb[] = [];
  const add = (id: string, label: string, act: () => void, testId?: string, enabled = true, title?: string) =>
    verbs.push({
      id,
      label,
      testId,
      title,
      enabled: () => enabled && !busy,
      run: act,
    });
  if (member.role === "ready" && member.detect) {
    const detected = member.detect;
    if (!detected.installed) add("copy", "Copy install", () => void copy(AGENT_INSTALL[detected.id]));
    else if (needsHooks(detected))
      add(
        "connect",
        `Connect ${AGENT_NAME[detected.id]}`,
        () => void useConductor.getState().installHooks(detected.id),
        "conductor-install-hooks",
        !installing,
      );
    else if (canRun(detected) && !onVerbs) add("ready-start", "Start an agent", onStart, "agents-plate-start");
  }
  if (asks && !member.helperRequest)
    add(
      "answer",
      "Answer",
      () => {
        setView("now");
        window.requestAnimationFrame(() => {
          answerAction.current?.();
          answerSeat.current?.querySelector<HTMLInputElement>("input")?.focus();
        });
      },
      undefined,
      !raw,
    );
  if (pr?.url)
    add("pr", "Open the PR", () => window.open(pr.url!, "_blank", "noopener,noreferrer"), "lane-open-pr", true, pr.url);
  if (terminal)
    add(
      "terminal",
      raw ? "Back to the agent" : "Open terminal",
      () => {
        if (launched) useLane.getState().setRaw(!raw);
        else openMember(member);
      },
      "agents-terminal",
    );
  if (tellIt) add("tell", "Tell it", () => useLane.getState().setRebrief(!rebrief), "lane-rebrief");
  if (stops(member)) add("stop", "Stop", () => setQuestion("stop"), "conductor-stop");
  if (member.helperRequest)
    add("helper", "Allow helper", () => run("helper", () => allowHelper(member)), "conductor-allow-helper");
  if (member.role === "stale") {
    const restart = member.flightState === "stopped_by_restart" && member.launchId;
    if (restart) add("resume", "Resume", () => run("resume", () => resumeAll([member])), "conductor-resume");
    if (HAND_AGAIN.has(String(member.flightState)) && member.origin)
      add("hand", "Hand again", () => handAgain(member), "conductor-hand-again");
    if (!restart && member.launchId) add("remove", "Remove", () => setQuestion("remove"), "conductor-remove");
  }
  if (member.live === "queued") add("cancel", "Cancel task", () => setQuestion("cancel"), "conductor-cancel-queued");
  if (member.live === "done" && member.launchId)
    add("done", "Done", () => run("done", () => doneMember(member)), "conductor-done");
  if (member.role !== "ready" && !member.ownAgent && !member.launchId && member.live !== "queued")
    add(
      "open",
      member.live === "done" || member.live === "idle" ? "Read" : "Open",
      () => openMember(member),
      "conductor-open",
    );
  useEffect(() => {
    onVerbs?.(verbs);
  });
  const facts = detailFacts(member, lane);
  const launchFacts = (
    <InspectorFacts
      name={memberTitle(member)}
      data-feedback-redact="true"
      rows={Object.entries(facts)
        .filter(([key]) => ["Project", "Branch", "Launched"].includes(key) && !(key === "Branch" && (member.live === "done" || member.flightState === "checked")))
        .map(([label, value]) => ({ label, value }))}
    />
  );
  const hasFiles = Boolean(lane && (!isNotRead(lane.worktree) || lane.worktree.not_read !== "the launch has no worktree" || pr?.url));
  useEffect(() => {
    if (view === "files" && !hasFiles) setView("now");
  }, [view, hasFiles]);
  const waitId =
    (row?.raw as { session?: { wait_id?: string }; wait_id?: string })?.session?.wait_id ??
    (row?.raw as { wait_id?: string })?.wait_id;
  const step = pr?.number ? "pr" : "work";
  const screen = member.screen?.said || row?.screen?.said;
  const latest = activityOf(row, activity);
  const NowSeat = asks ? InspectorBody : PreferenceWell;
  const now = (
    <NowSeat>
      {asks && !member.helperRequest ? (
        <div
          ref={answerSeat}
          className="surface-inspector-body"
          data-testid="conductor-asks"
          data-feedback-redact="true"
        >
          <AskPlate
            bare
            toolbarOwnsVerbs={Boolean(onVerbs)}
            focusQuestion={opened}
            answerAction={answerAction}
            facts={launchFacts}
            member={member}
            question={row?.question ?? ""}
            waitId={waitId}
            lead
            selected={false}
            onSelect={() => undefined}
            onTerminal={() => {
              if (launched) useLane.getState().setRaw(true);
              else if (member.launchId)
                openAgentLane(member.launchId, {
                  sessionKey: member.sessionKey,
                  raw: true,
                });
              else openMember(member);
            }}
            onOpenAnswer={() => answerMember(member)}
            onOpen={() => openMember(member)}
          />
        </div>
      ) : member.helperRequest ? (
        <AgentWords text={member.helperRequest.instruction} data-testid="conductor-helper-request" />
      ) : member.role === "ready" ? (
        <InspectorFacts
          name={memberTitle(member)}
          data-feedback-redact="true"
          rows={[
            {
              label: "Installed",
              value: member.detect?.installed ? "On this Mac" : "Not on this Mac",
            },
            { label: "Path", value: member.detect?.path },
          ]}
        />
      ) : (
        <>
          {lane && !["queued", "idle"].includes(String(member.live)) ? (
            <StepTrack
              label="Agent progress"
              steps={[
                {
                  id: "brief",
                  name: "Brief",
                  state: lane.launch.instruction_state === "sent" || lane.launch.brief_text ? "done" : "planned",
                },
                {
                  id: "work",
                  name: "Work",
                  state:
                    member.role === "stale"
                      ? ["checked", "merged"].includes(String(member.flightState))
                        ? "done"
                        : "parked"
                      : step === "pr" || member.live === "done"
                        ? "done"
                        : member.live === "no_signal"
                          ? "limited"
                          : "working",
                },
                {
                  id: "pr",
                  name: "PR",
                  state: pr?.number ? "done" : "planned",
                },
                {
                  id: "review",
                  name: "Review",
                  state: lane.follow_through?.merged
                    ? "done"
                    : lane.follow_through?.pr?.review_decision === "APPROVED"
                      ? "done"
                      : "planned",
                },
              ]}
              current={step}
              onSelect={(id) => {
                setQuestion(null);
                setView(id === "pr" ? "files" : id === "work" ? "now" : "facts");
              }}
            />
          ) : null}
          {pr?.number ? (
            <InspectorFigures
              label="Pull request"
              figures={[
                { label: "Pull request", value: `#${pr.number}`, tone: "info" },
                {
                  label: "Review",
                  value: lane?.follow_through?.pr?.review_decision === "APPROVED" ? "Approved" : "Not reviewed",
                  tone: "ask",
                },
              ]}
            />
          ) : null}
          {screen || latest ? (
            <LiveWell
              label={screen ? "Last screen" : "Latest activity"}
              lines={(screen || latest).split("\n").map((text, i) => ({ id: String(i), text }))}
              working={member.live === "work"}
              data-feedback-redact="true"
            />
          ) : null}
          {(member.live === "done" || member.flightState === "checked") && lane ? (
            <ResultBlock
              lane={lane}
              screenSaid={flight?.screen?.said ?? null}
              done={{
                word: member.flightState === "checked" ? "Done · checked by you" : "Done",
                age: flight?.doneAt ? spokeWord(new Date(flight.doneAt)) : null,
              }}
            />
          ) : report ? (
            <div data-feedback-redact="true">
              <AgentWords text={report} data-testid="agents-report" />
            </div>
          ) : null}
          {reviewResult(member.review) ? <ReviewResult review={member.review} /> : null}
          {!lane && !report && !screen && !latest ? <PaneNotice><span data-testid="conductor-receipt">{member.receipt ? plainReceipt(member.receipt) : "No activity yet."}</span></PaneNotice> : null}
          <DeskAnswerLine answer={member.deskAnswer} />
        </>
      )}
      {question !== "remove" && (!asks || member.helperRequest) ? launchFacts : null}
    </NowSeat>
  );
  return (
    <PaneInspector
      object={<img src={nameIsFile(memberTitle(member)) ? objectSprite("artifact", memberTitle(member)) : listSprite(member.sprite ?? "")} width={32} height={32} alt="" />}
      label={memberTitle(member)}
      subtitle={[agentWord(member), pill.word, agoWord(member.when)].filter(Boolean).join(" · ")}
      testId="agents-mast"
    >
      <InspectorBody>
        {question ? (
          <InspectorQuestion
            key={question}
            question={
              question === "stop"
                ? `Stop ${memberTitle(member)}?`
                : question === "remove"
                  ? `Remove ${memberTitle(member)}?`
                  : `Cancel ${memberTitle(member)}?`
            }
            consequence={question === "stop" ? "Ends the agent's session." : undefined}
            targetId={JSON.stringify([
              member.id,
              member.sessionKey,
              member.flightState,
              member.answerBinding?.wait_revision,
              member.answerBinding?.expected_pane_fingerprint,
            ])}
            actionId={question}
            cancelLabel={question === "cancel" ? "Keep it" : "Cancel"}
            cancel={() => setQuestion(null)}
            verb={{
              label: question === "stop" ? "Stop" : question === "remove" ? "Remove" : "Cancel task",
              testId: question === "stop" ? "conductor-stop-confirm" : "conductor-remove-confirm",
              busy: Boolean(busy),
              run: () => {
                run(question, async () => {
                  if (question === "stop") await stopMember(member);
                  else if (question === "remove") await removeLaunch(member);
                  else await cancelQueuedHand(member);
                  setQuestion(null);
                });
              },
            }}
          />
        ) : null}
        {copyReceipt}
        <MemberReceipt member={member} />
        {lane ? <LaneReceipts lane={lane} /> : null}
        {raw && launched ? (
          <PreferenceWell>
            <RawPane />
          </PreferenceWell>
        ) : rebrief && launched ? (
          <RebriefWell />
        ) : (
          <SegmentedTabs
            label="Agent view"
            value={question === "remove" ? "now" : view}
            onChange={setView}
            tabs={question === "remove" ? [{id: "now", label: "Now"}] : [
              { id: "now", label: "Now" },
              { id: "activity", label: "Activity" },
              ...(hasFiles ? [{ id: "files", label: "Files" }] : []),
              { id: "facts", label: "Facts" },
            ]}
          >
            {question === "remove" || view === "now" ? (
              now
            ) : view === "activity" ? (
              <div data-testid="agents-ledger" data-feedback-redact="true">
                <AgentLedger
                  lines={lines}
                  failed={Boolean(error) && !lane}
                  onRetry={() => void useLane.getState().load()}
                />
              </div>
            ) : view === "files" ? (
              lane ? (
                <PreferenceWell>
                  <PrRow lane={lane} itemTitle={String(member.facts.from || "")} showVerb={!onVerbs} />
                  <FilesFold lane={lane} />
                  <UnreadLines lane={lane} />
                </PreferenceWell>
              ) : <PaneNotice>No files for this agent.</PaneNotice>
            ) : (
              <PreferenceWell>
                <InspectorFacts
                  name={memberTitle(member)}
                  data-feedback-redact="true"
                  rows={[
                    { label: "Name", value: member.role === "ready" ? undefined : memberTitle(member) },
                    ...(member.program ? [{ label: "Program", value: <ProgramLink program={member.program} /> }] : []),
                    ...Object.entries(facts).map(([label, value]) => ({ label, value })),
                    { label: "Brief", value: lane?.launch.brief_text },
                  ]}
                />
                {lane ? <CheckLog lane={lane} /> : null}
                {member.launchId ? <WhyThisState launchId={member.launchId} /> : null}
              </PreferenceWell>
            )}
          </SegmentedTabs>
        )}
        {!question && !onVerbs ? (
          <PaneActions>
            {verbs
              .filter((verb) => !["answer", "stop", "remove", "cancel"].includes(verb.id))
              .map((verb) => (
                <Button
                  key={verb.id}
                  dense
                  variant={
                    verb.id === "pr" ? "primary" : verb.id === "done" || verb.id === "helper" || verb.id === "resume" ? "brass" : "secondary"
                  }
                  aria-pressed={verb.id === "terminal" ? raw : verb.id === "tell" ? rebrief : undefined}
                  title={verb.title}
                  data-testid={verb.testId}
                  disabled={!verb.enabled?.(null)}
                  onClick={() => verb.run(null)}
                >
                  {verb.label}
                </Button>
              ))}

            {/* The destructive trigger stays in the selected inspector as well as its shared verb row. */}
            {verbs
              .filter((verb) => ["stop", "remove", "cancel"].includes(verb.id))
              .map((verb) => (
                <Button
                  key={verb.id}
                  dense
                  data-testid={verb.testId}
                  disabled={Boolean(busy)}
                  onClick={() => verb.run(null)}
                >
                  {verb.label}
                </Button>
              ))}
          </PaneActions>
        ) : null}
      </InspectorBody>
    </PaneInspector>
  );
}
