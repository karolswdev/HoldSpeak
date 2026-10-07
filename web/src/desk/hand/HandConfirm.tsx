/** PHILO-14 C3 — the YOLO hand in one line (board A-3, A-3 at 393).
 *
 *  `<item> → <agent>  Write the cutover comms · CLAUDE CODE · YOLO ·
 *  hs/write-the-cutover-comms  [Brief ▸] [Cancel] [Hand]`. The fact line is
 *  the hub's preview (`POST /api/agent/hand/preview`, no side effect); Brief ▸
 *  unfolds the same brief text the launch sheet shows, read only; Hand calls
 *  `POST /api/agent/hand` and the line then reads the receipt the sheet reads
 *  (`LAUNCHED · BRIEF SENT`, pending, or not sent with Send again).
 *
 *  Nothing leaves the machine before Hand is pressed, except a Room issue's
 *  tracker read by the preview (its EgressChip and READ / NOT READ, as the
 *  sheet names it). The launch's own egress chip sits on the Hand side. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { ConfirmLine, EgressChip, StateChip, objectSprite } from "../surface";
import { countToken } from "../surface/count";
import { AGENT_PROFILE, HAND_PATH, HAND_PREVIEW_PATH } from "../agentHand";
import { useAgentFlights } from "../agentFlights";
import {
  HAND_DELIVER_PATH,
  HAND_LAUNCH_PATH,
  agentOfProfile,
  codeOf,
  deliveryToken,
  modeWord,
  refusalToken,
  trackerToken,
  type HandLaunch,
  type HandPreview,
} from "../components/HandSheet";
import { AGENT_HOST, AGENT_NAME } from "../firstrun/agentsStep";
import { useDropHand, type HandPending } from "./store";
import "./hand.css";

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
  return objectSprite("agent", `${agent}:hand`);
}

export function HandConfirm({ pending }: { pending: HandPending }) {
  const { origin, source, agent } = pending;
  const cancel = useDropHand((s) => s.cancel);
  const [preview, setPreview] = useState<HandPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [briefOpen, setBriefOpen] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [launchError, setLaunchError] = useState<string | null>(null);
  const [launched, setLaunched] = useState<HandLaunch | null>(null);
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

  const previewed = preview ? agentOfProfile(preview.profile, agent) : agent;
  const actual = launched ? agentOfProfile(launched.profile, previewed) : previewed;

  const hand = useCallback(async () => {
    if (launching || launched) return;
    setLaunching(true);
    setLaunchError(null);
    try {
      const answer = await apiFetch<HandLaunch>(HAND_PATH, { method: "POST", json: JSON.parse(requestKey) });
      setLaunched({ profile: AGENT_PROFILE[previewed], ...(answer ?? {}) });
    } catch (error) {
      setLaunchError(codeOf(error));
      if (!(error instanceof ApiError)) console.warn("hand to agent:", readableError(error));
    } finally {
      setLaunching(false);
    }
  }, [launching, launched, requestKey, previewed]);

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

  const refused = preview?.refused ?? [];
  const delivery = launched ? deliveryToken(launched) : null;
  const fact = [AGENT_NAME[actual].toUpperCase(), preview ? modeWord(preview.control_mode) : "", preview?.branch ?? ""]
    .filter(Boolean)
    .join(" · ");
  const tracker = origin.kind === "issue" ? trackerToken(origin, preview, previewError) : null;

  const status = (
    <>
      {tracker ? (
        <span className="desk-hand-tokens" data-testid="hand-confirm-tracker" data-state={tracker.state}>
          <EgressChip label={tracker.host ? tracker.host.toUpperCase() : undefined} scope="cloud" />
          <StateChip state={tracker.state} label={tracker.label} />
        </span>
      ) : null}
      {previewError ? (
        <span className="desk-hand-tokens" role="alert" data-testid="hand-confirm-no-brief">
          <StateChip state="failure" label="NO BRIEF" />
          <span className="surface-token" data-tone="danger">
            {refusalToken(previewError, agent)}
          </span>
        </span>
      ) : null}
      {refused.length && !launched ? (
        <span className="desk-hand-tokens" role="alert" data-testid="hand-confirm-refused">
          {refused.map((code) => (
            <span key={code} className="surface-token" data-tone="danger">
              {refusalToken(code, code === "launch_profile_mismatch" ? actual : agent)}
            </span>
          ))}
        </span>
      ) : null}
      {delivery ? (
        <span className="surface-token" data-tone={delivery.tone} role="status" data-testid="hand-confirm-receipt">
          {delivery.label}
        </span>
      ) : launchError ? (
        <span className="surface-token" data-tone="danger" role="alert" data-testid="hand-confirm-launch-refused">
          NOT LAUNCHED · {refusalToken(launchError, agent)}
        </span>
      ) : null}
    </>
  );
  const hasStatus = Boolean(tracker || previewError || (refused.length && !launched) || delivery || launchError);

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
        onBrief={preview ? () => setBriefOpen((open) => !open) : undefined}
        briefOpen={briefOpen}
        onCancel={cancel}
        onHand={() => void hand()}
        busy={launching}
        disabled={!preview || refused.length > 0}
        egress={<EgressChip label={AGENT_HOST[actual]} scope="cloud" />}
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
              <span className="surface-token" data-chip>
                {countToken(preview.sources.length, "SOURCE")}
              </span>
            ) : null}
            {preview.people_cut > 0 ? (
              <span className="surface-token" data-chip>
                PEOPLE CUT · {countToken(preview.people_cut, "PART")}
              </span>
            ) : null}
            {preview.acceptance.length ? (
              <span className="surface-token" data-chip>
                ACCEPTANCE · {countToken(preview.acceptance.length, "CHECK")}
              </span>
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
