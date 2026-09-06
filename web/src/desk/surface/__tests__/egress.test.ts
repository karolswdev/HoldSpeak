// HS-172-03 + HS-174-04 — egressFor + egressForEvent: the egress-label + scope mapper.
import { describe, expect, it } from "vitest";
import { egressFor, egressForEvent, receiptLabel } from "../egress";

describe("egressFor", () => {
  it("returns empty for null/undefined/empty", () => {
    expect(egressFor(null)).toEqual({ label: "", scope: undefined });
    expect(egressFor(undefined)).toEqual({ label: "", scope: undefined });
    expect(egressFor("")).toEqual({ label: "", scope: undefined });
  });

  it("maps local/LOCAL/this_device to THIS DEVICE + local", () => {
    expect(egressFor("local")).toEqual({ label: "THIS DEVICE", scope: "local" });
    expect(egressFor("LOCAL")).toEqual({ label: "THIS DEVICE", scope: "local" });
    expect(egressFor("this_device")).toEqual({ label: "THIS DEVICE", scope: "local" });
    expect(egressFor("THIS DEVICE")).toEqual({ label: "THIS DEVICE", scope: "local" });
  });

  it("maps RFC-1918 IPs to <ip> + LAN + local", () => {
    expect(egressFor("192.168.1.43")).toEqual({ label: "192.168.1.43 · LAN", scope: "local" });
    expect(egressFor("10.0.0.5")).toEqual({ label: "10.0.0.5 · LAN", scope: "local" });
    expect(egressFor("172.16.0.1")).toEqual({ label: "172.16.0.1 · LAN", scope: "local" });
  });

  it("maps cloud hosts to <host> + cloud", () => {
    expect(egressFor("api.anthropic.com")).toEqual({ label: "api.anthropic.com", scope: "cloud" });
    expect(egressFor("openrouter.ai")).toEqual({ label: "openrouter.ai", scope: "cloud" });
  });

  it("never returns LOCAL", () => {
    for (const host of ["local", "LOCAL", "this_device", "192.168.1.43", "api.anthropic.com"]) {
      expect(egressFor(host).label).not.toBe("LOCAL");
    }
  });
});

/* ── HS-174-04: egressForEvent — remote origin badge ── */

describe("egressForEvent", () => {
  it("returns REMOTE + caller IP with scope remote for origin=remote", () => {
    const result = egressForEvent({ origin: "remote", caller: "100.64.0.5" });
    expect(result).toEqual({ label: "REMOTE · 100.64.0.5", scope: "remote" });
  });

  it("returns REMOTE + caller IP for a tailnet address", () => {
    const result = egressForEvent({ origin: "remote", caller: "192.168.1.43" });
    expect(result).toEqual({ label: "REMOTE · 192.168.1.43", scope: "remote" });
  });

  it("falls through to egressFor for local origin", () => {
    const result = egressForEvent({ origin: "local", host: "local" });
    expect(result).toEqual({ label: "THIS DEVICE", scope: "local" });
  });

  it("falls through to egressFor when origin is missing", () => {
    const result = egressForEvent({ host: "api.anthropic.com" });
    expect(result).toEqual({ label: "api.anthropic.com", scope: "cloud" });
  });

  it("falls through to egressFor when origin is null", () => {
    const result = egressForEvent({ origin: null, caller: null, host: null });
    expect(result).toEqual({ label: "", scope: undefined });
  });

  it("the time is NEVER inside the label", () => {
    const result = egressForEvent({ origin: "remote", caller: "100.64.0.5" });
    expect(result.label).not.toMatch(/\d{2}:\d{2}/);
  });
});

/* ── HS-174-04: receiptLabel — human grammar for pipeline methods ── */

describe("receiptLabel", () => {
  it("maps run_sweep to SWEEP", () => {
    expect(receiptLabel({ op: "run_sweep" })).toBe("SWEEP");
  });

  it("maps project_run_steward to STEWARD RUN", () => {
    expect(receiptLabel({ op: "project_run_steward" })).toBe("STEWARD RUN");
  });

  it("maps list_meetings to READ MEETINGS", () => {
    expect(receiptLabel({ op: "list_meetings" })).toBe("READ MEETINGS");
  });

  it("maps get_delta to READ DELTA", () => {
    expect(receiptLabel({ op: "get_delta" })).toBe("READ DELTA");
  });

  it("maps room to READ", () => {
    expect(receiptLabel({ op: "room" })).toBe("READ");
  });

  it("unmapped op renders in caps with spaces", () => {
    expect(receiptLabel({ op: "evaluate_due" })).toBe("EVALUATE DUE");
  });

  it("strips Service. from title when op is missing", () => {
    expect(receiptLabel({ title: "ProjectService.list_meetings" })).toBe("LIST MEETINGS");
  });

  it("never contains Service.", () => {
    for (const input of [
      { op: "run_sweep", title: "HeartbeatService.run_sweep" },
      { op: "list_meetings", title: "ProjectService.list_meetings" },
      { title: "StewardService.project_run_steward" },
    ]) {
      expect(receiptLabel(input)).not.toContain("Service.");
      expect(receiptLabel(input)).not.toContain("Service");
    }
  });
});
