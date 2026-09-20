// HS-201-09 — the endpoint draft the face posts to the Model Library.
//
// The rehearsal proved a stranger could never connect his own engine: the
// face posted {request_id,label,endpoint,model,requires_key} while
// `ModelLibraryApplicationService._provider_draft`
// (holdspeak/services/model_library_service.py:276) refuses any body whose
// key set is not EXACTLY its allowed set, so every "Add an engine..."
// ended in 400 "Provider draft is invalid.".
//
// The smallest honest change is on this side: the face sends what the
// service already accepts. No route, no validation, no contract widened.
// `ENDPOINT_DRAFT_KEYS` is the pinned half of that contract — the Python
// fence in tests/unit/test_hs201_09_connect_an_engine_from_the_face.py
// reads it and compares it with the service's own allowed set, so the two
// sides can never drift apart again in silence.

export const ENDPOINT_DRAFT_KEYS = [
  "request_id",
  "profile_id",
  "expected_profile_revision",
  "label",
  "provider_family",
  "model",
  "endpoint",
  "requires_key",
] as const;

export interface EndpointDraft {
  request_id: string;
  profile_id: string;
  expected_profile_revision: number;
  label: string;
  provider_family: string;
  model: string;
  endpoint: string;
  requires_key: boolean;
}

/** host:port for a base URL — the label and the id both read from it. */
export function endpointHostPort(url: string): string {
  const trimmed = url.trim();
  try {
    const parsed = new URL(trimmed);
    return parsed.port ? `${parsed.hostname}:${parsed.port}` : parsed.hostname;
  } catch {
    return trimmed.replace(/^[a-z]+:\/\//i, "").split("/")[0] ?? trimmed;
  }
}

/** A stable, lawful profile id for one endpoint.
 *
 * The service's `_PROFILE_ID` is `^[a-z][a-z0-9_-]{0,95}$`, so the id is
 * derived, not typed: the same address always mints the same id, which is
 * what lets a second Add of the same engine replay instead of duplicating.
 */
export function endpointProfileId(url: string): string {
  const slug = endpointHostPort(url)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `engine-${slug || "endpoint"}`.slice(0, 96);
}

/** The label the library row carries. `_safe_field` refuses "/", so this
 *  is the host and port, never the full URL. */
export function endpointLabel(url: string): string {
  return endpointHostPort(url).slice(0, 200) || "Engine";
}

export function endpointDraft(args: {
  url: string;
  model: string;
  requestId: string;
  expectedProfileRevision?: number;
}): EndpointDraft {
  return {
    request_id: args.requestId,
    profile_id: endpointProfileId(args.url),
    expected_profile_revision: args.expectedProfileRevision ?? 0,
    label: endpointLabel(args.url),
    provider_family: "openai_compatible",
    model: args.model.trim(),
    endpoint: args.url.trim(),
    requires_key: false,
  };
}

/** Whether an address stays on this network.
 *
 * HS-201-09 (counsel finding 4c): the Check row names the host it will
 * contact BEFORE the owner presses Check (Article III), and the badge has
 * to say which side of the boundary it is. Same families the hub's own
 * `_is_lan_host` recognises (`holdspeak/services/concierge_service.py`).
 */
export function isLanAddress(url: string): boolean {
  const host = endpointHostPort(url).split(":")[0]?.toLowerCase() ?? "";
  if (!host) return true;
  if (
    host === "localhost" ||
    host.endsWith(".local") ||
    host.endsWith(".internal") ||
    host.endsWith(".lan") ||
    host.endsWith(".home") ||
    host.endsWith(".localhost") ||
    host.endsWith(".ts.net")
  )
    return true;
  const octets = host.split(".").map((part) => Number(part));
  if (octets.length !== 4 || octets.some((n) => !Number.isInteger(n))) return false;
  const [a, b] = octets;
  if (a === 10 || a === 127) return true;
  if (a === 192 && b === 168) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  if (a === 169 && b === 254) return true;
  if (a === 100 && b >= 64 && b <= 127) return true; // CGNAT / Tailscale
  return false;
}
