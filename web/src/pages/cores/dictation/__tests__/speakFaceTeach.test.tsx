/* HS-176-02 — the teach loop as it is DRAWN: the RESULT row's APPLIED
   chip and the well it unfolds, the teach row's FIELD cycle, and the
   receipt that takes the teach row's place. No modal, no sentence. */
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpeakFace } from "../SpeakFace";
import { ReceiptContext } from "../shared";

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
vi.mock("../../../../lib/speakToFill", () => ({
  speakToFillSupported: () => true,
  speakToFillUnsupportedReason: () => "",
  retryPendingTranscription: vi.fn(),
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
  teachReply = { recorded: true, kind: "text", key: "queue for", value: "Q4" };
  mocks.apiFetch.mockImplementation(
    (url: string, init?: { method?: string }) => {
      const path = String(url);
      if (init?.method === "POST" && path.includes("dry-run"))
        return Promise.resolve(landed);
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
