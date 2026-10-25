import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ThoughtDocumentPane } from "./ThoughtDocumentPane";

/* HS-201-12 — doctrine (a): the Original/Info disclosure, the tag row and
   the formatting rail were REMOVED from this window by the settled design
   (story-12 "The settled design"; the owner's verdict of 2026-09-20).  The
   original capture and the tags stay reachable in the Note pullout, which
   keeps its own cover.  This file now fences what the window MUST be. */
describe("ThoughtDocumentPane — bands 1 and 2", () => {
  const draft = { title: "Well, there's just a little bit of misunderstanding here", body: "Yeah, I have it that way and what about you?", tags: "team" };

  it("is the title of his own and the note — no rail, no tag row, no Info, no orphan mic", () => {
    render(<ThoughtDocumentPane draft={draft} onEdit={vi.fn()} disabled={false} />);

    expect(screen.getByRole("button", { name: "Edit Title" })).toHaveTextContent(draft.title);
    expect(screen.getByRole("region", { name: "Note" })).toBeInTheDocument();
    expect(screen.queryByRole("toolbar", { name: "Markdown formatting" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Info" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add tag" })).not.toBeInTheDocument();
    expect(screen.queryByText(/^Filed$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Saved$/)).not.toBeInTheDocument();
    // The note field carries its OWN mic (the voice law). Window grammar
    // (2026-10-24): it sits at the right end of the note's toolbar, not
    // floating in the body.
    const mic = screen.getByRole("button", { name: /Speak the note/ });
    expect(mic.closest(".thought-note-toolbar-voice")).not.toBeNull();
    expect(screen.getByRole("toolbar", { name: "Note actions" })).toContainElement(mic);
  });

  it("Betterment Q8: no heading repeats the first line; the title bar names the note", () => {
    const body = "Jun is nervous about the cutover weekend.\nMaybe pair him with Mira on call.";
    const { rerender } = render(<ThoughtDocumentPane draft={{ title: "Jun is nervous about the cutover weekend.", body, tags: "" }} onEdit={vi.fn()} disabled={false} />);
    expect(screen.queryByRole("button", { name: "Edit Title" })).not.toBeInTheDocument();
    rerender(<ThoughtDocumentPane draft={{ title: "Thought", body: "", tags: "" }} onEdit={vi.fn()} disabled={false} />);
    expect(screen.queryByRole("button", { name: "Edit Title" })).not.toBeInTheDocument();
  });
});
