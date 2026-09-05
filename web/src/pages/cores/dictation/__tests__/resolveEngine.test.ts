// HS-170-04 — resolveEngine: the ENGINE row reads the real model name
// and host from the concierge detect payload, never the stale assignment label.
import { describe, expect, it } from "vitest";
import { resolveEngine } from "../SpeakFace";
import type { Engine } from "../../../../features/concierge/api";
import type { AssignmentEditorProjection } from "../../assignmentExperience";

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

describe("resolveEngine (HS-170-04)", () => {
  it("uses the detect engine name, not the stale assignment label", () => {
    const assignment = fakeAssignment("p1", "Migrated intel endpoint", "private_network");
    const engines = [
      fakeEngine({
        profileId: "p1",
        name: "Qwen 3.5 0.8B",
        kind: "lan",
        host: "192.168.1.43",
      }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("Qwen 3.5 0.8B");
    expect(result.egressLabel).toBe("192.168.1.43 · LAN");
  });

  it("shows host · LAN for a private_network engine", () => {
    const assignment = fakeAssignment("p1", "LAN model", "private_network");
    const engines = [
      fakeEngine({ profileId: "p1", kind: "lan", host: "10.0.0.5", name: "Llama 3.1" }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("Llama 3.1");
    expect(result.egressLabel).toBe("10.0.0.5 · LAN");
    expect(result.egressHost).toBe("10.0.0.5");
  });

  it("shows THIS DEVICE for a local engine", () => {
    const assignment = fakeAssignment("p2", "Local MLX", "local");
    const engines = [
      fakeEngine({ profileId: "p2", kind: "local", host: "", name: "Whisper v3" }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("Whisper v3");
    expect(result.egressLabel).toBe("THIS DEVICE");
  });

  it("shows CLOUD for a cloud engine", () => {
    const assignment = fakeAssignment("p3", "OpenAI", "cloud");
    const engines = [
      fakeEngine({ profileId: "p3", kind: "cloud", host: "api.openai.com", name: "GPT-4o" }),
    ];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("GPT-4o");
    expect(result.egressLabel).toBe("CLOUD");
  });

  it("falls back to assignment label when detect has no match", () => {
    const assignment = fakeAssignment("p99", "Fallback Label", "local");
    const engines: Engine[] = [];
    const result = resolveEngine(assignment, engines);
    expect(result.name).toBe("Fallback Label");
    expect(result.egressLabel).toBe("THIS DEVICE");
  });

  it("returns null name when no assignment entries exist", () => {
    const result = resolveEngine(null, []);
    expect(result.name).toBeNull();
    expect(result.egressLabel).toBe("THIS DEVICE");
  });
});
