import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { Pullout } from "./Pullout";

describe("HS-93-04 contextual pull-out actions", () => {
  beforeEach(() => {
    localStorage.clear();
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [
          {
            kind: "note",
            id: "release",
            title: "Release checklist",
            bodyMarkdown: "Ship after checks pass.",
          },
        ],
        coder: [
          {
            kind: "coder",
            id: "waiting",
            sessionId: "session-7",
            title: "App",
            agent: "codex",
            state: "waiting",
            question: "Should I publish?",
          },
        ],
      },
      profiles: [],
      inferenceTargets: [],
      selectedIds: ["note:release"],
      pullouts: [],
      closePullout: vi.fn(),
      openPullout: vi.fn(),
      openEditor: vi.fn(),
      fileIntoDir: vi.fn(),
      removeFromDir: vi.fn(),
      answerCoder: vi.fn().mockResolvedValue(true),
      speakToCoder: vi.fn().mockResolvedValue(true),
      openChat: vi.fn(),
      openToolInspector: vi.fn(),
    });
  });

  it("retains an editable Coder reply through failed delivery and remount", async () => {
    useDesk.setState({ speakToCoder: vi.fn().mockResolvedValue(false) });
    const session = useDesk.getState().items.coder[0];
    const object = {
      kind: "coder" as const,
      id: session.id,
      title: String(session.title),
      ref: session,
    };
    const first = render(
      <MemoryRouter>
        <Pullout o={object} />
      </MemoryRouter>,
    );
    const editor = screen.getByRole("textbox", { name: "Coder reply draft" });
    fireEvent.change(editor, {
      target: { value: "Keep this answer until delivery succeeds." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send reply" }));

    expect(
      await screen.findByText("Delivery failed. Your reply remains editable."),
    ).toBeInTheDocument();
    expect(editor).toHaveValue("Keep this answer until delivery succeeds.");
    first.unmount();

    render(
      <MemoryRouter>
        <Pullout o={object} />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("textbox", { name: "Coder reply draft" }),
    ).toHaveValue("Keep this answer until delivery succeeds.");
    expect(
      screen.getByText("Recovered local reply draft."),
    ).toBeInTheDocument();
  });

  it("reviews and explicitly sends selected material only to a waiting Coder", async () => {
    const session = useDesk.getState().items.coder[0];
    render(
      <MemoryRouter>
        <Pullout
          o={{
            kind: "coder",
            id: session.id,
            title: String(session.title),
            ref: session,
          }}
        />
      </MemoryRouter>,
    );

    expect(
      screen.getByText("Selected source · Release checklist"),
    ).toBeInTheDocument();
    expect(screen.getByText("Ship after checks pass.")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Send Release checklist to App Coder session",
      }),
    );

    await waitFor(() =>
      expect(useDesk.getState().speakToCoder).toHaveBeenCalledWith(
        "codex",
        "session-7",
        "Ship after checks pass.",
      ),
    );
  });
});
