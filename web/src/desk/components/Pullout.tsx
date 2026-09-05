// The pull-out chrome shell (HS-117-15): the DeskWindowFrame wrapper that
// delegates body + footer to the kind-keyed content registry.
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import "./pullout.css";
import { spriteUrl } from "../sprites";
import { spriteVariantKey } from "../../lib/spriteVariants";
import { spriteStateCssClass } from "../../lib/spriteStates";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objGlow, type WorldObject } from "../world";
import { inferenceEgressLamp } from "../inferenceEgress";
import { DeskWindowFrame } from "./DeskWindow";
import { PULLOUT_CONTENT } from "../pullouts";
import { useEffect, useState, type ReactNode } from "react";
import { thoughtForNote, type NoteThoughtStatus, type Thought } from "../thoughts";
import { NotePullout } from "../pullouts/NotePullout";
import { ThoughtWorkspaceWindow } from "../thought-workspace/ThoughtWorkspaceWindow";

function PulloutFrame({
  o,
  origin,
  noteStatus,
  onThoughtOwned,
  overrideContent,
}: {
  o: WorldObject;
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

  return (
    <DeskWindowFrame
      id={`pullout:${o.id}`}
      glyph="▤"
      label={o.title}
      className="desk-pullout is-card"
      fitContent
      origin={origin}
      rootStyle={{ "--k": objGlow(o.kind) } as React.CSSProperties}
      icon={<img src={spriteUrl(o.kind, o.id)} alt="" width={30} height={30} className={spriteStateCssClass((o as { spriteState?: string }).spriteState ?? null) || undefined} data-sprite-variant={spriteVariantKey(o.kind, (o as { spriteState?: string }).spriteState ?? null)} />}
      title={o.title}
      open
      onClose={() => closePullout(o.id)}
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
        ? <NotePullout object={o} onClose={() => closePullout(o.id)} initialStatus={noteStatus} onThoughtOwned={onThoughtOwned} />
        : <Content object={o} onClose={() => closePullout(o.id)} />)}
    </DeskWindowFrame>
  );
}

function NoteWindowRouter({ o, origin }: { o: WorldObject; origin?: { x: number; y: number } | null }) {
  const [status, setStatus] = useState<NoteThoughtStatus | null>(null);
  const [failed, setFailed] = useState(false);
  const close = () => useDesk.getState().closePullout(o.id);
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

  if (status?.ownership === "thought") return <ThoughtWorkspaceWindow object={o} thought={status.thought} origin={origin} onClose={close} />;
  if (status?.ownership === "ordinary") return <PulloutFrame o={o} origin={origin} noteStatus={status} onThoughtOwned={(thought) => setStatus({ ownership: "thought", thought })} />;
  return <PulloutFrame o={o} origin={origin} overrideContent={<div className="desk-pullout-body desk-surface-body thought-workspace-opening" aria-busy={!failed}>{failed ? <><p>Could not check this Note on this hub.</p><button type="button" className="btn btn--primary" onClick={load}>Try again</button></> : <span>Opening Note…</span>}</div>} />;
}

export function Pullout({ o, origin }: { o: WorldObject; origin?: { x: number; y: number } | null }) {
  return o.kind === "note" ? <NoteWindowRouter o={o} origin={origin} /> : <PulloutFrame o={o} origin={origin} />;
}
