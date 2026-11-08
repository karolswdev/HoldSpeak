/* HS-S53: the account words a destination shows, with ONE owner.
 * `chipLabel` names an account row's state (Settings -> Connections uses it
 * too); `accountChip` is the destination warning (Settings' Destinations,
 * the destination form and the Send well use it). Pure functions over the
 * account wire types: no screen, no store, no module side effect.
 * Moved from pages/cores/connections/ConnectionsPane.tsx (chipLabel) and
 * desk/surface/send/SendWell.tsx (accountChip); both re-export them.
 */
import type { ConnectionsResponse, ConnectionState } from "../../pages/cores/connections/api";
import type { Destination } from "./channels";

/** Betterment ST2: a row's state in words: Works, Not signed in, Signed in
 *  as another account, Could not check: <reason>.  The reason is the hub's
 *  own words (`reason`); the face never reads the error text. */
export function chipLabel(
  state: ConnectionState,
  providerId: string,
  words: { reason?: string; other_account?: boolean } = {},
): string {
  const cli = providerId === "jira" || providerId === "confluence" ? "acli" : "gh";
  switch (state) {
    case "connected": return "Works";
    case "owner_action_required": return "Not signed in";
    case "unavailable": return `Could not check: ${words.reason ?? `${cli} is not installed`}`;
    case "degraded":
      if (words.other_account) return "Signed in as another account";
      return `Could not check: ${words.reason ?? `${cli} gave no answer`}`;
    case "not_configured":
      if (providerId === "jira" || providerId === "confluence") return "Not set up";
      return "Off";
    case "never_checked": return "Not checked";
    case "signed_in": return "Signed in";
  }
}

/** The account states that say "this account did not sign in". */
const SIGN_IN_FAILED = new Set<string>(["owner_action_required", "unavailable", "degraded"]);

/** The account warning a destination row shows (the Phase 9 B1 words, the
 *  Connections chip words), or null. Betterment send S1: a chip shows ONLY
 *  when the newest word on that account (a check or a send: the hub's
 *  `connection`, where a good send counts as a good check) says it failed to
 *  sign in. Never CONNECTED, NEVER CHECKED or KEY SET beside a good send.
 *  Null for a folder. Email and Slack: only a key known to be absent. */
export function accountChip(
  d: Pick<Destination, "channel" | "account"> & { connection?: Destination["connection"] },
  c: ConnectionsResponse | null,
): { state: "success" | "warning" | "idle" | "failure"; label: string; code: string } | null {
  if (d.channel === "file") return null;
  if (d.channel === "email" || d.channel === "slack") {
    // Present or absent only, and only when known (the list read does not open the keychain).
    if (d.account.key_present !== false) return null;
    return d.channel === "slack"
      ? { state: "warning", label: "NO WEBHOOK", code: "slack_webhook_missing" }
      : { state: "warning", label: "NO KEY", code: "email_key_missing" };
  }
  const tool = c?.tools.find((t) => t.provider_id === d.channel);
  let state: ConnectionState = "not_configured";
  // Betterment ST2: the Accounts row's own words (its reason) name the chip.
  let words: { reason?: string; other_account?: boolean } | undefined = tool;
  if (d.channel === "github") {
    state = (d.connection?.state ?? tool?.state ?? "not_configured") as ConnectionState;
    const login = tool?.account?.login;
    if (state === "connected" && login && d.account.login && login !== d.account.login) {
      return { state: "failure", label: "Account changed", code: "github_identity_changed" };
    }
  } else {
    const conn = tool?.connections?.find((x) => x.account.site === d.account.site && x.account.email === d.account.email);
    state = (d.connection?.state ?? conn?.state ?? "not_configured") as ConnectionState;
    words = conn;
  }
  if (!SIGN_IN_FAILED.has(state)) return null;
  const map: Record<string, "warning" | "failure"> = {
    owner_action_required: "warning", unavailable: "failure", degraded: "warning",
  };
  return { state: map[state] ?? "warning", label: chipLabel(state, d.channel, words ?? {}), code: state };
}
