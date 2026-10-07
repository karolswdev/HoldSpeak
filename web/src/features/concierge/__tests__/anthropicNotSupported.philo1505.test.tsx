/* PHILO-15 05, ruling 3 (inventory gap 5): an Anthropic key does nothing
 * today (no execution adapter). The Concierge's api.anthropic.com row reads
 * NOT SUPPORTED YET, never READY, offers no paid Check, and is never offered
 * as a pick; a runnable cloud row keeps READY and Check. */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConciergeCore } from "../ConciergeCore";
import type { DetectResponse, ProposeResponse } from "../api";

const mocks = vi.hoisted(() => ({
  detect: vi.fn(),
  propose: vi.fn(),
  probe: vi.fn(),
  taskProbe: vi.fn(),
  apply: vi.fn(),
  download: vi.fn(),
  openSurfaceOr: vi.fn(),
  openSurface: vi.fn(),
  closeSurfaceWindow: vi.fn(),
}));

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    conciergeDetect: mocks.detect,
    conciergePropose: mocks.propose,
    conciergeProbe: mocks.probe,
    conciergeTaskProbe: mocks.taskProbe,
    conciergeApply: mocks.apply,
    conciergeDownload: mocks.download,
  };
});

vi.mock("../../../desk/shell", () => ({
  openSurfaceOr: mocks.openSurfaceOr,
  openSurface: mocks.openSurface,
}));

vi.mock("../../../desk/store", () => ({
  useDesk: { getState: () => ({ closeSurfaceWindow: mocks.closeSurfaceWindow }) },
}));

const GROUPS: Array<[string, string]> = [
  ["thoughts_notes", "Thoughts & notes"],
  ["background", "Background"],
];

function detection(): DetectResponse {
  return {
    engines: [
      { id: "cloud:anthropic", kind: "cloud", name: "Claude", host: "api.anthropic.com", state: "NOT_SUPPORTED", keySet: true, profileId: "anthropic" },
      { id: "cloud:openrouter", kind: "cloud", name: "OpenRouter Qwen", host: "openrouter.ai", state: "READY", keySet: true, profileId: "openrouter" },
    ],
    hardware: { capability: { apple_silicon: true, system: "darwin", ram_gb: 36 } },
    runtimes: [],
    checkedAt: "2026-10-07T09:41:00Z",
    repairs: [],
    summaryAssignment: null,
  } as DetectResponse;
}

const proposal: ProposeResponse = {
  rows: GROUPS.map(([group, label]) => ({ group, label, engineId: "cloud:openrouter", host: "openrouter.ai", state: "READY" as const })),
  receipt: { groups: 2, engines: 2, waiting: 0 },
};

describe("the Concierge Anthropic row", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.detect.mockResolvedValue(detection());
    mocks.propose.mockResolvedValue(proposal);
  });

  it("reads NOT SUPPORTED YET with no Check; the runnable cloud row keeps READY and Check", async () => {
    render(<ConciergeCore scope="" />);
    const anthropic = await screen.findByTestId("concierge-found-cloud:anthropic");
    expect(anthropic.textContent).toContain("NOT SUPPORTED YET");
    expect(anthropic.textContent).not.toContain("READY");
    expect(screen.queryByTestId("concierge-check-cloud:anthropic")).toBeNull();

    const openrouter = screen.getByTestId("concierge-found-cloud:openrouter");
    expect(openrouter.textContent).toContain("READY");
    expect(screen.getByTestId("concierge-check-cloud:openrouter")).toBeTruthy();
  });

  it("is never offered as a pick", async () => {
    render(<ConciergeCore scope="" />);
    await screen.findByTestId("concierge-set-list");
    fireEvent.click(within(screen.getByTestId("concierge-set-thoughts_notes")).getAllByRole("button")[0]);
    await waitFor(() => expect(screen.getByTestId("concierge-picker-well-thoughts_notes")).toBeTruthy());
    expect(screen.queryByTestId("concierge-pick-thoughts_notes-cloud:anthropic")).toBeNull();
    expect(screen.getByTestId("concierge-pick-thoughts_notes-cloud:openrouter")).toBeTruthy();
  });
});
