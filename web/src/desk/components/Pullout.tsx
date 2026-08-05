// The pull-out chrome shell (HS-117-15): the DeskWindowFrame wrapper that
// delegates body + footer to the kind-keyed content registry.
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import "./pullout.css";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objGlow, type WorldObject } from "../world";
import { inferenceEgressLamp } from "../inferenceEgress";
import { DeskWindowFrame } from "./DeskWindow";
import { PULLOUT_CONTENT, FallbackPullout } from "../pullouts";

export function Pullout({
  o,
  origin,
}: {
  o: WorldObject;
  /** The client point the open gesture happened at (spatial motion). */
  origin?: { x: number; y: number } | null;
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
          text: `☁ ${
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
      icon={<img src={spriteUrl(o.kind, o.id)} alt="" width={30} height={30} />}
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
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() =>
                openSurfaceOr("review-meetings", "/history", resourceRef)
              }
            >
              Review meeting
            </button>
          )}
          {o.kind === "workflow" && (
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() =>
                openSurfaceOr("open-workbenches", "/workbenches", resourceRef)
              }
            >
              Edit Workflow
            </button>
          )}
        </>
      }
    >
      {Content ? (
        <Content object={o} onClose={() => closePullout(o.id)} />
      ) : (
        <FallbackPullout kind={o.kind} />
      )}
    </DeskWindowFrame>
  );
}
