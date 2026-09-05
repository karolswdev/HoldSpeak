// HS-172-03 — egressFor: the one egress-label + scope mapper.
import { describe, expect, it } from "vitest";
import { egressFor } from "../egress";

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
