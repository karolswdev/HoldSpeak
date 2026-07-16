// HS-94-08 — delivery objects render in the semantic List view, and open the
// same read-model windows a keyboard user reaches. Nothing renders until the
// delivery store has objects, so the plain Desk list stays untouched.
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { fromWireAttempt, fromWireSource, useDelivery } from "../delivery";
import { useDeliveryDossier } from "../deliveryDossier";
import { DeliveryListSection } from "./DeliveryListSection";

const SOURCE = {
  source_id: "src_1",
  label: "holdspeak",
  status: "live",
  observed_at: "t",
  worktrees: [{ worktree_id: "wt_1", branch: "main" }],
  projects: [
    {
      slug: "holdspeak",
      current_phase: { number: 94, title: "Delivery", status: "open", stories_done: 1, stories_total: 2 },
      phases: [],
      stories: [
        { story_id: "HS-94-08", title: "Web Desk", status: "in-progress", phase: 94, evidence_exists: false },
        { story_id: "HS-93-01", title: "Old", status: "done", phase: 93, evidence_exists: true },
      ],
      warnings: 0,
    },
  ],
};

describe("delivery objects in the List view", () => {
  afterEach(() => {
    useDelivery.setState({ sources: [], attempts: [] });
    useDeliveryDossier.setState({ dossier: null, refusal: null, loading: false });
  });

  it("renders nothing when the delivery read model is empty", () => {
    useDelivery.setState({ sources: [], attempts: [] });
    const { container } = render(<DeliveryListSection />);
    expect(container.firstChild).toBeNull();
  });

  it("lists current-phase Stories in a named, accessible table and opens the dossier", () => {
    useDelivery.setState({
      sources: [fromWireSource(SOURCE)],
      attempts: [],
    });
    render(<DeliveryListSection />);
    expect(
      screen.getByRole("table", { name: "Delivery work" }),
    ).toBeInTheDocument();
    // The current-phase story appears; the phase-93 story does not (bounded).
    const open = screen.getByRole("button", { name: "HS-94-08" });
    expect(open).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "HS-93-01" })).toBeNull();
    fireEvent.click(open);
    // Opening the row asks the hub for that Story's dossier (no route change).
    const state = useDeliveryDossier.getState();
    // openStory is async; the loading flag flips synchronously.
    expect(state.loading || state.dossier || state.refusal).toBeTruthy();
  });
});
