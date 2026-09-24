/* PHILO-4-01 — Generate is always reachable (ratified 2026-09-23, round six).
 *
 * The defect: the BRIEF section drew Ack and Defer but no Generate while a
 * day-one row was untriaged (`BriefSection` had no head verbs), so the
 * morning needed a detour: Ack every old row, then `Generate again`. The
 * ratified canvas (assets/story-01-canvas): the badge and the library
 * `Generate` Button in the head of EVERY branch, disabled only while a read
 * or a generation is open; `GENERATING…` in the status slot; a failed
 * generation says `BRIEF DID NOT GENERATE · <cause>` with no Retry (the
 * enabled Generate is the recovery); the read failure keeps its Retry; the
 * badge, the caption and the receipt survive every transition; Generate
 * never touches the old rows' triage. This drives the REAL Chair with a
 * mocked apiFetch.
 */
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const DAY1 = {
  id: "brief-day1",
  headline: "1 decision waiting.",
  generated_at: "2026-09-23T17:40:00",
  is_empty: false,
  period_label: "SEP 21 – 23",
  generated_label: "GENERATED SEP 23 17:40",
  shelf: {},
  sections: {
    decisions: [{ id: "d1-item", section: "decisions", text: "Review decision: Adopt the one desk bus", priority: 200 }],
  },
};

const DAY2 = {
  id: "brief-day2",
  headline: "2 decisions waiting.",
  generated_at: "2026-09-24T08:02:00",
  is_empty: false,
  period_label: "SEP 21 – 24",
  generated_label: "GENERATED SEP 24 08:02",
  shelf: {},
  sections: {
    decisions: [
      { id: "d2-new", section: "decisions", text: "Review decision: Keep summary retrieval on the local desk", priority: 200 },
      { id: "d2-old", section: "decisions", text: "Review decision: Adopt the one desk bus", priority: 200 },
    ],
  },
};

/** Each GET /api/brief/latest takes the next answer; each POST generate too. */
let latestAnswers: Array<() => Promise<unknown>> = [];
let generateAnswers: Array<() => Promise<unknown>> = [];
let calls: string[] = [];

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
    const url = String(path);
    const method = (init as { method?: string } | undefined)?.method ?? "GET";
    calls.push(`${method} ${url}`);
    if (url === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 } as never;
    if (url.startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    if (url.startsWith("/api/brief/latest")) {
      const next = latestAnswers.shift() ?? (async () => null);
      return (await next()) as never;
    }
    if (url === "/api/brief/generate" && method === "POST") {
      const next = generateAnswers.shift() ?? (async () => DAY2);
      return (await next()) as never;
    }
    return null as never;
  });
}

/** A promise the test resolves or rejects by hand: the generation is open. */
function pending<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const generateButton = () => screen.getByTestId("arrival-brief-generate") as HTMLButtonElement;

/** The head carries the badge, then Generate, both inside the section head. */
function expectHeadVerbs() {
  const section = screen.getByTestId("arrival-brief");
  const head = section.querySelector(".surface-section-head");
  expect(head).toBeTruthy();
  const chip = head!.querySelector(".gadget-chip-egress");
  const verb = within(head as HTMLElement).getByTestId("arrival-brief-generate");
  expect(chip?.textContent).toBe("THIS DEVICE");
  expect(verb.textContent).toBe("Generate");
  // badge BEFORE the verb (UX-CANON A.9)
  expect(chip!.compareDocumentPosition(verb) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
}

/** Every <button> in the section is the library Button (no raw button). */
function expectOnlyLibraryButtons() {
  const section = screen.getByTestId("arrival-brief");
  const buttons = Array.from(section.querySelectorAll("button"));
  expect(buttons.length).toBeGreaterThan(0);
  for (const button of buttons) expect(button.classList.contains("btn")).toBe(true);
}

describe("PHILO-4-01: Generate is always reachable on the Arrival", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    latestAnswers = [];
    generateAnswers = [];
    calls = [];
    wire();
  });

  it("draws Generate in the head while a day-one row is untriaged", async () => {
    latestAnswers = [async () => DAY1];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-row");
    expectHeadVerbs();
    expect(generateButton().disabled).toBe(false);
    expect(screen.getAllByTestId("arrival-brief-row")).toHaveLength(1);
    expectOnlyLibraryButtons();
  });

  it("disables Generate while the read is open", async () => {
    latestAnswers = [() => new Promise(() => undefined)];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-loading");
    expectHeadVerbs();
    expect(generateButton().disabled).toBe(true);
  });

  it("says GENERATING… in the status slot and disables Generate while it runs", async () => {
    latestAnswers = [async () => DAY1];
    const open = pending<unknown>();
    generateAnswers = [() => open.promise];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-row");
    const captionBefore = screen.getByTestId("arrival-brief-date").textContent;

    await act(async () => {
      generateButton().click();
    });
    const generating = screen.getByTestId("arrival-brief-generating");
    expect(generating.textContent).toBe("GENERATING…");
    expect(generating.classList.contains("surface-receipt-line")).toBe(true);
    expect(generateButton().disabled).toBe(true);
    expect(generateButton().textContent).toBe("Generate");
    expect(screen.queryByText("Generating...")).toBeNull();
    // the rows, the badge and the caption stay while it runs
    expect(screen.getAllByTestId("arrival-brief-row")).toHaveLength(1);
    expectHeadVerbs();
    expect(screen.getByTestId("arrival-brief-date").textContent).toBe(captionBefore);

    await act(async () => {
      open.resolve(DAY2);
    });
    await waitFor(() => expect(screen.queryByTestId("arrival-brief-generating")).toBeNull());
    expect(generateButton().disabled).toBe(false);
  });

  it("names a failed generation with no Retry and Generate enabled", async () => {
    latestAnswers = [async () => DAY1];
    generateAnswers = [
      async () => {
        throw new ApiError(500, "boom", null);
      },
    ];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-row");
    const captionBefore = screen.getByTestId("arrival-brief-date").textContent;

    await act(async () => {
      generateButton().click();
    });
    const failed = await screen.findByTestId("arrival-brief-generate-failed");
    expect(failed.textContent).toBe("BRIEF DID NOT GENERATE · HTTP 500");
    expect(failed.getAttribute("data-tone")).toBe("danger");
    expect(failed.classList.contains("surface-receipt-line")).toBe(true);
    const section = screen.getByTestId("arrival-brief");
    expect(within(section).queryByRole("button", { name: "Retry" })).toBeNull();
    expect(screen.queryByTestId("arrival-brief-retry")).toBeNull();
    expect(generateButton().disabled).toBe(false);
    // the day-one rows and the caption do not change
    expect(screen.getAllByTestId("arrival-brief-row")).toHaveLength(1);
    expect(screen.getByTestId("arrival-brief-date").textContent).toBe(captionBefore);
    expectHeadVerbs();
    expectOnlyLibraryButtons();
  });

  it("says NO ANSWER when the generation got no response", async () => {
    latestAnswers = [async () => DAY1];
    generateAnswers = [
      async () => {
        throw new TypeError("Failed to fetch");
      },
    ];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-row");
    await act(async () => {
      generateButton().click();
    });
    expect((await screen.findByTestId("arrival-brief-generate-failed")).textContent).toBe(
      "BRIEF DID NOT GENERATE · NO ANSWER",
    );
  });

  it("keeps Retry on a failed read, with Generate in the head", async () => {
    latestAnswers = [
      async () => {
        throw new ApiError(500, "boom", null);
      },
    ];
    const open = pending<unknown>();
    generateAnswers = [() => open.promise];
    render(<ChairHome />);
    const failed = await screen.findByTestId("arrival-brief-load-failed");
    expect(failed.textContent).toBe("BRIEF DID NOT LOAD · HTTP 500");
    expect(screen.getByTestId("arrival-brief-retry").textContent).toBe("Retry");
    expectHeadVerbs();
    expect(generateButton().disabled).toBe(false);
    expectOnlyLibraryButtons();

    // board 3c: Generate from the read failure; GENERATING… takes the slot
    await act(async () => {
      generateButton().click();
    });
    expect(screen.getByTestId("arrival-brief-generating").textContent).toBe("GENERATING…");
    expect(screen.queryByTestId("arrival-brief-load-failed")).toBeNull();
    expect(screen.queryByTestId("arrival-brief-retry")).toBeNull();
    expect(generateButton().disabled).toBe(true);

    await act(async () => {
      open.resolve(DAY2);
    });
    await screen.findByTestId("arrival-brief-receipt");
    expect(screen.getAllByTestId("arrival-brief-row")).toHaveLength(2);
    expect(screen.queryByTestId("arrival-brief-load-failed")).toBeNull();
  });

  it("keeps the badge, the caption and the receipt through every transition", async () => {
    latestAnswers = [async () => DAY1];
    const second = pending<unknown>();
    generateAnswers = [
      async () => DAY2,
      () => second.promise,
    ];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-row");

    // success: the next-day brief, its caption and the receipt
    await act(async () => {
      generateButton().click();
    });
    const receipt = await screen.findByTestId("arrival-brief-receipt");
    const receiptText = receipt.textContent;
    expect(receiptText).toMatch(/^Brief ready · 2 items · /);
    expect(screen.getByTestId("arrival-brief-date").textContent).toBe("SEP 21 – 24 · GENERATED SEP 24 08:02");
    expectHeadVerbs();

    // open: nothing moves but the status line
    await act(async () => {
      generateButton().click();
    });
    expect(screen.getByTestId("arrival-brief-generating").textContent).toBe("GENERATING…");
    expect(screen.getByTestId("arrival-brief-receipt").textContent).toBe(receiptText);
    expect(screen.getByTestId("arrival-brief-date").textContent).toBe("SEP 21 – 24 · GENERATED SEP 24 08:02");
    expectHeadVerbs();

    // failure: the same, with the failure line
    await act(async () => {
      second.reject(new ApiError(500, "boom", null));
    });
    await screen.findByTestId("arrival-brief-generate-failed");
    expect(screen.getByTestId("arrival-brief-receipt").textContent).toBe(receiptText);
    expect(screen.getByTestId("arrival-brief-date").textContent).toBe("SEP 21 – 24 · GENERATED SEP 24 08:02");
    expectHeadVerbs();
    expect(generateButton().disabled).toBe(false);
  });

  it("never touches the old rows' triage when it generates", async () => {
    latestAnswers = [async () => DAY1];
    generateAnswers = [async () => DAY2];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-row");

    await act(async () => {
      generateButton().click();
    });
    await screen.findByTestId("arrival-brief-receipt");
    // the triage route was never called: nothing was acknowledged or deferred
    expect(calls.filter((call) => call.includes("/shelf"))).toEqual([]);
    expect(calls.filter((call) => call.startsWith("POST "))).toEqual(["POST /api/brief/generate"]);
    // the next brief's rows arrive untriaged
    expect(screen.getAllByTestId("arrival-brief-row").map((row) => row.textContent)).toEqual([
      expect.stringContaining("Keep summary retrieval on the local desk"),
      expect.stringContaining("Adopt the one desk bus"),
    ]);
  });

  it("draws Generate on the quiet branch (every row triaged), not Generate again", async () => {
    latestAnswers = [async () => ({ ...DAY1, shelf: { "d1-item": "acknowledged" } })];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-headline");
    expectHeadVerbs();
    expect(screen.queryByText("Generate again")).toBeNull();
  });

  it("puts a failed generation in the place of No brief yet", async () => {
    latestAnswers = [async () => null];
    generateAnswers = [
      async () => {
        throw new ApiError(500, "boom", null);
      },
    ];
    render(<ChairHome />);
    await screen.findByText("No brief yet");
    expectHeadVerbs();
    await act(async () => {
      generateButton().click();
    });
    expect((await screen.findByTestId("arrival-brief-generate-failed")).textContent).toBe(
      "BRIEF DID NOT GENERATE · HTTP 500",
    );
    expect(screen.queryByText("No brief yet")).toBeNull();
    expect(screen.queryByTestId("arrival-brief-retry")).toBeNull();
    expect(generateButton().disabled).toBe(false);
  });
});
