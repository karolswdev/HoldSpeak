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
import { Blocks } from "../../pages/cores/dictation/Blocks";
import { inventedFields, recorded } from "../../test/wireShape";
import JOURNAL_WIRE from "../../test/wire/dictation-journal.wire.json";
import READINESS_WIRE from "../../test/wire/dictation-readiness.target.wire.json";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  // Betterment C8: the Talk press that listens opens a stream session.
  startStream: vi.fn(),
  micPhase: null as null | ((phase: string) => void),
}));

vi.mock("../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
  newDeliveryId: () => "speak:test",
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
}));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
}));
// The Speak window (below) mounts the mic seams: no microphone in jsdom
// (the pattern of pages/cores/__tests__/dictationWings.test.tsx).
vi.mock("../../lib/micSession", () => ({
  subscribeMicPhase: (listener: (phase: string) => void) => {
    mocks.micPhase = listener;
    return () => undefined;
  },
  micCaptureSupported: () => true,
  micCaptureReason: () => null,
  openMicRunning: () => false,
  startOpenMic: vi.fn(),
  stopOpenMic: vi.fn(),
}));
vi.mock("../../lib/micStreamSession", () => ({
  micStreamSupported: () => true,
  startStreamSession: mocks.startStream,
}));
vi.mock("../../lib/openMic", () => ({ openMicDrop: vi.fn(), openMicListen: vi.fn() }));
vi.mock("../../lib/speakToFill", () => ({
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => "",
  retryPendingTranscription: vi.fn(async () => null),
  subscribeCaptureLevel: () => () => undefined,
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

openFind();
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
    expect(body).toContain("Landed in Claude Code");
    expect(body).toContain("Landed in Editor");
    expect(body).not.toContain("claude_code");
    expect(body).not.toContain("dry_run");
    expect(body).toContain("38 ms");
    expect(body).not.toContain(" MS");

    const badges = Array.from(container.querySelectorAll(".journal-badge")).map((n) => n.textContent?.trim());
    expect([...badges].sort()).toEqual(["Browser", "Dictation", "Dictation", "Dry run", "Hotkey"]);

    expect(container.querySelectorAll(".journal-mark")).toHaveLength(5);
    expect(Array.from(container.querySelectorAll(".journal-mark")).filter((m) => m.textContent?.includes("Applied"))).toHaveLength(1);
    expect(Array.from(container.querySelectorAll(".journal-mark")).filter((m) => m.textContent?.includes("Taught"))).toHaveLength(1);
    expect(body).not.toContain("SIMILAR");
    expect(body).not.toContain("LEARNED");

    // No caption count on this wing (A.7).
    expect((container.querySelector(".surface-ledger-count")?.textContent ?? "").trim()).toBe("");

    openFind();
    const tokens = Array.from(container.querySelectorAll(".surface-filter-token")).map((t) => t.textContent?.trim());
    expect(tokens).toEqual(["All", "Dictation", "Browser", "Hotkey"]);
    expect(token(container, "All")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByRole("button", { name: "Clear" })).toHaveLength(1);

    const raw = Array.from(container.querySelectorAll("button")).filter(
      (b) => !b.classList.contains("btn") && !b.classList.contains("btn--chrome")
        && !b.classList.contains("surface-ledger-line") && !b.classList.contains("desk-mic"),
    );
    expect(raw.map((b) => b.className || b.textContent)).toEqual([]);
  });
});

describe("Speak's wings when empty (DELIGHT 2): the Speak object, one line, one verb where one makes the first", () => {
  it("the Journal: the object and What you say shows here, no verb and no zero", async () => {
    wire(() => []);
    const { container } = render(<Journal />);
    await screen.findByText("What you say shows here");
    const object = container.querySelector('.surface-state[data-object="dictation"]') as HTMLElement;
    expect(object.querySelector(".surface-state-sprite")?.getAttribute("src")).toMatch(/48\/dock-speak\.png$/);
    expect(object.querySelector("button")).toBeNull();
    expect(object.textContent).not.toMatch(/\b0\b/);
  });

  it("Blocks: the object, No blocks yet and New block, which opens the draft in place", async () => {
    mocks.apiFetch.mockImplementation(() => Promise.resolve({ document: { blocks: [] } }));
    const { container } = render(<Blocks />);
    await screen.findByText("No blocks yet");
    const object = container.querySelector('.surface-state[data-object="dictation"]') as HTMLElement;
    expect(object.querySelector(".surface-state-sprite")?.getAttribute("src")).toMatch(/48\/dock-speak\.png$/);
    const verbs = Array.from(object.querySelectorAll("button"));
    expect(verbs.map((b) => b.textContent?.trim())).toEqual(["New block"]);
    fireEvent.click(verbs[0]);
    expect(await screen.findByRole("group", { name: "New block" })).toBeTruthy();
    expect(container.querySelector('.surface-state[data-object="dictation"]')).toBeNull();
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

    openFind();
    fireEvent.click(token(container, "Dictation"));
    await waitFor(() => expect(container.querySelectorAll(".surface-ledger-row")).toHaveLength(2));
    expect(mocks.apiFetch.mock.calls.map((c) => String(c[0]))).toContain("/api/dictation/journal?limit=50&source=dictation");

    expect(token(container, "Dictation")).toHaveAttribute("aria-pressed", "true");
    expect(token(container, "Dictation")).toHaveAttribute("data-filter-active");
    expect(token(container, "All")).toHaveAttribute("aria-pressed", "false");
    const badges = Array.from(container.querySelectorAll(".journal-badge")).map((n) => n.textContent?.trim());
    expect(badges).toEqual(["Dictation", "Dictation"]);
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

// ── The Speak window over the hub's recorded answers (the teach loop) ──────
//
// The successors of tests/e2e/test_hs170_speak_glass.py,
// test_hs176_speak_glass.py and test_hs176_loop_glass.py (the test diet,
// 2026-10-11). The window is the real DictationCore (its wings, its footer)
// with the real SpeakFace, Journal and Learned. Only `apiFetch` is mocked, and
// it answers from fixtures/speak-hub/loop.json: the real hub's answers to the
// same loop (the dry-run, correct, corrections and journal routes, a durable
// store, the correction loop on), recorded by
// tests/unit/test_desk_speak.py::test_the_teach_loop_runs_on_the_real_routes.
// Each press is replayed in the hub's order; every read after a press answers
// what the hub answered after that press. A read the hub never answered (the
// Concierge scan) rejects, as a closed route does.
import { useState as useHostState, type ReactNode } from "react";
import userEvent from "@testing-library/user-event";
import { within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { DictationCore } from "../../pages/cores/DictationCore";
import { WingSlotContext } from "../surface/wings";
import LOOP from "./fixtures/speak-hub/loop.json";

type Step = { step: string; call: string; body: unknown; status: number; answer: unknown; reads: Record<string, unknown> };
const STEPS = LOOP.steps as unknown as Step[];
const BOOT = LOOP.boot as unknown as Record<string, unknown>;

let pressed = 0;
let misses: string[] = [];
let presses: { call: string; body: unknown }[] = [];

function replayLoop() {
  pressed = 0;
  misses = [];
  presses = [];
  mocks.apiFetch.mockImplementation((url: string, init: { method?: string; json?: unknown } = {}) => {
    const path = String(url);
    const method = (init.method ?? "GET").toUpperCase();
    const reads = pressed === 0 ? BOOT : STEPS[pressed - 1].reads;
    const readKey = method === "GET" ? path : `${method} ${path}`;
    if (readKey in reads) return Promise.resolve(structuredClone(reads[readKey]));
    const next = STEPS[pressed];
    if (method !== "GET" && next && next.call === `${method} ${path}`) {
      pressed += 1;
      presses.push({ call: next.call, body: init.json });
      return Promise.resolve(structuredClone(next.answer));
    }
    misses.push(readKey);
    return Promise.reject(new Error(`the hub recorded no answer for ${readKey}`));
  });
}

function mountSpeak() {
  function Host() {
    const [slot, setSlot] = useHostState<ReactNode>(null);
    return (
      <WingSlotContext.Provider value={setSlot}>
        <div data-testid="window-head">{slot}</div>
        <DictationCore />
      </WingSlotContext.Provider>
    );
  }
  return render(<MemoryRouter><Host /></MemoryRouter>);
}

const HEARD = "Ship the queue for platform on schedule";
const SAID = "Ship the Q4 platform on schedule";
const AGAIN = "Ship the queue for platform in October";
const SECRET_HEARD = "Set the token to placeholder";
const SECRET_SAID = "Set the token to sk-live4f2a9c1b2d3e4f";

/** Betterment C8: the DRY RUN latch is gone; `Try it here` (in `land`)
 *  previews and types nothing. */
async function latchDryRun() {
  await screen.findByTestId("speak-try-it-here");
}

/** Type one utterance in the well and press `Try it here` (betterment C8). */
async function land(text: string) {
  const well = await screen.findByLabelText("Utterance");
  await userEvent.clear(well);
  await userEvent.click(well);
  await userEvent.paste(text);
  await userEvent.click(screen.getByTestId("speak-try-it-here"));
  const result = await screen.findByRole("region", { name: "Pipeline result" });
  await waitFor(() => expect(result.querySelector(".speak-result-text")?.textContent ?? "").toContain(text.split(" ").slice(-1)[0] === "October" ? "October" : text.split(" ")[0]));
  return result;
}

// Window grammar (2026-10-24): the footer is the window's status bar.
const footerText = () => document.querySelector(".speak-footer")?.textContent ?? "";

describe("the Speak window at rest, over the hub's cold answers", () => {
  it("the placeholder, an ENGINE state chip in a known state, no Details (behind RAW), and Review and Export in the toolbar, clean-up in the status bar, no placement", async () => {
    // replaces: tests/e2e/test_hs170_speak_glass.py::test_speak_idle_1440
    // replaces: tests/e2e/test_hs170_speak_glass.py::test_speak_details_folded
    // replaces: tests/e2e/test_hs170_speak_glass.py::test_speak_footer_this_device
    // replaces: tests/e2e/test_hs170_speak_glass.py::test_speak_unset_1440
    replayLoop();
    const { container } = mountSpeak();
    const well = (await screen.findByLabelText("Utterance")) as HTMLTextAreaElement;
    expect(well.getAttribute("placeholder")).toBe("Talk, or type here");

    const engine = container.querySelector(".speak-engine")!;
    expect(engine).toBeTruthy();
    await waitFor(() => expect(engine.querySelector(".surface-state-chip")).toBeTruthy());
    expect(["not-set", "ready", "pending", "unknown", "waiting"]).toContain(
      container.querySelector(".speak-engine")!.getAttribute("data-engine-state"));

    // Betterment C8: Details (the pipeline, the budget, the states) is
    // behind RAW; it is not on the face at rest.
    expect(container.querySelector(".surface-disclosure-trigger")).toBeNull();
    expect(container.querySelector(".surface-disclosure-body")).toBeNull();

    // Lane speak (2026-10-25): on the Speak wing Review and Export sit at
    // the toolbar's right end; the status bar says the state, one line.
    const toolbar = () => document.querySelector("[data-testid=speak-toolbar]")?.textContent ?? "";
    await waitFor(() => expect(toolbar()).toContain("Review"));
    expect(toolbar()).toContain("Export");
    await waitFor(() => expect(footerText()).toContain("Clean-up"));
    expect(footerText()).not.toContain("Review");
    expect(footerText()).not.toContain("THIS DEVICE");
    // Nothing was pressed: the cold reads were all the hub's own.
    expect(pressed).toBe(0);
  });

  it("the ENGINE row never claims READY when the engine scan fails", async () => {
    // replaces: tests/e2e/test_hs170_speak_glass.py::test_speak_engine_never_ready_while_pending
    // The browser rig answered /api/concierge/detect with a 503; this replay
    // rejects it (the hub recorded no answer for it), the same failed scan.
    replayLoop();
    const { container } = mountSpeak();
    await screen.findByLabelText("Utterance");
    await waitFor(() => expect(misses).toContain("/api/concierge/detect"));
    await waitFor(() => expect(container.querySelector(".speak-engine .surface-state-chip")).toBeTruthy());
    const engine = container.querySelector(".speak-engine")!;
    expect(engine.getAttribute("data-engine-state")).not.toBe("ready");
    expect(engine.querySelector(".surface-state-chip")!.textContent).not.toMatch(/ready/i);
  });
});

describe("the teach loop on the Speak window, replayed from the hub", () => {
  it("land, Wrong, teach, refuse a secret, land again with the rule applied; the Journal and Learned wings; Forget; Review", async () => {
    // replaces: tests/e2e/test_hs170_speak_glass.py::test_speak_landed_1440
    // replaces: tests/e2e/test_hs176_speak_glass.py::test_speak_teach_loop_1440 (every board but the
    //   teach well's no-truncation measure, which stays in the browser file)
    // replaces: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 (every board but the Learned
    //   row's geometry probe, which stays in the browser file)
    replayLoop();
    const { container } = mountSpeak();
    await latchDryRun();

    // ── 1. land: the RESULT row, OK and Wrong ──
    let result = await land(HEARD);
    expect(result.querySelector(".speak-result-text")!.textContent).toContain("Ship the queue");
    expect(within(result).getByRole("button", { name: "OK" })).toBeTruthy();
    // The press reached the hub as the dry run, with the typed words.
    expect(presses[0]).toEqual({ call: "POST /api/dictation/dry-run", body: expect.objectContaining({ utterance: HEARD }) });

    // ── 2. Wrong unfolds the teach row in place: FIELD at TEXT, the raw words ──
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await waitFor(() => {
      const el = container.querySelector(".speak-teach");
      expect(el).toBeTruthy();
      return el as HTMLElement;
    });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(teach.textContent).toContain("FIELD");
    const field = within(teach).getByLabelText("Correction field") as HTMLSelectElement;
    expect(field.value).toBe("text");
    expect(Array.from(field.options).map((o) => o.textContent?.trim())).toEqual(["TEXT", "INTENT", "TARGET"]);
    let said = within(teach).getByRole("textbox", { name: "What you said" }) as HTMLTextAreaElement;
    expect(said.value).toBe(HEARD);
    expect(said.tagName).toBe("TEXTAREA");
    expect(teach.querySelectorAll(".desk-mic").length).toBeGreaterThanOrEqual(1);

    // ── 3. FIELD at TARGET: the readiness route's six labels, never `auto` ──
    await userEvent.selectOptions(field, "target");
    const pick = (await within(teach).findByLabelText("Delivery target")) as HTMLSelectElement;
    expect(Array.from(pick.options).map((o) => o.textContent?.trim())).toEqual(
      ["Claude Code", "Codex CLI", "Terminal shell", "Browser", "Editor", "Chat"]);
    expect(Array.from(pick.options).map((o) => o.value)).not.toContain("auto");
    expect(within(teach).queryByRole("textbox", { name: "What you said" })).toBeNull();

    // ── 4. back to TEXT, the one word edited, Teach: the receipt replaces the row ──
    await userEvent.selectOptions(field, "text");
    said = (await within(teach).findByRole("textbox", { name: "What you said" })) as HTMLTextAreaElement;
    await userEvent.clear(said);
    await userEvent.paste(SAID);
    await userEvent.click(screen.getByRole("button", { name: "Teach correction" }));
    let receipt = await waitFor(() => {
      const el = container.querySelector(".speak-receipt");
      expect(el).toBeTruthy();
      return el as HTMLElement;
    });
    expect(receipt.textContent).toContain("TAUGHT");
    expect(receipt.textContent).toContain("queue for");
    expect(receipt.textContent).toContain("Q4");
    expect(container.querySelector(".speak-teach")).toBeNull();
    expect(footerText()).not.toContain("TAUGHT");
    expect(presses[1].call).toMatch(/^POST \/api\/dictation\/journal\/\d+\/correct$/);
    expect(presses[1].body).toEqual({ kind: "text", heard: HEARD, said: SAID });

    // ── 5. a secret-shaped teach is refused by name and writes nothing ──
    result = await land(SECRET_HEARD);
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    said = (await screen.findByRole("textbox", { name: "What you said" })) as HTMLTextAreaElement;
    await userEvent.clear(said);
    await userEvent.paste(SECRET_SAID);
    await userEvent.click(screen.getByRole("button", { name: "Teach correction" }));
    await waitFor(() => expect(container.querySelector(".speak-receipt")?.textContent ?? "").toContain("REFUSED"));
    receipt = container.querySelector(".speak-receipt") as HTMLElement;
    expect(receipt.textContent).toContain("SECRET");
    expect(receipt.textContent).toContain("nothing written");
    expect(footerText()).not.toContain("REFUSED");

    // ── 6. speak it again: the rule fires and says so ──
    result = await land(AGAIN);
    expect(result.querySelector(".speak-result-text")!.textContent).toBe("Ship the Q4 platform in October");
    const chip = await within(result).findByRole("button", { name: "Corrections applied" });
    expect(chip.textContent?.trim()).toBe("APPLIED");
    expect(container.querySelector(".speak-well .desk-mic")).toBeNull();
    await userEvent.click(chip);
    const disclosed = await waitFor(() => {
      const el = container.querySelector(".speak-applied-body");
      expect(el).toBeTruthy();
      return el!.textContent ?? "";
    });
    for (const word of ["HEARD", "queue for", "SAID", "Q4", "TEXT"]) expect(disclosed).toContain(word);

    // ── 7. the Journal wing: every landing, newest first; APPLIED, then TAUGHT ──
    await userEvent.click(screen.getByRole("tab", { name: "Journal" }));
    await waitFor(() => expect(container.querySelectorAll(".speak-journal .surface-ledger-row").length).toBe(3));
    const rows = Array.from(container.querySelectorAll(".speak-journal .surface-ledger-row"));
    expect(rows[0].textContent).toContain(AGAIN);
    expect(rows[0].querySelector(".journal-mark")?.textContent).toContain("Applied");
    expect(rows[2].textContent).toContain(HEARD);
    expect(rows[2].querySelector(".journal-mark")?.textContent).toContain("Taught");

    // ── 8. the Learned wing: the one rule the desk now knows ──
    await userEvent.click(screen.getByRole("tab", { name: "Learned" }));
    await waitFor(() => expect(container.querySelectorAll(".speak-learned .surface-ledger-row").length).toBe(1));
    const wing = container.querySelector(".speak-learned") as HTMLElement;
    const row = wing.querySelector(".surface-ledger-row") as HTMLElement;
    expect(row.querySelector(".learned-kind")?.textContent?.trim()).toBe("Text");
    expect(row.querySelector(".surface-ledger-primary")?.textContent?.trim()).toBe("queue for");
    expect(row.querySelector(".learned-value")?.textContent?.trim()).toBe("Q4");
    expect(row.querySelector(".learned-cells")?.textContent).toContain("→");
    expect(row.querySelector(".learned-applied")?.textContent?.trim()).toBe("1 applied");
    const body = wing.textContent ?? "";
    for (const wire of ["claude_code", "dry_run", "snake", "similar", "SIMILAR", "LEARNED"]) expect(body).not.toContain(wire);
    expect(Array.from(wing.querySelectorAll(".surface-ledger-count")).map((c) => c.textContent?.trim()).filter(Boolean)).toEqual([]);
    const raw = Array.from(wing.querySelectorAll("button")).filter(
      (b) => !b.classList.contains("btn") && !b.classList.contains("btn--chrome")
        && !b.classList.contains("surface-ledger-line") && !b.classList.contains("desk-mic"));
    expect(raw).toEqual([]);

    // ── 9. Forget arms in place, then removes the rule: the wing stands quiet ──
    const forget = row.querySelector(".learned-forget .btn") as HTMLElement;
    expect(forget.textContent?.trim()).toBe("Forget");
    await userEvent.click(forget);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect((wing.querySelector(".learned-forget .btn") as HTMLElement).textContent?.trim()).toBe("Forget?");
    await userEvent.click(wing.querySelector(".learned-forget .btn") as HTMLElement);
    await waitFor(() => expect(container.querySelector('.speak-learned .surface-state[data-kind="empty"]')).toBeTruthy());
    const quiet = container.querySelector(".speak-learned") as HTMLElement;
    expect(quiet.querySelectorAll(".surface-ledger-row")).toHaveLength(0);
    expect(quiet.textContent).toContain("Press Wrong on a phrase to teach a fix");
    expect(quiet.querySelector('.surface-state[data-object="dictation"] .surface-state-sprite')).toBeTruthy();
    expect(quiet.textContent).not.toMatch(/applied/i);
    expect(quiet.textContent).not.toContain("0");
    expect(quiet.textContent).not.toContain(".");
    expect(presses.map((p) => p.call.replace(/\d+/g, "N"))).toEqual([
      "POST /api/dictation/dry-run", "POST /api/dictation/journal/N/correct",
      "POST /api/dictation/dry-run", "POST /api/dictation/journal/N/correct",
      "POST /api/dictation/dry-run", "DELETE /api/dictation/corrections/N",
    ]);

    // ── 10. Review reviews: it crosses to the Journal wing, not the door ──
    // W1 (2026-10-27): Review is a Talk toolbar verb (never the status bar).
    await userEvent.click(screen.getByRole("tab", { name: "Talk" }));
    await userEvent.click(await screen.findByRole("button", { name: "Review" }));
    await waitFor(() => expect(container.querySelector(".speak-journal")).toBeTruthy());
    expect(screen.getByRole("tab", { name: "Journal" }).getAttribute("aria-selected")).toBe("true");
    expect(container.querySelector(".surface-door")).toBeNull();
    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual(["Talk", "Journal", "Blocks", "Learned", "Commands"]);
    // Every read the window made was one the hub answered, but the scan.
    expect([...new Set(misses)]).toEqual(["/api/concierge/detect"]);
  });
});

// ── The HOTKEY custody block over the hub's five recorded readiness answers ──
//
// The successor of tests/e2e/test_hs200_voice_custody_glass.py's face legs.
// fixtures/speak-hub/custody.json holds the real readiness route's answer for
// each of the browser rig's five platform states (the same seam: the three
// permission probes and the runtime status), recorded by
// tests/unit/test_desk_speak.py::test_the_readiness_route_carries_the_hotkey_custody.
// Every other read the window makes answers from the loop's cold boot.
import CUSTODY from "./fixtures/speak-hub/custody.json";

/** PHILO-17 refit r3: search and the source tokens fold until asked for. */
function openFind(): void {
  const find = screen.queryByRole("button", { name: "Search" });
  if (find) fireEvent.click(find);
}

const CUSTODY_READINESS = CUSTODY.readiness as unknown as Record<string, unknown>;
let custodyState = "all_granted";

function replayCustody(state: string) {
  custodyState = state;
  misses = [];
  mocks.apiFetch.mockImplementation((url: string, init: { method?: string } = {}) => {
    const path = String(url);
    const method = (init.method ?? "GET").toUpperCase();
    if (method === "GET" && path === "/api/dictation/readiness")
      return Promise.resolve(structuredClone(CUSTODY_READINESS[custodyState]));
    const key = method === "GET" ? path : `${method} ${path}`;
    if (key in BOOT) return Promise.resolve(structuredClone(BOOT[key]));
    misses.push(key);
    return Promise.reject(new Error(`the hub recorded no answer for ${key}`));
  });
}

async function custodyBlock() {
  mountSpeak();
  await screen.findByLabelText("Utterance");
  return await screen.findByTestId("speak-hotkey");
}

describe("the HOTKEY custody block, from the hub's readiness answers", () => {
  // replaces: tests/e2e/test_hs200_voice_custody_glass.py::test_hotkey_custody_block_1440 (the words and
  //   the rows of each state; the one-right-edge and no-overflow measures stay in the browser file)
  it("every grant refused: three rows, each with its System Settings path and DENIED; UNAVAILABLE; no modal", async () => {
    replayCustody("all_denied");
    const block = await custodyBlock();
    for (const pid of ["microphone", "input_monitoring", "accessibility"]) {
      const row = await screen.findByTestId(`speak-permission-${pid}`);
      expect(row.textContent).toContain("SYSTEM SETTINGS");
      expect(row.textContent).toContain("PRIVACY & SECURITY");
      expect(row.textContent).toContain("Denied");
    }
    expect(block.textContent).toContain("Unavailable");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("one refused: only that row draws, and the head says BLOCKED, never ACTIVE", async () => {
    replayCustody("one_denied");
    const block = await custodyBlock();
    await screen.findByTestId("speak-permission-input_monitoring");
    expect(screen.queryByTestId("speak-permission-microphone")).toBeNull();
    expect(screen.queryByTestId("speak-permission-accessibility")).toBeNull();
    const head = block.querySelector(".speak-hotkey-head")!;
    expect(head.textContent).toContain("Blocked");
    expect(head.textContent).not.toContain("Active");
  });

  it("never asked: NOT ASKED, with Accessibility read as DENIED beside it", async () => {
    replayCustody("never_asked");
    const block = await custodyBlock();
    expect(block.textContent).toContain("Not asked");
    expect((await screen.findByTestId("speak-permission-accessibility")).textContent).toContain("Denied");
  });

  it("the listener failed with every grant held: the reason token, never the exception, and no permission rows", async () => {
    replayCustody("listener_failed");
    const block = await custodyBlock();
    expect((await screen.findByTestId("speak-hotkey-reason")).textContent).toBe("PYNPUT MISSING");
    expect(block.textContent).not.toContain("pynput is not available");
    expect(document.querySelectorAll('[data-testid^="speak-permission-"]')).toHaveLength(0);
  });

  it("granted, then Re-check: the block goes, and nothing green takes its place", async () => {
    replayCustody("listener_failed");
    await custodyBlock();
    custodyState = "all_granted"; // he gives the grant on the machine
    await userEvent.click(screen.getByTestId("speak-hotkey-recheck"));
    await waitFor(() => expect(screen.queryByTestId("speak-hotkey")).toBeNull());
    expect(document.querySelector(".speak-face")!.textContent).not.toContain("HOTKEY");
  });
});

// ── Betterment capture C8: the one Talk rule and the words ─────────────────
//
// The loop's cold boot is the real hub with no speech model
// (`/api/setup/local-ai` answers `speech.state: will_download`). The answer
// after setup is the real hub's with the model on the device
// (fixtures/meetings-hub/p17t-ready.json, `speech.state: on_device`).
import { act } from "@testing-library/react";
import { MicLamp } from "../components/DeskChrome";
import { TALK_STOP_EVENT } from "../components/MicButton";
import { useBuilderTools } from "../builderTools";
import { SPEECH_SETUP_EVENT } from "../firstrun/SpeechSetup";
import READY_HUB from "./fixtures/meetings-hub/p17t-ready.json";

/** Words no Speak face says any more (capture DESIGN.md §4, the words). */
function expectNoOldWords(face: HTMLElement) {
  const text = face.textContent ?? "";
  for (const gone of [/LANDS IN/i, /DRY RUN/i, /MIC HELD/i, /Write a thought/i, /\bopen\b/i, /\blevel\b/i]) {
    expect(text).not.toMatch(gone);
  }
}

/** The loop's boot, and after `setUp()` the hub's answer with the model here. */
function replaySpeech() {
  replayLoop();
  const loop = mocks.apiFetch.getMockImplementation()!;
  let ready = false;
  mocks.apiFetch.mockImplementation((url: string, init?: unknown) =>
    ready && String(url) === "/api/setup/local-ai"
      ? Promise.resolve(structuredClone((READY_HUB as Record<string, unknown>)["/api/setup/local-ai"]))
      : loop(url, init));
  return { setUp: () => { ready = true; } };
}

describe("C8: Speak in plain words, one Talk rule", () => {
  beforeEach(() => {
    mocks.startStream.mockReset();
    mocks.startStream.mockResolvedValue({ stop: vi.fn(async () => ""), cancel: vi.fn(), retained: vi.fn(async () => false) });
    useBuilderTools.getState().setOn(false);
    // The well keeps a durable draft; each case starts with an empty box.
    localStorage.clear();
  });

  it("no speech model: Talk is live, its press opens Set up speech in place; none of the old words", async () => {
    replaySpeech();
    const { container } = mountSpeak();
    const talk = await screen.findByTestId("speak-speech-setup-key");
    expect(talk).not.toBeDisabled();
    expect(talk.getAttribute("aria-label")).toBe("Talk");
    expect(screen.getByTestId("speak-fact").textContent).toBe("Talk sets up speech first");
    // Nothing is offered before the press: the press opens it, in place.
    expect(screen.queryByTestId("speak-speech-setup-verb")).toBeNull();
    await userEvent.click(talk);
    const verb = await screen.findByTestId("speak-speech-setup-verb");
    expect(verb.textContent?.trim()).toMatch(/^Set up speech · \d+ MB$/);
    expect(container.querySelector(".speak-plate")!.contains(verb)).toBe(true);
    // Egress where the fetch happens (UX-CANON A.9): the host beside the verb.
    expect(screen.getByTestId("speak-speech-setup").textContent?.toUpperCase()).toContain("HUGGINGFACE.CO");
    // Types into: the app in front · Try it here.
    const row = screen.getByTestId("speak-types-into");
    expect(row.textContent).toContain("Types into");
    expect((within(row).getByLabelText("Types into") as HTMLSelectElement).selectedOptions[0].textContent).toBe("the app in front");
    expect(Array.from((within(row).getByLabelText("Types into") as HTMLSelectElement).options).map((o) => o.textContent))
      .toEqual(["the app in front", "an agent"]);
    expect(screen.getByTestId("speak-try-it-here")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Open mic" })).toBeNull();
    expectNoOldWords(container.querySelector(".speak-face") as HTMLElement);
  });

  it("then it listens: the model lands, the same press listens, and the key reads Listening · Stop", async () => {
    const hub = replaySpeech();
    mountSpeak();
    await userEvent.click(await screen.findByTestId("speak-speech-setup-key"));
    await screen.findByTestId("speak-speech-setup-verb");
    expect(mocks.startStream).not.toHaveBeenCalled();
    hub.setUp();
    act(() => { window.dispatchEvent(new Event(SPEECH_SETUP_EVENT)); });
    await waitFor(() => expect(mocks.startStream).toHaveBeenCalledTimes(1));
    const key = await screen.findByRole("button", { name: "Listening · Stop" });
    expect(key.textContent).toContain("Listening · Stop");
    expect(screen.queryByTestId("speak-speech-setup-verb")).toBeNull();
    expect(screen.getByTestId("speak-fact").textContent).not.toBe("Talk sets up speech first");
    // The menu bar's Stop (TALK_STOP_EVENT) ends this capture, as a second press would.
    const session = await mocks.startStream.mock.results[0].value;
    act(() => { window.dispatchEvent(new Event(TALK_STOP_EVENT)); });
    await waitFor(() => expect(session.stop).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Listening · Stop" })).toBeNull());
  });

  it("Try it here runs the typed words and shows the result; it types nothing into an app", async () => {
    replaySpeech();
    const { container } = mountSpeak();
    const result = await land(HEARD);
    expect(result.querySelector(".speak-result-text")!.textContent).toContain("Ship the queue");
    expect(presses.map((p) => p.call)).toEqual(["POST /api/dictation/dry-run"]);
    expect(presses.map((p) => p.call)).not.toContain("POST /api/dictation/remote");
    expectNoOldWords(container.querySelector(".speak-face") as HTMLElement);
  });

  it("RAW (Builder tools) shows Details and the Open mic latch; off, the face has neither", async () => {
    replaySpeech();
    useBuilderTools.getState().setOn(true);
    try {
      const { container } = mountSpeak();
      await screen.findByLabelText("Utterance");
      expect(container.querySelector(".surface-disclosure-trigger")?.textContent).toContain("Details");
      expect(screen.getByRole("button", { name: "Open mic" })).toBeTruthy();
    } finally {
      useBuilderTools.getState().setOn(false);
    }
  });

  it("the open mic receipt uses plain words", async () => {
    const hub = replaySpeech();
    useBuilderTools.getState().setOn(true);
    try {
      mountSpeak();
      await screen.findByLabelText("Utterance");
      hub.setUp();
      act(() => { window.dispatchEvent(new Event(SPEECH_SETUP_EVENT)); });
      const open = await screen.findByRole("button", { name: "Open mic" });
      await waitFor(() => expect(open).not.toBeDisabled());

      await userEvent.click(open);
      await waitFor(() => expect(footerText()).toContain("Listening"));
      expect(footerText()).not.toMatch(/OPEN MIC/i);

      await userEvent.click(open);
      await waitFor(() => expect(footerText()).toContain("Stopped listening"));
      expect(footerText()).not.toMatch(/OPEN MIC/i);
    } finally {
      useBuilderTools.getState().setOn(false);
    }
  });

  it("the menu bar says Listening · Stop, never MIC HELD, and Stop asks the Talk to stop", async () => {
    const stops = vi.fn();
    window.addEventListener(TALK_STOP_EVENT, stops);
    try {
      render(<MicLamp />);
      act(() => mocks.micPhase?.("held"));
      const lamp = await screen.findByTestId("desk-mic-lamp");
      expect(lamp.textContent).toContain("Listening");
      expect(lamp.textContent).not.toMatch(/held/i);
      await userEvent.click(within(lamp).getByRole("button", { name: "Stop" }));
      expect(stops).toHaveBeenCalledTimes(1);
      act(() => mocks.micPhase?.("closed"));
      expect(screen.queryByTestId("desk-mic-lamp")).toBeNull();
    } finally {
      window.removeEventListener(TALK_STOP_EVENT, stops);
    }
  });
});
