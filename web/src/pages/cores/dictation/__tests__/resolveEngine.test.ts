// HS-170-04 — resolveEngine: the ENGINE row reads the real model name
// and host from the concierge detect payload, never the stale assignment label.
// Three resolution paths:
//   (a) profileId match on detect engines
//   (b) base_url host match via targets when profileId fails
//   (c) last-resort classification from profile base_url host
import { describe, expect, it } from "vitest";
import { resolveEngine, isLanHost, type TargetProfile } from "../SpeakFace";
import type { Engine } from "../../../../features/concierge/api";
import type { AssignmentEditorProjection } from "../../assignmentExperience";

/* ── Fixtures ── */

function fakeAssignment(
  profileId: string,
  label: string,
  boundary: string,
): AssignmentEditorProjection {
  return {
    schema: "AssignmentEditorProjection@1",
    scope: { kind: "capability", capability_id: "speech.rewrite" },
    selected_capability: {
      id: "speech.rewrite",
      revision: 1,
      label: "Dictation",
      group: { id: "speech", label: "Speech" },
      allowed_boundaries: [],
      fallback_dispositions: [],
    },
    draft_base_revision: 0,
    configured_assignment: null,
    effective: {
      status: "assigned",
      inherited_from: null,
      assignment: {
        id: "a1",
        revision: 1,
        scope: { kind: "capability", capability_id: "speech.rewrite" },
        entries: [
          {
            ordinal: 0,
            profile_id: profileId,
            profile_revision: 1,
            label,
            boundary,
            readiness: "ready",
          },
        ],
        retry_policy_id: null,
        issues: [],
      },
      repair: null,
    },
    candidates: [],
    retry_policy: { permitted_ids: [], default_id: "" },
  };
}

function fakeEngine(overrides: Partial<Engine>): Engine {
  return {
    id: overrides.id ?? "e1",
    kind: overrides.kind ?? "local",
    name: overrides.name ?? "Test Engine",
    host: overrides.host ?? "",
    state: overrides.state ?? "READY",
    profileId: overrides.profileId ?? "p1",
    ...overrides,
  };
}

const LEGACY_PROFILE_ID = "legacy-llama43";
const LEGACY_LABEL = "Migrated intel endpoint";

/** The legacy target profile from /api/inference-targets — the migration
 *  profile has name="Migrated intel endpoint", base_url on 192.168.1.43:8081,
 *  provider=openai_compatible, model="default". */
const LEGACY_TARGET: TargetProfile = {
  id: "this_machine_legacy-llama43",
  profile_id: LEGACY_PROFILE_ID,
  name: LEGACY_LABEL,
  base_url: "http://192.168.1.43:8081/v1",
  model: "default",
  engine: "llama.cpp",
};

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

/* ── resolveEngine ── */

describe("resolveEngine (HS-170-04)", () => {
  // (a) profileId match on detect engines
  it("(a) matches by profileId and uses detect engine name + host", () => {
    const assignment = fakeAssignment(LEGACY_PROFILE_ID, LEGACY_LABEL, "private_network");
    const engines = [
      fakeEngine({
        profileId: LEGACY_PROFILE_ID,
        name: "Qwen3.6 35B",
        kind: "lan",
        host: "192.168.1.43",
      }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("Qwen3.6 35B");
    expect(result.egressLabel).toBe("192.168.1.43 · LAN");
  });

  it("(a) matches by id prefix (lan:profileId)", () => {
    const assignment = fakeAssignment(LEGACY_PROFILE_ID, LEGACY_LABEL, "private_network");
    const engines = [
      fakeEngine({
        id: `lan:${LEGACY_PROFILE_ID}`,
        profileId: LEGACY_PROFILE_ID,
        name: "Qwen3.6 35B",
        kind: "lan",
        host: "192.168.1.43",
      }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("Qwen3.6 35B");
    expect(result.egressLabel).toBe("192.168.1.43 · LAN");
  });

  // (b) base_url host match via targets when profileId doesn't match
  it("(b) falls back to base_url host match via targets", () => {
    const assignment = fakeAssignment(LEGACY_PROFILE_ID, LEGACY_LABEL, "private_network");
    // Detect engines have a DIFFERENT profileId (no direct match)
    const engines = [
      fakeEngine({
        profileId: "different-profile",
        name: "Qwen3.6 35B",
        kind: "lan",
        host: "192.168.1.43",
      }),
    ];
    const result = resolveEngine(assignment, engines, [LEGACY_TARGET]);
    expect(result.name).toBe("Qwen3.6 35B");
    expect(result.egressLabel).toBe("192.168.1.43 · LAN");
  });

  // (c) no detect match — classify from profile base_url
  it("(c) classifies LAN host from target base_url when detect is empty", () => {
    const assignment = fakeAssignment(LEGACY_PROFILE_ID, LEGACY_LABEL, "cloud");
    // Note: boundary says "cloud" but the base_url is on 192.168.1.43 (LAN).
    // The resolver must classify by the actual host, not the stale boundary.
    const result = resolveEngine(assignment, [], [LEGACY_TARGET]);
    // Name: "Migrated ..." is rejected; model is "default" also rejected;
    // falls back to host:port
    expect(result.name).toBe("192.168.1.43:8081");
    expect(result.egressLabel).toBe("192.168.1.43 · LAN");
    expect(result.egressHost).toBe("192.168.1.43");
  });

  it("(c) uses non-migration label as the name", () => {
    const assignment = fakeAssignment("p2", "My Custom Model", "private_network");
    const target: TargetProfile = {
      id: "t2", profile_id: "p2", name: "My Custom Model",
      base_url: "http://10.0.0.5:8080/v1", model: "llama-3.1",
    };
    const result = resolveEngine(assignment, [], [target]);
    expect(result.name).toBe("My Custom Model");
    expect(result.egressLabel).toBe("10.0.0.5 · LAN");
  });

  it("(c) uses model id when label is migration and model is not default", () => {
    const assignment = fakeAssignment("p3", "Migrated endpoint", "cloud");
    const target: TargetProfile = {
      id: "t3", profile_id: "p3", name: "Migrated endpoint",
      base_url: "http://192.168.1.43:8081/v1", model: "qwen-3.5-0.8b",
    };
    const result = resolveEngine(assignment, [], [target]);
    expect(result.name).toBe("qwen-3.5-0.8b");
    expect(result.egressLabel).toBe("192.168.1.43 · LAN");
  });

  // Edge cases
  it("shows THIS DEVICE for a local/loopback engine", () => {
    const assignment = fakeAssignment("p4", "Local MLX", "local");
    const engines = [
      fakeEngine({ profileId: "p4", kind: "local", host: "", name: "Whisper v3" }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("Whisper v3");
    expect(result.egressLabel).toBe("THIS DEVICE");
  });

  // The owner's real fixture: legacy-intel profile → cloud:legacy-intel detect engine
  it("(a) matches legacy-intel by cloud:profileId prefix and shows GPT-5 mini + host", () => {
    const assignment = fakeAssignment("legacy-intel", LEGACY_LABEL, "cloud");
    const engines = [
      fakeEngine({
        id: "cloud:legacy-intel",
        profileId: "legacy-intel",
        kind: "cloud",
        name: "GPT 5 mini",
        host: "api.openai.com",
        state: "NOT_SET",
        keySet: false,
      }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("GPT 5 mini");
    expect(result.egressLabel).toBe("API.OPENAI.COM");
    expect(result.engineState).toBe("NOT_SET");
    expect(result.keySet).toBe(false);
  });

  // State: READY only when detect says READY
  it("carries READY state from the detect engine", () => {
    const assignment = fakeAssignment("p5", "OpenAI", "cloud");
    const engines = [
      fakeEngine({ profileId: "p5", kind: "cloud", host: "api.openai.com", name: "GPT-4o", state: "READY", keySet: true }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("GPT-4o");
    expect(result.egressLabel).toBe("API.OPENAI.COM");
    expect(result.engineState).toBe("READY");
    expect(result.keySet).toBe(true);
  });

  it("carries NOT_SET state when key is missing", () => {
    const assignment = fakeAssignment("p5b", "OpenAI", "cloud");
    const engines = [
      fakeEngine({ profileId: "p5b", kind: "cloud", host: "api.openai.com", name: "GPT-4o", state: "NOT_SET", keySet: false }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.engineState).toBe("NOT_SET");
    expect(result.keySet).toBe(false);
  });

  it("returns null name when no assignment entries exist", () => {
    const result = resolveEngine(null, []);
    expect(result.name).toBeNull();
    expect(result.egressLabel).toBe("THIS DEVICE");
  });

  it("falls back to assignment boundary when no targets and no detect", () => {
    const assignment = fakeAssignment("p6", "Some Model", "private_network");
    const result = resolveEngine(assignment, []);
    expect(result.name).toBe("Some Model");
    expect(result.egressLabel).toBe("LAN");
  });
});
