// The other window families obey the same rule (owner ratified 2026-10-04):
// the title is the name of the thing; no face shows a raw id as a name.
// Real mappers, real world list, real frame and registry.
import { lazy } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import {
  EMPTY_ITEMS, fromWireDecision, fromWireKb, fromWireMeeting, fromWireNote, fromWireThread,
} from "../api";
import { allObjects } from "../world";
import { wireString } from "../wireGuard";
import { primitiveName } from "../windowName";
import { SurfaceWindowHost, type SurfaceRow } from "../components/SurfaceWindows";
import { registrySnapshot } from "../components/window/windowRegistry";
import { useWindowTitle } from "../surface/title";
import { windowName } from "../windowName";
import { useDesk } from "../store";

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({ panelRects: {}, panelSaved: [], panelOrder: [], panelMin: [], panelMax: [], windowsById: {} });
});

describe("the shared cause: an empty title from the hub", () => {
  it("wireString: an empty string takes the fallback; with no fallback it stays empty", () => {
    expect(wireString({ title: "" }, "title", "Fallback")).toBe("Fallback");
    expect(wireString({ title: "   " }, "title", "Fallback")).toBe("Fallback");
    expect(wireString({ title: "Real" }, "title", "Fallback")).toBe("Real");
    expect(wireString({ title: "" }, "title")).toBe("");
    expect(wireString({ title: 7 }, "title", "Fallback")).toBe("Fallback");
  });

  it("the mappers name a thread, a meeting and a decision that have no title", () => {
    expect(fromWireThread({ id: "th_9f8a7b6c5d4e", title: "" })?.title).toBe("New thread");
    expect(fromWireThread({ id: "th_9f8a7b6c5d4e", title: "th_9f8a7b6c5d4e" })?.title).toBe("New thread");
    expect(fromWireThread({ id: "th_9f8a7b6c5d4e", title: "Ledger questions" })?.title).toBe("Ledger questions");
    expect(fromWireMeeting({ id: "m1", title: "", started_at: "2026-10-03T21:06:00" })?.title).toBe("Meeting, Oct 3, 21:06");
    expect(fromWireMeeting({ id: "m1", title: "Ledger review", started_at: "2026-10-03T21:06:00" })?.title).toBe("Ledger review");
    expect(fromWireDecision({ id: "d1", title: "", decision_markdown: "Freeze the ledger on Friday.\nMore." })?.title)
      .toBe("Freeze the ledger on Friday.");
  });

  it("the Desk's list of things never shows an id as a name", () => {
    const items = {
      ...EMPTY_ITEMS,
      note: [
        fromWireNote({ id: "note_624495deb1f5", title: "", body_markdown: "- Check the queue depth\nmore" })!,
        fromWireNote({ id: "note_096c07e82f35", title: "", body_markdown: "" })!,
        fromWireNote({ id: "note_f050942fc320", title: "Thought", body_markdown: "Ask Priya about the freeze" })!,
        fromWireNote({ id: "note_3eba286de7ff", title: "Thought", body_markdown: "" })!,
      ],
      thread: [fromWireThread({ id: "th_9f8a7b6c5d4e", title: "" })!],
      kb: [fromWireKb({ id: "kb_12ab34cd56ef", name: "" })!],
      meeting: [fromWireMeeting({ id: "m_0a1b2c3d4e5f", title: "", started_at: "2026-10-03T21:06:00" })!],
      decision: [fromWireDecision({ id: "d_0a1b2c3d4e5f", title: "", decision_markdown: "" })!],
    };
    const names = Object.fromEntries(allObjects(items).map((o) => [o.id, o.title]));
    expect(names).toEqual({
      note_624495deb1f5: "Check the queue depth",
      note_096c07e82f35: "New note",
      note_f050942fc320: "Ask Priya about the freeze",
      note_3eba286de7ff: "New thought",
      th_9f8a7b6c5d4e: "New thread",
      kb_12ab34cd56ef: "New knowledge base",
      m_0a1b2c3d4e5f: "Meeting, Oct 3, 21:06",
      d_0a1b2c3d4e5f: "New decision",
    });
    for (const o of allObjects(items)) expect(o.title).not.toBe(o.id);
  });

  it("a thread with no title takes the first words of its first message", () => {
    expect(primitiveName("thread", { title: "" }, "th_9f8a7b6c5d4e", "What changed in the ledger this week?"))
      .toBe("What changed in the ledger this week?");
    expect(primitiveName("thread", { title: "Ledger questions" }, "th_9f8a7b6c5d4e", "What changed?")).toBe("Ledger questions");
    // A kind with no rule of its own keeps its title; an id is not a name.
    expect(primitiveName("story", { title: "HS-201-12" }, "s1")).toBe("HS-201-12");
    expect(primitiveName("workflow", { name: "" }, "wf_1")).toBe("Workflow");
  });
});

describe("a window that shows one record of a program", () => {
  const core = (body: () => JSX.Element) => lazy(async () => ({ default: body }));
  const project = { kind: "project", id: "p-ledger", name: "Payments ledger cutover" };

  it("a Project Room is named by its project; Desk memory with no project keeps its word", async () => {
    const row: SurfaceRow = { key: "open-project-memory", id: "surface-project-memory", title: "Desk memory", glyph: "▤", eyebrow: "", Core: core(() => <p>room</p>) };
    const items = { ...EMPTY_ITEMS, project: [project] } as typeof EMPTY_ITEMS;
    const { rerender } = render(<SurfaceWindowHost row={row} scope="project:p-ledger" items={items} />);
    await screen.findByText("room");
    expect(registrySnapshot.find((w) => w.id === "surface-project-memory")?.label).toBe("Payments ledger cutover");
    expect(screen.getByRole("region", { name: "Payments ledger cutover" })).toBeTruthy();
    rerender(<SurfaceWindowHost row={row} scope={undefined} items={items} />);
    await waitFor(() => expect(registrySnapshot.find((w) => w.id === "surface-project-memory")?.label).toBe("Desk memory"));
  });

  it("a core names its window by the open section: Settings · Connections", async () => {
    const Section = () => { useWindowTitle(windowName({ kind: "settings", section: "Connections" }), []); return <p>section</p>; };
    const row: SurfaceRow = { key: "configure-settings", id: "surface-settings", title: "Settings", glyph: "⚙", eyebrow: "", Core: core(Section) };
    render(<SurfaceWindowHost row={row} scope="integrations" items={EMPTY_ITEMS} />);
    await screen.findByText("section");
    await waitFor(() => expect(registrySnapshot.find((w) => w.id === "surface-settings")?.label).toBe("Settings · Connections"));
  });
});
