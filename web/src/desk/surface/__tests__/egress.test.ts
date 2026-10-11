// HS-172-03 + HS-174-04 — egressFor + egressForEvent: the egress-label + scope mapper.
import { describe, expect, it } from "vitest";
import { bareHost, egressFor, egressForEvent, hostPlace, isLoopbackHost, receiptLabel } from "../egress";

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

describe("hostPlace — the one helper for host words (PHILO-17 U16)", () => {
  it("loopback and the wire words for here are this Mac", () => {
    for (const host of ["127.0.0.1", "http://127.0.0.1:8899/v1", "localhost", "http://localhost:11434", "::1", "http://[::1]:8080/v1", "local", "same_device", "THIS DEVICE"]) {
      expect(hostPlace(host)).toEqual({ place: "mac", host: "", words: "this Mac" });
    }
    // A loopback server added as a network engine is still this Mac.
    expect(hostPlace("http://127.0.0.1:8899/v1", "lan").words).toBe("this Mac");
  });

  it("only what the transport pins as loopback is this Mac (loopback_http.py; Astra r1 M1)", () => {
    for (const host of ["dev.localhost", "http://dev.localhost:8080/v1", "0.0.0.0", "http://0.0.0.0:8080", "127.0.0.256", "::"]) {
      expect(hostPlace(host).place, host).not.toBe("mac");
      expect(egressFor(host).label, host).not.toBe("THIS DEVICE");
    }
    // A host the transport does not pin is never this Mac, whatever the kind says.
    expect(hostPlace("http://dev.localhost:8080/v1", "local").place).not.toBe("mac");
    expect(hostPlace("127.1.2.3").place).toBe("mac");
    expect(hostPlace("0:0:0:0:0:0:0:1").place).toBe("mac");
  });

  it("parser parity: every spelling is classified as holdspeak/loopback_http.py classifies it (Astra r2 M3)", () => {
    // The right-hand values are `is_loopback_engine_host(h)` from the backend
    // (Python 3.14), printed on 2026-10-10: strict dotted quad, no leading
    // zeros, valid IPv6 loopback only, a scope id allowed, no trailing dot.
    const backend: [string, boolean][] = [
      ["127.00.0.1", false], [":::1", false], ["::1", true], ["0:0:0:0:0:0:0:1", true], ["::0:1", true],
      ["0::1", true], ["127.1.2.3", true], ["::ffff:127.0.0.1", true], ["::ffff:7f00:1", true], ["0000::1", true],
      ["00000::1", false], ["127.0.0.1.", false], ["localhost.", false], ["LOCALHOST", true], ["[::1]", true],
      ["1::1", false], ["::", false], ["0.0.0.0", false], ["127.0.0.256", false], ["127.0.0", false],
      ["dev.localhost", false], ["::1%lo0", true], ["1:2:3:4:5:6:7:8:9", false], ["::ffff:10.0.0.1", false],
      ["127.0.0.01", false], ["0127.0.0.1", false], ["::1:", false], ["1:0:0:0:0:0:0:1", false],
      ["0:0:0:0:0:0:0:0:1", false],
    ];
    for (const [host, loopback] of backend) expect(isLoopbackHost(host), host).toBe(loopback);
  });

  it("classifies the RAW spelling, before any URL normalisation (Astra r2 M3)", () => {
    expect(bareHost("http://127.0.0.1.:8080/v1")).toBe("127.0.0.1.");
    expect(bareHost("http://u:p@[::1]:8/x")).toBe("::1");
    expect(bareHost("http://127.00.0.1:8080/v1")).toBe("127.00.0.1");
    // Lead, badge and attempt all read hostPlace: these are never this Mac.
    for (const url of ["http://127.0.0.1.:8080/v1", "http://localhost.:11434", "http://127.00.0.1:8080", "http://[:::1]:8080"]) {
      expect(hostPlace(url).place, url).not.toBe("mac");
      expect(hostPlace(url, "local").place, url).not.toBe("mac");
      expect(egressFor(bareHost(url)).label, url).not.toBe("THIS DEVICE");
    }
    // The backend calls a trailing-dot loopback the private network.
    expect(hostPlace("http://127.0.0.1.:8080/v1").place).toBe("lan");
  });

  it("a server on his network is its host name or IP", () => {
    expect(hostPlace("http://192.168.1.43:8080/v1")).toEqual({ place: "lan", host: "192.168.1.43", words: "192.168.1.43" });
    expect(hostPlace("studio.local", "lan")).toEqual({ place: "lan", host: "studio.local", words: "studio.local" });
    expect(hostPlace("", "lan").words).toBe("your network");
  });

  it("a cloud engine is its provider's host", () => {
    expect(hostPlace("openrouter.ai", "cloud")).toEqual({ place: "cloud", host: "openrouter.ai", words: "openrouter.ai" });
    expect(hostPlace("https://api.openai.com/v1")).toEqual({ place: "cloud", host: "api.openai.com", words: "api.openai.com" });
  });

  it("egressFor reads it: 127.0.0.1 is THIS DEVICE, never a cloud host", () => {
    expect(egressFor("127.0.0.1")).toEqual({ label: "THIS DEVICE", scope: "local" });
    expect(egressFor("localhost")).toEqual({ label: "THIS DEVICE", scope: "local" });
  });
});

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
