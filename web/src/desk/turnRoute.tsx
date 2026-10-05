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
  /** The receipt id the route was read from; the face prints its last
   * four characters. */
  receipt: string;
  /** True when another attempt answered: the route shown was a fallback's
   * earlier, less private send. */
  fallback?: boolean;
}

/** The hub's receipt route (`route` on an Ask result or refusal); null when
 * the hub sent none or no attempt was sent (no lamp). */
export function routeFromWire(raw: unknown): TurnRoute | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  const lamp = routeLamp(typeof r.lamp === "string" ? r.lamp : "");
  if (!lamp) return null;
  return {
    lamp,
    host: String(r.host || ""),
    model: String(r.model || ""),
    receipt: String(r.receipt || ""),
    fallback: Boolean(r.fallback),
  };
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

/** The footer's receipt line: LAST TURN · model · [FALLBACK ·] RECEIPT ··a91f. */
export function lastTurnLine(route: TurnRoute): string {
  const short = route.receipt.length > 4 ? route.receipt.slice(-4) : route.receipt;
  return ["LAST TURN", route.model, route.fallback ? "FALLBACK" : "", short ? `RECEIPT ··${short}` : ""]
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
