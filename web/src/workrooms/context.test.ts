import { describe, expect, it } from "vitest";
import {
  decodeWorkroomContext,
  encodeWorkroomContext,
  makeWorkroomContext,
  normalizeWorkroomContext,
  workroomHref,
  workroomReturnHref,
  workroomSubjectId,
} from "./context";

describe("HS-93-02 workroom context", () => {
  it("round-trips identity and resolves the originating Desk subject", () => {
    const href = workroomHref("/workbench", {
      action: "edit-workflow",
      subjectRef: "workflow:wf-7",
      draftRef: "note:draft-2",
      runRef: "artifact:run-3",
    });
    const context = decodeWorkroomContext(new URL(href, "https://x").search);

    expect(context).toMatchObject({
      version: 1,
      origin: "desk",
      subject_ref: "workflow:wf-7",
      action: "edit-workflow",
      draft_ref: "note:draft-2",
      run_ref: "artifact:run-3",
      return_to: "desk",
      return_ref: "workflow:wf-7",
    });
    expect(workroomSubjectId(context, "workflow")).toBe("wf-7");
    expect(workroomReturnHref(context)).toBe("/?open=workflow%3Awf-7");
  });

  it("ignores unknown orientation metadata for forward compatibility", () => {
    expect(
      normalizeWorkroomContext({
        version: 2,
        origin: "desk",
        subject_ref: "meeting:m1",
        action: "review-meeting",
        return_to: "desk",
        future_hint: "ignored",
      }),
    ).toEqual({
      version: 2,
      origin: "desk",
      subject_ref: "meeting:m1",
      action: "review-meeting",
      return_to: "desk",
    });
  });

  it("refuses authored content in either the envelope or URL", () => {
    expect(
      normalizeWorkroomContext({
        version: 1,
        origin: "desk",
        action: "dictate",
        return_to: "desk",
        transcript: "private words",
      }),
    ).toBeNull();

    const encoded = encodeWorkroomContext(
      makeWorkroomContext({ action: "dictate" }),
    );
    expect(
      decodeWorkroomContext(`?room=${encoded}&text=private%20words`),
    ).toBeNull();
    expect(() =>
      workroomHref("/dictation?prompt=private", { action: "dictate" }),
    ).toThrow(/authored content/i);
  });

  it("uses an explicit Desk fallback for a direct link", () => {
    expect(decodeWorkroomContext("")).toBeNull();
    expect(workroomReturnHref(null)).toBe("/");
  });
});
