/**
 * HS-156-04 — Front Door vitest: pack cards, health strip, advanced fold.
 *
 * Acceptance:
 * - unconfigured → cards render (complete per-job lines, sizes, recommended)
 * - confirm posts apply and the plan renders its states incl. failed+resume
 * - configured → strip + fold opens the advanced view
 * - attention state renders exactly ONE action button
 * - imports only via barrel (fence enforces; not tested here)
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FrontDoorView } from "../frontDoor";
import { getAssignmentSummary, type AssignmentSummary, type AssignmentSummaryRow } from "../assignmentExperience";
import { apiFetch } from "../../../lib/api";

// ── Mocks ────────────────────────────────────────────────────────────────

vi.mock("../assignmentExperience", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../assignmentExperience")>()),
  getAssignmentSummary: vi.fn(),
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));

// Stub child cores so they render without their own network calls
vi.mock("../ModelLibraryCore", () => ({
  ModelLibraryCore: () => <div data-testid="model-library-core">Model Library</div>,
}));
vi.mock("../CapabilityAssignmentsCore", () => ({
  CapabilityAssignmentsCore: () => <div data-testid="assignments-core">Assignments</div>,
}));
vi.mock("../TopologyMapView", () => ({
  TopologyMapView: () => <div data-testid="topology-map-view">Topology Map</div>,
}));

const mockApiFetch = vi.mocked(apiFetch);
const mockGetSummary = vi.mocked(getAssignmentSummary);

// ── Fixtures ─────────────────────────────────────────────────────────────

const DISPLAY_LINES = [
  { group_id: "thoughts_notes", group_label: "Thoughts & notes", source_label: "Qwen 4B (Q4_K_M)" },
  { group_id: "chat_practice", group_label: "Chat practice", source_label: "Qwen 4B (Q4_K_M)" },
  { group_id: "writing_dictation", group_label: "Writing & dictation", source_label: "Qwen 4B (Q4_K_M)" },
  { group_id: "meetings", group_label: "Meetings", source_label: "Qwen 4B (Q4_K_M)" },
  { group_id: "agents_tools", group_label: "Agents & tools", source_label: "Qwen 4B (Q4_K_M)" },
  { group_id: "background", group_label: "Background", source_label: "Qwen 4B (Q4_K_M)" },
  { group_id: "speech_recognition", group_label: "Speech recognition", source_label: "Whisper small (444 MB)", job: "speech" },
  { group_label: "Text-to-speech", source_label: "Kokoro TTS (fp16) (197 MB)", job: "tts" },
];

const PLAN_ENTRIES = [
  { group_id: "thoughts_notes", kind: "catalog_download", preset_id: "preset_qwen", download_bytes: 2_740_000_000 },
  { group_id: "speech_recognition", kind: "builtin_whisper", preset_id: null, download_bytes: 466_000_000 },
];

function makePack(id: string, label: string, recommended: boolean, totalBytes = 3_200_000_000) {
  return {
    id,
    label,
    summary: recommended ? "Recommended for this hardware." : `${label} pack.`,
    recommended,
    display_lines: DISPLAY_LINES,
    plan: PLAN_ENTRIES,
    total_download_bytes: totalBytes,
  };
}

const PACKS = [
  makePack("light", "Light", false, 500_000_000),
  makePack("balanced", "Balanced", true, 3_200_000_000),
  makePack("full", "Full", false, 8_000_000_000),
];

const RECOMMENDATION = { packs: PACKS, facts: { apple_silicon: true } };

function assignmentRow(id: string, label: string, hasAssignment: boolean, repair: string | null = null): AssignmentSummaryRow {
  return {
    id,
    label,
    editor_capability_id: "ask.answer",
    inherited_from: id === "global" ? null : "global",
    assignment: hasAssignment
      ? { id: "ia", revision: 1, scope: { kind: "global" }, entries: [{ ordinal: 1, profile_id: "q", profile_revision: 1, label: "Qwen", boundary: "local", readiness: "ready" }], retry_policy_id: null, issues: [] }
      : null,
    status: hasAssignment ? "assigned" : "no_assignment",
    repair,
  };
}

function unconfiguredSummary(): AssignmentSummary {
  return {
    schema: "InferenceAssignmentSummary@1",
    rows: [
      assignmentRow("global", "Default", false),
      assignmentRow("thoughts_notes", "Thoughts & notes", false),
      assignmentRow("chat_practice", "Chat practice", false),
      assignmentRow("speech_recognition", "Speech recognition", false),
      assignmentRow("meetings", "Meetings", false),
      assignmentRow("agents_tools", "Agents & tools", false),
      assignmentRow("background", "Background", false),
    ],
    task_overrides: [],
    issue_count: 0,
  };
}

function configuredSummary(repair?: { id: string; label: string; text: string }): AssignmentSummary {
  const rows = [
    assignmentRow("global", "Default", true),
    assignmentRow("thoughts_notes", "Thoughts & notes", true),
    assignmentRow("chat_practice", "Chat practice", true),
    assignmentRow("speech_recognition", "Speech recognition", true, repair?.id === "speech_recognition" ? repair.text : null),
    assignmentRow("meetings", "Meetings", true),
    assignmentRow("agents_tools", "Agents & tools", true),
    assignmentRow("background", "Background", true),
  ];
  return {
    schema: "InferenceAssignmentSummary@1",
    rows,
    task_overrides: [],
    issue_count: repair ? 1 : 0,
  };
}

// ── Setup ────────────────────────────────────────────────────────────────

function setupMocks(
  summary: AssignmentSummary,
  plan: { plan: unknown } = { plan: null },
  recommendation = RECOMMENDATION,
) {
  mockGetSummary.mockResolvedValue(summary);
  mockApiFetch.mockImplementation(async (url: string) => {
    if (typeof url === "string" && url.includes("/api/front-door/recommendation")) {
      return recommendation as never;
    }
    if (typeof url === "string" && url.includes("/api/front-door/apply")) {
      return plan as never;
    }
    throw new Error(`Unexpected API call: ${url}`);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.useRealTimers();
});

// ── Tests ────────────────────────────────────────────────────────────────

describe("FrontDoorView", () => {
  describe("unconfigured state — cards", () => {
    it("renders pack cards with per-job lines, sizes, and recommended", async () => {
      setupMocks(unconfiguredSummary());
      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-cards")).toBeTruthy();
      });

      // All three packs render
      expect(screen.getByText("Light")).toBeTruthy();
      expect(screen.getByText("Balanced")).toBeTruthy();
      expect(screen.getByText("Full")).toBeTruthy();

      // Recommended badge on Balanced
      const balancedCard = screen.getByText("Balanced").closest(".surface-choice-card");
      expect(balancedCard?.getAttribute("data-recommended")).toBeTruthy();

      // Per-job lines render
      expect(screen.getAllByText("Thoughts & notes").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Speech recognition").length).toBeGreaterThanOrEqual(1);

      // Download sizes render (500_000_000 = 477 MB in binary, 3.2G = 3.0 GB, 8G = 7.5 GB)
      expect(screen.getByText("477 MB download")).toBeTruthy();
      expect(screen.getByText("3.0 GB download")).toBeTruthy();
      expect(screen.getByText("7.5 GB download")).toBeTruthy();

      // "Set up my own" action
      expect(screen.getByText("Set up my own")).toBeTruthy();
    });

    it("'Set up my own' opens the advanced layer", async () => {
      setupMocks(unconfiguredSummary());
      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-cards")).toBeTruthy();
      });

      fireEvent.click(screen.getByText("Set up my own"));

      await waitFor(() => {
        expect(screen.getByTestId("front-door-advanced")).toBeTruthy();
      });

      // Default view is Map; switch to Table to see Library + Assignments
      fireEvent.click(screen.getByRole("tab", { name: "Table" }));

      await waitFor(() => {
        expect(screen.getByTestId("model-library-core")).toBeTruthy();
        expect(screen.getByTestId("assignments-core")).toBeTruthy();
      });
    });
  });

  describe("confirm and apply", () => {
    it("posts apply and renders the plan with step states", async () => {
      const planResult = {
        plan_id: "fdap_test",
        status: "done",
        items: [
          { ordinal: 0, entry: { kind: "catalog_download", group_id: "thoughts_notes" }, status: "done", receipt: {}, error: null },
          { ordinal: 1, entry: { kind: "builtin_whisper", group_id: "speech_recognition" }, status: "done", receipt: {}, error: null },
        ],
      };

      setupMocks(unconfiguredSummary());
      // Override apiFetch to handle POST
      mockApiFetch.mockImplementation(async (url: string, init?: unknown) => {
        const opts = init as { method?: string; json?: unknown } | undefined;
        if (typeof url === "string" && url.includes("/api/front-door/recommendation")) {
          return RECOMMENDATION as never;
        }
        if (typeof url === "string" && url.includes("/api/front-door/apply")) {
          if (opts?.method === "POST") {
            return planResult as never;
          }
          // GET: return the done plan after POST
          return { plan: { ...planResult, id: planResult.plan_id, pack_id: "balanced", created_at: "2026-08-30T12:00:00Z", updated_at: "2026-08-30T12:00:00Z" } } as never;
        }
        throw new Error(`Unexpected: ${url}`);
      });

      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-cards")).toBeTruthy();
      });

      // Select Balanced
      const balancedRadio = screen.getByDisplayValue("balanced");
      fireEvent.click(balancedRadio);

      // Confirm
      const confirmBtn = screen.getByText("Set up");
      fireEvent.click(confirmBtn);

      // Plan view should appear
      await waitFor(() => {
        expect(screen.getByTestId("front-door-plan")).toBeTruthy();
      });
    });

    it("failed plan renders resume action", async () => {
      const failedPlan = {
        id: "fdap_fail",
        pack_id: "balanced",
        status: "failed" as const,
        items: [
          { ordinal: 0, entry: { kind: "catalog_download", group_id: "thoughts_notes" }, status: "done" as const, receipt: {}, error: null },
          { ordinal: 1, entry: { kind: "builtin_whisper", group_id: "speech_recognition" }, status: "failed" as const, receipt: null, error: "Download timed out" },
        ],
        created_at: "2026-08-30T12:00:00Z",
        updated_at: "2026-08-30T12:01:00Z",
      };

      setupMocks(unconfiguredSummary(), { plan: failedPlan });

      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-plan")).toBeTruthy();
      });

      // Failed step shows its error
      expect(screen.getByText("Download timed out")).toBeTruthy();

      // Resume action button
      const resumeBtn = screen.getByText("Resume");
      expect(resumeBtn).toBeTruthy();
    });
  });

  describe("configured state — strip + fold", () => {
    it("renders the health strip and advanced fold opens", async () => {
      const donePlan = {
        id: "fdap_done",
        pack_id: "balanced",
        status: "done" as const,
        items: [],
        created_at: "2026-08-30T12:00:00Z",
        updated_at: "2026-08-30T12:00:00Z",
      };

      setupMocks(configuredSummary(), { plan: donePlan });

      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-strip")).toBeTruthy();
      });

      // Health strip content
      expect(screen.getByText(/Everything wired/)).toBeTruthy();
      expect(screen.getByText(/Balanced/)).toBeTruthy();

      // Disclosure fold
      const advancedTrigger = screen.getByText("Advanced");
      expect(advancedTrigger).toBeTruthy();

      // Open the fold
      fireEvent.click(advancedTrigger);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-advanced")).toBeTruthy();
      });

      // Default view is Map; switch to Table to see Library + Assignments
      fireEvent.click(screen.getByRole("tab", { name: "Table" }));

      await waitFor(() => {
        expect(screen.getByTestId("model-library-core")).toBeTruthy();
        expect(screen.getByTestId("assignments-core")).toBeTruthy();
      });
    });
  });

  describe("attention state", () => {
    it("renders exactly ONE action button for an attention state", async () => {
      const donePlan = {
        id: "fdap_done",
        pack_id: "balanced",
        status: "done" as const,
        items: [],
        created_at: "2026-08-30T12:00:00Z",
        updated_at: "2026-08-30T12:00:00Z",
      };

      setupMocks(
        configuredSummary({ id: "speech_recognition", label: "Speech recognition", text: "has no model" }),
        { plan: donePlan },
      );

      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-strip")).toBeTruthy();
      });

      // The attention notice names the issue as a proper sentence
      expect(screen.getByText(/Speech recognition has no model/)).toBeTruthy();

      // Exactly ONE action button ("Fix it" per D3)
      const actionButtons = screen.getAllByRole("button").filter(
        (btn) => btn.classList.contains("surface-action-notice-btn"),
      );
      expect(actionButtons).toHaveLength(1);
      expect(actionButtons[0].textContent).toBe("Fix it");
    });

    it("short action-verb repair falls back to 'needs attention'", async () => {
      const donePlan = {
        id: "fdap_done",
        pack_id: "balanced",
        status: "done" as const,
        items: [],
        created_at: "2026-08-30T12:00:00Z",
        updated_at: "2026-08-30T12:00:00Z",
      };

      // When repair is just "Fix" (an action verb, not a description)
      setupMocks(
        configuredSummary({ id: "speech_recognition", label: "Speech recognition", text: "Fix" }),
        { plan: donePlan },
      );

      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-strip")).toBeTruthy();
      });

      // "Fix" alone becomes "needs attention" -- no label collision with the button
      expect(screen.getByText(/Speech recognition needs attention/)).toBeTruthy();
    });

    it("descriptive repair passes through as a sentence", async () => {
      const donePlan = {
        id: "fdap_done",
        pack_id: "balanced",
        status: "done" as const,
        items: [],
        created_at: "2026-08-30T12:00:00Z",
        updated_at: "2026-08-30T12:00:00Z",
      };

      setupMocks(
        configuredSummary({ id: "speech_recognition", label: "Speech recognition", text: "needs a model" }),
        { plan: donePlan },
      );

      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-strip")).toBeTruthy();
      });

      // Descriptive repair text passes through as a sentence
      expect(screen.getByText(/Speech recognition needs a model/)).toBeTruthy();
    });
  });

  describe("wording states", () => {
    it("pack cards show human model names, not raw filenames", async () => {
      setupMocks(unconfiguredSummary());
      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-cards")).toBeTruthy();
      });

      const text = document.body.textContent ?? "";
      // No raw GGUF filenames on the cards
      expect(text).not.toContain(".gguf");
      // Human labels should be visible
      expect(text).toContain("Qwen 4B");
    });

    it("speech recognition appears exactly once per card (not duplicated)", async () => {
      setupMocks(unconfiguredSummary());
      render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-cards")).toBeTruthy();
      });

      // Speech recognition should appear (as label) in each of 3 cards = 3 times
      // NOT 6 times (which would indicate duplication within each card)
      const speechMatches = screen.getAllByText("Speech recognition");
      expect(speechMatches).toHaveLength(3); // One per card
    });
  });

  describe("copy fence -- no jargon on the door path", () => {
    const BANNED_JARGON = [
      "catalog",
      "no_assignment",
      "no_compatible_assignment",
      "provider_family",
      ".gguf",
    ];

    it("unconfigured cards contain no banned jargon", async () => {
      setupMocks(unconfiguredSummary());
      const { container } = render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-cards")).toBeTruthy();
      });

      const text = container.textContent ?? "";
      for (const word of BANNED_JARGON) {
        expect(text.toLowerCase()).not.toContain(word.toLowerCase());
      }
    });

    it("configured strip contains no banned jargon", async () => {
      const donePlan = {
        id: "fdap_done",
        pack_id: "balanced",
        status: "done" as const,
        items: [],
        created_at: "2026-08-30T12:00:00Z",
        updated_at: "2026-08-30T12:00:00Z",
      };

      setupMocks(configuredSummary(), { plan: donePlan });
      const { container } = render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-strip")).toBeTruthy();
      });

      const text = container.textContent ?? "";
      for (const word of BANNED_JARGON) {
        expect(text.toLowerCase()).not.toContain(word.toLowerCase());
      }
    });

    it("attention strip contains no banned jargon", async () => {
      const donePlan = {
        id: "fdap_done",
        pack_id: "balanced",
        status: "done" as const,
        items: [],
        created_at: "2026-08-30T12:00:00Z",
        updated_at: "2026-08-30T12:00:00Z",
      };

      setupMocks(
        configuredSummary({ id: "speech_recognition", label: "Speech recognition", text: "has no model" }),
        { plan: donePlan },
      );
      const { container } = render(<FrontDoorView />);

      await waitFor(() => {
        expect(screen.getByTestId("front-door-strip")).toBeTruthy();
      });

      const text = container.textContent ?? "";
      for (const word of BANNED_JARGON) {
        expect(text.toLowerCase()).not.toContain(word.toLowerCase());
      }
    });
  });
});
