/* HS-202-04 — one name per thing on the Live face, and a receipt that
 * never restates the row above it.
 *
 * Doctrine (docs/internal/SURFACE-INVENTORY-2026-09-20.md §3.6 and
 * `surface-inventory-2026-09-20/02-coherence-astra.md` F06 and F21;
 * Constitution tenet 4 = ASD-STE100; UX-CANON A.7):
 *
 *  - F06: a meeting result is `Summary` on the record and `Intelligence`
 *    on Live. The registry already ruled on it — "Every face says Summary"
 *    (`docs/product-language.json:23`) — and Live disobeyed its own
 *    registry. `Intelligence` stays the name of the durable ledger
 *    application; it is never the name of a meeting's result.
 *  - F21: `SEG` is an abbreviation nobody defined on a face. HS-201-06
 *    already spelled it out in the recovery slab
 *    (`meetings/MeetingIntelRecovery.tsx:60`); Live's footer kept it.
 *  - M6: the same fact twice on one screen. Live printed the running
 *    clock in the facts row AND in the footer receipt, and the segment
 *    count in three places (facts row, stream head, footer). One fact,
 *    one place: the host row states where it runs, the stream head counts
 *    the segments, the footer receipt carries the clock.
 */
import { render, screen, waitFor, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

type Frame = { type: string; data: unknown };

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
}));

function subscribe(type: string, listener: (frame: Frame) => void) {
  const set = mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
  set.add(listener);
  mocks.listeners.set(type, set);
  return () => set.delete(listener);
}

function emit(type: string, data: unknown) {
  act(() => {
    for (const listener of [...(mocks.listeners.get(type) ?? [])])
      listener({ type, data });
    for (const listener of [...(mocks.listeners.get("*") ?? [])])
      listener({ type, data });
  });
}

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) =>
    error instanceof Error ? error.message : "Request failed",
}));

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));

import { LiveCore } from "../LiveCore";

async function mount() {
  const view = render(<LiveCore />);
  await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
  /* `/api/state` answers with a fresh object, and the face resets its
   * segment list from that answer (`LiveCore.tsx:135-137`). A frame emitted
   * before the answer lands is wiped by it, so settle the resources first. */
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  return view;
}

describe("Live calls the meeting result a Summary (F06)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    mocks.apiFetch.mockResolvedValue({});
  });

  it("labels the result section Summary", async () => {
    await mount();
    emit("intel_complete", {
      summary: "Shipping is on for Friday.",
      topics: ["release"],
      action_items: [{ task: "cut the branch" }],
      final: true,
    });
    await screen.findByText("Shipping is on for Friday.");
    expect(screen.getByText("Summary")).toBeInTheDocument();
  });

  it("never says Intelligence on the Live face", async () => {
    await mount();
    emit("intel_complete", {
      summary: "Shipping is on for Friday.",
      topics: ["release"],
      action_items: [],
      final: true,
    });
    await screen.findByText("Shipping is on for Friday.");
    expect(document.body.textContent ?? "").not.toMatch(/Intelligence/);
  });
});

describe("Live spells its words and states each fact once (F21, M6)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    mocks.apiFetch.mockResolvedValue({});
  });

  it("never renders the undefined abbreviation SEG", async () => {
    await mount();
    emit("segment", { id: 1, text: "first line", timestamp: "00:00:01" });
    emit("segment", { id: 2, text: "second line", timestamp: "00:00:05" });
    await screen.findByText("first line");
    expect(document.body.textContent ?? "").not.toMatch(/\bSEG\b/);
  });

  it("states the segment count exactly once", async () => {
    await mount();
    emit("segment", { id: 1, text: "first line", timestamp: "00:00:01" });
    emit("segment", { id: 2, text: "second line", timestamp: "00:00:05" });
    await screen.findByText("first line");
    // The stream head owns the count (`Surface.tsx:686-692` draws the
    // number and its noun as two elements).
    const heads = [...document.querySelectorAll(".surface-stream-head")].map(
      (head) => head.textContent ?? "",
    );
    expect(heads).toEqual(["2segments"]);
    // …and nothing else on the face counts them a second time.
    const elsewhere = (document.body.textContent ?? "").replace("2segments", "");
    expect(elsewhere).not.toMatch(/2 ?segments?/i);
  });
});
