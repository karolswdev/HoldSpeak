/* PHILO-5-04 C2-C3 — a fresh Chair read owns the rendered receipt.
 *
 * The populated answer is a complete retained producer response. The null
 * and rejected answers exercise the two distinct read outcomes: null means
 * no brief, while a failed read names the failure and does not invent one.
 * The C3 later-read tests use StrictMode's two actual mount reads; they do
 * not claim to exercise an already-open refresh.
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";
import { briefReceipt, type GeneratedBrief } from "../briefEgress";
import latestPayload from "./fixtures/philo504/latest-run4.json";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

let latest: Record<string, unknown> | null = latestPayload;
let latestFailure = false;

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T | PromiseLike<T>) => void;
  reject: (reason?: unknown) => void;
};

function deferred<T>(): Deferred<T> {
  let resolve!: Deferred<T>["resolve"];
  let reject!: Deferred<T>["reject"];
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function wireWithLatestReader(readLatest: () => unknown) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    const url = String(path);
    if (url === "/api/inference/assignments") {
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 } as never;
    }
    if (url.startsWith("/api/desk/needs-you")) {
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    }
    if (url.startsWith("/api/brief/latest")) return await readLatest() as never;
    return null as never;
  });
}

function wire() {
  wireWithLatestReader(() => {
    if (latestFailure) throw new Error("retained read failure");
    return latest;
  });
}

const LATEST_RECEIPT = "Brief ready · 5 items · SEP 25 18:08";

async function actResolve<T>(pending: Deferred<T>, value: T) {
  await act(async () => {
    pending.resolve(value);
  });
}

describe("fresh brief read (PHILO-5-04 C2-C3)", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    latest = latestPayload;
    latestFailure = false;
    wire();
  });

  it("renders the latest producer receipt without pressing Generate", async () => {
    render(<ChairHome />);

    const receipt = await screen.findByTestId("arrival-brief-receipt");
    expect(briefReceipt(latestPayload as unknown as GeneratedBrief)).toBe(LATEST_RECEIPT);
    expect(receipt.textContent).toBe(LATEST_RECEIPT);
    expect(screen.getByTestId("arrival-brief-generate")).toBeEnabled();
    expect(
      vi.mocked(apiFetch).mock.calls.some(([path]) => path === "/api/brief/generate"),
    ).toBe(false);
  });

  it("leaves the receipt slot absent when latest answers null", async () => {
    latest = null;
    render(<ChairHome />);

    await screen.findByText("No brief yet");
    expect(screen.queryByTestId("arrival-brief-receipt")).toBeNull();
    expect(screen.getByTestId("arrival-brief-generate")).toBeEnabled();
  });

  it("names a latest read failure instead of claiming no brief exists", async () => {
    latest = null;
    latestFailure = true;
    render(<ChairHome />);

    const failure = await screen.findByTestId("arrival-brief-load-failed");
    expect(failure.textContent).toContain("BRIEF DID NOT LOAD");
    expect(failure.textContent).toContain("NO ANSWER");
    expect(screen.queryByText("No brief yet")).toBeNull();
    await waitFor(() => expect(screen.getByTestId("arrival-brief-retry")).toBeEnabled());
  });

  it("retains the first receipt when StrictMode's later mount read fails", async () => {
    const firstRead = deferred<Record<string, unknown>>();
    const laterRead = deferred<Record<string, unknown>>();
    let latestReads = 0;
    let laterReadRejected = false;
    laterRead.promise.catch(() => { laterReadRejected = true; });
    wireWithLatestReader(() => {
      latestReads += 1;
      return latestReads === 1 ? firstRead.promise : laterRead.promise;
    });

    render(
      <StrictMode>
        <ChairHome />
      </StrictMode>,
    );
    await waitFor(() => expect(latestReads).toBe(2));

    await actResolve(firstRead, latestPayload);
    const receipt = await screen.findByTestId("arrival-brief-receipt");
    expect(receipt.textContent).toBe(LATEST_RECEIPT);

    await act(async () => {
      laterRead.reject(new Error("later retained read failure"));
    });
    await waitFor(() => expect(laterReadRejected).toBe(true));
    expect(screen.getByTestId("arrival-brief-receipt").textContent).toBe(LATEST_RECEIPT);
  });

  it("clears the first receipt when StrictMode's later mount read answers null", async () => {
    const firstRead = deferred<Record<string, unknown>>();
    const laterRead = deferred<Record<string, unknown> | null>();
    let latestReads = 0;
    wireWithLatestReader(() => {
      latestReads += 1;
      return latestReads === 1 ? firstRead.promise : laterRead.promise;
    });

    render(
      <StrictMode>
        <ChairHome />
      </StrictMode>,
    );
    await waitFor(() => expect(latestReads).toBe(2));

    await actResolve(firstRead, latestPayload);
    await screen.findByTestId("arrival-brief-receipt");
    await act(async () => { laterRead.resolve(null); });
    await waitFor(() => expect(screen.queryByTestId("arrival-brief-receipt")).toBeNull());
    expect(screen.getByText("No brief yet")).toBeInTheDocument();
  });
});
