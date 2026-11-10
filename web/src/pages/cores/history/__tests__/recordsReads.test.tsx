import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { useMeetingList } from "../useMeetingList";
import { MeetingPreview } from "../MeetingPreview";
import first from "../../../../desk/__tests__/fixtures/meetings-hub/hs170.json";
import second from "../../../../desk/__tests__/fixtures/meetings-hub/hs172.json";
import prepared from "../../../../desk/__tests__/fixtures/meetings-hub/prepared.json";
vi.mock("../../../../lib/api", async (original) => ({ ...(await original<typeof import("../../../../lib/api")>()), apiFetch: vi.fn() }));
beforeEach(() => vi.mocked(apiFetch).mockReset());

it("a late find response cannot replace the newer search result", async () => {
  let finish: (body: unknown) => void = () => {};
  vi.mocked(apiFetch).mockImplementation((path) => String(path).endsWith("old")
    ? new Promise((resolve) => { finish = resolve; }) as never
    : Promise.resolve(second["/api/meetings?limit=100"]) as never);
  const { result, rerender } = renderHook(({ url }) => useMeetingList(url), { initialProps: { url: "/api/meetings?search=old" } });
  rerender({ url: "/api/meetings?search=new" });
  await waitFor(() => expect(result.current.data).toEqual(second["/api/meetings?limit=100"]));
  await act(async () => finish(first["/api/meetings?limit=100"]));
  expect(result.current.data).toEqual(second["/api/meetings?limit=100"]);
});

it("a late preview cannot insert the previous meeting's summary", async () => {
  let finish: (body: unknown) => void = () => {};
  const previous = prepared["/api/meetings/c5-review?include_parked=true"];
  const next = first["/api/meetings/m-saved-outcomes?include_parked=true"];
  vi.mocked(apiFetch).mockImplementation((path) => {
    if (String(path) === "/api/meetings/c5-review") return new Promise((resolve) => { finish = resolve; }) as never;
    return Promise.resolve(String(path).includes("decisions") ? { decisions: [] } : next) as never;
  });
  const { rerender } = render(<MeetingPreview meeting={previous} />);
  rerender(<MeetingPreview meeting={next} />);
  await waitFor(() => expect(screen.getByTestId("meeting-list-preview")).toHaveTextContent("No summary"));
  await act(async () => finish(previous));
  expect(screen.getByTestId("meeting-list-preview")).toHaveTextContent(next.title!);
  expect(screen.getByTestId("meeting-list-preview")).not.toHaveTextContent(previous.intel.summary);
});


it("selection shows the saved transcript without opening a fold", async () => {
  const meeting = first["/api/meetings/m-saved-outcomes?include_parked=true"];
  vi.mocked(apiFetch).mockImplementation((path) => Promise.resolve(String(path).includes("decisions") ? { decisions: [] } : meeting) as never);
  render(<MeetingPreview meeting={meeting} />);
  const words = meeting.segments[0].text;
  expect(await screen.findByText(words, { exact: true })).toBeVisible();
});
