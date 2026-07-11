import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import {
  normalizeWorkroomContext,
  workroomHref,
} from "../workrooms/context";
import { PageHero, WorkroomBar } from "./pageSupport";

describe("HS-93-02 workroom orientation", () => {
  it("shows the Desk subject, intended action, and deterministic return", () => {
    render(
      <MemoryRouter
        initialEntries={[
          workroomHref("/workbench", {
            action: "edit-workflow",
            subjectRef: "workflow:wf-7",
          }),
        ]}
      >
        <PageHero title="Workbench" workroomSubject="Release flow" />
      </MemoryRouter>,
    );

    const context = screen.getByRole("navigation", {
      name: "Workroom context",
    });
    expect(context).toHaveTextContent("From Desk");
    expect(context).toHaveTextContent("Release flow");
    expect(context).toHaveTextContent("Edit workflow");
    expect(
      screen.getByRole("link", { name: "Back to subject on Desk" }),
    ).toHaveAttribute("href", "/?open=workflow%3Awf-7");
  });

  it("does not fabricate a subject for a pasted direct link", () => {
    render(
      <MemoryRouter initialEntries={["/dictation"]}>
        <PageHero title="Dictation" />
      </MemoryRouter>,
    );

    expect(screen.getByText("Opened directly")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Desk" })).toHaveAttribute(
      "href",
      "/",
    );
  });

  it("labels a compatible subject-only return as a subject return", () => {
    const context = normalizeWorkroomContext({
      version: 2,
      origin: "desk",
      subject_ref: "meeting:m1",
      action: "review-meeting",
      return_to: "desk",
      future_hint: "ignored",
    });
    render(
      <MemoryRouter>
        <WorkroomBar context={context} />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("link", { name: "Back to subject on Desk" }),
    ).toHaveAttribute("href", "/?open=meeting%3Am1");
  });
});
