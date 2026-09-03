import { describe, expect, it } from "vitest";
import { automationFromWire } from "./api";

// Counsel S-2 (HS-166-07): jira has a live adapter; only unknown connectors are unavailable.
describe("automationFromWire adapter status", () => {
  it("marks a jira watch ready", () => {
    const row = automationFromWire({
      reaction: { id: "r1", name: "Due risk", enabled: true, event_pattern: "jira.issue.due_changed" },
      watch: { connector_id: "jira", enabled: true },
    });
    expect(row.provider).toBe("jira");
    expect(row.adapter_status).toBe("ready");
    expect(row.status).toBe("active");
  });
  it("marks a github watch ready", () => {
    const row = automationFromWire({ reaction: { id: "r2", enabled: true }, watch: { connector_id: "gh" } });
    expect(row.adapter_status).toBe("ready");
  });
  it("marks an unknown connector unavailable", () => {
    const row = automationFromWire({ reaction: { id: "r3", enabled: true }, watch: { connector_id: "custom" } });
    expect(row.adapter_status).toBe("unavailable");
  });
});
