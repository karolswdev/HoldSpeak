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
import { useState, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WingSlotContext } from "../../../desk/surface/wings";

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

/* The wing strip (and with it the gear door) lives in the HOSTING
 * window's head: the core publishes it through `WingSlotContext`
 * (`desk/surface/wings.tsx:45`). A bare `render(<LiveCore />)` has no
 * host, so the door cannot be pressed and the door face is unreachable —
 * which is why the first round of this fence never saw the gear door's
 * six zeros. This host is the smallest thing that provides the slot. */
function WindowHost({ children }: { children: ReactNode }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <WingSlotContext.Provider value={setWings}>
      <div data-testid="window-head">{wings}</div>
      {children}
    </WingSlotContext.Provider>
  );
}

/** Press the Live window's configuration door. */
async function openDoor() {
  const gear = screen.getByRole("button", { name: "Configure meeting" });
  await act(async () => {
    gear.click();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

async function mount() {
  const view = render(
    <WindowHost>
      <LiveCore />
    </WindowHost>,
  );
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

/* Astra's counsel on #599, finding 2: the touched Live flow was not
 * finished. `live-door-summary-393.png` showed SIX counters of zero in the
 * gear door's queue section, the Summary could still print `0 action
 * items`, and the facts row repeated the footer receipt's state word. */
describe("the Live gear door counts nothing to zero (A.8)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    mocks.apiFetch.mockResolvedValue({});
  });

  it("names its run-state section Summary, never Intelligence", async () => {
    await mount();
    await openDoor();
    const labels = [...document.querySelectorAll("h3")].map(
      (head) => head.textContent ?? "",
    );
    expect(labels).toContain("Summary");
    expect(labels).not.toContain("Intelligence");
    expect(document.body.textContent ?? "").not.toMatch(/Intelligence/);
  });

  it("says the true thing instead of six zeros on an idle queue", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) =>
      String(path).startsWith("/api/plugin-jobs/summary")
        ? ({
            total_jobs: 0,
            queued_jobs: 0,
            running_jobs: 0,
            failed_jobs: 0,
            queued_due_jobs: 0,
            scheduled_retry_jobs: 0,
          } as never)
        : ({} as never),
    );
    await mount();
    await openDoor();
    const text = document.body.textContent ?? "";
    expect(text).toContain("No jobs waiting");
    expect(text).not.toMatch(/\b0\b/);
  });

  it("says it on the REAL idle wire, which carries a null next retry", async () => {
    // `holdspeak/services/plugin_job_service.py:29` — the hub always
    // sends `next_retry_at`, null when nothing is scheduled. Counted as a
    // fact it drew an empty section (header + lone verb) on the shot.
    mocks.apiFetch.mockImplementation(async (path: string) =>
      String(path).startsWith("/api/plugin-jobs/summary")
        ? ({
            total_jobs: 0,
            queued_jobs: 0,
            running_jobs: 0,
            failed_jobs: 0,
            queued_due_jobs: 0,
            scheduled_retry_jobs: 0,
            next_retry_at: null,
          } as never)
        : ({} as never),
    );
    await mount();
    await openDoor();
    expect(document.body.textContent ?? "").toContain("No jobs waiting");
  });

  it("still counts the jobs that exist", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) =>
      String(path).startsWith("/api/plugin-jobs/summary")
        ? ({ total_jobs: 2, queued_jobs: 0, failed_jobs: 1 } as never)
        : ({} as never),
    );
    await mount();
    await openDoor();
    const facts = [...document.querySelectorAll(".surface-facts div")].map(
      (row) => row.textContent ?? "",
    );
    expect(facts).toEqual(["total jobs2", "failed jobs1"]);
  });
});

describe("the Summary never counts its action items to zero (A.8)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    mocks.apiFetch.mockResolvedValue({});
  });

  it("omits the line when a final Summary has nothing to do", async () => {
    await mount();
    emit("intel_complete", {
      summary: "Nothing was assigned.",
      topics: [],
      action_items: [],
      final: true,
    });
    await screen.findByText("Nothing was assigned.");
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(/0 action items/);
    expect(text).toContain("final");
  });

  it("counts the action items that exist", async () => {
    await mount();
    emit("intel_complete", {
      summary: "Two things to do.",
      topics: [],
      action_items: [{ task: "a" }, { task: "b" }],
      final: true,
    });
    await screen.findByText("Two things to do.");
    expect(document.body.textContent ?? "").toContain("2 action items · final");
  });
});

describe("Live's row and its receipt hold different facts (M6)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    mocks.apiFetch.mockResolvedValue({});
  });

  it("never says the same state word twice", async () => {
    await mount();
    const row = document.querySelector(".surface-fact-line")?.textContent ?? "";
    const receipt =
      document.querySelector(".surface-footer-receipt-line")?.textContent ?? "";
    expect(row).toBe("Link · connected");
    expect(receipt).toBe("READY");
    expect(row.toUpperCase()).not.toContain(receipt.toUpperCase());
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
