/* HS-176-02 — the first correction: the teach row, the receipts, the
   APPLIED chip and its unfolded well, and the Configure door's
   corrections list.

   The Tuesday case is a WORDS mistake, so FIELD defaults to TEXT and
   the well pre-fills with the RAW transcript (N2) — a key harvested
   from the landed text would be matched against a string it never
   equals whenever the rewrite pass did its job. */
import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSpeakDeck } from "../useSpeakDeck";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
  ApiError: class ApiError extends Error {},
}));
vi.mock("../../../../lib/micSession", () => ({
  subscribeMicPhase: () => () => undefined,
  micCaptureSupported: () => true,
  micCaptureReason: () => null,
}));
vi.mock("../../../../lib/openMic", () => ({
  openMicDrop: vi.fn(),
  openMicListen: vi.fn(),
}));

/** The six ids the readiness route offers — never `auto` (N1). */
const OVERRIDES = [
  { id: "claude_code", label: "Claude Code" },
  { id: "codex_cli", label: "Codex CLI" },
  { id: "terminal_shell", label: "Terminal shell" },
  { id: "browser", label: "Browser" },
  { id: "editor", label: "Editor" },
  { id: "chat", label: "Chat" },
];

const BLOCKS = {
  document: {
    blocks: [
      { id: "action_item", description: "Action item" },
      { id: "delivery", description: "Delivery" },
    ],
  },
};

type Post = { method?: string; json?: Record<string, unknown> };

function posts(match: string): { url: string; init: Post }[] {
  return mocks.apiFetch.mock.calls
    .filter((c: unknown[]) => String(c[0]).includes(match))
    .map((c: unknown[]) => ({ url: String(c[0]), init: (c[1] ?? {}) as Post }))
    .filter((c) => c.init.method === "POST");
}

/** The run the dry-run route hands back for this case. */
let landed: Record<string, unknown> = {};

/** The GET wire every mount reads, plus whatever a case overrides. */
function wire(extra: Record<string, unknown> = {}, teach?: unknown) {
  mocks.apiFetch.mockImplementation((url: string, init?: Post) => {
    if (init?.method === "POST" && String(url).includes("dry-run"))
      return Promise.resolve(landed);
    if (init?.method === "POST" && String(url).includes("correct"))
      return Promise.resolve(teach ?? { recorded: true });
    for (const [key, value] of Object.entries(extra))
      if (String(url).startsWith(key)) return Promise.resolve(value);
    if (String(url).startsWith("/api/dictation/readiness"))
      return Promise.resolve({ config: {}, target: { label: "Claude Code", overrides: OVERRIDES } });
    if (String(url).startsWith("/api/dictation/blocks")) return Promise.resolve(BLOCKS);
    if (String(url).startsWith("/api/dictation/corrections")) return Promise.resolve({ items: [] });
    return Promise.resolve({});
  });
}

/** A landed run, as the routes now serve it (raw_text + the ids that fired). */
const LANDED = {
  final_text: "Ship the Q4 platform on schedule",
  raw_text: "Ship the queue for platform on schedule",
  journal_id: 7,
  corrections_applied: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  landed = LANDED;
  wire();
});

/** Land one run through the deck's own seam — no state is poked. */
async function deckWithResult(run: Record<string, unknown> = LANDED) {
  landed = run;
  const hook = renderHook(() => useSpeakDeck(() => undefined));
  await act(async () => {
    await hook.result.current.run("Ship the queue for platform on schedule");
  });
  return hook;
}

describe("the teach row's three FIELDs", () => {
  it("defaults to TEXT and pre-fills the well with the RAW transcript, not the landed text", async () => {
    const { result } = await deckWithResult();
    expect(result.current.correctionKind).toBe("text");
    expect(result.current.correctionSaid).toBe(
      "Ship the queue for platform on schedule",
    );
    expect(result.current.rawText).toBe("Ship the queue for platform on schedule");
    expect(result.current.correctionFields.map((f) => f.label)).toEqual([
      "TEXT",
      "INTENT",
      "TARGET",
    ]);
  });

  it("TARGET offers the readiness route's six labels and sends the id", async () => {
    const { result } = await deckWithResult();
    await act(async () => result.current.pickCorrectionKind("target"));
    await waitFor(() =>
      expect(result.current.correctionOptions).toHaveLength(6),
    );
    expect(result.current.correctionOptions.map((o) => o.label)).toEqual([
      "Claude Code",
      "Codex CLI",
      "Terminal shell",
      "Browser",
      "Editor",
      "Chat",
    ]);
    // never `auto` (N1) — it clears the membership guard and then raises
    expect(result.current.correctionOptions.map((o) => o.value)).not.toContain("auto");
    await act(async () => result.current.setCorrectionValue("terminal_shell"));
    await act(async () => {
      await result.current.teach();
    });
    const sent = posts("/correct");
    expect(sent).toHaveLength(1);
    expect(sent[0].init.json).toEqual({ kind: "target", value: "terminal_shell" });
    expect(result.current.receipt).toEqual({
      token: "TAUGHT",
      tone: "ok",
      tail: "Terminal shell",
    });
  });

  it("INTENT picks over the loaded blocks — the description on the face, the id on the wire", async () => {
    const { result } = await deckWithResult();
    await act(async () => result.current.pickCorrectionKind("intent"));
    await waitFor(() => expect(result.current.correctionOptions).toHaveLength(2));
    expect(result.current.correctionOptions[0]).toEqual({
      value: "action_item",
      label: "Action item",
    });
    await act(async () => {
      await result.current.teach();
    });
    expect(posts("/correct")[0].init.json).toEqual({
      kind: "intent",
      value: "action_item",
    });
    expect(result.current.receipt?.tail).toBe("Action item");
  });
});

describe("the receipts — a token pair, never a sentence", () => {
  it("TAUGHT names the stored span pair the server diffed", async () => {
    wire({}, { recorded: true, id: 3, kind: "text", key: "queue for", value: "Q4" });
    const { result } = await deckWithResult();
    await act(async () => result.current.setCorrectionSaid("Ship the Q4 platform on schedule"));
    await act(async () => {
      await result.current.teach();
    });
    const sent = posts("/correct");
    expect(sent[0].url).toBe("/api/dictation/journal/7/correct");
    expect(sent[0].init.json).toEqual({
      kind: "text",
      heard: "Ship the queue for platform on schedule",
      said: "Ship the Q4 platform on schedule",
    });
    expect(result.current.receipt).toEqual({
      token: "TAUGHT",
      tone: "ok",
      tail: "queue for → Q4",
    });
  });

  it("NO CHANGE when he edited nothing — and nothing was written", async () => {
    wire({}, { recorded: false, reason: "no_change" });
    const { result } = await deckWithResult();
    await act(async () => {
      await result.current.teach();
    });
    expect(result.current.receipt).toEqual({ token: "NO CHANGE" });
  });

  it("REFUSED · SECRET says what happened, and that nothing was written", async () => {
    wire({}, { recorded: false, reason: "secret" });
    const { result } = await deckWithResult();
    await act(async () => {
      await result.current.teach();
    });
    expect(result.current.receipt).toEqual({
      token: "REFUSED · SECRET",
      tone: "danger",
      tail: "nothing written",
    });
  });

  it("REFUSED · ONE WORD is the store's own refusal, named on the face", async () => {
    wire({}, { recorded: false, reason: "one_word" });
    const { result } = await deckWithResult();
    await act(async () => result.current.pickCorrectionKind("target"));
    await act(async () => {
      await result.current.teach();
    });
    expect(result.current.receipt?.token).toBe("REFUSED · ONE WORD");
  });

  it("reads `taught` when a route answers with the mirror key alone (R4)", async () => {
    wire({}, { taught: true, kind: "text", key: "postgress", value: "PostgreSQL" });
    const { result } = await deckWithResult();
    await act(async () => {
      await result.current.teach();
    });
    expect(result.current.receipt?.token).toBe("TAUGHT");
    expect(result.current.receipt?.tail).toBe("postgress → PostgreSQL");
  });

  it("falls back to the corrections route when the run carried no journal_id", async () => {
    const { result } = await deckWithResult({
      final_text: "Ship it",
      raw_text: "Ship it",
    });
    await act(async () => result.current.setCorrectionSaid("Ship that"));
    await act(async () => {
      await result.current.teach();
    });
    const sent = posts("/api/dictation/corrections");
    expect(sent).toHaveLength(1);
    expect(sent[0].url).toBe("/api/dictation/corrections");
    expect(sent[0].init.json).toEqual({
      kind: "text",
      heard: "Ship it",
      said: "Ship that",
    });
  });
});

describe("the APPLIED chip reads the run's own stored fact (R2)", () => {
  it("is absent when nothing fired", async () => {
    const { result } = await deckWithResult();
    expect(result.current.appliedRules).toEqual([]);
  });

  it("resolves each fired id against the store, with the label for a routing rule", async () => {
    wire({
      "/api/dictation/corrections": {
        items: [
          { id: 3, kind: "text", key: "queue for", value: "Q4", applied: 2 },
          {
            id: 5,
            kind: "target",
            key: "ship the q4 platform on schedule",
            value: "claude_code",
            applied: 1,
          },
        ],
      },
    });
    const { result } = await deckWithResult({ ...LANDED, corrections_applied: [3, 5] });
    await waitFor(() => expect(result.current.appliedRules).toHaveLength(2));
    expect(result.current.appliedRules[0]).toEqual({
      id: 3,
      kind: "text",
      key: "queue for",
      value: "Q4",
      label: "Q4",
    });
    // E.4 — the routing value renders its label, never `claude_code`
    expect(result.current.appliedRules[1].label).toBe("Claude Code");
  });
});

/* HS-176-05 — the Configure door's corrections list is RETIRED: the table
   moved out of the door and became the `Learned` wing (settled design
   D2(c)), because "the only path to what the pipeline learned is the gear"
   was the defect. Every assertion this block made — the gist rendered from
   `key`, the real `APPLIED` count, no counter of zero, `Forget` as the word
   and not the `x` glyph, the in-world confirm and the DELETE — now runs
   against the wing in `__tests__/learned.test.tsx`. The door keeps only the
   learning digest, covered above. */
