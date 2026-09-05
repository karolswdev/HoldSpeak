// HS-172-03 — ONE canonical egress-label + scope mapper.
// Maps a model host string to the label the EgressChip shows and the
// scope colour it wears.  Three callers (ProjectRoomCore, MeetingHeader,
// SettingsCore) collapsed here; the vocabulary is:
//   THIS DEVICE  (local/LOCAL/this_device)
//   <ip> · LAN   (RFC-1918 private IPs)
//   <host>       (everything else — cloud hosts show as-is)

const PRIVATE_IP_RE = /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/;

/**
 * Derive the egress label and scope for an EgressChip from a raw host
 * string.  Never returns "LOCAL" (the vocabulary is THIS DEVICE / LAN /
 * the host name).
 */
export function egressFor(host: string | null | undefined): {
  label: string;
  scope: "local" | "cloud" | undefined;
} {
  if (!host) return { label: "", scope: undefined };
  if (host === "local" || host === "LOCAL" || host === "this_device") {
    return { label: "THIS DEVICE", scope: "local" };
  }
  if (host === "THIS DEVICE") {
    return { label: host, scope: "local" };
  }
  if (PRIVATE_IP_RE.test(host)) {
    return { label: `${host} · LAN`, scope: "local" };
  }
  return { label: host, scope: "cloud" };
}
