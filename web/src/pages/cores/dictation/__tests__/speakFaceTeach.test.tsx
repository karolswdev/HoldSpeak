/* HS-176-02 — the teach loop as it is DRAWN: the RESULT row's APPLIED
   chip and the well it unfolds, the teach row's FIELD cycle, and the
   receipt that takes the teach row's place. No modal, no sentence. */
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpeakFace } from "../SpeakFace";
import { ReceiptContext } from "../shared";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), startStreamSession: vi.fn() }));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  /* counsel C1 — the DELIVERY path mints one id per utterance. */
  newDeliveryId: () => "speak:test-delivery-id",
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
vi.mock("../../../../lib/speakToFill", () => ({
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => "",
  /* nothing was retained: a click starts a real session rather than
     replaying a pending capture. */
  retryPendingTranscription: vi.fn(async () => null),
  subscribeCaptureLevel: () => () => undefined,
}));
vi.mock("../../../../lib/micStreamSession", () => ({
  micStreamSupported: () => true,
  startStreamSession: mocks.startStreamSession,
  subscribeCaptureLevel: () => () => undefined,
}));
vi.mock("../../assignmentExperience", () => ({
  getAssignmentEditor: () => Promise.resolve(null),
}));
vi.mock("../../../../features/concierge/api", () => ({
  conciergeDetect: () => Promise.resolve({ engines: [] }),
}));

const OVERRIDES = [
  { id: "claude_code", label: "Claude Code" },
  { id: "codex_cli", label: "Codex CLI" },
  { id: "terminal_shell", label: "Terminal shell" },
  { id: "browser", label: "Browser" },
  { id: "editor", label: "Editor" },
  { id: "chat", label: "Chat" },
];

const RULES = [
  { id: 3, kind: "text", key: "queue for", value: "Q4", applied: 2 },
  {
    id: 5,
    kind: "intent",
    key: "ship the q4 platform on schedule",
    value: "delivery",
    applied: 1,
  },
];

let landed: Record<string, unknown> = {};
/* counsel C1 — the DELIVERY reply (`/api/dictation/remote`), which now
   carries the same three loop keys the dry run does. */
let remoteReply: Record<string, unknown> = {};
let teachReply: Record<string, unknown> = { recorded: true };

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  localStorage.setItem("holdspeak.speakAim", "field");
  landed = {
    final_text: "Ship the Q4 platform on schedule",
    raw_text: "Ship the queue for platform on schedule",
    journal_id: 7,
    corrections_applied: [],
  };
  remoteReply = { success: true, delivered: true, final_text: "" };
  teachReply = { recorded: true, kind: "text", key: "queue for", value: "Q4" };
  mocks.apiFetch.mockImplementation(
    (url: string, init?: { method?: string }) => {
      const path = String(url);
      if (init?.method === "POST" && path.includes("dry-run"))
        return Promise.resolve(landed);
      if (init?.method === "POST" && path.includes("/api/dictation/remote"))
        return Promise.resolve(remoteReply);
      if (init?.method === "POST" && path.includes("correct"))
        return Promise.resolve(teachReply);
      if (path.startsWith("/api/dictation/readiness"))
        return Promise.resolve({
          config: {},
          target: { label: "Claude Code", overrides: OVERRIDES },
        });
      if (path.startsWith("/api/dictation/blocks"))
        return Promise.resolve({
          document: { blocks: [{ id: "delivery", description: "Delivery" }] },
        });
      if (path.startsWith("/api/dictation/corrections"))
        return Promise.resolve({ items: RULES });
      return Promise.resolve({});
    },
  );
});

/** Every token the face pushed into the footer's ONE receipt channel. */
let announced: string[] = [];

/** Type into the well and land the run (aim = THIS FIELD -> preview). */
async function land() {
  announced = [];
  render(
    <ReceiptContext.Provider value={(text: string) => void announced.push(text)}>
      <SpeakFace />
    </ReceiptContext.Provider>,
  );
  const well = await screen.findByLabelText("Utterance");
  await userEvent.click(well);
  await userEvent.paste("Ship the queue for platform on schedule");
  await userEvent.keyboard("{Control>}{Enter}{/Control}");
  return await screen.findByRole("region", { name: "Pipeline result" });
}

describe("the RESULT row's teach loop", () => {
  it("Wrong unfolds the teach row in-world — FIELD at TEXT, the well on the raw transcript", async () => {
    const result = await land();
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));

    const teach = await screen.findByRole("group", { name: "Correct this result" });
    // in-world, never a modal (rule A.4)
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(within(teach).getByText("FIELD")).toBeTruthy();

    const field = within(teach).getByRole("combobox", { name: "Correction field" });
    expect(
      Array.from(field.querySelectorAll("option")).map((o) => o.textContent),
    ).toEqual(["TEXT", "INTENT", "TARGET"]);
    expect((field as HTMLSelectElement).value).toBe("text");

    // N2 — the well holds what the mic HEARD, not what landed
    const said = within(teach).getByLabelText(
      "What you said",
    ) as HTMLTextAreaElement;
    // the value he EDITS wraps, so the species is the kit's textarea
    // face — an <input> would truncate the sentence at 393.
    expect(said.tagName).toBe("TEXTAREA");
    expect(said.value).toBe("Ship the queue for platform on schedule");
    // the voice law: every text well carries its mic
    expect(within(teach).getByRole("button", { name: /Speak What you said/ })).toBeTruthy();
  });

  it("FIELD at TARGET draws a pick over the six real ids, labels verbatim", async () => {
    const result = await land();
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    await userEvent.selectOptions(
      within(teach).getByRole("combobox", { name: "Correction field" }),
      "target",
    );

    const pick = await within(teach).findByRole("combobox", { name: "Delivery target" });
    const options = Array.from(pick.querySelectorAll("option"));
    expect(options.map((o) => o.textContent)).toEqual([
      "Claude Code",
      "Codex CLI",
      "Terminal shell",
      "Browser",
      "Editor",
      "Chat",
    ]);
    // the id rides the wire, never the typed label
    expect(options.map((o) => (o as HTMLOptionElement).value)).toContain("terminal_shell");
    // no free-text well while a routing kind is picked
    expect(within(teach).queryByLabelText("What you said")).toBeNull();
  });

  it("Teach replaces the teach row with the token receipt", async () => {
    const result = await land();
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    await userEvent.clear(within(teach).getByLabelText("What you said"));
    await userEvent.type(
      within(teach).getByLabelText("What you said"),
      "Ship the Q4 platform on schedule",
    );
    await userEvent.click(within(teach).getByRole("button", { name: "Teach correction" }));

    const receipt = await within(result).findByRole("status");
    expect(receipt.textContent).toContain("TAUGHT");
    expect(receipt.textContent).toContain("queue for → Q4");
    // the row it replaced is gone; no sentence took its place
    await waitFor(() =>
      expect(screen.queryByRole("group", { name: "Correct this result" })).toBeNull(),
    );
    expect(receipt.textContent).not.toContain("reaches similar dictations");
    // A.7 — the name is said ONCE per face: the footer keeps its own
    // status vocabulary and never mirrors the teach outcome.
    expect(announced).toContain("REHEARSED · NOT DELIVERED");
    expect(announced.filter((t) => t.includes("TAUGHT"))).toEqual([]);
    expect(announced.filter((t) => t.includes("queue for"))).toEqual([]);
  });

  it("a refused teach names the refusal and says nothing was written", async () => {
    teachReply = { recorded: false, reason: "secret" };
    const result = await land();
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    await userEvent.click(within(teach).getByRole("button", { name: "Teach correction" }));

    const receipt = await within(result).findByRole("status");
    expect(receipt.textContent).toContain("REFUSED · SECRET");
    expect(receipt.textContent).toContain("nothing written");
    // the refusal is said once too — in the row, never in the footer
    expect(announced.filter((t) => t.includes("REFUSED"))).toEqual([]);
  });
});

describe("the APPLIED chip", () => {
  it("is absent when this run fired nothing (rule A.8)", async () => {
    const result = await land();
    expect(within(result).queryByRole("button", { name: "Corrections applied" })).toBeNull();
  });

  it("names the text rule that fired — HEARD / SAID / TEXT", async () => {
    landed = { ...landed, corrections_applied: [3] };
    const result = await land();
    const chip = await within(result).findByRole("button", { name: "Corrections applied" });
    expect(chip.textContent).toBe("APPLIED");
    expect(chip.getAttribute("aria-expanded")).toBe("false");
    await userEvent.click(chip);

    const body = await screen.findByRole("region", { name: "Corrections applied" });
    expect(within(body).getByText("HEARD")).toBeTruthy();
    expect(within(body).getByText("queue for")).toBeTruthy();
    expect(within(body).getByText("SAID")).toBeTruthy();
    expect(within(body).getByText("Q4")).toBeTruthy();
    expect(within(body).getByText("TEXT")).toBeTruthy();
  });

  it("names a routing rule by its LABEL, never its id — WHEN / ROUTE / INTENT", async () => {
    landed = { ...landed, corrections_applied: [5] };
    const result = await land();
    await userEvent.click(
      await within(result).findByRole("button", { name: "Corrections applied" }),
    );
    const body = await screen.findByRole("region", { name: "Corrections applied" });
    expect(within(body).getByText("WHEN")).toBeTruthy();
    expect(within(body).getByText("ROUTE")).toBeTruthy();
    expect(within(body).getByText("Delivery")).toBeTruthy();
    expect(within(body).getByText("INTENT")).toBeTruthy();
    expect(body.textContent).not.toContain("delivery,");
  });
});

/* HS-176 counsel C1 — the loop has to close on the path a Tuesday
   utterance actually takes.

   `land()` above aims at THIS FIELD, so it previews through
   `/api/dictation/dry-run`. A real utterance is DELIVERED: aim FOCUSED
   APP, `/api/dictation/remote`. The deck reads `raw_text`,
   `corrections_applied` and `journal_id` off ONE `result` object
   (`useSpeakDeck.ts:161, 166, 443`), so a delivery reply that omitted
   them left the chip blank, the teach well pre-filled from the LANDED
   text, and `teach()` on the corrections fallback. Same three keys, same
   loop. */
describe("the DELIVERED run feeds the same loop (counsel C1)", () => {
  /** Land for real: aim FOCUSED APP, through `/api/dictation/remote`. */
  async function deliver(reply: Record<string, unknown>) {
    localStorage.setItem("holdspeak.speakAim", "focused");
    remoteReply = reply;
    announced = [];
    render(
      <ReceiptContext.Provider value={(text: string) => void announced.push(text)}>
        <SpeakFace />
      </ReceiptContext.Provider>,
    );
    const well = await screen.findByLabelText("Utterance");
    await userEvent.click(well);
    await userEvent.paste("Ship the queue for platform on schedule");
    await userEvent.keyboard("{Control>}{Enter}{/Control}");
    await waitFor(() =>
      expect(
        mocks.apiFetch.mock.calls.filter((c: unknown[]) =>
          String(c[0]).includes("/api/dictation/remote"),
        ),
      ).toHaveLength(1),
    );
    return await screen.findByRole("region", { name: "Pipeline result" });
  }

  it("renders the APPLIED chip from a delivery reply's corrections_applied", async () => {
    const result = await deliver({
      success: true,
      delivered: true,
      final_text: "Ship the Q4 platform on schedule",
      raw_text: "Ship the queue for platform on schedule",
      corrections_applied: [3],
      journal_id: 11,
    });
    const chip = await within(result).findByRole("button", {
      name: "Corrections applied",
    });
    await userEvent.click(chip);
    const body = await screen.findByRole("region", { name: "Corrections applied" });
    expect(within(body).getByText("queue for")).toBeTruthy();
    expect(within(body).getByText("Q4")).toBeTruthy();
  });

  it("pre-fills the TEXT teach well from the delivery's raw transcript", async () => {
    const result = await deliver({
      success: true,
      delivered: true,
      final_text: "Ship the Q4 platform on schedule",
      raw_text: "Ship the queue for platform on schedule",
      corrections_applied: [],
      journal_id: 11,
    });
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    const said = within(teach).getByLabelText("What you said") as HTMLTextAreaElement;
    // the RAW transcript, not the LANDED text — the diff is heard vs said
    expect(said.value).toBe("Ship the queue for platform on schedule");
  });

  it("teaches through the JOURNAL route when the delivery named its row", async () => {
    const result = await deliver({
      success: true,
      delivered: true,
      final_text: "Ship the Q4 platform on schedule",
      raw_text: "Ship the queue for platform on schedule",
      corrections_applied: [],
      journal_id: 11,
    });
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    await userEvent.click(
      within(teach).getByRole("button", { name: "Teach correction" }),
    );

    await within(result).findByRole("status");
    const taught = mocks.apiFetch.mock.calls.filter(
      (c: unknown[]) => (c[1] as { method?: string })?.method === "POST"
        && String(c[0]).includes("correct"),
    );
    expect(taught).toHaveLength(1);
    expect(String(taught[0][0])).toBe("/api/dictation/journal/11/correct");
  });

  it("falls back to the corrections route when the delivery named no row", async () => {
    const result = await deliver({
      success: true,
      delivered: true,
      final_text: "Ship the Q4 platform on schedule",
      raw_text: "Ship the queue for platform on schedule",
      corrections_applied: [],
      journal_id: null,
    });
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    await userEvent.click(
      within(teach).getByRole("button", { name: "Teach correction" }),
    );

    await within(result).findByRole("status");
    const taught = mocks.apiFetch.mock.calls.filter(
      (c: unknown[]) => (c[1] as { method?: string })?.method === "POST"
        && String(c[0]).includes("/api/dictation/corrections"),
    );
    expect(taught).toHaveLength(1);
  });
});


/* HS-176 counsel C1 (the SPOKEN half) — the walk's own beat 1.

   Pressing TALK and speaking is the path the owner actually takes. The
   words are piped and journaled by the STREAM (`voice_stream.py`), and the
   delivery that follows sends `raw: true`, so the delivery reply carries no
   run facts and rightly invents none. The facts ride the `final` frame
   instead: MicButton hands them to `onReleased`, and the deck merges them
   into the same `result` the typed landing produces. R2: carried out of the
   run that computed them, never re-derived from "the newest journal row". */
describe("the SPOKEN run feeds the same loop (counsel C1)", () => {
  /** Press TALK, speak, release — with the run's facts on the final frame. */
  async function speak(frame: Record<string, unknown>) {
    localStorage.setItem("holdspeak.speakAim", "focused");
    /* the honest `raw: true` reply: delivered, with NO run facts in it. */
    remoteReply = {
      success: true,
      delivered: true,
      final_text: "Ship the Q4 platform on schedule",
    };
    mocks.startStreamSession.mockImplementation(
      async (onEvent: (event: unknown) => void) => ({
        stop: vi.fn().mockImplementation(async () => {
          onEvent(frame);
          return String(frame.text ?? "");
        }),
        cancel: vi.fn(),
        retained: vi.fn().mockResolvedValue(false),
      }),
    );
    announced = [];
    render(
      <ReceiptContext.Provider value={(text: string) => void announced.push(text)}>
        <SpeakFace />
      </ReceiptContext.Provider>,
    );
    const talk = await screen.findByRole("button", { name: "Talk" });
    await userEvent.click(talk);
    await waitFor(() => expect(talk).toHaveAttribute("aria-pressed", "true"));
    await userEvent.click(talk);
    await waitFor(() =>
      expect(
        mocks.apiFetch.mock.calls.filter((c: unknown[]) =>
          String(c[0]).includes("/api/dictation/remote"),
        ),
      ).toHaveLength(1),
    );
    return await screen.findByRole("region", { name: "Pipeline result" });
  }

  const SPOKEN = {
    type: "final",
    text: "Ship the Q4 platform on schedule",
    raw_text: "Ship the queue for platform on schedule",
    corrections_applied: [3],
    journal_id: 11,
  };

  it("delivers the piped words verbatim — one pipeline per utterance", async () => {
    await speak(SPOKEN);
    const [call] = mocks.apiFetch.mock.calls.filter((c: unknown[]) =>
      String(c[0]).includes("/api/dictation/remote"),
    );
    const body = (call[1] as { json: Record<string, unknown> }).json;
    expect(body.raw).toBe(true);
    expect(body.text).toBe("Ship the Q4 platform on schedule");
  });

  it("renders the APPLIED chip from the frame's corrections_applied", async () => {
    const result = await speak(SPOKEN);
    const chip = await within(result).findByRole("button", {
      name: "Corrections applied",
    });
    await userEvent.click(chip);
    const body = await screen.findByRole("region", { name: "Corrections applied" });
    expect(within(body).getByText("queue for")).toBeTruthy();
    expect(within(body).getByText("Q4")).toBeTruthy();
  });

  it("pre-fills the TEXT teach well from the frame's raw transcript", async () => {
    const result = await speak(SPOKEN);
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    const said = within(teach).getByLabelText("What you said") as HTMLTextAreaElement;
    // the RAW transcript, not the LANDED text the delivery reply carried
    expect(said.value).toBe("Ship the queue for platform on schedule");
  });

  it("teaches through the JOURNAL route the frame named", async () => {
    const result = await speak(SPOKEN);
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    await userEvent.clear(within(teach).getByLabelText("What you said"));
    await userEvent.type(
      within(teach).getByLabelText("What you said"),
      "Ship the Q4 platform on schedule",
    );
    await userEvent.click(
      within(teach).getByRole("button", { name: "Teach correction" }),
    );

    const receipt = await within(result).findByRole("status");
    expect(receipt.textContent).toContain("TAUGHT");
    const taught = mocks.apiFetch.mock.calls.filter(
      (c: unknown[]) => (c[1] as { method?: string })?.method === "POST"
        && String(c[0]).includes("/api/dictation/journal/11/correct"),
    );
    expect(taught).toHaveLength(1);
  });

  it("a frame with no facts leaves the reply's own shape alone", async () => {
    const result = await speak({
      type: "final",
      text: "Ship the Q4 platform on schedule",
    });
    // nothing fired, so no chip is drawn (A.8: no counter of zero)
    expect(
      within(result).queryByRole("button", { name: "Corrections applied" }),
    ).toBeNull();
    await userEvent.click(within(result).getByRole("button", { name: "Wrong" }));
    const teach = await screen.findByRole("group", { name: "Correct this result" });
    await userEvent.click(
      within(teach).getByRole("button", { name: "Teach correction" }),
    );
    await within(result).findByRole("status");
    // no `journal_id` to name -> the corrections fallback, as before
    const taught = mocks.apiFetch.mock.calls.filter(
      (c: unknown[]) => (c[1] as { method?: string })?.method === "POST"
        && String(c[0]).includes("/api/dictation/corrections"),
    );
    expect(taught).toHaveLength(1);
  });
});
