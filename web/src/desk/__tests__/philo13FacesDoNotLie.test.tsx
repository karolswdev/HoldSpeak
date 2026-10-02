/** PHILO-13-04 (A3) — faces that do not lie.
 *
 * 1. Each status face names the one fact it shows: Settings = configured
 *    (`SUMMARY SET ON`), Trust = sends out or not (no lit dot on OFF), the
 *    meeting record = stored (`SUMMARY STORED`, never `SUMMARY OFF` above its
 *    own summary).
 * 2. A failure is plain words with a verb, never the hub's own text: the
 *    Intelligence BRIEF, the Room publish, People, Ask, the voice failure.
 *    A static fence over those faces' failure branches holds it.
 * 3. A People store failure keeps the person and the unsent note; the
 *    failure is one row with Try again.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../lib/api";
import { plainFailure, plainReason } from "../surface/plainFailure";
import { askFailureLabel } from "../components/AskPanel";
import { PeopleCore } from "../../pages/cores/PeopleCore";
import { MeetingHeader } from "../../pages/cores/history/MeetingHeader";
import type { MeetingData } from "../../pages/cores/history/useMeetingData";

const SRC = resolve(__dirname, "../..");
const read = (rel: string) => readFileSync(resolve(SRC, rel), "utf8");

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

afterEach(() => vi.unstubAllGlobals());

describe("plain failure words (A.3, A.10, Tenet 4)", () => {
  it("names the failure and never carries the hub's own text", () => {
    const cause = new ApiError(503, "people_store_unavailable", { detail: "people_store_unavailable" });
    expect(plainFailure("PEOPLE STORE", cause)).toBe("PEOPLE STORE · NOT AVAILABLE NOW");
    expect(plainFailure("NOT PUBLISHED", new ApiError(500, "injected failure", {}))).toBe(
      "NOT PUBLISHED · HUB FAILED",
    );
    expect(plainReason(new TypeError("Failed to fetch"))).toBe("HUB UNREACHABLE");
    expect(plainFailure("BRIEF DID NOT LOAD", new ApiError(500, "injected", {}))).not.toMatch(/injected/);
  });

  it("Ask with no model names the fact, not the model path", () => {
    const failed = askFailureLabel("model file not found: ~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf");
    expect(failed.label).toBe("NOT ANSWERED · NO MODEL TO RUN IT");
    expect(failed.label).not.toMatch(/gguf|Models/);
    // Asking again cannot add a model: the verb is withheld (A.11).
    expect(failed.canAskAgain).toBe(false);
  });

  it("static fence: the failure branches of these faces print no raw server text", () => {
    for (const file of [
      "desk/pullouts/views/BriefView.tsx",
      "features/project-room/update/useUpdateController.ts",
      "pages/cores/PeopleCore.tsx",
    ]) {
      expect(read(file), file).not.toMatch(/readableError\(/);
    }
    const ask = read("desk/components/AskPanel.tsx");
    expect(ask).not.toMatch(/setError\(r\.output\)/);
    // The voice failure is a name + library Buttons, never the sentence.
    const mic = read("desk/components/MicButton.tsx");
    const face = mic.slice(mic.indexOf('className="desk-mic-failure"'));
    // The message may ride the title attribute; it is never a child line.
    expect(face.slice(0, face.indexOf("</span>"))).not.toMatch(/^\s*\{DICTATION_FAILURES\[failure\]\.message\}\s*$/m);
    expect(face).toMatch(/Open Setup/);
  });
});

describe("each face names its fact", () => {
  it("the meeting record says SUMMARY STORED above its own summary", () => {
    const detail = { id: "m1", title: "Checkout latency review", intel_status: "disabled", intel: { summary: "Latency came from a cold cache." } };
    const data = { detail, startedAt: "2026-10-01T08:00:00", durationS: 2700 } as unknown as MeetingData;
    render(<MeetingHeader meeting={detail} data={data} />);
    expect(document.body.textContent).toMatch(/SUMMARY STORED/);
    expect(document.body.textContent).not.toMatch(/SUMMARY OFF/);
  });

  it("a meeting with no summary still says OFF", () => {
    const detail = { id: "m2", title: "Vendor call", intel_status: "disabled", intel: null };
    const data = { detail, startedAt: "2026-10-01T09:00:00", durationS: 1800 } as unknown as MeetingData;
    render(<MeetingHeader meeting={detail} data={data} />);
    expect(document.body.textContent).toMatch(/SUMMARY OFF/);
  });

  it("Trust: a route that sends nothing is not a lit green dot", async () => {
    vi.resetModules();
    vi.doMock("../../lib/api", async (orig) => ({
      ...(await orig<typeof import("../../lib/api")>()),
      apiFetch: vi.fn().mockResolvedValue({
        trust: {
          transcript_egress: "none",
          destinations: [{ id: "meeting_intel", name: "Meeting summary", enabled: false, destination: "Summary route unavailable" }],
        },
      }),
    }));
    const { TrustWindow, useTrustWindow } = await import("../components/TrustWindow");
    useTrustWindow.setState({ open: true });
    render(<TrustWindow />);
    const lamp = await screen.findByText("SENDS NOTHING");
    expect(lamp.closest(".gadget-lamp")).toHaveAttribute("data-on", "false");
    expect(screen.queryByText("Off")).toBeNull();
    vi.doUnmock("../../lib/api");
  });
});

describe("a People store failure keeps the window and the note", () => {
  it("Priya and the unsent note stay; the failure is one row with Try again", async () => {
    let storeDown = true;
    const routes: Record<string, () => Response> = {
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Priya Nair", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Priya Nair", relationship_kind: "direct_report", notes: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/projects": () => json({ projects: [] }),
      "/api/door": () => json({ upcoming: [] }),
      "/api/people/relationships/r1/notes": () =>
        storeDown ? json({ detail: "people_store_unavailable" }, 503) : json({ note: { id: "n1" } }),
    };
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const handler = routes[String(input)];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    }));
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("tab", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    const note = await screen.findByLabelText("Grounding note");
    fireEvent.change(note, { target: { value: "Wants the cutover plan in writing" } });
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));

    expect(await screen.findByText("PEOPLE STORE · NOT AVAILABLE NOW")).toBeTruthy();
    // The window keeps the person and the unsent note.
    expect(screen.queryByTestId("people-joy-state")).toBeNull();
    expect(screen.getAllByText("Priya Nair").length).toBeGreaterThan(0);
    expect((screen.getByLabelText("Grounding note") as HTMLTextAreaElement).value).toBe(
      "Wants the cutover plan in writing",
    );
    // Never the hub's code on the face.
    expect(document.body.textContent).not.toMatch(/people_store_unavailable/);

    // Try again re-reads the store; the row leaves and the note is still there.
    storeDown = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.queryByText("PEOPLE STORE · NOT AVAILABLE NOW")).toBeNull());
    expect((screen.getByLabelText("Grounding note") as HTMLTextAreaElement).value).toBe(
      "Wants the cutover plan in writing",
    );
  });
});
