// The Speak app, Journal wing (HS-176-03). The test diet (2026-10-11) moves
// tests/e2e/test_hs176_journal_glass.py here.
//
// Most of the glass rig's facts are already asserted by
// web/src/pages/cores/dictation/__tests__/journal.test.tsx (cited per test
// below). This file adds what that file does not assert: the glass rig's
// five-row seed in the route's FULL row shape (`_journal_to_dict`,
// holdspeak/web/routes/dictation/pipeline.py) under its real envelope, the
// TODAY day band, the four filter tokens in order with the pressed state, the
// empty caption count, and the no-raw-<button> rule.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Journal } from "../../pages/cores/dictation/Journal";
import { inventedFields, recorded } from "../../test/wireShape";
import JOURNAL_WIRE from "../../test/wire/dictation-journal.wire.json";
import READINESS_WIRE from "../../test/wire/dictation-readiness.target.wire.json";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
}));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
}));

/** The readiness route's `target.overrides` (`_target_override_options`). */
const READINESS = {
  target: {
    overrides: [
      { id: "claude_code", label: "Claude Code" },
      { id: "codex_cli", label: "Codex CLI" },
      { id: "terminal_shell", label: "Terminal shell" },
      { id: "browser", label: "Browser" },
      { id: "editor", label: "Editor" },
      { id: "chat", label: "Chat" },
    ],
  },
};

/** One row as `_journal_to_dict` serializes a `DictationJournalRecord`. */
function stored(id: number, source: string, transcript: string, target: string | null, ms: number, extra: Record<string, unknown> = {}) {
  return {
    id,
    created_at: new Date().toISOString().replace("Z", "+00:00"), // utc_now_iso()
    source,
    transcript,
    final_text: transcript,
    project_root: null,
    intent: null,
    block_id: null,
    target_profile: target,
    stage_ms: {},
    total_ms: ms,
    rewrite_pass_ms: [],
    confidence: null,
    warnings: [],
    corrected: false,
    correction_id: null,
    taught_from: false,
    corrections_applied: [],
    ...extra,
  };
}

/** The glass rig's SEED, newest first, with its TAUGHT and APPLIED rows. */
const SEED = [
  stored(5, "dictation", "Ship the Q4 platform in October", "claude_code", 38, { corrections_applied: [7] }),
  stored(4, "browser", "Payments cut-over runbook needs a second reviewer", "browser", 62),
  stored(3, "hotkey", "Draft the release note for the metrics change", "editor", 55),
  stored(2, "dry_run", "Move the design review to Thursday", null, 33, { corrected: true, taught_from: true }),
  stored(1, "dictation", "Cut the Q4 scope to the payments path", "claude_code", 44),
];

function envelope(items: unknown[]) {
  return { enabled: true, retention: 500, count: items.length, today: items.length, items };
}

function wire(items: (url: string) => unknown[]) {
  mocks.apiFetch.mockImplementation((url: string) => {
    if (url.startsWith("/api/dictation/readiness")) return Promise.resolve(READINESS);
    if (url.startsWith("/api/dictation/journal")) return Promise.resolve(envelope(items(url)));
    return Promise.resolve({});
  });
}

function token(container: HTMLElement, label: string): HTMLElement {
  const found = Array.from(container.querySelectorAll<HTMLElement>(".surface-filter-token"))
    .find((t) => t.textContent?.trim() === label);
  if (!found) throw new Error(`no token ${label}`);
  return found;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("The typed Journal bodies carry only the hub's fields (the SCAR LAW)", () => {
  // The hub's own answers: tests/integration/test_face_wire_fences.py::test_journal_reads.
  it("the row, the envelope and the readiness overrides", () => {
    const hub = recorded<{ items: unknown[] }>(JOURNAL_WIRE);
    expect(inventedFields(envelope(SEED), hub)).toEqual([]);
    for (const row of SEED) expect(inventedFields(row, hub.items[0])).toEqual([]);
    expect(Object.keys(SEED[0]).sort()).toEqual(Object.keys(hub.items[0] as object).sort());
    expect(READINESS).toEqual(recorded(READINESS_WIRE));
  });
});

describe("Speak Journal: the stream board", () => {
  it("draws the seed's row grammar, the TODAY band, the four tokens with ALL on, no caption count, no raw button", async () => {
    // replaces: tests/e2e/test_hs176_journal_glass.py::test_journal_stream
    // Also asserted by journal.test.tsx: "draws LANDED IN <label>, N MS, the
    // source badge, and the APPLIED chip only where a rule fired" and "draws
    // TAUGHT only on the row he taught FROM".
    wire(() => SEED);
    const { container } = render(<Journal />);
    await screen.findByText("Cut the Q4 scope to the payments path");

    expect(container.querySelectorAll(".surface-ledger-row")).toHaveLength(5);
    const band = container.querySelector(".surface-stream-day-label");
    expect(band?.textContent?.trim().toUpperCase()).toBe("TODAY");

    const body = container.textContent || "";
    expect(body).toContain("LANDED IN CLAUDE CODE");
    expect(body).toContain("LANDED IN EDITOR");
    expect(body).not.toContain("claude_code");
    expect(body).not.toContain("dry_run");
    expect(body).toContain("38 MS");
    expect(body).not.toContain(" ms");

    const badges = Array.from(container.querySelectorAll(".surface-ledger-trailing")).map((n) => n.textContent?.trim());
    expect([...badges].sort()).toEqual(["BROWSER", "DICTATION", "DICTATION", "DRY RUN", "HOTKEY"]);

    expect(container.querySelectorAll(".journal-mark")).toHaveLength(5);
    expect(Array.from(container.querySelectorAll(".journal-mark")).filter((m) => m.textContent?.includes("APPLIED"))).toHaveLength(1);
    expect(Array.from(container.querySelectorAll(".journal-mark")).filter((m) => m.textContent?.includes("TAUGHT"))).toHaveLength(1);
    expect(body).not.toContain("SIMILAR");
    expect(body).not.toContain("LEARNED");

    // No caption count on this wing (A.7).
    expect((container.querySelector(".surface-ledger-count")?.textContent ?? "").trim()).toBe("");

    const tokens = Array.from(container.querySelectorAll(".surface-filter-token")).map((t) => t.textContent?.trim());
    expect(tokens).toEqual(["ALL", "DICTATION", "BROWSER", "HOTKEY"]);
    expect(token(container, "ALL")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByRole("button", { name: "Clear" })).toHaveLength(1);

    const raw = Array.from(container.querySelectorAll("button")).filter(
      (b) => !b.classList.contains("btn") && !b.classList.contains("btn--chrome")
        && !b.classList.contains("surface-ledger-line") && !b.classList.contains("desk-mic"),
    );
    expect(raw.map((b) => b.className || b.textContent)).toEqual([]);
  });
});

describe("Speak Journal: the filtered board", () => {
  it("DICTATION sends source=dictation, reads pressed and active, and the stream narrows to its rows", async () => {
    // replaces: tests/e2e/test_hs176_journal_glass.py::test_journal_filtered
    // The `source` param alone is also asserted by journal.test.tsx:
    // "drives the route's `source` param, with ALL sending none". The wire
    // half (the route filters by source) is
    // tests/unit/test_hs176_routes.py::test_journal_source_filter_accepts_every_recorder_source.
    wire((url) => (url.includes("source=dictation") ? SEED.filter((r) => r.source === "dictation") : SEED));
    const { container } = render(<Journal />);
    await screen.findByText("Cut the Q4 scope to the payments path");

    fireEvent.click(token(container, "DICTATION"));
    await waitFor(() => expect(container.querySelectorAll(".surface-ledger-row")).toHaveLength(2));
    expect(mocks.apiFetch.mock.calls.map((c) => String(c[0]))).toContain("/api/dictation/journal?limit=50&source=dictation");

    expect(token(container, "DICTATION")).toHaveAttribute("aria-pressed", "true");
    expect(token(container, "DICTATION")).toHaveAttribute("data-filter-active");
    expect(token(container, "ALL")).toHaveAttribute("aria-pressed", "false");
    const badges = Array.from(container.querySelectorAll(".surface-ledger-trailing")).map((n) => n.textContent?.trim());
    expect(badges).toEqual(["DICTATION", "DICTATION"]);
    expect(container.querySelectorAll(".surface-filter-token")).toHaveLength(4);
    expect(container.querySelector(".surface-ledger-head")?.textContent ?? "").not.toContain("/");
  });
});

// The rest of the rig's rows are asserted by journal.test.tsx, read and
// confirmed 2026-10-11 (no duplicate written here):
// - test_journal_row_open -> "keeps every verb on the opened row and tokenises the replay preview"
// - test_journal_quiet -> "reads NOTHING SPOKEN with no Clear when nothing was ever spoken"
//   and "renders the tokens over an empty stream (no sparse rule)"
// - test_journal_taught_row_wears_taught -> "draws TAUGHT only on the row he taught FROM";
//   the teach route sets the flag: tests/unit/test_hs176_routes.py::test_journal_correct_links_the_id_record_returned
//   and ::test_journal_rows_carry_the_two_split_facts_and_no_learning
// - test_journal_search_marks_a_final_text_only_hit -> "marks a row whose search hit lives only in final_text (C15)"
// - test_journal_live_frame_obeys_the_active_filter -> "drops a HOTKEY frame while the wing is filtered to BROWSER, and takes it under ALL (C2)"
// - test_journal_pushes_without_a_reload -> "prepends a pushed entry and never doubles one already loaded"
//   (the broadcast half: tests/unit/test_desk_speak.py::test_the_servers_recorder_broadcasts_each_stored_row)
