// HS-151-07 — ThreadsSection: lists threads by ref, opens pullout on click.
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ThreadsSection } from "../pullouts/shared/ThreadsSection";

const mockListThreadsByRef = vi.fn();
const mockOpenPullout = vi.fn();

vi.mock("../threads", () => ({
  listThreadsByRef: (...args: unknown[]) => mockListThreadsByRef(...args),
}));

vi.mock("../store", () => {
  const useDesk = () => ({});
  useDesk.getState = () => ({ openPullout: mockOpenPullout });
  return { useDesk };
});

afterEach(() => {
  mockListThreadsByRef.mockReset();
  mockOpenPullout.mockReset();
});

describe("ThreadsSection", () => {
  it("renders nothing when no threads reference the object", async () => {
    mockListThreadsByRef.mockResolvedValue([]);
    const { container } = render(<ThreadsSection refId="person_1" />);
    await waitFor(() => expect(mockListThreadsByRef).toHaveBeenCalledWith("person_1"));
    expect(container.querySelector("section")).toBeNull();
  });

  it("renders thread titles when threads reference the object", async () => {
    mockListThreadsByRef.mockResolvedValue([
      {
        id: "thread_1",
        title: "Sprint planning chat",
        last_turn_at: "2026-08-29T10:00:00Z",
        updated_at: "2026-08-29T10:00:00Z",
      },
      {
        id: "thread_2",
        title: "Code review discussion",
        last_turn_at: null,
        updated_at: "2026-08-28T10:00:00Z",
      },
    ]);
    render(<ThreadsSection refId="meeting_42" />);

    expect(await screen.findByText("Sprint planning chat")).toBeInTheDocument();
    expect(screen.getByText("Code review discussion")).toBeInTheDocument();
    expect(screen.getByText("Threads")).toBeInTheDocument();
  });

  it("opens the thread pullout when a row is clicked", async () => {
    mockListThreadsByRef.mockResolvedValue([
      {
        id: "thread_1",
        title: "Sprint planning chat",
        last_turn_at: "2026-08-29T10:00:00Z",
        updated_at: "2026-08-29T10:00:00Z",
      },
    ]);
    render(<ThreadsSection refId="person_1" />);

    const row = await screen.findByText("Sprint planning chat");
    await userEvent.click(row);
    expect(mockOpenPullout).toHaveBeenCalledWith("thread:thread_1");
  });
});
