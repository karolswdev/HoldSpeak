// The route of one model turn (owner pick 2026-10-05, canvas section 4,
// option C "Route in footer"): each turn wears only its LAMP (LOCAL / LAN /
// CLOUD); the footer's egress slot names the FULL route of the LAST turn
// (host chip, model, receipt). The lamp is the turn's receipt boundary
// (Article III; the hub reads it through inference_locality.served_route);
// a turn with no model call wears no lamp.
import { EgressChip, LampGadget } from "./surface/gadgets";
import "./turn-route.css";
import {
  boundaryEgressLamp,
  egressScopeLamp,
  type EgressLamp,
} from "./inferenceEgress";

export interface TurnRoute {
  lamp: EgressLamp;
  host: string;
  model: string;
  /** The receipt id; the face prints its last four characters. */
  receipt: string;
}

/** The lamp for a route word from the wire (the boundary or the egress
 * vocabulary); null when the word names no route (no model call). */
export function routeLamp(word: string | null | undefined): EgressLamp | null {
  const w = String(word || "").trim();
  if (!w) return null;
  if (w === "lan") return { label: "LAN", tone: "warn" };
  if (w === "paired_device_then_external_service")
    return { label: "CLOUD", tone: "fail" };
  const boundary = boundaryEgressLamp(w);
  if (boundary.label !== "NO MODEL") return boundary;
  const scope = egressScopeLamp(w);
  if (scope.label !== "NO MODEL") return scope;
  return null;
}

/** The footer's host chip for a route: where the bytes went. */
export function routeEgress(route: TurnRoute): {
  label: string;
  scope: "local" | "cloud" | "remote";
} {
  switch (route.lamp.label) {
    case "LOCAL":
      return { label: "THIS DEVICE", scope: "local" };
    case "CLOUD":
      return { label: route.host || "CLOUD", scope: "cloud" };
    case "LAN":
      return { label: route.host ? `${route.host} · LAN` : "LAN", scope: "local" };
    default:
      return {
        label: route.host ? `${route.host} · ${route.lamp.label}` : route.lamp.label,
        scope: "remote",
      };
  }
}

/** The footer's receipt line: LAST TURN · model · RECEIPT ··a91f. */
export function lastTurnLine(route: TurnRoute): string {
  const short = route.receipt.length > 4 ? route.receipt.slice(-4) : route.receipt;
  return ["LAST TURN", route.model, short ? `RECEIPT ··${short}` : ""]
    .filter(Boolean)
    .join(" · ");
}

/** The per-turn lamp. */
export function TurnLamp({ lamp }: { lamp: EgressLamp | null }) {
  return lamp ? <LampGadget on {...lamp} /> : null;
}

/** The footer egress slot: the last turn's host chip. */
export function RouteEgressChip({ route }: { route: TurnRoute }) {
  const chip = routeEgress(route);
  return (
    <EgressChip
      className="turn-route-egress"
      label={chip.label}
      scope={chip.scope}
      title={[chip.label, route.model].filter(Boolean).join(" · ")}
    />
  );
}
