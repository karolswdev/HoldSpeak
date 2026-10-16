// PHILO-6-02 round 2 — the rendered brief tells a failed operation once, as a
// failure, in product words (Astra's check on built, findings 1 and 5).
//
// The fixture is the REAL producer's brief
// (tests/unit/test_philo6_02_round2_outcome_words.py writes it and holds it
// equal to the wire): five real observed calls, each FAILED — a desk decision
// record of a missing decision, a refused summary request, a brief triage of
// an unknown item, a lifecycle transition and a desk decision read of the
// missing decision. Before the repair the Arrival and the Brief view showed
// `Decision recorded` and `Summary requested` beside their failures, and
// `Primitive: get decision did not complete`.
import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));

import brief from "./fixtures/philo6/brief-failed-ops.json";
import { ChairHome } from "../ChairHome";
import { BriefView } from "../../pullouts/views/BriefView";
import { openChairWindows } from "./fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

const SUCCESS = /Decision recorded|Summary requested|Brief triage saved|Decision changed|Decision loaded/;
const IMPLEMENTATION = /Primitive|[A-Z][A-Za-z]*Service\b|[a-z]_[a-z]/;

describe("PHILO-6-02 round 2: a failed operation never reads as a success", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    // The fixture is the real producer's (stale under its frozen clock); the
    // view makes it again once, and the hub answers that POST with the brief
    // it made (PHILO-17, Astra r2: a truthful response, never null).
    mocks.apiFetch.mockImplementation(async (path: string) =>
      String(path) === "/api/brief/latest"
        ? brief
        : String(path) === "/api/brief/generate"
          ? { ...brief, stale: false }
          : null,
    );
  });

  it("the Arrival BRIEF section shows the failures and no success line", async () => {
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-receipt");
    const section = screen.getByTestId("arrival-brief");
    const text = section.textContent ?? "";
    expect(text).not.toMatch(SUCCESS);
    expect(text).not.toMatch(IMPLEMENTATION);
    // The rows not triaged yet: the failures, the recorded meeting, and the
    // two members of the one needs-you rule the real producer now writes
    // (no engine; the failed summary). The fold holds the rest. The head
    // says the hub's one needs-you number (none mocked here: no count).
    const shown = screen.getAllByTestId("arrival-brief-row").length;
    const folded = Number(screen.queryByTestId("arrival-brief-more")?.textContent?.match(/^(\d+) more$/)?.[1] ?? 0);
    expect(shown + folded).toBe(8);
    expect(text).not.toContain("THINGS WAITING");
  });

  it("the Brief view (the fold's destination) shows no success line and no implementation word", async () => {
    render(<BriefView header={null} />);
    await screen.findByText("Decision did not record");
    // The settled view: the one rebuild ran and its brief is on the glass.
    await waitFor(() =>
      expect(mocks.apiFetch.mock.calls.filter(([path]) => path === "/api/brief/generate")).toHaveLength(1),
    );
    await screen.findByTestId("brief-refresh");
    expect(screen.getByText("Decision did not record")).toBeInTheDocument();
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(SUCCESS);
    expect(text).not.toMatch(/Primitive|[A-Z][A-Za-z]*Service\./);
    expect(text).toContain("Decision did not load");
    // The subject and its failed receipt stay together even when the reading
    // order puts the subject before its subordinate outcome facts.
    const failed = screen.getByText("SUMMARY DID NOT START");
    const row = failed.closest(".intelligence-brief-sf-row") as HTMLElement;
    expect(within(row).getByRole("button", { name: "Architecture review" })).toBeInTheDocument();
    expect(within(row).getByText(/The summary route is not available/)).toBeInTheDocument();
    expect(row.textContent).not.toMatch(SUCCESS);
  });
});
