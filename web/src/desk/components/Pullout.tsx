// The pull-out chrome shell (HS-117-15): the DeskWindowFrame wrapper that
// delegates body + footer to the kind-keyed content registry.
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import "./pullout.css";
import { refAgent, spriteUrl } from "../sprites";
import { spriteVariantKey } from "../../lib/spriteVariants";
import { spriteStateCssClass } from "../../lib/spriteStates";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objGlow, type WorldObject } from "../world";
import { inferenceEgressLamp } from "../inferenceEgress";
import { DeskWindowFrame } from "./DeskWindow";
import { kindWord, primitiveName } from "../windowName";
import { useThreadStore } from "../threads";
import { PULLOUT_CONTENT } from "../pullouts";
import { PULLOUT_SIZE } from "../pullouts/size";
import { useEffect, useState, type ReactNode } from "react";
import { thoughtForNote, type NoteThoughtStatus, type Thought } from "../thoughts";
import { NotePullout } from "../pullouts/NotePullout";
import { ThoughtWorkspaceWindow } from "../thought-workspace/ThoughtWorkspaceWindow";

function PulloutFrame({
  o,
  pulloutId,
  origin,
  noteStatus,
  onThoughtOwned,
  overrideContent,
}: {
  o: WorldObject;
  /** PHILO-13-05 — the id the store keeps for this card (`decision:d1` or a
   * bare `d1`, as the opener gave it). The frame and Close use it, so Close
   * removes exactly this card. */
  pulloutId: string;
  /** The client point the open gesture happened at (spatial motion). */
  origin?: { x: number; y: number } | null;
  noteStatus?: NoteThoughtStatus;
  onThoughtOwned?: (thought: Thought) => void;
  overrideContent?: ReactNode;
}) {
  const profiles = useDesk((s) => s.profiles);
  const { closePullout } = useDesk.getState();

  const resourceRef = qualifiedRef(o.kind, o.id);
  const profileId = "profileId" in o.ref ? String(o.ref.profileId || "") : "";
  const profile = profiles.find((p) => p.id === profileId);
  const egress = profile
    ? (profile.kind || "onDevice") === "onDevice"
      ? { scope: "local", text: "⌂ This device" }
      : {
          scope: "cloud",
          text: `${
            String(profile.base_url || "endpoint")
              .replace(/^https?:\/\//, "")
              .split("/")[0]
          }`,
        }
    : null;

  const Content = PULLOUT_CONTENT[o.kind];
  // A thread with no title is named by the first words of its first message
  // (the open thread holds its messages; the Desk list does not).
  const firstMessage = useThreadStore((s) =>
    o.kind === "thread"
      ? (s.threads[o.id]?.messages.find((m) => m.role === "user")?.parts.find((p) => p.text?.trim())?.text ?? "")
      : "");
  const name = o.kind === "thread" ? primitiveName("thread", o.ref, o.id, firstMessage) : o.title;

  return (
    <DeskWindowFrame
      id={`pullout:${pulloutId}`}
      glyph="▤"
      label={name}
      kindWord={kindWord(o.kind)}
      className="desk-pullout is-card"
      fitContent
      defaultW={PULLOUT_SIZE[o.kind]?.w}
      defaultH={PULLOUT_SIZE[o.kind]?.h}
      origin={origin}
      rootStyle={{ "--k": objGlow(o.kind) } as React.CSSProperties}
      icon={<img src={spriteUrl(o.kind, o.id, "rest", refAgent(o.ref))} alt="" width={30} height={30} className={spriteStateCssClass((o as { spriteState?: string }).spriteState ?? null) || undefined} data-sprite-variant={spriteVariantKey(o.kind, (o as { spriteState?: string }).spriteState ?? null)} />}
      title={name}
      open
      onClose={() => closePullout(pulloutId)}
      actions={
        <>
          {egress && (
            <span className={`egress-badge is-${egress.scope}`}>
              {egress.text}
            </span>
          )}
          {o.kind === "meeting" && (
            <Button
              dense
              variant="ghost"
              onClick={() =>
                openSurfaceOr("review-meetings", "/history", resourceRef)
              }
            >
              Review meeting
            </Button>
          )}
          {o.kind === "workflow" && (
            <Button
              dense
              variant="ghost"
              onClick={() =>
                openSurfaceOr("open-workbenches", "/workbenches", resourceRef)
              }
            >
              Edit Workflow
            </Button>
          )}
        </>
      }
    >
      {overrideContent ?? (o.kind === "note"
        ? <NotePullout object={o} onClose={() => closePullout(pulloutId)} initialStatus={noteStatus} onThoughtOwned={onThoughtOwned} />
        : <Content object={o} onClose={() => closePullout(pulloutId)} />)}
    </DeskWindowFrame>
  );
}

function NoteWindowRouter({ o, pulloutId, origin }: { o: WorldObject; pulloutId: string; origin?: { x: number; y: number } | null }) {
  const [status, setStatus] = useState<NoteThoughtStatus | null>(null);
  const [failed, setFailed] = useState(false);
  const close = () => useDesk.getState().closePullout(pulloutId);
  const load = () => {
    setFailed(false);
    void thoughtForNote(o.id).then(setStatus).catch(() => setFailed(true));
  };
  useEffect(() => {
    let live = true;
    setStatus(null); setFailed(false);
    void thoughtForNote(o.id).then((next) => { if (live) setStatus(next); }).catch(() => { if (live) setFailed(true); });
    return () => { live = false; };
  }, [o.id]);

  if (status?.ownership === "thought") return <ThoughtWorkspaceWindow object={o} pulloutId={pulloutId} thought={status.thought} origin={origin} onClose={close} />;
  if (status?.ownership === "ordinary") return <PulloutFrame o={o} pulloutId={pulloutId} origin={origin} noteStatus={status} onThoughtOwned={(thought) => setStatus({ ownership: "thought", thought })} />;
  return <PulloutFrame o={o} pulloutId={pulloutId} origin={origin} overrideContent={<div className="desk-pullout-body desk-surface-body thought-workspace-opening" aria-busy={!failed}>{failed ? <><p>Could not check this Note on this hub.</p><Button variant="primary" onClick={load}>Try again</Button></> : <span>Opening Note…</span>}</div>} />;
}

export function Pullout({
  o,
  pulloutId,
  origin,
}: {
  o: WorldObject;
  /** The id the store keeps (`pullouts[].id`); defaults to the bare `o.id`. */
  pulloutId?: string;
  origin?: { x: number; y: number } | null;
}) {
  const storeId = pulloutId ?? o.id;
  return o.kind === "note"
    ? <NoteWindowRouter o={o} pulloutId={storeId} origin={origin} />
    : <PulloutFrame o={o} pulloutId={storeId} origin={origin} />;
}
