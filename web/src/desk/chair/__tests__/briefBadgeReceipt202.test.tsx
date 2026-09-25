/* HS-202-02 arrival item — `Generate` is badged before and receipted after.
 *
 * 03-interaction-walk.md finding 4 and Appendix B.1 list `Generate` among
 * "eleven egress verbs [that] carry neither a badge before nor a receipt
 * after", and it was one of the two FIRED live on the wire
 * (`POST /api/brief/generate` "recorded with no badge on the row").
 *
 * What the audit assumed about the destination is not what the hub does:
 * `MondayBriefService.generate` and `_compose_overlay`
 * (holdspeak/web/routes/monday_brief.py:110-115) read the database, the
 * People sidecar and the follow-through service — SQL and local files, no
 * model, no network (neither module imports an inference path). So the
 * honest badge names THIS DEVICE, and the honest receipt names what was
 * built.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BriefEgress, briefReceipt } from "../briefEgress";

describe("the brief's badge (HS-202-02)", () => {
  it("names the destination the hub actually uses", () => {
    render(<BriefEgress />);
    expect(screen.getByText("THIS DEVICE")).toBeVisible();
  });

  it("carries the local scope, not a bare chip", () => {
    const { container } = render(<BriefEgress />);
    expect(
      container.querySelector(".gadget-chip-egress")?.getAttribute("data-scope"),
    ).toBe("local");
  });
});

describe("the brief's receipt (HS-202-02)", () => {
  it("says nothing before the verb is pressed", () => {
    expect(briefReceipt(null)).toBeNull();
  });

  it("names what was built and when", () => {
    const line = briefReceipt({
      sections: { changed: [{ id: "a" }], waiting: [{ id: "b" }] },
      generated_at: "2026-09-20T15:41:00",
    });
    expect(line).toBe("Brief ready · 2 items · SEP 20 15:41");
  });

  it("never counts zero (UX-CANON A.8)", () => {
    expect(
      briefReceipt({ sections: {}, generated_at: "2026-09-20T15:41:00" }),
    ).toBe("Brief ready · SEP 20 15:41");
  });

  it("states one item in the singular", () => {
    expect(
      briefReceipt({
        sections: { changed: [{ id: "a" }] },
        generated_at: "2026-09-20T15:41:00",
      }),
    ).toBe("Brief ready · 1 item · SEP 20 15:41");
  });
});
