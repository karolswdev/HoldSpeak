import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../lib/api";
import { keptReceipt } from "../keptReceipt";
import { useDesk } from "../store";
import type { Thought, ThoughtWorkspaceProjection } from "../thoughts";
import { ThoughtWorkspaceWindow } from "./ThoughtWorkspaceWindow";

/* PHILO-3-04 — the thought's receipt (canvas ratified 2026-09-23).
 *
 * Lying-double law (reference_lying_test_doubles): nothing here mocks the
 * writer or `desk/thoughts`. The REAL `useThoughtNoteWriter` drives the REAL
 * `saveThoughtWorkingInWorkspace`; only `apiFetch` — the wire — is replaced,
 * and it answers the way the wire does: a payload, a thrown TypeError (no
 * response), or the real `ApiError` with a status. */

vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../components/DeskWindow", () => ({
  DeskWindowFrame: ({ children }: { children: React.ReactNode }) => <section aria-label="Thought">{children}</section>,
}));
vi.mock("./ThoughtDocumentPane", () => ({
  ThoughtDocumentPane: ({ draft, onEdit }: { draft: { body: string }; onEdit: (patch: { body: string }) => void }) =>
    <textarea aria-label="Note body" value={draft.body} onChange={(event) => onEdit({ body: event.target.value })} />,
}));
vi.mock("./ThoughtReadsWell", () => ({ ThoughtReadsWell: () => null }));
vi.mock("../sprites", () => ({ spriteUrl: () => "note.png" }));
vi.mock("../shell", () => ({ openSurfaceOr: vi.fn() }));

const LOADED = "2026-09-22T09:05:00Z";
const WRITTEN = "2026-09-22T17:41:00Z";
/* The client clock sits far from both hub stamps: a receipt read from the
   clock cannot pass these assertions. */
const CLIENT_CLOCK = new Date("2031-03-03T23:59:00Z");
const receiptOf = (stamp: string) => keptReceipt(Date.parse(stamp))!.toUpperCase();

const thought: Thought = {
  id: "thought-1", source: { kind: "typed" }, raw_captured_at: "2026-09-22T09:00:00Z", state: "working",
  aggregate_revision: 3, lifecycle_revision: 1, working_revision: 2, attachment_revision: 1, attachments: [],
  working_note: { id: "note-1", title: "Restart plan", body_markdown: "Drain the queue", tags: [], last_modified: LOADED },
  filing_status: "filed", directory_id: "dir-planning", directory_name: "Planning",
};
const cursor = { hub_id: "hub-1", thought_id: thought.id, aggregate_revision: 3, continuity_revision: 4 };

function projection(of: Thought): ThoughtWorkspaceProjection {
  return {
    schema_version: 1, process_scope: { kind: "hub_local", hub_id: "hub-1", state: "available" },
    workspace_cursor: { ...cursor, aggregate_revision: of.aggregate_revision }, thought: of, workspace_state: "idle",
    actions: { primary: { kind: "refine" }, state: [{ kind: "refine" }], ambient: ["update_working", "attach_context", "complete"] },
    review: null, context_status: { summary: "None", state: "empty", repair_ref: null },
    inference: { availability: "ready", continuation_admission: "ready", intended_placement: { target_id: "this_machine", target_name: "This device", target_kind: "this_device", boundary: "same_device", readiness: "ready" } },
    terminal_status: null,
  };
}

const written = (): Thought => ({
  ...thought, aggregate_revision: 4, working_revision: 3,
  working_note: { ...thought.working_note, body_markdown: "Drain the queue first", last_modified: WRITTEN },
});

/** The wire: GET workbench answers the projection; PATCH working answers `patch`. */
function wire(patch: () => Promise<unknown>, start: Thought = thought) {
  vi.mocked(apiFetch).mockImplementation(async (input: string, init?: RequestInit) => {
    if (input.endsWith("/workbench")) return projection(start) as never;
    if (input.endsWith("/working") && init?.method === "PATCH") return await patch() as never;
    throw new Error(`unexpected request ${init?.method ?? "GET"} ${input}`);
  });
}
const patchCalls = () => vi.mocked(apiFetch).mock.calls.filter(([input]) => String(input).endsWith("/working"));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function writeLine(): HTMLElement {
  const line = document.querySelector<HTMLElement>(".thought-note-foot .surface-footer-receipt-line:not([data-line])");
  if (!line) throw new Error("no write line in the foot");
  return line;
}
const filingLine = () => document.querySelector<HTMLElement>(".thought-note-foot .surface-footer-receipt-line[data-line=\"filing\"]");

async function openAndEdit(value = "Drain the queue first") {
  render(<ThoughtWorkspaceWindow object={{ id: "note-1", kind: "note", title: "Thought" } as never} thought={thought} onClose={vi.fn()} />);
  const body = await screen.findByRole("textbox", { name: "Note body" });
  fireEvent.change(body, { target: { value } });
  return body;
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(CLIENT_CLOCK);
  sessionStorage.clear();
  useDesk.setState({ editingId: null, closeEditor: vi.fn() });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("PHILO-3-04 the thought's receipt", () => {
  it("KEPT: opens on the loaded note's stamp, with the drawer on its own line", async () => {
    wire(async () => ({ thought: written(), workbench: projection(written()) }));
    render(<ThoughtWorkspaceWindow object={{ id: "note-1", kind: "note", title: "Thought" } as never} thought={thought} onClose={vi.fn()} />);
    await screen.findByRole("textbox", { name: "Note body" });
    expect(writeLine()).toHaveTextContent(receiptOf(LOADED));
    expect(writeLine().textContent).toMatch(/^KEPT · /);
    expect(writeLine()).toHaveAttribute("role", "status");
    expect(writeLine()).not.toHaveAttribute("data-tone");
    expect(filingLine()).toHaveTextContent(/^IN PLANNING$/);
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("SAVING… from the edit through the 450 ms wait and the PATCH, then KEPT at the HUB's stamp", async () => {
    const answer = deferred<unknown>();
    wire(() => answer.promise);
    await openAndEdit();
    // Inside the 450 ms wait: nothing is sent yet, the foot already says so.
    expect(patchCalls()).toHaveLength(0);
    expect(writeLine()).toHaveTextContent(/^SAVING…$/);
    // The PATCH in flight.
    await waitFor(() => expect(patchCalls()).toHaveLength(1));
    expect(writeLine()).toHaveTextContent(/^SAVING…$/);
    await act(async () => { answer.resolve({ thought: written(), workbench: projection(written()) }); });
    await waitFor(() => expect(writeLine()).toHaveTextContent(receiptOf(WRITTEN)));
    // The time is the response's last_modified — never the loaded stamp, never the client clock.
    expect(receiptOf(WRITTEN)).not.toBe(receiptOf(LOADED));
    expect(writeLine().textContent).not.toBe(keptReceipt(CLIENT_CLOCK.getTime())!.toUpperCase());
    expect(filingLine()).toHaveTextContent(/^IN PLANNING$/);
  });

  it("DID NOT SAVE · THE HUB DID NOT ANSWER when the write gets no response, and Retry keeps it", async () => {
    let calls = 0;
    wire(async () => {
      calls += 1;
      if (calls === 1) throw new TypeError("Failed to fetch");
      return { thought: written(), workbench: projection(written()) };
    });
    const body = await openAndEdit();
    await waitFor(() => expect(writeLine()).toHaveTextContent(/^DID NOT SAVE · THE HUB DID NOT ANSWER$/));
    expect(writeLine()).toHaveAttribute("data-tone", "danger");
    expect(body).toHaveValue("Drain the queue first");
    expect(screen.queryByText(/Could not save|Try again|Retry save/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reload" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(writeLine()).toHaveTextContent(receiptOf(WRITTEN)));
    expect(patchCalls()).toHaveLength(2);
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it.each([422, 500])("DID NOT SAVE · THE HUB DID NOT ACCEPT THE CHANGE on HTTP %i", async (status) => {
    wire(async () => { throw new ApiError(status, "refused", { error: "refused" }); });
    await openAndEdit();
    await waitFor(() => expect(writeLine()).toHaveTextContent(/^DID NOT SAVE · THE HUB DID NOT ACCEPT THE CHANGE$/));
    expect(writeLine()).toHaveAttribute("data-tone", "danger");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(filingLine()).toHaveTextContent(/^IN PLANNING$/);
  });

  it("CHANGED ELSEWHERE on a conflict, with Reload and no Retry", async () => {
    const elsewhere: Thought = { ...thought, aggregate_revision: 9, working_revision: 7, working_note: { ...thought.working_note, body_markdown: "The hub's version" } };
    wire(async () => { throw new ApiError(409, "conflict", { error: "thought_revision_conflict", context: { current: elsewhere } }); });
    await openAndEdit();
    await waitFor(() => expect(writeLine()).toHaveTextContent(/^CHANGED ELSEWHERE$/));
    expect(writeLine()).toHaveAttribute("data-tone", "danger");
    expect(screen.getByRole("button", { name: "Reload" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
    expect(screen.queryByText(/changed elsewhere\.|unsaved edits/i)).not.toBeInTheDocument();
  });

  it("NOT IN A DRAWER when the note is not filed", async () => {
    const loose: Thought = { ...thought, filing_status: "missing", directory_id: undefined, directory_name: undefined };
    wire(async () => ({ thought: loose }), loose);
    render(<ThoughtWorkspaceWindow object={{ id: "note-1", kind: "note", title: "Thought" } as never} thought={loose} onClose={vi.fn()} />);
    await screen.findByRole("textbox", { name: "Note body" });
    expect(filingLine()).toHaveTextContent(/^NOT IN A DRAWER$/);
  });
});
