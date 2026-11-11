import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { useDesk } from "../../../../desk/store";
import { HistoryCore } from "../../HistoryCore";
import tape from "../../../../desk/__tests__/fixtures/meetings-hub/hs170.json";

vi.mock("../../../../lib/api", async original => ({ ...(await original<typeof import("../../../../lib/api")>()), apiFetch: vi.fn() }));
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: () => () => undefined }), useRuntimeFrame: () => null,
}));
// Capture is the boundary: this lane changes only the saved-record handoff.
vi.mock("../../LiveCore", async () => {
  const { Button } = await import("../../../../components/signal/Signal");
  return { LiveCore: ({ onStopped }: { onStopped(): void }) => <Button onClick={onStopped}>Stop meeting</Button> };
});
const saved = tape["/api/meetings/m-saved-outcomes?include_parked=true"];
beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  useDesk.setState({ liveMeetingId: saved.id, recording: "recording", recordingEpoch: 0, windowsById: {} } as never);
});

it("Stop applies and selects the saved record while the old collection read is still pending", async () => {
  let finishList: (body: unknown) => void = () => {};
  let listAsked = false;
  vi.mocked(apiFetch).mockImplementation((path) => {
    if (String(path) === "/api/meetings?limit=100") {
      listAsked = true;
      return new Promise(resolve => { finishList = resolve; }) as never;
    }
    if (String(path).startsWith(`/api/meetings/${saved.id}`)) return Promise.resolve(saved) as never;
    return Promise.resolve({}) as never;
  });
  render(<HistoryCore scope={`meeting:${saved.id}`} />);
  await waitFor(() => expect(listAsked).toBe(true));
  fireEvent.click(await screen.findByRole("button", { name: "Stop meeting" }));
  // A pre-Stop read cannot replace the newly applied saved record.
  await act(async () => finishList(tape["/api/meetings?parked=true"]));
  const row = await screen.findByTestId(`meeting-row-${saved.id}`);
  expect(row).toHaveAttribute("aria-selected", "true");
  expect(screen.getByTestId("meeting-list-preview")).toHaveTextContent(saved.segments[0].text);
  expect(screen.queryByRole("button", { name: "Stop meeting" })).toBeNull();
});
