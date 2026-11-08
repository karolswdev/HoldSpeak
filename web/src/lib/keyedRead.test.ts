import { afterEach, describe, expect, it, vi } from "vitest";
import { hydrateBuilderTools, useBuilderTools } from "../desk/builderTools";
import { phoneIsOn } from "../desk/calls/phoneApi";
import { writeCallsSetting } from "../desk/calls/api";
import { readHubSettings, readPeopleReadiness } from "./keyedRead";

// Desk open (2026-11-08): one GET per resource for every reader.
function stubHub(answers: Record<string, unknown>) {
  const calls: string[] = [];
  const fetcher = vi.fn(async (input: string, init: RequestInit = {}) => {
    calls.push(`${init.method ?? "GET"} ${input}`);
    const body = answers[`${init.method ?? "GET"} ${input}`] ?? answers[input] ?? {};
    return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetcher);
  return calls;
}

describe("readKeyed", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("reads the settings once for the builder tools, the phone and the mascot at open", async () => {
    const calls = stubHub({ "/api/settings": { ui: { builder_tools: true }, calls: { phone_on: true } } });
    hydrateBuilderTools();
    const on = await phoneIsOn();
    await vi.waitFor(() => expect(useBuilderTools.getState().on).toBe(true));
    // A reader that comes after the answer takes it (the mascot's read).
    await readHubSettings();
    expect(on).toBe(true);
    expect(calls).toEqual(["GET /api/settings"]);
  });

  it("reads the settings again after a write the hub accepted", async () => {
    const calls = stubHub({
      "GET /api/settings": { calls: { phone_on: false } },
      "PUT /api/settings": { settings: { calls: { phone_on: true } } },
    });
    expect(await phoneIsOn()).toBe(false);
    await writeCallsSetting("phone_on", true);
    await phoneIsOn();
    expect(calls).toEqual(["GET /api/settings", "PUT /api/settings", "GET /api/settings"]);
  });

  it("a fresh read after a change frame reads again, and joins a read that is out", async () => {
    const calls = stubHub({ "/api/people/readiness": { state: "ready" } });
    await readPeopleReadiness();
    await readPeopleReadiness();
    expect(calls).toEqual(["GET /api/people/readiness"]);
    await Promise.all([readPeopleReadiness({ fresh: true }), readPeopleReadiness({ fresh: true })]);
    expect(calls).toEqual(["GET /api/people/readiness", "GET /api/people/readiness"]);
  });
});
