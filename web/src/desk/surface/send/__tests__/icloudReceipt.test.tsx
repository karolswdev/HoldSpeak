// Astra's review of #864, defect 2: a prepared send to the built-in HoldSpeak
// folder in an iCloud Drive Documents folder keeps ICLOUD on every receipt:
// the waiting row, the terminal result and the history row. The answers are
// the REAL hub's, recorded from a real prepare + send
// (fixtures/icloud-prepared-send.json: tests/unit/_philo10_send.py rig,
// isolated HOME, the detector's xattr boundary answering for its Documents).

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import fixture from "./fixtures/icloud-prepared-send.json";

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../lib/api")>("../../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../pages/cores/connections/api")>("../../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import { SendWells, resetSendStore } from "..";

type Fx = typeof fixture;
const plain = (): Fx => {
  const f = JSON.parse(JSON.stringify(fixture)) as Fx;
  // Its own document (the send store keeps what it knows per document).
  f.ref = `${f.ref}-plain`;
  for (const s of [...f.before.sends, f.after.send]) { s.document_ref = f.ref; s.id = `${s.id}-plain`; }
  for (const d of f.destinations.destinations) { delete (d.target as Record<string, unknown>).cloud; d.badge = "local"; d.synced = false; }
  for (const s of [...f.before.sends, f.after.send]) {
    delete (s.target as Record<string, unknown>).cloud; (s as { egress: unknown }).egress = null; s.badge = "local";
    if (s.proof) delete (s.proof as Record<string, unknown>).egress;
  }
  return f;
};

function wire(f: Fx) {
  let sent = false;
  apiFetch.mockImplementation((path: string, init: RequestInit = {}) => {
    if (path.startsWith("/api/channels/destinations")) return Promise.resolve(f.destinations);
    if (path === "/api/channels/send" && init.method === "POST") { sent = true; return Promise.resolve(f.after); }
    if (path.startsWith("/api/channels/sends")) return Promise.resolve(sent ? { sends: [f.after.send] } : f.before);
    return Promise.reject(new Error(`unrouted ${path}`));
  });
}

async function pressPrepared(f: Fx) {
  wire(f);
  render(<SendWells doc={{ ref: f.ref, title: "Review update", label: "Update" }} />);
  const before = (await screen.findByTestId("prepared-row")).textContent ?? "";  // read now: the row re-renders as its result
  fireEvent.click(await screen.findByTestId("prepared-send"));
  const after = await screen.findByTestId("prepared-result");
  const history = await screen.findByTestId("history-row");
  return { before, after: after.textContent ?? "", history: history.textContent ?? "" };
}

beforeEach(() => { resetSendStore(); apiFetch.mockReset(); });
afterEach(() => cleanup());

describe("a prepared send to the iCloud HoldSpeak folder", () => {
  it("names ICLOUD on the waiting row, the terminal result and the history row", async () => {
    expect(fixture.after.send.proof.egress).toBe("icloud");
    const t = await pressPrepared(fixture);
    expect(t.before).toContain("ICLOUD");
    expect(t.after).toContain("SAVED");
    expect(t.after).toContain("ICLOUD");
    expect(t.history).toContain("ICLOUD");
  });

  it("a plain Documents folder: THIS DEVICE while waiting, no ICLOUD after", async () => {
    const t = await pressPrepared(plain());
    expect(t.before).toContain("THIS DEVICE");
    expect(t.after).not.toContain("ICLOUD");
    expect(t.history).not.toContain("ICLOUD");
  });
});
