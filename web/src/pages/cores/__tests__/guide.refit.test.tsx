// PHILO-17 REFIT: the Guide wing reads what is ready and what is not from
// the hub's readiness checks; the checks that need him lead with their one
// verb; the ready ones and the install commands fold.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import MICROPHONE from "../../../desk/__tests__/fixtures/setup-st3-st5/microphone.json";

vi.mock("../../../lib/api", async (importOriginal) => {
  const original = await importOriginal<typeof import("../../../lib/api")>();
  return {
    ...original,
    apiFetch: vi.fn(async (url: string) => {
      if (url === "/api/setup/status") {
        return {
          overall: "blocked",
          sections: [
            { id: "database", label: "Database", status: "pass", detail: "~/.local/share/holdspeak/holdspeak.db" },
            { id: "where-ai-runs", label: "Where AI runs", status: "warn", detail: "No engine for summaries", fix: null },
            { id: "ffmpeg", label: "ffmpeg", status: "fail", detail: "ffmpeg is not installed", raw: "Not found in PATH", fix: "brew install ffmpeg" },
          ],
        };
      }
      return {};
    }),
  };
});

import { RuntimeDocsCore, commandOf } from "../RuntimeDocsCore";
import { apiFetch } from "../../../lib/api";

afterEach(() => cleanup());

describe("the Guide wing", () => {
  it("a failed readiness read never claims everything is ready", async () => {
    vi.mocked(apiFetch).mockRejectedValueOnce(new Error("Hub unavailable"));
    render(<RuntimeDocsCore />);
    await waitFor(() => expect(screen.getByTestId("guide-headline").textContent).toBe("Readiness not known"));
    expect(screen.queryByText("Everything is ready")).toBeNull();
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
  });

  it("unknown checks keep readiness unknown", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce({ sections: [{ id: "database", label: "Database", status: "unknown", detail: "Not checked" }] });
    render(<RuntimeDocsCore />);
    await waitFor(() => expect(screen.getByTestId("guide-headline").textContent).toBe("Readiness not known"));
    expect(screen.queryByText("Everything is ready")).toBeNull();
    expect(screen.getByText("Not known")).toBeTruthy();
  });
  it("leads with what needs him, one primary, the command on demand, the ready rows folded", async () => {
    const { container } = render(<RuntimeDocsCore />);
    await waitFor(() => expect(screen.getByTestId("guide-headline").textContent).toBe("2 things need you"));
    const list = container.querySelector(".guide-list[aria-label='Needs you']") as HTMLElement;
    const rows = Array.from(list.querySelectorAll(".guide-row-name")).map((n) => n.textContent);
    expect(rows).toEqual(["ffmpeg", "Where AI runs"]);
    // The failing row carries the one primary; the command shows on demand.
    const ffmpeg = screen.getByTestId("guide-check-ffmpeg");
    expect(within(ffmpeg).queryByText("brew install ffmpeg")).toBeNull();
    const show = within(ffmpeg).getByRole("button", { name: "Show the fix" });
    expect(show.className).toContain("btn--primary");
    expect(container.querySelectorAll(".btn--primary")).toHaveLength(1);
    fireEvent.click(show);
    expect(within(ffmpeg).getByText("brew install ffmpeg")).toBeTruthy();
    // The technical fact shows only on demand, under the name.
    expect(within(ffmpeg).queryByText("Not found in PATH")).toBeNull();
    fireEvent.click(within(ffmpeg).getByTestId("guide-raw-toggle-ffmpeg"));
    expect(within(ffmpeg).getByTestId("guide-raw-ffmpeg").textContent).toBe("Not found in PATH");
    // An engine check opens Runs on.
    expect(within(screen.getByTestId("guide-check-where-ai-runs")).getByRole("button", { name: "Choose engines" })).toBeTruthy();
    // The ready check is inside the closed Ready fold.
    const fold = screen.getByTestId("guide-check-database").closest("details");
    expect(fold?.open).toBe(false);
    expect(container.textContent).not.toMatch(/Runtime reference/);
  });

  it("uses the recorded producer state words and keeps the reason in the detail", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce(MICROPHONE);
    render(<RuntimeDocsCore />);
    const row = await screen.findByTestId("guide-check-microphone");
    expect(within(row).getByText("Does not work")).toBeTruthy();
    expect(within(row).getByText("No microphone found")).toBeTruthy();
  });

  it("does not invent a fix verb for a warning with no producer fix", async () => {
    const warningWithoutFix = {
      ...MICROPHONE,
      sections: MICROPHONE.sections.map((section) => ({ ...section, status: "warn", fix: null })),
    };
    vi.mocked(apiFetch).mockResolvedValueOnce(warningWithoutFix);
    render(<RuntimeDocsCore />);
    const row = await screen.findByTestId("guide-check-microphone");
    expect(within(row).getByText("Not ready")).toBeTruthy();
    expect(row.querySelector(".guide-row-verb")).toBeNull();
  });

  it("finds the command in a fix sentence, and none in plain words", () => {
    expect(commandOf("brew install ffmpeg")).toBe("brew install ffmpeg");
    expect(commandOf("Install the hooks for Claude Code and Codex: `holdspeak agent-hook install`")).toBe("holdspeak agent-hook install");
    expect(commandOf("Start HoldSpeak (`holdspeak`) and push Set up local AI")).toBe("holdspeak");
    expect(commandOf("Unset HOLDSPEAK_PEOPLE_KEYSTORE_FILE for production use.")).toBeNull();
  });
});
