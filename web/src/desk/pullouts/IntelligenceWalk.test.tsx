import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { IntelligencePullout } from "./IntelligencePullout";
import { INTELLIGENCE_NAVIGATE } from "../intelligenceNavigation";
import windowChromeCss from "../components/window-chrome.css?raw";

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../lib/api", () => ({
  apiFetch,
  readableError: (reason: unknown) => reason instanceof Error ? reason.message : "Request failed",
}));

const object = {
  kind: "intelligence" as const,
  id: "desk",
  title: "Intelligence",
  ref: { kind: "intelligence" as const, id: "desk", name: "Intelligence" },
};

const brief = {
  id: "brief-1",
  headline: "One decision needs your attention.",
  is_empty: false,
  sections: {
    changed: [{
      id: "brief-item-1",
      section: "changed",
      text: "Desk Intelligence is ready.",
      detail: "The pullout is now openable from the dock.",
      source_ref: "follow-through:card-1",
      priority: 1,
    }],
    broke: [],
    waiting: [],
    decisions: [],
  },
};

const largeBrief = {
  ...brief,
  headline: "193 things changed, 55 things broke, and an intentionally unbroken source reference verifies wrapping.",
  sections: {
    changed: Array.from({ length: 193 }, (_, index) => ({
      id: `brief-item-${index}`,
      section: "changed" as const,
      text: `Changed material ${index + 1}`,
      detail: "A large Brief remains inside the pullout body.",
      source_ref: null,
      priority: index + 1,
    })),
  },
};

const board = {
  now: [{
    id: "card-1",
    text: "Review the Intelligence walk",
    owner: "Karol",
    due: "2099-08-08",
    source: "decision",
    decision_id: "meeting-1",
    provenance: null,
  }],
  waiting: [],
  unassigned: [],
  overdue: [],
};

const receipt = {
  id: "receipt-1",
  decision_text: "Ship Desk Intelligence",
  rationale: "The Desk needs a durable operating picture.",
  alternatives: null,
  owner: "Karol",
  review_date: null,
  lifecycle: "active",
};

describe("HS-128-10 Desk Intelligence walk", () => {
  beforeEach(() => {
    localStorage.clear();
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/brief/latest") return Promise.resolve(brief);
      if (path === "/api/follow-through/board") return Promise.resolve(board);
      if (path.startsWith("/api/receipts")) return Promise.resolve([receipt]);
      return Promise.resolve([]);
    });
  });

  it("opens with the segmented Intelligence header", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(screen.getByRole("group", { name: "Intelligence view" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Brief" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Follow-through" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Receipts" })).toHaveAttribute("aria-pressed", "false");
    expect(await screen.findByText(brief.headline)).toBeInTheDocument();
  });

  it("renders the Brief headline and its operating groups", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(await screen.findByText(brief.headline)).toBeInTheDocument();
    expect(screen.getByText("Changed")).toBeInTheDocument();
    expect(screen.getByText("Broke")).toBeInTheDocument();
    expect(screen.getByText("Waiting")).toBeInTheDocument();
    expect(screen.getByText("Your Decisions")).toBeInTheDocument();
    expect(screen.getByText("Desk Intelligence is ready.")).toBeInTheDocument();
  });

  it("renders Follow-Through lanes and their cards", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Follow-through" }));

    expect(await screen.findByText("Now")).toBeInTheDocument();
    expect(screen.getByText("Waiting")).toBeInTheDocument();
    expect(screen.getByText("Unassigned")).toBeInTheDocument();
    expect(screen.getByText("Overdue")).toBeInTheDocument();
    expect(screen.getByText(board.now[0].text)).toBeInTheDocument();
  });

  it("renders Receipts with a search input that queries the ledger", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Receipts" }));

    const search = await screen.findByRole("searchbox", { name: "Search decision receipts" });
    expect(screen.getByText(receipt.decision_text)).toBeInTheDocument();
    fireEvent.change(search, { target: { value: "Intelligence" } });

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/api/receipts/search?q=Intelligence"),
    );
  });

  it("preserves the selected view when the pullout closes and reopens", async () => {
    const first = render(<IntelligencePullout object={object} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Receipts" }));
    await screen.findByRole("searchbox", { name: "Search decision receipts" });
    first.unmount();

    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(await screen.findByRole("searchbox", { name: "Search decision receipts" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Receipts" })).toHaveAttribute("aria-pressed", "true");
  });

  it("HS-129-03 keeps a large Brief in the scrollable body under the card cap", async () => {
    apiFetch.mockImplementation((path: string) =>
      path === "/api/brief/latest" ? Promise.resolve(largeBrief) : Promise.resolve([]),
    );
    const { container } = render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(await screen.findByText(largeBrief.headline)).toBeInTheDocument();
    expect(container.querySelector(".desk-pullout-body.intelligence-pullout")).toBeInTheDocument();
    expect(container.querySelectorAll(".intelligence-brief-rows .surface-ledger-row")).toHaveLength(193);
    expect(windowChromeCss).toContain(".desk-next .desk-window.is-floating:not(.is-card)");
    expect(windowChromeCss).toContain("max-height: none;");
  });

  it("HS-129-03 hides BACK until a cross-link drill and returns to Brief", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(screen.queryByRole("button", { name: "← BACK" })).not.toBeInTheDocument();
    fireEvent(window, new CustomEvent(INTELLIGENCE_NAVIGATE, { detail: { view: "brief" } }));
    expect(screen.queryByRole("button", { name: "← BACK" })).not.toBeInTheDocument();
    await screen.findByText(brief.headline);
    fireEvent.click(screen.getByRole("button", { name: "Changed: Desk Intelligence is ready." }));

    expect(await screen.findByText(board.now[0].text)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "← BACK" }));

    expect(await screen.findByText(brief.headline)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "← BACK" })).not.toBeInTheDocument();
  });
});
