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
import { render, screen } from "@testing-library/react";
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

const SUCCESS = /Decision recorded|Summary requested|Brief triage saved|Decision changed|Decision loaded/;
const IMPLEMENTATION = /Primitive|[A-Z][A-Za-z]*Service\b|[a-z]_[a-z]/;

describe("PHILO-6-02 round 2: a failed operation never reads as a success", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    mocks.apiFetch.mockImplementation(async (path: string) =>
      String(path) === "/api/brief/latest" ? brief : null,
    );
  });

  it("the Arrival BRIEF section shows the failures and no success line", async () => {
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-receipt");
    const section = screen.getByTestId("arrival-brief");
    const text = section.textContent ?? "";
    expect(text).not.toMatch(SUCCESS);
    expect(text).not.toMatch(IMPLEMENTATION);
    // Every waiting row is a failure or the recorded meeting; the fold holds
    // the rest (its destination is the Brief view, below).
    expect(text).toContain("BRIEF · 6 THINGS WAITING");
  });

  it("the Brief view (the fold's destination) shows no success line and no implementation word", async () => {
    render(<BriefView header={null} />);
    await screen.findByText("Decision did not record");
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(SUCCESS);
    expect(text).not.toMatch(/Primitive|[A-Z][A-Za-z]*Service\./);
    expect(text).toContain("Decision did not load");
    // The Brief view says a `<Kind>: <subject>` row as its kind head.
    expect(text).toContain("SUMMARY DID NOT STARTArchitecture review");
  });
});
