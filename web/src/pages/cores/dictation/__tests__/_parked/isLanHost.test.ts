// Parked 2026-10-25 (owner ruling, UX-CANON A.9 amended): isLanHost had no
// caller on the Speak face once the LAN chip was retired. The function is
// parked here with its test (lifted from SpeakFace.tsx and resolveEngine.test.ts).
import { describe, expect, it } from "vitest";

/** Whether a hostname is on a local/LAN network (RFC1918, loopback,
 *  link-local, CGNAT/Tailscale, or named local suffixes). Mirrors
 *  concierge_service._is_lan_host on the server. */
export function isLanHost(host: string): boolean {
  if (!host) return false;
  // Named local suffixes
  for (const suffix of [".local", ".internal", ".lan", ".home", ".localhost", ".ts.net"])
    if (host.endsWith(suffix)) return true;
  if (host === "localhost") return true;
  // IPv4 classification
  const parts = host.split(".");
  if (parts.length === 4 && parts.every((p) => /^\d{1,3}$/.test(p))) {
    const octets = parts.map(Number);
    if (octets.some((o) => o > 255)) return false;
    const [a, b] = octets;
    // 10.0.0.0/8
    if (a === 10) return true;
    // 172.16.0.0/12
    if (a === 172 && b >= 16 && b <= 31) return true;
    // 192.168.0.0/16
    if (a === 192 && b === 168) return true;
    // 127.0.0.0/8
    if (a === 127) return true;
    // 169.254.0.0/16 (link-local)
    if (a === 169 && b === 254) return true;
    // 100.64.0.0/10 (CGNAT / Tailscale)
    if (a === 100 && b >= 64 && b <= 127) return true;
  }
  return false;
}

/* ── isLanHost ── */

describe("isLanHost", () => {
  it("classifies RFC1918 addresses as LAN", () => {
    expect(isLanHost("192.168.1.43")).toBe(true);
    expect(isLanHost("10.0.0.5")).toBe(true);
    expect(isLanHost("172.16.0.1")).toBe(true);
    expect(isLanHost("172.31.255.255")).toBe(true);
  });
  it("classifies loopback as LAN", () => {
    expect(isLanHost("127.0.0.1")).toBe(true);
    expect(isLanHost("localhost")).toBe(true);
  });
  it("classifies CGNAT/Tailscale as LAN", () => {
    expect(isLanHost("100.64.0.1")).toBe(true);
    expect(isLanHost("100.127.255.255")).toBe(true);
  });
  it("classifies named local suffixes as LAN", () => {
    expect(isLanHost("mydevice.local")).toBe(true);
    expect(isLanHost("node.ts.net")).toBe(true);
  });
  it("classifies public IPs as non-LAN", () => {
    expect(isLanHost("8.8.8.8")).toBe(false);
    expect(isLanHost("api.openai.com")).toBe(false);
  });
});

