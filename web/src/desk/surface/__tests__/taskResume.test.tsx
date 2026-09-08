// HS-200-41 — the TaskResume species: the ratified `UNFINISHED` row.
//
// What is proved here is what the ratified row PROMISES: every state the
// backend can actually reach draws its own chip and its own one verb; an
// absent fact draws no token at all; custody wears `SAVED HERE` / `SAVED ON
// <host>` and never the egress word; and the whole list is one Tab stop the
// arrows walk.
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TaskResume, TaskResumeList } from "../patterns/TaskResume";

const SAVED_AT = "2026-09-07T09:04:00";

function row(props: Partial<React.ComponentProps<typeof TaskResume>> = {}) {
  return (
    <TaskResumeList label="UNFINISHED">
      <TaskResume
        purpose="the architecture review brief"
        state="saved"
        savedAt={SAVED_AT}
        onVerb={() => undefined}
        {...props}
      />
    </TaskResumeList>
  );
}

describe("TaskResume — the states a Room ask can actually reach", () => {
  // Ruling B8: a Room ask is one blocking POST with no job row, so the ONLY
  // states its own record produces are these four. The species accepts the
  // wider vocabulary for story 15; these are the ones this story ships.
  it("saved draws SAVED HH:MM and Resume", () => {
    render(row());
    expect(screen.getByRole("status", { name: "SAVED 09:04" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Resume: the architecture review brief",
      }),
    ).toBeInTheDocument();
  });

  it("failed quotes the target's own words on their OWN row, and draws Check", () => {
    render(
      row({
        state: "failed",
        stoppedReason: "192.168.1.43 UNREACHABLE",
      }),
    );
    // F3: the chip says FAILED and nothing else. `StateChip` neither wraps
    // nor truncates, and a quoted engine reason is routinely a filesystem
    // path — it ran off-glass mid-token at 393.
    expect(screen.getByRole("status", { name: "FAILED" })).toBeInTheDocument();
    // Ruling B5: the reason is QUOTED, never composed by the face — and it
    // lives on a row that can wrap.
    const reason = document.querySelector("[data-task-resume-reason]");
    expect(reason).not.toBeNull();
    expect(reason).toHaveTextContent("192.168.1.43 UNREACHABLE");
    expect(
      screen.getByRole("button", { name: /^Check: / }),
    ).toBeInTheDocument();
    // And never twice: it is not also a token in the chip row.
    expect(
      document.querySelectorAll('[data-task-resume-token="stopped"]'),
    ).toHaveLength(0);
  });

  it("a long quoted path is never truncated to fit a chip (F3)", () => {
    // The shot that caught this: `FAILED · MODEL FILE NOT FOUND:
    // ~/MODELS/GGUF/QWE|` — sliced 205px off-glass with the red border cut
    // through it. The engine's words are not shortened to fit our furniture.
    const PATH =
      "model file not found: ~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf";
    render(row({ state: "failed", stoppedReason: PATH }));
    const reason = document.querySelector("[data-task-resume-reason]");
    expect(reason).toHaveTextContent(PATH);
    // No chip carries it, so no chip can clip it.
    expect(screen.getByRole("status", { name: "FAILED" })).toBeInTheDocument();
  });

  it("falls back to the refusal CODE when the store had no words to quote", () => {
    // The server quotes the destination only while it still observes the
    // state the code names. When the engine came back in the meantime the row
    // holds a code and no reason — and the face draws the code rather than
    // composing a sentence out of it (ruling B5).
    render(row({ state: "failed", stoppedCode: "inference_target_unavailable" }));
    expect(
      document.querySelector("[data-task-resume-reason]"),
    ).toHaveTextContent("inference_target_unavailable");
  });

  it("prefers the quoted words over the code when the store has both", () => {
    render(
      row({
        state: "failed",
        stoppedReason: "model file not found: qwen3-35b.gguf",
        stoppedCode: "inference_target_unavailable",
      }),
    );
    expect(
      document.querySelector("[data-task-resume-reason]"),
    ).toHaveTextContent("model file not found: qwen3-35b.gguf");
    expect(screen.queryByText(/inference_target_unavailable/)).toBeNull();
  });

  it("draws no reason at all when the store holds neither (A.8)", () => {
    render(row({ state: "failed" }));
    expect(screen.getByRole("status", { name: "FAILED" })).toBeInTheDocument();
    expect(document.querySelector("[data-task-resume-reason]")).toBeNull();
    expect(
      document.querySelectorAll('[data-task-resume-token="stopped"]'),
    ).toHaveLength(0);
  });

  it("a failed row keeps its verb — it is the row he comes back to", () => {
    render(row({ state: "failed", stoppedCode: "inference_target_unavailable" }));
    const verb = screen.getByRole("button", { name: /^Check: / });
    expect(verb).toBeEnabled();
  });

  it("accepted draws ACCEPTED MM-DD and Open", () => {
    render(row({ state: "accepted", settledAt: "2026-09-02T11:20:00" }));
    expect(screen.getByRole("status", { name: "ACCEPTED 09-02" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Open: / })).toBeInTheDocument();
  });

  it("discarded draws its chip and NO verb — discard is a state, not a door", () => {
    render(row({ state: "discarded" }));
    expect(screen.getByRole("status", { name: "DISCARDED" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Resume/ })).toBeNull();
  });

  it("carries the three states story 15 will pass from their own owners", () => {
    // The vocabulary is a union across three owners (ruling B8). A Room ask
    // must never be handed a running clock; the species must still draw one
    // when the owner of that state has one.
    const { unmount } = render(row({ state: "running", detail: "00:52" }));
    expect(screen.getByRole("status", { name: "RUNNING · 00:52" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Stop: / })).toBeInTheDocument();
    unmount();

    const waiting = render(row({ state: "waiting" }));
    expect(screen.getByRole("status", { name: "WAITING ON YOU" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Answer: / })).toBeInTheDocument();
    waiting.unmount();

    render(row({ state: "incomplete", detail: "3 OF 4 SOURCES" }));
    expect(
      screen.getByRole("status", { name: "INCOMPLETE · 3 OF 4 SOURCES" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Re-read: / })).toBeInTheDocument();
  });
});

describe("TaskResume — no token for an absent fact (UX-CANON A.8)", () => {
  it("an ask with no recipe draws NO recipe chip — never RECIPE · NONE", () => {
    render(row());
    expect(screen.queryByText(/RECIPE/)).toBeNull();
    expect(
      document.querySelectorAll('[data-task-resume-token="recipe"]'),
    ).toHaveLength(0);
  });

  it("a recipe, when there IS one, rides its own token", () => {
    render(row({ recipe: "Preparation brief" }));
    expect(screen.getByText("RECIPE · Preparation brief")).toBeInTheDocument();
  });

  it("no custody fact draws no custody token", () => {
    render(row());
    expect(
      document.querySelectorAll('[data-task-resume-token="custody"]'),
    ).toHaveLength(0);
  });

  it("an empty list renders NOTHING — no caption of zero", () => {
    const { container } = render(<TaskResumeList label="UNFINISHED">{[]}</TaskResumeList>);
    expect(container.textContent).toBe("");
  });

  it("the caption counts what is there", () => {
    render(
      <TaskResumeList label="UNFINISHED">
        <TaskResume purpose="one" state="saved" savedAt={SAVED_AT} onVerb={() => undefined} />
        <TaskResume purpose="two" state="saved" savedAt={SAVED_AT} onVerb={() => undefined} />
      </TaskResumeList>,
    );
    expect(screen.getByText("UNFINISHED 2")).toBeInTheDocument();
  });
});

describe("TaskResume — custody is SAVED HERE, never THIS DEVICE (ruling B7)", () => {
  it("the host that holds the row says SAVED HERE", () => {
    render(row({ custody: "here" }));
    expect(screen.getByText("SAVED HERE")).toBeInTheDocument();
    // THIS DEVICE is the EGRESS vocabulary (desk/surface/egress.ts:16,25).
    // Two different facts must not wear one token.
    expect(screen.queryByText(/THIS DEVICE/)).toBeNull();
  });

  it("another machine says so in WORDS — never a host id (F1)", () => {
    // The shot that caught this read `SAVED ON
    // REFHOST_671A4CBA26CA42F292CF1EA7252F3C70`. A 40-character opaque id in
    // a token row breaks the `raw-ids` canon rule, and the species has no
    // host prop at all now, so no caller can put one there.
    render(row({ custody: "elsewhere" }));
    expect(screen.getByText("SAVED ON ANOTHER DESK")).toBeInTheDocument();
    expect(screen.queryByText(/THIS DEVICE/)).toBeNull();
    // Nothing that looks like an opaque id is anywhere on the row.
    expect(document.body.textContent).not.toMatch(/[0-9a-f]{16,}/i);
    expect(document.body.textContent).not.toMatch(/refhost/i);
  });
});

describe("TaskResume — the verbs", () => {
  it("every verb is the library Button; no raw <button> (UX-CANON A.1)", () => {
    render(row({ onDiscard: () => undefined }));
    // The one exempt control is `Disclosure`'s own trigger, which the
    // library owns and the contract already specifies as a button trigger
    // with aria-expanded. It is a fold, not a verb.
    const verbs = screen
      .getAllByRole("button")
      .filter((b) => !b.classList.contains("surface-disclosure-trigger"));
    expect(verbs.length).toBeGreaterThan(0);
    for (const button of verbs) expect(button.className).toContain("btn");
  });

  it("Discard is a ConfirmVerb behind MORE, never a bare destructive verb", async () => {
    const onDiscard = vi.fn();
    render(row({ onDiscard }));
    // Closed by default: the destructive verb is not lying in the open.
    expect(screen.queryByRole("button", { name: "Discard the unfinished ask" })).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: /MORE/ }));
    const discard = screen.getByRole("button", { name: "Discard the unfinished ask" });
    // First press ARMS, and fires nothing.
    await userEvent.click(discard);
    expect(onDiscard).not.toHaveBeenCalled();
    expect(discard).toHaveTextContent("Sure?");
    await userEvent.click(discard);
    expect(onDiscard).toHaveBeenCalledTimes(1);
  });

  it("a refused verb is NATIVE disabled and says why in its name", () => {
    render(row({ verbDisabledReason: "unavailable until a route is ready" }));
    const verb = screen.getByRole("button", {
      name: "Resume: unavailable until a route is ready",
    });
    expect(verb).toBeDisabled();
    expect(verb).toHaveAttribute("aria-disabled", "true");
  });

  it("the Project button names the way back", async () => {
    const onOpenProject = vi.fn();
    render(row({ projectName: "Q4 platform", onOpenProject }));
    await userEvent.click(
      screen.getByRole("button", { name: "Open the Project: Q4 platform" }),
    );
    expect(onOpenProject).toHaveBeenCalledTimes(1);
  });
});

describe("TaskResume — keyboard reach", () => {
  it("is ONE Tab stop; Up/Down rove rows and Left/Right walk a row's verbs", async () => {
    const first = vi.fn();
    const second = vi.fn();
    render(
      <TaskResumeList label="UNFINISHED">
        <TaskResume
          purpose="first"
          state="saved"
          savedAt={SAVED_AT}
          onVerb={first}
          onDiscard={() => undefined}
        />
        <TaskResume purpose="second" state="saved" savedAt={SAVED_AT} onVerb={second} />
      </TaskResumeList>,
    );
    const rows = document.querySelectorAll<HTMLElement>(".surface-task-resume");
    const firstVerb = within(rows[0]).getByRole("button", { name: /^Resume: first/ });
    const secondVerb = within(rows[1]).getByRole("button", { name: /^Resume: second/ });

    // Roving tabindex: exactly one stop is tabbable for the whole list.
    const stops = document.querySelectorAll<HTMLElement>(".surface-task-resume button");
    expect([...stops].filter((s) => s.tabIndex === 0)).toHaveLength(1);

    firstVerb.focus();
    fireEvent.keyDown(firstVerb, { key: "ArrowDown" });
    expect(document.activeElement).toBe(secondVerb);
    fireEvent.keyDown(secondVerb, { key: "ArrowUp" });
    expect(document.activeElement).toBe(firstVerb);
    // Left/Right walk the row's own controls (the MORE trigger is one).
    fireEvent.keyDown(firstVerb, { key: "ArrowRight" });
    expect(document.activeElement).not.toBe(firstVerb);
    expect(rows[0].contains(document.activeElement)).toBe(true);
  });

  it("the verb fires from the keyboard", async () => {
    const onVerb = vi.fn();
    render(row({ onVerb }));
    const verb = screen.getByRole("button", { name: /^Resume: / });
    verb.focus();
    await userEvent.keyboard("{Enter}");
    expect(onVerb).toHaveBeenCalledTimes(1);
  });
});
