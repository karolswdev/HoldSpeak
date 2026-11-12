import { guideOwnsView } from "../walk/viewState";
import { useWindowId } from "../components/window/windowIdContext";
/* The launched agent in the Agents pane (2026-11-08, "one face per agent"):
 * the lane window folded into the pane. The pane binds the one lane store
 * (lane/laneStore.ts) to the picked launch; these are the parts only the
 * lane held: a cut held call read whole in the terminal (B63; the held
 * plate is the ask row, agents/AgentRow.tsx),
 * Tell it (a Re-brief, B46) with its queued receipts and Take back (B67),
 * the receipts of what was sent, the terminal (the lane's own pane, its
 * keys), the PR row, the files changed and the check log. Moved from
 * lane/LaneWindow.tsx (parked) with their behaviour unchanged. */
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { markLaunchSeen } from "../agentFlights";
import { WhyThisState } from "../agents/WhyThisState";
import { AgentWords, cutAtWord } from "../components/AgentWords";
import { ArmStrip, KeyPalette, PANE_STATE_LABEL } from "../components/SessionPullout";
import { useGate } from "../gate";
import { spriteUrl } from "../sprites";
import { useSteering } from "../steering";
import {
  DotWord,
  FoldGadget,
  PaneWell,
  StringGadget,
  wireDate,
  InspectorFacts,
  PaneActions,
  InspectorForm,
  InspectorBody,
  PreferenceWell,
  SurfaceCode,
} from "../surface";
import { Spine, type SpineTone } from "../surface/patterns/Spine";
import { stateWords } from "../surface/words";
import { useOnCoderFrame } from "../useDeskChangedRefresh";
import { filesWords } from "../lane/ResultBlock";
import { checksSummary, isNotRead, unreadParts, type LaneEvent, type LaneGated, type LaneWire } from "../lane/laneWire";
import { TERMINAL_GONE_WORDS, launchForSession, useLane } from "../lane/laneStore";

const NO_EVENTS: LaneEvent[] = [];

/** Bind the lane store to the picked launch while the pane shows it: one
 *  read now, one on each coder frame; the done turn is seen (AG0). */
export function useLaneOf(launchId: string | null | undefined, seen = true) {
  const windowId = useWindowId();
  // Opening the agent sees its done turn (AG0); the agent Agents picks by
  // itself (nothing pressed) is not opened yet.
  useEffect(() => {
    if (launchId && seen && !guideOwnsView(windowId)) void markLaunchSeen(launchId, null);
  }, [launchId, seen, windowId]);
  useEffect(() => {
    if (!launchId) return;
    // Steering bound to another launch's session (its terminal) lets go:
    // one agent at a time is in the pane.
    const key = useSteering.getState().openKey;
    const other = key ? launchForSession(key) : null;
    if (other && other !== launchId) useSteering.getState().closeSession();
    useLane.getState().open(launchId);
  }, [launchId]);
  useOnCoderFrame(() => {
    if (launchId && useLane.getState().launchId === launchId) void useLane.getState().load();
  });
  const bound = useLane((s) => s.launchId === launchId);
  const lane = useLane((s) => (bound ? s.lane : null));
  const events = useLane((s) => (bound ? s.events : NO_EVENTS));
  const error = useLane((s) => (bound ? s.error : null));
  const raw = useLane((s) => bound && s.raw);
  const rebrief = useLane((s) => bound && s.rebrief);
  // A partial answer with no launch block is not a lane (an older hub).
  return {
    lane: launchId && bound && lane?.launch ? lane : null,
    events,
    error,
    raw,
    rebrief,
  };
}

/** The PR as one row: the spine steel while open, moss merged, coral when a
 *  check is red; its own title; its checks and review; Open the PR. */
export function PrRow({ lane, itemTitle }: { lane: LaneWire; itemTitle: string }) {
  const pr = lane.follow_through?.pr;
  if (!pr || pr.number == null) return null;
  const checks = checksSummary(pr.checks);
  const merged = String(pr.state ?? "").toLowerCase() === "merged" || Boolean(lane.follow_through?.merged);
  const tone: SpineTone = checks?.failed ? "coral" : merged ? "moss" : "steel";
  const review = prReviewWords(pr.review_decision);
  return (
    <div data-testid="lane-pr" data-feedback-redact="true">
      <InspectorFacts
        header={false}
        name="Pull request"
        rows={[
          { label: "PR", value: `#${pr.number} ${pr.title || itemTitle}` },
          {
            label: "Item",
            value: <span data-testid="lane-pr-item">{itemTitle}</span>,
          },
          {
            label: "Checks",
            value: checks ? (
              <DotWord
                tone={checks.failed ? "fail" : checks.running ? "warn" : "ok"}
                data-testid="lane-pr-checks"
              >{`Checks ${checks.passed} of ${checks.total}`}</DotWord>
            ) : null,
          },
          {
            label: "Review",
            value: (
              <DotWord tone={review.tone} data-testid="lane-pr-review">
                {review.word}
              </DotWord>
            ),
          },
        ]}
      />
      {pr.url ? (
        <PaneActions>
          <Button
            dense
            title={pr.url}
            data-testid="lane-file-open-pr"
            onClick={() => window.open(pr.url!, "_blank", "noopener,noreferrer")}
          >
            Open the PR
          </Button>
        </PaneActions>
      ) : null}
    </div>
  );
}

/** The PR's review in sentence case, as a dot and a word. */
function prReviewWords(decision: string | null | undefined): {
  word: string;
  tone: "ok" | "warn" | "fail" | "idle";
} {
  const d = String(decision ?? "").toUpperCase();
  if (d === "APPROVED") return { word: "Approved", tone: "ok" };
  if (d === "CHANGES_REQUESTED") return { word: "Changes asked", tone: "fail" };
  if (d === "REVIEW_REQUIRED") return { word: "Review asked", tone: "warn" };
  return { word: "No review yet", tone: "idle" };
}

/** The files the agent changed, one fold; an unread worktree says so. */
export function FilesFold({ lane }: { lane: LaneWire }) {
  const worktree = lane.worktree;
  if (!worktree) return null;
  if (isNotRead(worktree)) return <NotReadLine part="FILES" reason={worktree.not_read} testId="lane-files-not-read" />;
  const files = worktree.files ?? [];
  if (!files.length) return null;
  return (
    <div className="aw-fold" data-testid="lane-files" data-feedback-redact="true">
      <FoldGadget title={filesWords(files.length)}>
        <ul className="aw-files">
          {files.map((f) => (
            <li key={f.path}>
              <code className="lw-file">{f.path}</code>
            </li>
          ))}
        </ul>
      </FoldGadget>
    </div>
  );
}

/** Each part of the lane the hub could not read: one quiet line each
 *  (UX-CANON A.10), never an empty list. */
export function UnreadLines({ lane }: { lane: LaneWire }) {
  const parts: Array<[string, unknown, string]> = [
    ["TIMELINE", lane.events, "lane-events-not-read"],
    ["ASKS", lane.wait, "lane-not-read-asks"],
    ["HELD", lane.gated, "lane-not-read-held"],
    ...unreadParts(lane).map(
      ([part, reason]) =>
        [part, { not_read: reason }, `lane-not-read-${part.toLowerCase()}`] as [string, unknown, string],
    ),
  ];
  const shown = parts.filter(([, value]) => isNotRead(value));
  if (!shown.length) return null;
  return (
    <div className="aw-unread">
      {shown.map(([part, value, testId]) => (
        <NotReadLine key={part} part={part} reason={(value as { not_read: string }).not_read} testId={testId} />
      ))}
    </div>
  );
}

/** The PR's check log (Details): each check, its state, its link. */
export function CheckLog({ lane }: { lane: LaneWire }) {
  const checks = lane.follow_through?.pr?.checks ?? [];
  if (!checks.length) return null;
  return (
    <ul className="aw-checks" data-testid="lane-checks">
      {checks.map((check, i) => (
        <li key={`${check.name}:${i}`}>
          <DotWord
            tone={
              /^(success|neutral|skipped)$/i.test(String(check.state))
                ? "ok"
                : /fail|error|cancel/i.test(String(check.state))
                  ? "fail"
                  : "warn"
            }
          >
            {String(check.name ?? "Check")}
          </DotWord>
          <span className="aw-check-state">{stateWords(String(check.state ?? ""))}</span>
        </li>
      ))}
    </ul>
  );
}

/** The lane title icon: the launch's OWN agent sprite at 32 (Codex keeps
 * its face; PHILO-14 A0c r2). */
export function laneTitleSprite(agent: string | null | undefined, key: string): string {
  return spriteUrl("agent", key, "rest", agent, 32);
}

/** A part of the lane that could not be read: `Files not read · <reason>`
 * (UX-CANON A.10), never an empty list; quiet sans in sentence case (W5-WORDS). */
export function NotReadLine({ part, reason, testId }: { part: string; reason: string; testId?: string }) {
  const word = part.charAt(0).toUpperCase() + part.slice(1).toLowerCase();
  return (
    <p className="lw-notread" role="status" data-testid={testId}>
      {`${word} not read · ${reason}`}
    </p>
  );
}

/** Betterment AG0/AG2: an answer or ARM the hub refused because the pane is
 * gone says so where the ARM was. */
export function TerminalGone() {
  const terminalGone = useLane((s) => s.terminalGone);
  return terminalGone ? (
    <span className="lw-fact" data-testid="lane-terminal-gone">
      {TERMINAL_GONE_WORDS}
    </span>
  ) : null;
}

/** The lane's receipts, kept when the well that made them closes or the
 * wait clears: the stop (from the launch), the last send or refusal. */
export function LaneReceipts({ lane }: { lane: LaneWire }) {
  const receipt = useLane((s) => s.receipt);
  const stopped = lane.launch.stopped;
  const answers = Array.isArray(lane.answers) ? lane.answers : [];
  // PHILO-15 15 (B47): an answer the desk typed is its own receipt, named
  // as the desk's (never the owner's SENT).
  const last = [...answers]
    .reverse()
    .find((a) => (a.outcome === "delivered" || a.outcome === "auto_answered") && a.text_head);
  const lastAt = last ? wireDate(last.ts)?.getTime() : undefined;
  // PHILO-15 15 (B47): an answer the desk typed is its own receipt.
  const word = last?.outcome === "auto_answered" ? "The desk answered" : "Sent";
  const shown = receipt ?? (last ? { word, at: lastAt, text: String(last.text_head), tone: "ok" as const } : null);
  const queuedList = Array.isArray(lane.launch.queued_rebriefs)
    ? lane.launch.queued_rebriefs.filter((q) => q?.text)
    : lane.launch.queued_rebrief?.text
      ? [lane.launch.queued_rebrief]
      : [];
  const queued = !stopped && queuedList.length ? queuedList : null;
  // Phase 16: what was typed into the agent (the brief, an answer) is drawn
  // by AgentWords, cut at a whole word; the other receipts are tokens.
  const sentWords = Boolean(shown && /^(SENT|Sent|The desk answered)$/.test(shown.word) && shown.text);
  return (
    <>
      {stopped ? (
        <ReceiptTokens testId="lane-stopped" word="Stopped by you" at={wireDate(stopped.at)?.getTime()} />
      ) : null}
      {queued
        ? queued.map((q, i) => (
            <div className="lw-queued" data-feedback-redact="true" key={String(q.id ?? i)}>
              <ReceiptTokens
                testId="lane-queued"
                tone="warn"
                word={i === 0 ? "Queued after this turn" : `Queued after ${i + 1} turns`}
                text={String(q.text)}
              />
              {q.id ? (
                <Button
                  dense
                  variant="ghost"
                  data-testid="lane-take-back"
                  aria-label={`Take back: ${String(q.text)}`}
                  onClick={() => void useLane.getState().takeBack(String(q.id), String(q.text ?? ""))}
                >
                  Take back
                </Button>
              ) : null}
            </div>
          ))
        : null}
      {shown && !(stopped && shown.word === "STOPPED") && !(queued && shown.word === "QUEUED") ? (
        <ReceiptTokens
          testId="lane-receipt"
          tone={shown.tone}
          word={shown.word}
          at={shown.at}
          text={sentWords ? "" : shown.text}
          words={sentWords ? (receipt ? shown.text : sentHead(shown.text)) : undefined}
        />
      ) : null}
    </>
  );
}

/** The hub keeps the first 120 characters of what was typed
 *  (`TEXT_HEAD_CHARS`, holdspeak/db/steering.py): a head that long was cut,
 *  maybe inside a word, so its last word goes and `…` says so (Phase 16:
 *  the owner saw `…line". P`). */
export const SENT_HEAD_CHARS = 120;
export function sentHead(text: string): string {
  const raw = String(text ?? "");
  if (raw.length < SENT_HEAD_CHARS) return raw;
  const flat = raw.replace(/\s+/g, " ").trim();
  const space = flat.lastIndexOf(" ");
  return space > 0 ? `${flat.slice(0, space).replace(/[\s·]+$/, "")} …` : cutAtWord(flat, flat.length);
}

/** One receipt (W4 AGENT 2, slice 2): a dot and a sentence-case word, the
 *  age quiet (`6 min ago`), then what was sent: one or two lines by
 *  AgentWords (compact), or the receipt's own fact. */
function ReceiptTokens({
  word,
  at,
  text,
  tone,
  testId,
  words,
}: {
  word: string;
  at?: number;
  text?: string;
  tone?: string;
  testId: string;
  words?: string;
}) {
  const dot = tone === "ok" || tone === "warn" || tone === "fail" ? tone : "idle";
  const when = at ? spokeWord(new Date(at)) : "";
  const head = (
    <>
      <DotWord tone={dot} className="lw-receipt-word">
        {sentenceCaps(word)}
      </DotWord>
      {when ? <span className="lw-receipt-age">{` · ${when}`}</span> : null}
      {text ? <span className="lw-receipt-fact">{` · ${sentenceCaps(text)}`}</span> : null}
    </>
  );
  if (!words?.trim()) {
    return (
      <p className="lw-receipt" data-feedback-redact="true" data-tone={tone} data-testid={testId}>
        {head}
      </p>
    );
  }
  return (
    <div className="lw-receipt lw-receipt-words" data-feedback-redact="true" data-tone={tone} data-testid={testId}>
      <span className="lw-receipt-head">
        {head}
        {" · "}
      </span>
      <AgentWords compact lines={2} ask={false} className="lw-receipt-text" text={words} />
    </div>
  );
}

/** The call the gate holds now (the newest held one the Control mode held). */
export function heldNow(lane: LaneWire): LaneGated | undefined {
  const gated = Array.isArray(lane.gated) ? lane.gated : [];
  return [...gated].reverse().find((g) => (g.state === "held" || g.state === "pending") && g.was_held !== false);
}

export function spokeWord(at: Date, now: number = Date.now()): string {
  const minutes = Math.floor((now - at.getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 24 * 60) return `${Math.floor(minutes / 60)} h ago`;
  return `on ${at.toLocaleDateString([], { month: "short", day: "numeric" })}`;
}

/** The gate's hold reason (`OUTSIDE THE WORKTREE · /tmp/x`) in his words:
 *  the reason in sentence case, the path or command word as code. */
export function reasonWords(reason: string): { word: string; target: string } {
  const [head, ...rest] = String(reason).split(" · ");
  return { word: sentenceCaps(head), target: rest.join(" · ") };
}

/** `HUB UNREACHABLE` → `Hub unreachable`; a token with any lower case letter
 *  (an agent's words, a path) stays as it is; `PR` keeps its caps. */
export function sentenceCaps(token: string): string {
  const text = String(token ?? "");
  if (!/[A-Z]/.test(text) || /[a-z]/.test(text)) return text;
  const lower = text.toLowerCase().replace(/\bpr\b/g, "PR");
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** Tell it (was Re-brief; Betterment AG1): the owner's new instruction to
 * the lane's own agent, in his own words. The hub types it now when the
 * agent is idle or asks; mid-turn it is QUEUED · AFTER THIS TURN
 * (PHILO-15 B46). */
export function RebriefWell() {
  const sending = useLane((s) => s.sending);
  const [text, setText] = useState("");
  const ready = text.trim().length > 0;
  const send = async () => {
    if (!ready) return;
    if (await useLane.getState().sendRebrief(text.trim())) useLane.getState().setRebrief(false);
  };
  return (
    <div data-testid="lane-rebrief-well" data-feedback-redact="true">
      <InspectorForm
        fit="rows"
        rows={[
          {
            label: "Tell it",
            control: (
              <StringGadget
                label="Tell it"
                value={text}
                onChange={setText}
                micLabel="Speak what to tell it"
                autoFocus
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.nativeEvent.isComposing) {
                    event.preventDefault();
                    void send();
                  }
                }}
              />
            ),
          },
        ]}
        completion={{
          cancel: () => useLane.getState().setRebrief(false),
          primary: {
            label: "Send",
            disabled: !ready || sending,
            busy: sending,
            run: () => void send(),
          },
        }}
      />
    </div>
  );
}

/* ── Raw ──────────────────────────────────────────────────────────── */

/** PHILO-15 20 (B63): the whole command of a held CUT call, read from the
 * hub (it keeps it for this read only, never for the agent), with Deny and
 * Approve. The Needs row and the lane rail say `CUT · APPROVE IN RAW`. */
interface FullCall {
  id: string;
  state: string;
  command: string;
  /** The text kept has the length the hook declared (Astra r1 on #1011). */
  whole: boolean;
  shown_chars?: number;
  declared_chars?: number;
  hold_reason?: string;
}

function RawHeldCall({ call }: { call: LaneGated }) {
  const [full, setFull] = useState<FullCall | null>(null);
  const [notRead, setNotRead] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let live = true;
    apiFetch<FullCall>(`/api/gate/proposals/${encodeURIComponent(call.id)}/command`)
      .then((data) => {
        if (!live) return;
        // A read with no command text is said, never drawn as a call.
        if (data && typeof data.command === "string") setFull(data);
        else setNotRead("NO COMMAND");
      })
      .catch((err: unknown) => {
        if (live) setNotRead(err instanceof Error ? err.message : String(err));
      });
    return () => {
      live = false;
    };
  }, [call.id]);
  const decide = async (decision: "approved" | "denied") => {
    setBusy(true);
    try {
      // The hub's answer is the receipt: what it decided, and when (a call
      // decided elsewhere first answers 409 with its standing state).
      const done = await apiFetch<{
        state?: string;
        decided_at?: number | null;
      }>(`/api/gate/proposals/${encodeURIComponent(call.id)}/decide`, {
        method: "POST",
        json: { decision },
      });
      const state = String(done?.state ?? decision);
      const at = done?.decided_at ? done.decided_at * 1000 : Date.now();
      useLane.getState().setReceipt({
        word: state === "approved" ? "APPROVED" : "DENIED",
        at,
        text: "",
        tone: state === "approved" ? "ok" : "warn",
      });
    } catch (err: unknown) {
      const standing =
        err instanceof ApiError ? String((err.payload as { state?: string } | undefined)?.state ?? "") : "";
      useLane.getState().setReceipt({
        word: "NOT DECIDED",
        at: Date.now(),
        text: standing ? `Already ${standing.replace(/_/g, " ")}` : "Hub unreachable",
        tone: "fail",
      });
    } finally {
      setBusy(false);
      void useGate.getState().refresh();
      void useLane.getState().load();
    }
  };
  const reason = full?.hold_reason || call.hold_reason || "";
  // A part of the call is never approved: it says how much is there.
  const part =
    full && !full.whole
      ? `CUT · ${full.shown_chars ?? full.command.length} OF ${full.declared_chars ?? "?"} CHARS`
      : "";
  const caption = stateWords(["HELD", reason, part].filter(Boolean).join(" · "));
  return (
    <section aria-label="Held call" data-testid="lane-raw-held" data-feedback-redact="true">
      <InspectorBody>
        <p className="lw-caption">{caption}</p>
        {notRead ? (
          <p className="lw-notread" role="status">{`Call not read · ${notRead}`}</p>
        ) : full ? (
          <SurfaceCode>
            <span data-testid="lane-raw-command">{full.command}</span>
          </SurfaceCode>
        ) : (
          <p className="lw-notread">Reading the call</p>
        )}
        <PaneActions>
          <Button
            dense
            variant="ghost"
            disabled={busy}
            onClick={() => void decide("denied")}
            data-testid="lane-raw-deny"
          >
            Deny
          </Button>
          {full?.whole ? (
            <Button
              dense
              variant="primary"
              disabled={busy}
              onClick={() => void decide("approved")}
              data-testid="lane-raw-approve"
            >
              Allow
            </Button>
          ) : null}
        </PaneActions>
      </InspectorBody>
    </section>
  );
}

export function RawPane() {
  const lane = useLane((s) => s.lane);
  const launchId = useLane((s) => s.launchId);
  const gated = lane && Array.isArray(lane.gated) ? lane.gated : [];
  const cut = gated.filter((g) => g.args_cut && (g.state === "held" || g.state === "pending"));
  const paneStatus = useSteering((s) => s.paneStatus);
  const paneDetail = useSteering((s) => s.paneDetail);
  const paneId = useSteering((s) => s.paneId);
  const paneLines = useSteering((s) => s.paneLines);
  const paneRaw = useSteering((s) => s.paneRaw);
  const paneGeom = useSteering((s) => s.paneGeom);
  const paneChangedAt = useSteering((s) => s.paneChangedAt);
  const armed = useSteering((s) => s.armed);
  const postureAuthorized = useSteering((s) => s.postureAuthorized);
  // Betterment AG10: Terminal opens at the bottom: the prompt line, the
  // newest output (the well itself follows the tail).
  const rawRef = useRef<HTMLDivElement>(null);
  const live = paneStatus === "live";
  useEffect(() => {
    if (live) rawRef.current?.querySelector(".terminal-well")?.scrollIntoView?.({ block: "end" });
  }, [live]);
  return (
    <div data-feedback-redact="true" data-testid="lane-raw-pane" ref={rawRef}>
      <InspectorBody>
        {/* Betterment AG7: the hook or the screen rule behind the state. */}
        {launchId ? <WhyThisState launchId={launchId} /> : null}
        {cut.map((call) => (
          <RawHeldCall key={call.id} call={call} />
        ))}
        <PaneWell
          live={paneStatus === "live"}
          lines={paneLines}
          raw={paneRaw}
          pane={paneGeom}
          changedAt={paneChangedAt}
          absence={
            <>
              <span>Terminal unavailable · {PANE_STATE_LABEL[paneStatus] || paneStatus}</span>
              {paneDetail ? <span className="lw-pane-detail">{paneDetail}</span> : null}
            </>
          }
        />
        {/* PHILO-17 THE REFIT: the pane's controls fold until asked for. */}
        {paneStatus !== "live" ? (
          <PaneActions>
            <Button dense variant="ghost" onClick={() => void useSteering.getState().poll()}>
              Retry
            </Button>
            <Button dense variant="ghost" onClick={() => useLane.getState().setRaw(false)}>
              Back to the agent
            </Button>
          </PaneActions>
        ) : null}
        {paneStatus === "live" && paneId ? (
          <FoldGadget title="Keys" className="lw-keys">
            <ArmStrip />
            {armed || postureAuthorized ? <KeyPalette /> : null}
          </FoldGadget>
        ) : null}
      </InspectorBody>
    </div>
  );
}
