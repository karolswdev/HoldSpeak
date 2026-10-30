/** PHILO-14 C3 — the YOLO hand in one line (board A-3, A-3 at 393).
 *
 *  `<item> → <agent>  Write the cutover comms · [CLAUDE CODE ⇄] · OPEN THROTTLE ·
 *  hs/write-the-cutover-comms  [Brief ▸] [Cancel] [Hand]`. The agent is a
 *  token the owner flips (PHILO-15 16, B39: CLAUDE CODE ⇄ CODEX). The fact line is
 *  the hub's preview (`POST /api/agent/hand/preview`, no side effect); Brief ▸
 *  unfolds the same brief text the launch sheet shows, read only; Hand calls
 *  `POST /api/agent/hand` and the line then reads the receipt the sheet reads
 *  (`Launched · Brief sent`, pending, or not sent with Send again).
 *
 *  Nothing leaves the machine before Hand is pressed, except a Room issue's
 *  tracker read by the preview (its EgressChip and READ / NOT READ, as the
 *  sheet names it). The launch's own egress chip sits on the Hand side. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { ConfirmLine, DotWord, EgressChip, StateChip, objectSprite } from "../surface";
import { countToken } from "../surface/count";
import { AGENT_PROFILE, HAND_PATH, HAND_PREVIEW_PATH, rememberAgent } from "../agentHand";
import { useAgentFlights } from "../agentFlights";
import {
  HAND_DELIVER_PATH,
  HAND_LAUNCH_PATH,
  agentOfProfile,
  cloneOf,
  cloneWords,
  codeOf,
  deliveryToken,
  engineEgress,
  modeWord,
  refusalToken,
  trackerToken,
  type HandClone,
  type HandLaunch,
  type HandPreview,
} from "../components/HandSheet";
import { AGENT_NAME, type AgentId } from "../firstrun/agentsStep";
import { useDropHand, type HandPending } from "./store";
import { branchFace } from "../lane/laneWire";
import "./hand.css";
import { Token } from "../surface/Token";
import { stateWords } from "../surface/words";

const DELIVERY_POLL_MS = 2000;
/** Astra P1 on #946: after Hand, the flights are re-read until the launch's
 *  session is in them (the agent object is drawn), at most this many times. */
export const FLIGHTS_POLL_LIMIT = 30;

/** True when the flights read holds the launch's session (its agent is drawn). */
export function launchSessionDrawn(launchId: string): boolean {
  const { sessions, flights } = useAgentFlights.getState();
  const key = flights.find((f) => f.launchId === launchId)?.sessionKey ?? null;
  return sessions.some((row) => row.flight?.launchId === launchId || (key !== null && row.key === key));
}

/** The agent's end of the line: the agent family's sprite. */
export function agentSprite(agent: string): string {
  return objectSprite("agent", `${agent}:hand`, "rest", 64, agent);
}

/** The next agent: the flip on the line's agent token (B39), now a turn of
 *  three: CLAUDE CODE → CODEX → PI → CLAUDE CODE (pi spike #1020). */
export function otherAgent(agent: AgentId): AgentId {
  return agent === "claude" ? "codex" : agent === "codex" ? "pi" : "claude";
}

export function HandConfirm({ pending }: { pending: HandPending }) {
  const { origin, source, skipped, unknown } = pending;
  // PHILO-15 16 (B39): the line opens on the agent the drop named (the
  // Conductor's default agent for the Conductor drawer and the verb); the
  // owner flips it on the line, CLAUDE CODE ⇄ CODEX.
  const [agent, setAgent] = useState<AgentId>(pending.agent);
  const cancel = useDropHand((s) => s.cancel);
  const [preview, setPreview] = useState<HandPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [briefOpen, setBriefOpen] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [launchError, setLaunchError] = useState<string | null>(null);
  const [launched, setLaunched] = useState<HandLaunch | null>(null);
  // PHILO-15 16 (Astra r1 on #1000): a clone this hand made, kept when the
  // launch after it refuses (CLONED stands; CLONES never comes back).
  const [cloneDone, setCloneDone] = useState<HandClone | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  // The line takes the focus: the next key acts on the hand.
  useEffect(() => {
    ref.current?.focus();
  }, []);

  const request = { kind: origin.kind, id: origin.id, profile: AGENT_PROFILE[agent], project_id: origin.projectId || null };
  const requestKey = JSON.stringify(request);

  useEffect(() => {
    let live = true;
    apiFetch<HandPreview>(HAND_PREVIEW_PATH, { method: "POST", json: JSON.parse(requestKey) })
      .then((p) => {
        if (live) setPreview(p);
      })
      .catch((error) => {
        if (live) setPreviewError(codeOf(error));
      });
    return () => {
      live = false;
    };
  }, [requestKey]);

  // The delivery is known once it leaves `pending`: read the launch until then.
  useEffect(() => {
    if (!launched?.launch_id || deliveryToken(launched).done) return;
    let live = true;
    const timer = window.setTimeout(() => {
      apiFetch<HandLaunch>(HAND_LAUNCH_PATH(String(launched.launch_id)))
        .then((next) => {
          if (live) setLaunched({ ...launched, ...next });
        })
        .catch(() => {
          if (live) setLaunched({ ...launched });
        });
    }, DELIVERY_POLL_MS);
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [launched]);

  // The agent appears on the screen and in the drawer with no other desk
  // action: the flights are re-read (bounded) until its session is in them.
  const launchId = launched?.launch_id ? String(launched.launch_id) : null;
  useEffect(() => {
    if (!launchId) return;
    let live = true;
    let tries = 0;
    let timer = 0;
    const tick = async () => {
      if (!live) return;
      await useAgentFlights.getState().load();
      tries += 1;
      if (!live || launchSessionDrawn(launchId) || tries >= FLIGHTS_POLL_LIMIT) return;
      timer = window.setTimeout(() => void tick(), DELIVERY_POLL_MS);
    };
    void tick();
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [launchId]);

  const flip = useCallback(() => {
    if (launching || launched) return;
    setPreview(null);
    setPreviewError(null);
    setBriefOpen(false);
    setAgent((now) => {
      const next = otherAgent(now);
      // The owner's flip is remembered for this Project's next hand.
      rememberAgent(origin.projectId, next);
      return next;
    });
  }, [launching, launched, origin.projectId]);

  // Betterment AG5: the working-at-once limit is not a dead end: the verb
  // reads "Start when one is free" and the hand waits in the hub's queue.
  const atLimit = (preview?.refused ?? []).includes("launch_cap_reached");
  const refused = (preview?.refused ?? []).filter((code) => code !== "launch_cap_reached");
  const previewed = preview ? agentOfProfile(preview.profile, agent) : agent;
  const actual = launched ? agentOfProfile(launched.profile, previewed) : previewed;

  const hand = useCallback(async () => {
    if (launching || launched) return;
    setLaunching(true);
    setLaunchError(null);
    try {
      // Betterment AG5: at the working-at-once limit the press queues the hand.
      const body = { ...JSON.parse(requestKey), ...(atLimit ? { queue: true } : {}) };
      const answer = await apiFetch<HandLaunch>(HAND_PATH, { method: "POST", json: body });
      if (answer?.clone) setCloneDone(answer.clone);
      setLaunched({ profile: AGENT_PROFILE[previewed], ...(answer ?? {}) });
    } catch (error) {
      const made = cloneOf(error);
      if (made) setCloneDone(made);
      setLaunchError(codeOf(error));
      if (!(error instanceof ApiError)) console.warn("hand to agent:", readableError(error));
    } finally {
      setLaunching(false);
    }
  }, [launching, launched, requestKey, previewed, atLimit]);

  const sendAgain = useCallback(async () => {
    if (!launched?.launch_id || launching) return;
    setLaunching(true);
    try {
      const next = await apiFetch<HandLaunch>(HAND_DELIVER_PATH(String(launched.launch_id)), { method: "POST" });
      setLaunched({ ...launched, ...next });
    } catch (error) {
      setLaunched({ ...launched, instruction_state: codeOf(error) });
    } finally {
      setLaunching(false);
    }
  }, [launched, launching]);

  const delivery = launched ? deliveryToken(launched) : null;
  // EGRESS-CHIP-WORDS: the agent's name as typed, the mode in sentence case
  // beside it (`Claude Code · Open throttle · hs/…`); the branch is an id.
  const fact = [preview ? stateWords(modeWord(preview.control_mode)) : "", branchFace(preview?.branch)].filter(Boolean).join(" · ");
  const frozen = launching || launched !== null;
  const agentToken = (
    <Button
      dense
      variant="ghost"
      className="hand-confirm-agent"
      disabled={frozen}
      aria-label={`Agent: ${AGENT_NAME[actual]}. Press to hand to ${AGENT_NAME[otherAgent(actual)]}`}
      data-testid="hand-confirm-agent"
      data-agent={actual}
      onClick={flip}
    >
      {AGENT_NAME[actual]}
    </Button>
  );
  // PHILO-15 16 (B38): the first hand clones the Project's repository from
  // GitHub: the egress is named here, before the press, and the clone after.
  const clone = cloneDone ?? launched?.clone ?? null;
  const toClone = !clone && !launched && preview?.clone ? preview.clone : null;
  // PHILO-15 B36: why the line is not on Claude Code.
  const passedOver = skipped && !launched && skipped !== actual ? skipped : null;
  // And for the agent the line shows when its own sign-in is unknown (also after a flip).
  const selectedUnknown = !launched && (unknown ?? []).includes(actual) ? actual : null;
  const tracker = origin.kind === "issue" ? trackerToken(origin, preview, previewError) : null;

  const status = (
    <>
      {passedOver ? (
        <Token className="surface-token" data-chip data-testid="hand-confirm-skipped">
          {AGENT_NAME[passedOver]} · SIGN-IN UNKNOWN
        </Token>
      ) : null}
      {selectedUnknown ? (
        <Token className="surface-token" data-chip data-tone="warn" data-testid="hand-confirm-selected-unknown">
          {AGENT_NAME[selectedUnknown]} · SIGN-IN UNKNOWN
        </Token>
      ) : null}
      {toClone ? (
        <span className="desk-hand-tokens" data-testid="hand-confirm-clone" data-state="to_clone">
          <EgressChip label={toClone.host} scope="cloud" />
          <Token className="surface-token" data-chip data-wrap>CLONES {toClone.repository}</Token>
        </span>
      ) : null}
      {clone ? (
        <span className="desk-hand-tokens" data-testid="hand-confirm-clone" data-state="cloned">
          <EgressChip label={clone.host} scope="cloud" />
          <Token className="surface-token" data-tone="ok" data-chip data-wrap>
            {cloneWords(clone)}
          </Token>
          {clone.folder ? (
            <Token className="surface-token" data-chip data-wrap data-testid="hand-confirm-clone-folder">
              {clone.folder}
            </Token>
          ) : null}
        </span>
      ) : null}
      {tracker ? (
        <span className="desk-hand-tokens" data-testid="hand-confirm-tracker" data-state={tracker.state}>
          <EgressChip label={tracker.host || undefined} scope="cloud" />
          <StateChip state={tracker.state} label={tracker.label} />
        </span>
      ) : null}
      {previewError ? (
        <span className="desk-hand-tokens" role="alert" data-testid="hand-confirm-no-brief">
          <StateChip state="failure" label="NO BRIEF" />
          <Token className="surface-token" data-tone="danger">
            {refusalToken(previewError, agent)}
          </Token>
        </span>
      ) : null}
      {refused.length && !launched ? (
        <span className="desk-hand-tokens" role="alert" data-testid="hand-confirm-refused">
          {refused.map((code) => (
            <Token key={code} className="surface-token" data-tone="danger">
              {refusalToken(code, code === "launch_profile_mismatch" ? actual : agent)}
            </Token>
          ))}
        </span>
      ) : null}
      {delivery ? (
        // W6-H / W6-J words: the delivery reads as a dot + words, sans.
        <span role="status" data-testid="hand-confirm-receipt" title={delivery.title}>
          <DotWord tone={delivery.tone === "danger" ? "fail" : delivery.tone === "warning" ? "warn" : delivery.tone === "ok" ? "ok" : "info"}>{delivery.label}</DotWord>
        </span>
      ) : launchError ? (
        <Token className="surface-token" data-tone="danger" role="alert" data-testid="hand-confirm-launch-refused">
          NOT LAUNCHED · {refusalToken(launchError, agent)}
        </Token>
      ) : null}
    </>
  );
  const hasStatus = Boolean(
    passedOver || selectedUnknown || toClone || clone || tracker || previewError || (refused.length && !launched) || delivery || launchError,
  );

  return (
    <div
      className="hand-confirm"
      ref={ref}
      tabIndex={-1}
      data-testid="hand-confirm"
      data-host={pending.host}
      onKeyDown={(event) => {
        // Astra P2 on #946: Escape cancels the hand first; it never reaches
        // the window's close (the drawer stays open).
        if (event.key !== "Escape") return;
        event.preventDefault();
        event.stopPropagation();
        cancel();
      }}
    >
      <ConfirmLine
        from={{ kind: source.kind, id: source.id, sprite: source.sprite }}
        to={{ kind: "agent", id: `${actual}:hand`, sprite: agentSprite(actual) }}
        title={origin.title}
        fact={fact}
        agentToken={agentToken}
        onBrief={preview ? () => setBriefOpen((open) => !open) : undefined}
        briefOpen={briefOpen}
        onCancel={cancel}
        onHand={() => void hand()}
        handLabel={atLimit ? "Start when one is free" : undefined}
        busy={launching}
        disabled={!preview || refused.length > 0}
        egress={<EgressChip {...engineEgress(actual, preview)} />}
        status={hasStatus ? status : undefined}
        verbs={
          launched ? (
            <>
              <Button dense variant="ghost" onClick={cancel}>
                Close
              </Button>
              {delivery?.tone === "danger" ? (
                <Button
                  dense
                  variant="primary"
                  loading={launching}
                  disabled={launching}
                  onClick={() => void sendAgain()}
                  data-testid="hand-confirm-send-again"
                >
                  Send again
                </Button>
              ) : null}
            </>
          ) : undefined
        }
      />
      {briefOpen && preview ? (
        <div className="hand-confirm-brief bevel-sunken" data-testid="hand-confirm-brief">
          <span className="desk-hand-tokens">
            {preview.sources.length ? (
              <Token className="surface-token" data-chip>
                {countToken(preview.sources.length, "SOURCE")}
              </Token>
            ) : null}
            {preview.people_cut > 0 ? (
              <Token className="surface-token" data-chip>
                PEOPLE CUT · {countToken(preview.people_cut, "PART")}
              </Token>
            ) : null}
            {preview.acceptance.length ? (
              <Token className="surface-token" data-chip>
                ACCEPTANCE · {countToken(preview.acceptance.length, "CHECK")}
              </Token>
            ) : null}
          </span>
          <pre className="desk-pullout-md desk-hand-text">{preview.text}</pre>
        </div>
      ) : null}
    </div>
  );
}

/** The line for `host`, while a hand waits there. */
export function HandConfirmSlot({ host, className }: { host: string; className?: string }) {
  const pending = useDropHand((s) => s.pending);
  if (!pending || pending.host !== host) return null;
  const line = <HandConfirm key={`${pending.origin.kind}:${pending.origin.id}:${pending.agent}`} pending={pending} />;
  return className ? <div className={className}>{line}</div> : line;
}
