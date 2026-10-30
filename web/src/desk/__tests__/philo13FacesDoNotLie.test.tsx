/** PHILO-13-04 (A3) — faces that do not lie.
 *
 * 1. Each status face names the one fact it shows: Settings = configured
 *    (`SUMMARY SET ON`), Trust = sends out or not (no lit dot on OFF), the
 *    meeting record = stored (`SUMMARISED` since Phase 16's interior kit,
 *    compositor canvas "Cutover sync"; never `SUMMARY OFF` above its own
 *    summary).
 * 2. A failure is plain words with a verb, never the hub's own text: the
 *    Intelligence BRIEF, the Room publish, People, Ask, the voice failure.
 *    A static fence over those faces' failure branches holds it.
 * 3. A People store failure keeps the person and the unsent note; the
 *    failure is one row with Try again.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../lib/api";
import { failureTitle, plainFailure, plainReason, plainWords } from "../surface/plainFailure";
import { askFailureLabel } from "../components/AskPanel";
import { PeopleCore } from "../../pages/cores/PeopleCore";
import { meetingSummaryState } from "../../pages/cores/history/MeetingHeader";

const SRC = resolve(__dirname, "../..");
const read = (rel: string) => readFileSync(resolve(SRC, rel), "utf8");

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

afterEach(() => vi.unstubAllGlobals());

// replaces: tests/e2e/test_philo13_04_faces_glass.py::TestFacesDoNotLie::test_failures_are_plain_words_with_a_verb
// replaces: tests/e2e/test_philo13_04_faces_glass.py::TestFacesDoNotLie::test_ask_with_no_model_names_the_fact
// replaces: tests/e2e/test_philo13_04_faces_glass.py::TestFacesDoNotLie::test_people_try_again_rereads_the_person
// replaces (with settings.app.test.tsx, chair/arrivalOneThing.test.tsx, history/__tests__/railSummaryStored.philo13.test.tsx):
//   tests/e2e/test_philo13_04_faces_glass.py::TestFacesDoNotLie::test_each_face_names_its_fact
describe("plain failure words (A.3, A.10, Tenet 4)", () => {
  it("names the failure and never carries the hub's own text", () => {
    const cause = new ApiError(503, "people_store_unavailable", { detail: "people_store_unavailable" });
    expect(plainFailure("PEOPLE STORE", cause)).toBe("People store · Not available now");
    // W6-G words: the plain sentence face, and the reason for the hover only.
    expect(plainWords("Could not load people")).toBe("Could not load people · Nothing changed");
    expect(plainWords("Could not park it", "It stays here", "Try again")).toBe("Could not park it · It stays here · Try again");
    expect(failureTitle(cause)).toBe("Not available now · HTTP 503");
    expect(failureTitle(new TypeError("Failed to fetch"))).toBe("Hub unreachable");
    expect(plainFailure("NOT PUBLISHED", new ApiError(500, "injected failure", {}))).toBe(
      "Not published · Hub failed",
    );
    expect(plainReason(new TypeError("Failed to fetch"))).toBe("Hub unreachable");
    expect(plainFailure("BRIEF DID NOT LOAD", new ApiError(500, "injected", {}))).not.toMatch(/injected/);
  });

  it("Ask with no model names the fact, not the model path", () => {
    const failed = askFailureLabel("model file not found: ~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf");
    expect(failed.label).toBe("Engine did not answer");
    expect(failed.label).not.toMatch(/gguf|Models/);
    // Asking again cannot add a model: the verb is withheld (A.11).
    expect(failed.canAskAgain).toBe(true);
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
    expect(face).toMatch(/Open Setup/);
  });

  // PHILO-13-04 fix round (Astra counsel P2): a tooltip is product UI. No
  // title= on these faces may carry the hub's words (r.output, a `detail`,
  // an error string) or a contract sentence (DICTATION_FAILURES ... .message).
  it("static fence: no title= carries server text or a sentence", () => {
    const RAW_TITLE = /title=\{[^}]*(errorDetail|r\.output|\.message\b|\.detail\b|readableError)/s;
    for (const file of [
      "desk/components/AskPanel.tsx",
      "desk/components/MicButton.tsx",
      "desk/pullouts/views/BriefView.tsx",
      "features/project-room/update/UpdatePosture.tsx",
      "pages/cores/PeopleCore.tsx",
    ]) {
      expect(read(file), file).not.toMatch(RAW_TITLE);
    }
    // Round three: the unsupported-browser branch names the fact too; its
    // sentence never rides the title or the accessible name.
    const mic = read("desk/components/MicButton.tsx");
    expect(mic).not.toMatch(/title=\{reason\}/);
    expect(mic).not.toMatch(/unavailable: \$\{reason\}/);
    expect(mic).not.toMatch(/This browser cannot capture/);
    // The contract sentences never reach the mic's face, by any attribute.
    expect(read("desk/components/MicButton.tsx")).not.toMatch(/DICTATION_FAILURES\[failure\]\.message/);
    // Ask keeps no copy of the hub's refusal text for the face at all.
    expect(read("desk/components/AskPanel.tsx")).not.toMatch(/errorDetail/);
  });
});

describe("each face names its fact", () => {
  // Window grammar (2026-10-24): the state is the meeting window's status bar word.
  it("the meeting record says Summary stored over its own summary", () => {
    const detail = { id: "m1", title: "Checkout latency review", intel_status: "disabled", intel: { summary: "Latency came from a cold cache." } };
    expect(meetingSummaryState(detail)).toEqual({ text: "Summary stored", lamp: "ok" });
  });

  it("a meeting with no summary still says it did not run (or that summaries are off)", () => {
    const detail = { id: "m2", title: "Vendor call", intel_status: "disabled", intel: null };
    expect(meetingSummaryState(detail).text).toBe("Summary not run");
    expect(meetingSummaryState(detail, true).text).toBe("Summaries off");
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
    const lamp = await screen.findByText("Sends nothing");
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
      "/api/people/relationships/r1/brief": () => json({ brief: { open_commitments: [], agenda_items: [] } }),
      "/api/projects": () => json({ projects: [] }),
      "/api/door": () => json({ upcoming: [] }),
      "/api/people/relationships/r1/notes": () =>
        storeDown ? json({ detail: "people_store_unavailable" }, 503) : json({ note: { id: "n1" } }),
    };
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const handler = routes[String(input).replace("?counts=1", "")];
      if (!handler) throw new Error(`Unexpected request: ${String(input)}`);
      return handler();
    }));
    render(<PeopleCore scope="people:r1" />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Context" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Context" }));
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    const note = await screen.findByLabelText("Note");
    fireEvent.change(note, { target: { value: "Wants the cutover plan in writing" } });
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));

    expect(await screen.findByText("Could not read the people store · What is on screen stays · Try again")).toBeTruthy();
    // The window keeps the person and the unsent note.
    expect(screen.queryByTestId("people-joy-state")).toBeNull();
    expect(screen.getAllByText("Priya Nair").length).toBeGreaterThan(0);
    expect((screen.getByLabelText("Note") as HTMLTextAreaElement).value).toBe(
      "Wants the cutover plan in writing",
    );
    // Never the hub's code on the face.
    expect(document.body.textContent).not.toMatch(/people_store_unavailable/);

    // Try again re-reads the store; the row leaves and the note is still there.
    storeDown = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.queryByText("Could not read the people store · What is on screen stays · Try again")).toBeNull());
    expect((screen.getByLabelText("Note") as HTMLTextAreaElement).value).toBe(
      "Wants the cutover plan in writing",
    );
  });
});

// PHILO-13-04 fix round (Astra counsel P2): Try again re-runs the read that
// failed, and the failure row leaves only when the person really loads.
describe("People Try again re-reads the person", () => {
  function people(detailAnswers: Array<"down" | "up">) {
    const calls: Record<string, number> = {};
    const routes: Record<string, () => Response> = {
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Priya Nair", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => {
        const next = detailAnswers.shift() ?? "up";
        return next === "down"
          ? json({ detail: "people_store_unavailable" }, 503)
          : json({ relationship: { id: "r1", display_name: "Priya Nair", relationship_kind: "direct_report", notes: [{ id: "n1", topic: "Growth", body: "Wants to lead the EU shard work.", visibility: "leader_private" }] } });
      },
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/people/relationships/r1/brief": () => json({ brief: { open_commitments: [], agenda_items: [] } }),
      "/api/projects": () => json({ projects: [] }),
      "/api/door": () => json({ upcoming: [] }),
    };
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const key = String(input).replace("?counts=1", "");
      calls[key] = (calls[key] ?? 0) + 1;
      const handler = routes[key];
      if (!handler) throw new Error(`Unexpected request: ${key}`);
      return handler();
    }));
    return calls;
  }

  it("a failed detail read: Try again fetches the person again, then the row leaves", async () => {
    const calls = people(["down", "up"]);
    render(<PeopleCore scope="people:r1" />);
    expect(await screen.findByText("Could not read the people store · What is on screen stays · Try again")).toBeTruthy();
    expect(calls["/api/people/relationships/r1"]).toBe(1);

    // The window's own failure row. The Next 1:1 side section has a Try again
    // too when its read fails; which one is on the face first is a race.
    fireEvent.click(within(screen.getByTestId("people-failure")).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(calls["/api/people/relationships/r1"]).toBe(2));
    await waitFor(() => expect(screen.queryByText("Could not read the people store · What is on screen stays · Try again")).toBeNull());
    // Betterment D7: Context is a fold; the kept place may already hold it open.
    const context = screen.getByRole("button", { name: "Context" });
    if (context.getAttribute("aria-expanded") !== "true") fireEvent.click(context);
    expect(await screen.findByText("Wants to lead the EU shard work.")).toBeTruthy();
  });

  it("the row stays while the person read still fails", async () => {
    const calls = people(["down", "down", "up"]);
    render(<PeopleCore scope="people:r1" />);
    expect(await screen.findByText("Could not read the people store · What is on screen stays · Try again")).toBeTruthy();
    // The window's own failure row. The Next 1:1 side section has a Try again
    // too when its read fails; which one is on the face first is a race.
    fireEvent.click(within(screen.getByTestId("people-failure")).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(calls["/api/people/relationships/r1"]).toBe(2));
    await new Promise((r) => setTimeout(r, 50));
    expect(screen.getByText("Could not read the people store · What is on screen stays · Try again")).toBeTruthy();
  });
});

