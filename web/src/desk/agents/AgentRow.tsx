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
import { ProgramLink } from "../programs/ProgramLink";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { useDurableDraft } from "../../lib/durableDraft";
import { PreferenceWell, DotWord, SurfaceState, SurfaceCode, InspectorBody, InspectorForm, InspectorFacts, PaneActions } from "../surface";
import { StringGadget } from "../surface/gadgets";
import { AgentWords } from "../components/AgentWords";
import { useGate } from "../gate";
import { gatedHead, type LaneGated, type LaneWait } from "../lane/laneWire";
import { AGENT_NAME, type AgentId } from "../firstrun/agentsStep";
import { reviewWords, type ConductorMember } from "../conductor/members";
import { ReviewResult } from "../conductor/ReviewResult";
import { stateWords } from "../surface/words";
import { useConductor } from "../conductor/store";
import { questionChoices, type AgentChoice } from "./choices";
import { reviewResult, type DeskAnswer, type DeskAnswerSource } from "../agentFlights";
// The row is drawn in Agents and in Needs you (Betterment AG9): its style travels with it.

/** Betterment AG3: where the line the desk used comes from, in his words. */
const SOURCE_WORD: Record<string, string> = {
  decision: "your decision",
  memory: "your memory",
  meeting: "the meeting",
  note: "the note",
  brief: "the brief",
};

/** What the desk typed, without its voice and its quote: `The desk: Yes,
 *  "…"` -> `Yes`; a choice is its number. */
export function deskSaid(text: string): string {
  const bare = text.replace(/^\s*the desk:\s*/i, "");
  const head = bare
    .replace(/"[^"]*"|\u201c[^\u201d]*\u201d|`[^`]*`/g, " ")
    .replace(/[\s,.:;]+$/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return head || bare.trim();
}

/** `The desk answered: 1, from your decision 'The rollback flag moves into
 *  config/flags.yaml.'` */
export function deskAnswerWords(answer: { text: string; source: DeskAnswerSource | null }): string {
  const said = deskSaid(answer.text);
  const source = answer.source;
  if (!source?.text) return `The desk answered: ${said}`;
  return `The desk answered: ${said}, from ${SOURCE_WORD[source.kind] ?? SOURCE_WORD.brief} '${source.text}'`;
}

/** The desk's answer on a row: the words, and New until he opens the agent. */
export function DeskAnswerLine({ answer }: { answer: DeskAnswer | null | undefined }) {
  if (answer?.state !== "answered") return null;
  return (
    <span
      data-feedback-redact="true"
      className="cw-desk-answer"
      data-testid="agent-row-desk-answer"
      data-new={answer.isNew ? "" : undefined}
    >
      <span className="cw-desk-answer-text">{deskAnswerWords(answer)}</span>
      {answer.isNew ? (
        <span className="kit-pill" data-tone="ok" data-testid="agent-row-desk-answer-new">
          New
        </span>
      ) : null}
    </span>
  );
}

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
      const lane = await apiFetch<{
        gated?: LaneGated[] | unknown;
        wait?: LaneWait | unknown;
      } | null>(`/api/agent/launches/${encodeURIComponent(launchId)}/lane?after=0&limit=1`);
      const gated = Array.isArray(lane?.gated) ? (lane!.gated as LaneGated[]) : [];
      const held = [...gated]
        .reverse()
        .find((g) => (g.state === "held" || g.state === "pending") && g.was_held !== false);
      const laneWait =
        lane?.wait && typeof lane.wait === "object" && "kind" in (lane.wait as object) ? (lane.wait as LaneWait) : null;
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

/* Betterment AG7: the row's own read of the pane (usePaneTail) and its
 * parse are parked in desk/_parked/agents/paneParse.ts: the hub's screen
 * rules read the command and the choices (member.screen). */

/** `Asked just now` (under a minute), `Asked 6 min ago`; `Asks` with no
 *  age. Betterment AG8: "1 min ago" ten seconds after the ask was a lie. */
export function askedWord(when: string | undefined, whenSort?: number, now: number = Date.now()): string {
  if (!when) return "Asks";
  if (whenSort != null && now - whenSort < 60_000) return "Asked just now";
  if (/^\d+ (MIN|H)$/.test(when)) return `Asked ${when.toLowerCase()} ago`;
  return `Asked ${when.charAt(0)}${when.slice(1).toLowerCase()}`;
}

/** A refusal in his words. */
function refusalWords(error: unknown): string {
  const status =
    error instanceof ApiError ? String((error.payload as Record<string, unknown> | null)?.status ?? "") : "";
  if (status === "wait_not_current") return "The question changed · Nothing was sent";
  if (status === "pane_gone" || status === "pane_mismatch" || status === "target_gone")
    return "This agent's terminal is gone · Nothing was sent";
  if (status === "tmux_absent") return "The terminal is not running · Nothing was sent";
  const said = readableError(error);
  // The hub's custody words ("a current registered session and pane
  // identity are required") in his words.
  if (/pane identity|registered session/i.test(said))
    return "The desk cannot reach this agent's terminal · Nothing was sent";
  return `Not sent · ${said}`;
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
  /** The plate under the agent's mast (the Agents window): the mast says
   *  the sprite and the title, so the plate draws neither. */
  bare?: boolean;
  answerAction?: { current: (() => void) | null };
  toolbarOwnsVerbs?: boolean;
  focusQuestion?: boolean;
}

export function AgentRow({
  member,
  question,
  waitId,
  lead,
  selected,
  onSelect,
  onTerminal,
  onOpenAnswer,
  onOpen,
  bare = false,
  answerAction,
  toolbarOwnsVerbs = false,
  focusQuestion = true,
}: AgentRowProps) {
  const { call, wait, error: callError, reread } = useHeldCall(member);

  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [decidedId, setDecidedId] = useState<string | null>(null);
  const [failure, setFailure] = useState<{
    label: string;
    retry?(): void;
  } | null>(null);
  const [sent, setSent] = useState<string | null>(null);
  /** Betterment AG3: he chose to answer while the desk drafts. */
  const [mine, setMine] = useState(false);

  const held =
    Boolean(call) ||
    (member.answerBinding
      ? member.answerBinding.wait_kind === "approve"
      : member.live === "held" || wait?.kind === "TO APPROVE");
  const reviewNeedsYou = member.live === "needs_you";
  // A durable pair result belongs to the ordinary flight row as well as the
  // lane.  An active round has no pair result and therefore stays in its
  // existing review row without a premature MUST verdict.
  const hasReviewResult = Boolean(reviewResult(member.review));
  const currentWait = String(member.answerBinding?.wait_id ?? wait?.wait_id ?? waitId ?? "");
  // Betterment AG7: an agent with no hook asks in its last words on screen.
  const shownQuestion = member.answerBinding
    ? member.answerQuestion || ""
    : String(wait?.question || question || (member.screen?.state === "asks" ? member.screen.said : "") || "");
  const answerScope = `agent-answer:${member.id}:${member.answerBinding?.wait_revision || currentWait || member.screen?.since || shownQuestion}`;
  const { value: text, setDraft: setText } = useDurableDraft(answerScope);
  const scopeNow = useRef(answerScope);
  scopeNow.current = answerScope;
  useEffect(() => {
    setFailure(null);
    setSent(null);
    setMine(false);
    setDecidedId(null);
  }, [answerScope]);
  // Betterment AG7: the gate's held call first, else what the hub's screen
  // rules read on the agent's pane (the command, its own numbered menu).
  const screenRead = member.screen ?? null;
  const command = call
    ? gatedHead(call)
    : held
      ? ((member.answerBinding ? member.answerCommand?.text : screenRead?.command) ?? null)
      : null;
  const holdReason = call?.hold_reason ? {word: stateWords(call.hold_reason.split(" · ")[0]), target: call.hold_reason.split(" · ").slice(1).join(" · ")} : null;
  const choices: AgentChoice[] = held ? [] : questionChoices(shownQuestion);
  const menu: AgentChoice[] = held || choices.length ? [] : (screenRead?.choices ?? []);
  const draft = wait?.draft?.text?.trim() || "";
  // Betterment AG3: the line the draft used, in his words; else why.
  const used = wait?.draft?.source;
  const draftSource = used?.text
    ? `from ${SOURCE_WORD[used.kind ?? ""] ?? SOURCE_WORD.brief} '${used.text}'`
    : wait?.draft?.reason?.trim() || "";
  // Betterment AG3: the desk holds the question while it drafts (YOLO).
  const drafting = !held && !mine && member.deskAnswer?.state === "drafting";
  const agentName = AGENT_NAME[member.agent as AgentId] ?? member.agent;
  const key = member.sessionKey;
  // An agent whose hooks are off: its row answers its screen prompt.
  const screenOnly =
    !key &&
    Boolean(
      (member.launchId || member.ownAgent) &&
      member.screen?.since &&
      (member.screen.state === "approve" || member.screen.state === "asks"),
    );

  const after = async (word: string) => {
    setSent(word);
    await reread();
    void useConductor.getState().readFlights();
  };

  const press = async (path: "steer" | "keys", body: Record<string, unknown>, word: string) => {
    if ((!key && !screenOnly) || pending.current) return;
    const pressedScope = answerScope;
    pending.current = true;
    setBusy(true);
    setFailure(null);
    try {
      if (key) {
        await apiFetch(`/api/coders/${encodeURIComponent(key)}/${path}`, {
          method: "POST",
          json: {
            ...body,
            kind: "answer",
            wait_id: currentWait,
            ...member.answerBinding,
          },
        });
      } else if (member.ownAgent) {
        const keys = Array.isArray(body.keys)
          ? (body.keys as Array<string | { literal: string }>).map((k) => (typeof k === "string" ? k : k.literal))
          : undefined;
        await apiFetch("/api/coders/own-agents/answer", {
          method: "POST",
          json: {
            pane_id: member.ownAgent.paneId,
            since: member.screen?.since,
            ...(keys ? { keys } : { text: body.text }),
          },
        });
      } else {
        // An agent with no hook: his press goes to its screen prompt, named
        // by when that prompt began (the hub reads the pane again first).
        const keys = Array.isArray(body.keys)
          ? (body.keys as Array<string | { literal: string }>).map((k) => (typeof k === "string" ? k : k.literal))
          : undefined;
        await apiFetch(`/api/agent/launches/${encodeURIComponent(String(member.launchId))}/answer`, {
          method: "POST",
          json: {
            since: member.screen?.since,
            ...(keys ? { keys } : { text: body.text }),
          },
        });
      }
      if (scopeNow.current !== pressedScope) return;
      await after(word);
      if (path === "steer" && scopeNow.current === pressedScope) setText("");
    } catch (error) {
      if (scopeNow.current !== pressedScope) return;
      setFailure({
        label: refusalWords(error),
        retry: () => void press(path, body, word),
      });
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
      setFailure(
        gateError
          ? {
              label: `Gate read failed · Decisions unchanged · Retry · ${gateError}`,
              retry: () => void recoverRead(),
            }
          : null,
      );
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
        if (gateError)
          setFailure({
            label: `Decision saved · Gate read failed · Retry · ${gateError}`,
            retry: () => void recoverRead(),
          });
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
    void press(
      "keys",
      { keys: [decision === "approved" ? "Enter" : "Escape"] },
      decision === "approved" ? "Allowed" : "Denied",
    );
  };

  const denySeat = useRef<HTMLButtonElement>(null);
  useEffect(() => { if (!held || !focusQuestion) return; const frame = requestAnimationFrame(() => denySeat.current?.focus()); return () => cancelAnimationFrame(frame); }, [held, call?.id, currentWait, focusQuestion]);
  const decided = Boolean(call && call.id === decidedId);
  const canKeys = Boolean(key && currentWait) || screenOnly;
  const ownPane = Boolean(member.ownAgent);

  useEffect(() => {
    if (!answerAction) return;
    answerAction.current = () => {
      if (canKeys) {
        if (text.trim()) answer(text.trim());
      } else onOpenAnswer();
    };
    return () => {
      answerAction.current = null;
    };
  });

  const input = (
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
  );

  return (
    <article
      className="surface-inspector-body"
      data-object-id={member.id}
      data-selected={selected ? "" : undefined}
      data-testid="conductor-ask-row"
      data-feedback-redact="true"
      aria-label={`${agentName} ${reviewNeedsYou ? "needs you" : held ? "wants to run" : "asks"}`}
    >
      <InspectorBody>
        {!bare ? (
          <PaneActions>
            <Button dense onClick={onSelect}>
              {String(member.facts.from || member.name)}
            </Button>
            <ProgramLink program={member.program} />
          </PaneActions>
        ) : null}
        <PaneActions><span data-testid="agent-question-label">{held ? "Wants to run" : "It asks"}</span></PaneActions>
        <PreferenceWell fit="reading">
          {command ? <div data-testid="conductor-held-call"><SurfaceCode><span data-testid="agent-row-command">{command}</span></SurfaceCode></div> : shownQuestion ? <AgentWords text={shownQuestion} data-testid="agent-row-question" /> : null}
        </PreferenceWell>
        {holdReason ? <span>{holdReason.word}{holdReason.target ? ` · ${holdReason.target}` : ""}</span> : null}
        {held ? <span>The agent runs this command one time.</span> : null}
        {hasReviewResult ? <ReviewResult review={member.review} /> : null}
        {failure ? (
          <PaneActions>
            <span role="alert" data-testid="agent-row-refusal">
              <DotWord tone="fail">{failure.label}</DotWord>
            </span>
            {busy || !failure.retry ? null : (
              <Button dense onClick={failure.retry}>
                Try again
              </Button>
            )}
          </PaneActions>
        ) : null}
        {!failure && callError ? (
          <SurfaceState error={callError} onRetry={busy ? undefined : () => void reread()} />
        ) : null}
        {sent && !failure ? (
          <span role="status" data-testid="agent-row-receipt">
            Sent · {sent}
          </span>
        ) : null}
        {!drafting ? <DeskAnswerLine answer={member.deskAnswer} /> : null}
        {drafting ? (
          <PaneActions>
            <span role="status" data-testid="agent-row-drafting">
              The desk is drafting an answer
            </span>
            <Button dense onClick={() => setMine(true)} data-testid="agent-row-answer-myself">
              Answer it myself
            </Button>
          </PaneActions>
        ) : reviewNeedsYou || hasReviewResult ? (
          <PaneActions>
            <Button dense onClick={onOpen} data-testid="conductor-open-review">
              Open
            </Button>
          </PaneActions>
        ) : held ? (
          decided ? null : (
            <PaneActions>
              {call?.args_cut || (!call && !canKeys) ? (
                ownPane ? null : (
                  <Button dense onClick={onTerminal} data-testid="agent-row-terminal">
                    Terminal
                  </Button>
                )
              ) : (
                <>
                  <Button dense ref={denySeat} disabled={busy || (!call && !canKeys)} onClick={() => void decide("denied")} data-testid="conductor-deny">Deny</Button>
                  <Button dense variant="secondary" loading={busy} disabled={!call && (!canKeys || !(member.answerBinding ? member.answerCommand?.complete : screenRead?.commandComplete))} onClick={() => void decide("approved")} data-testid="conductor-approve">Allow</Button>
                  {ownPane || toolbarOwnsVerbs ? null : (
                    <Button dense onClick={onTerminal} data-testid="agent-row-terminal">
                      Terminal
                    </Button>
                  )}
                </>
              )}
            </PaneActions>
          )
        ) : (
          <>
            {choices.length || menu.length ? (
              <PaneActions>
                <span data-testid="agent-row-choices">
                  <PaneActions>
                    {(choices.length ? choices : menu).map((choice) => (
                      <Button
                        key={choice.n}
                        dense
                        disabled={busy || !canKeys}
                        onClick={() => choose(choice, !choices.length)}
                        data-testid="agent-row-choice"
                      >{`${choice.n} · ${choice.label}`}</Button>
                    ))}
                  </PaneActions>
                </span>
              </PaneActions>
            ) : null}
            {canKeys ? <InspectorForm fit="rows" rows={[{ label: "Your answer", control: input }]} /> : null}
            <PaneActions>
              <Button
                dense
                variant="brass"
                loading={busy}
                disabled={canKeys ? !text.trim() : false}
                onClick={() => (canKeys ? answer(text.trim()) : onOpenAnswer())}
                data-testid="conductor-answer"
              >
                Answer
              </Button>
              {ownPane || toolbarOwnsVerbs ? null : (
                <Button dense onClick={onTerminal} data-testid="conductor-open">
                  Open terminal
                </Button>
              )}
            </PaneActions>
            {draft ? (
              <InspectorFacts
                header={false}
                name="Draft"
                rows={[
                  {
                    label: "Draft",
                    value: (
                      <span data-testid="agent-row-draft">
                        {draft}
                        {draftSource ? ` · ${draftSource}` : ""}
                      </span>
                    ),
                  },
                ]}
                trailing={undefined}
              />
            ) : null}
            {draft ? (
              <PaneActions>
                <Button dense disabled={busy} onClick={() => setText(draft)}>
                  Use draft
                </Button>
              </PaneActions>
            ) : null}
          </>
        )}
      </InspectorBody>
    </article>
  );
}
