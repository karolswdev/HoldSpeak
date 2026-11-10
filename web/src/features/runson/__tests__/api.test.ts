// The LAN answers are recorded from SetupService.scan_lan over the real
// discovery producer with injected interfaces and a pure probe (no network).
import { afterEach, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { discoverLan } from "../api";
import recorded from "./fixtures/setup-lan.recorded.json";

vi.mock("../../../lib/api", () => ({ apiFetch: vi.fn() }));
afterEach(() => vi.resetAllMocks());

it("reads the one Setup scan and keeps the found engine", async () => {
  vi.mocked(apiFetch).mockResolvedValue(structuredClone(recorded.found));
  const answer = await discoverLan();
  expect(apiFetch).toHaveBeenCalledExactlyOnceWith("/api/setup/lan", { method: "POST", json: {} });
  expect(answer.engines[0]).toMatchObject({ name: "qwen3.8-27b", host: "192.168.1.43", found: true });
  expect(answer.hostsChecked).toBe(recorded.found.hostsChecked);
  expect(answer.unavailable).toBe(false);
});

it("keeps the scanner's failure reason", async () => {
  vi.mocked(apiFetch).mockResolvedValue(structuredClone(recorded.unavailable));
  expect(await discoverLan()).toMatchObject({
    engines: [], unavailable: true, reason: recorded.unavailable.reason, hostsChecked: 0,
  });
});

it("reports a disabled scan and leaves a failed request available for retry", async () => {
  vi.mocked(apiFetch).mockResolvedValueOnce({ rows: [], disabled: true });
  expect(await discoverLan()).toMatchObject({ engines: [], unavailable: true, reason: "LAN scan is off" });
  vi.mocked(apiFetch).mockRejectedValueOnce(new Error("scan failed"));
  await expect(discoverLan()).rejects.toThrow("scan failed");
  vi.mocked(apiFetch).mockResolvedValueOnce(structuredClone(recorded.found));
  expect((await discoverLan()).engines[0].name).toBe("qwen3.8-27b");
});
