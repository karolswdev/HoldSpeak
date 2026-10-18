/** Betterment AG2: one row for an agent that needs him (agents/DESIGN.md §4,
 *  "The Agents window"). The row is the whole job: he answers or allows from
 *  it in ONE press, and sees the command before he allows it.
 *
 *  - Asks you: the question in full, the choice buttons (`1 · config`), the
 *    answer box with the mic and Answer, the desk's draft with its source.
 *  - Wants to run: the command (the gate's held call, else the lines above
 *    "Do you want to proceed?" on the agent's screen), Allow and Deny.
 *
 *  Answer, a choice, Allow and Deny post `kind: "answer"` with the current
 *  `wait_id`: the press is the authority for that one wait, so there is no
 *  ARM step (the hub checks the pane and the wait again before it types).
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { ActionNotice, SurfaceState } from "../surface";
import { StringGadget } from "../surface/gadgets";
import { AgentWords } from "../components/AgentWords";
import { useGate } from "../gate";
import { gatedHead, type LaneGated, type LaneWait } from "../lane/laneWire";
import { AGENT_NAME, type AgentId } from "../firstrun/agentsStep";
import type { ConductorMember } from "../conductor/members";
import { useConductor } from "../conductor/store";
import { questionChoices, menuChoices, wantsToRun, type AgentChoice } from "./choices";

/** What the lane read says of this agent now: the gate's held call and the
 *  wait (its id and the desk's draft). Read from the launch's lane (its gated
 *  calls are not paged); a call the hub cannot show whole is never allowed
 *  here (PHILO-14 A5). */
export function useHeldCall(member: ConductorMember): {
  call: LaneGated | null;
  wait: LaneWait | null;
  error: string | null;
  reread(): Promise<void>;
} {
  const [call, setCall] = useState<LaneGated | null>(null);
  const [wait, setWait] = useState<LaneWait | null>(null);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);
  const launchId = member.launchId;
  const reread = useCallback(async () => {
    const read = ++generation.current;
    if (!launchId) return;
    try {
      const lane = await apiFetch<{ gated?: LaneGated[] | unknown; wait?: LaneWait | unknown } | null>(
        `/api/agent/launches/${encodeURIComponent(launchId)}/lane?after=0&limit=1`,
      );
      const gated = Array.isArray(lane?.gated) ? (lane!.gated as LaneGated[]) : [];
      const held = [...gated].reverse().find((g) => (g.state === "held" || g.state === "pending") && g.was_held !== false);
      const laneWait = lane?.wait && typeof lane.wait === "object" && "kind" in (lane.wait as object) ? (lane.wait as LaneWait) : null;
      if (read === generation.current) {
        setCall(held ?? null);
        setWait(laneWait);
        setError(null);
      }
    } catch (cause) {
      if (read === generation.current) setError(`Call read failed · Calls unchanged · Retry · ${readableError(cause)}`);
    }
  }, [launchId]);
  useEffect(() => {
    void reread();
    return () => {
      generation.current++;
    };
  }, [reread, member.live, member.when]);
  return { call, wait, error, reread };
}

/** The bottom of the agent's screen (read only; watching is free). An
 *  unread screen is no menu and no command: the row still answers. */
export function usePaneTail(sessionKey: string | null | undefined, when: unknown): string[] {
  const [lines, setLines] = useState<string[]>([]);
  useEffect(() => {
    let live = true;
    if (!sessionKey) return;
    void apiFetch<{ peek?: { status?: string; lines?: string[] } }>(
      `/api/coders/${encodeURIComponent(sessionKey)}/peek?lines=40`,
    )
      .then((answer) => {
        if (live && answer?.peek?.status === "live" && Array.isArray(answer.peek.lines)) setLines(answer.peek.lines);
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [sessionKey, when]);
  return lines;
}

/** `Asked 6 min ago`; `Asks` with no age. */
function askedWord(when: string | undefined): string {
  if (!when) return "Asks";
  if (/^\d+ (MIN|H)$/.test(when)) return `Asked ${when.toLowerCase()} ago`;
  return `Asked ${when.charAt(0)}${when.slice(1).toLowerCase()}`;
}

/** A refusal in his words. */
function refusalWords(error: unknown): string {
  const status = error instanceof ApiError ? String((error.payload as Record<string, unknown> | null)?.status ?? "") : "";
  if (status === "wait_not_current") return "The question changed · Nothing was sent";
  if (status === "pane_gone" || status === "pane_mismatch" || status === "target_gone") return "This agent's terminal is gone · Nothing was sent";
  if (status === "tmux_absent") return "The terminal is not running · Nothing was sent";
  return `Not sent · ${readableError(error)}`;
}

export interface AgentRowProps {
  member: ConductorMember;
  /** The question the session holds (the hook's last words). */
  question: string;
  /** The session's wait id, from the session list (the lane read wins). */
  waitId?: string | null;
  /** The one filled primary of the window. */
  lead: boolean;
  selected: boolean;
  onSelect(): void;
  /** Open the agent's window on its Terminal. */
  onTerminal(): void;
  /** No wait id known (an older hub): Answer opens the agent's ask well. */
  onOpenAnswer(): void;
  /** Open the agent's window (its Story). */
  onOpen(): void;
}

export function AgentRow({ member, question, waitId, lead, selected, onSelect, onTerminal, onOpenAnswer, onOpen }: AgentRowProps) {
  const { call, wait, error: callError, reread } = useHeldCall(member);
  const tail = usePaneTail(member.sessionKey, member.when);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [decidedId, setDecidedId] = useState<string | null>(null);
  const [failure, setFailure] = useState<{ label: string; retry?(): void } | null>(null);
  const [sent, setSent] = useState<string | null>(null);

  const held = member.live === "held" || Boolean(call) || wait?.kind === "TO APPROVE";
  const currentWait = String(wait?.wait_id ?? waitId ?? "");
  const shownQuestion = String(wait?.question || question || "");
  const command = call ? gatedHead(call) : held ? wantsToRun(tail) : null;
  const choices: AgentChoice[] = held ? [] : questionChoices(shownQuestion);
  const menu: AgentChoice[] = held || choices.length ? [] : menuChoices(tail);
  const draft = wait?.draft?.text?.trim() || "";
  const draftSource = wait?.draft?.reason?.trim() || "";
  const agentName = AGENT_NAME[member.agent as AgentId] ?? member.agent;
  const key = member.sessionKey;

  const after = async (word: string) => {
    setSent(word);
    await reread();
    void useConductor.getState().readFlights();
  };

  const press = async (path: "steer" | "keys", body: Record<string, unknown>, word: string) => {
    if (!key || pending.current) return;
    pending.current = true;
    setBusy(true);
    setFailure(null);
    try {
      await apiFetch(`/api/coders/${encodeURIComponent(key)}/${path}`, {
        method: "POST",
        json: { ...body, kind: "answer", wait_id: currentWait },
      });
      await after(word);
      if (path === "steer") setText("");
    } catch (error) {
      setFailure({ label: refusalWords(error), retry: () => void press(path, body, word) });
      void useConductor.getState().readFlights();
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };

  const answer = (value: string, word = value) => void press("steer", { text: value, submit: true }, word);
  const choose = (choice: AgentChoice, fromMenu: boolean) =>
    fromMenu
      ? void press("keys", { keys: [{ literal: choice.n }] }, `${choice.n} · ${choice.label}`)
      : answer(choice.n, `${choice.n} · ${choice.label}`);

  /** After a decision the gate could not read back: read the gate and the
   *  lane again; the decision itself is never sent twice. */
  const recoverRead = async () => {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    try {
      await useGate.getState().refresh();
      await reread();
      const gateError = useGate.getState().error;
      setFailure(gateError ? { label: `Gate read failed · Decisions unchanged · Retry · ${gateError}`, retry: () => void recoverRead() } : null);
    } finally {
      pending.current = false;
      setBusy(false);
      void useConductor.getState().readFlights();
    }
  };

  const decide = async (decision: "approved" | "denied") => {
    if (call && !call.args_cut) {
      const id = call.id;
      if (pending.current || decidedId === id) return;
      pending.current = true;
      setBusy(true);
      setFailure(null);
      try {
        await useGate.getState().decide(id, decision);
        setDecidedId(id);
        const gateError = useGate.getState().error;
        if (gateError) setFailure({ label: `Decision saved · Gate read failed · Retry · ${gateError}`, retry: () => void recoverRead() });
        setSent(decision === "approved" ? "Allowed" : "Denied");
      } catch (error) {
        setFailure({
          label: `${decision === "approved" ? "Allow" : "Deny"} failed · ${readableError(error)}`,
          retry: () => void decide(decision),
        });
      } finally {
        await reread();
        pending.current = false;
        setBusy(false);
        void useConductor.getState().readFlights();
      }
      return;
    }
    // A permission prompt on the agent's own screen: its "yes" key is Enter
    // on the selected Yes, its "no" key is Escape.
    void press("keys", { keys: [decision === "approved" ? "Enter" : "Escape"] }, decision === "approved" ? "Allowed" : "Denied");
  };

  const decided = Boolean(call && call.id === decidedId);
  const canKeys = Boolean(key && currentWait);

  return (
    <article
      className="cw-ask"
      data-object-id={member.id}
      data-selected={selected ? "" : undefined}
      data-testid="conductor-ask-row"
      aria-label={`${agentName} ${held ? "wants to run" : "asks"}`}
    >
      <header className="cw-ask-bar">
        <span className="cw-ask-label">{held ? "Wants to run" : "Asks you"}</span>
        <span className="cw-ask-age">{askedWord(member.when)}</span>
      </header>
      <div className="cw-ask-body">
        <span className="cw-plate-sprite" aria-hidden="true">
          <img src={member.sprite} alt="" draggable={false} />
        </span>
        <div className="cw-ask-text">
          <Button variant="chrome" className="cw-row-title" aria-pressed={selected} onClick={onSelect}>
            {member.role === "ready" ? member.name : String(member.facts.from || member.name)}
          </Button>
          <span className="cw-row-meta">
            <span>{agentName}</span>
            {member.facts.where ? <span className="kit-pill" data-tone="info">{String(member.facts.where)}</span> : null}
          </span>
          {held ? (
            <>
              {command ? (
                <code className="cw-ask-call" data-testid="conductor-held-call">
                  {call?.hold_reason ? <span className="cw-ask-why">{call.hold_reason}</span> : null}
                  <span data-testid="agent-row-command">{command}</span>
                </code>
              ) : shownQuestion ? (
                <AgentWords className="cw-ask-q" text={shownQuestion} />
              ) : null}
            </>
          ) : shownQuestion ? (
            <AgentWords className="cw-ask-q" text={shownQuestion} data-testid="agent-row-question" />
          ) : null}
        </div>
      </div>
      {failure ? (
        <ActionNotice tone="danger" role="alert" action={busy || !failure.retry ? undefined : { label: "Retry", onClick: failure.retry }}>
          {failure.label}
        </ActionNotice>
      ) : null}
      {!failure && callError ? <SurfaceState error={callError} onRetry={busy ? undefined : () => void reread()} /> : null}
      {sent && !failure ? (
        <span className="cw-ask-sent" role="status" data-testid="agent-row-receipt">{`Sent · ${sent}`}</span>
      ) : null}
      {held ? (
        decided ? null : (
          <div className="cw-ask-verbs cw-ask-verbs--wide">
            {call?.args_cut ? (
              <Button dense variant={lead ? "primary" : "secondary"} onClick={onTerminal} data-testid="agent-row-terminal">
                Terminal
              </Button>
            ) : (
              <>
                <Button
                  dense
                  variant={lead ? "primary" : "secondary"}
                  loading={busy}
                  disabled={!call && !canKeys}
                  onClick={() => void decide("approved")}
                  data-testid="conductor-approve"
                >
                  Allow
                </Button>
                <Button dense variant="secondary" disabled={busy || (!call && !canKeys)} onClick={() => void decide("denied")} data-testid="conductor-deny">
                  Deny
                </Button>
                <Button dense variant="ghost" onClick={onTerminal} data-testid="agent-row-terminal">
                  Terminal
                </Button>
              </>
            )}
          </div>
        )
      ) : (
        <>
          {choices.length || menu.length ? (
            <div className="cw-choices" data-testid="agent-row-choices">
              {(choices.length ? choices : menu).map((choice) => (
                <Button
                  key={choice.n}
                  dense
                  variant="secondary"
                  disabled={busy || !canKeys}
                  onClick={() => choose(choice, !choices.length)}
                  data-testid="agent-row-choice"
                >
                  {`${choice.n} · ${choice.label}`}
                </Button>
              ))}
            </div>
          ) : null}
          {canKeys ? <div className="cw-answer">
            <StringGadget
              label={`Answer ${agentName}`}
              value={text}
              onChange={setText}
              placeholder="Say or type the answer"
              micLabel="Speak the answer"
              disabled={busy || !canKeys}
              inputProps={{ "data-testid": "agent-row-answer-field" } as Record<string, string>}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.nativeEvent.isComposing && text.trim()) {
                  event.preventDefault();
                  answer(text.trim());
                }
              }}
            />
            <Button
              dense
              variant={lead ? "primary" : "secondary"}
              loading={busy}
              disabled={!text.trim() || !canKeys}
              onClick={() => answer(text.trim())}
              data-testid="conductor-answer"
            >
              Answer
            </Button>
            <Button dense variant="ghost" onClick={onOpen} data-testid="conductor-open">
              Open
            </Button>
          </div> : (
            <div className="cw-ask-verbs">
              <Button dense variant={lead ? "primary" : "secondary"} onClick={onOpenAnswer} data-testid="conductor-answer">
                Answer
              </Button>
              <Button dense variant="ghost" onClick={onOpen} data-testid="conductor-open">
                Open
              </Button>
            </div>
          )}
          {draft ? (
            <div className="cw-draft" data-testid="agent-row-draft">
              <span className="cw-draft-text">
                {`Draft: ${draft}`}
                {draftSource ? <span className="cw-draft-source">{` · ${draftSource}`}</span> : null}
              </span>
              <Button dense variant="ghost" disabled={busy} onClick={() => setText(draft)}>
                Use draft
              </Button>
            </div>
          ) : null}
        </>
      )}
    </article>
  );
}
