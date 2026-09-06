import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { clearWriteFailure, useDeskWriteReceipt } from "../hooks/useWriteReceipt";
import { ChairHome } from "./ChairHome";

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));

function WithReceipt() {
  const { receipt } = useDeskWriteReceipt();
  return <><ChairHome />{receipt}</>;
}

describe("Chair write recovery", () => {
  beforeEach(() => {
    clearWriteFailure();
    vi.mocked(apiFetch).mockReset();
  });

  it("keeps a failed generation actionable and clears the receipt after retry", async () => {
    let attempts = 0;
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/brief/generate") {
        if (++attempts === 1) throw new Error("Connection lost");
        return { sections: {}, shelf: {} };
      }
      return null;
    });
    render(<WithReceipt />);
    fireEvent.click(await screen.findByRole("button", { name: "Generate" }));
    expect(await screen.findByText(/GENERATE BRIEF FAILED/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Generate" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    await waitFor(() => expect(attempts).toBe(2));
    await waitFor(() => expect(screen.queryByText(/GENERATE BRIEF FAILED/)).not.toBeInTheDocument());
  });
});
