// Phase 16 — the interior kit: AppHead + StatusStrip (COMPOSITOR.md §11;
// contract.md "The interior kit"). The one big fact (display 26/650, once per
// window) with the strip of tokens on the same baseline; never prose.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AppHead, StatusStrip } from "..";
import { Button } from "../../../components/signal/Signal";

describe("AppHead + StatusStrip (Phase 16 kit)", () => {
  it("draws the fact once, at the display step, with the strip beside it", () => {
    const { container } = render(
      <AppHead fact="7 need you" data-testid="head" factTestId="fact">
        <StatusStrip
          items={[
            { key: "cov", lamp: "ok", text: "7 of 7 available" },
            { key: "chk", text: "Checked just now" },
            { key: "status", text: "Status", value: "On track" },
            { key: "verb", verb: <Button dense variant="ghost">Connect calendar</Button> },
          ]}
        />
      </AppHead>,
    );
    const fact = screen.getByTestId("fact");
    expect(fact.tagName).toBe("H2");
    expect(fact.className).toContain("surface-display");
    expect(fact.className).toContain("kit-disp");
    expect(container.querySelectorAll(".kit-disp")).toHaveLength(1);
    const strip = container.querySelector(".kit-strip") as HTMLElement;
    expect(strip.parentElement).toBe(screen.getByTestId("head"));
    const tokens = [...strip.children].map((c) => c.textContent);
    expect(tokens).toEqual(["7 of 7 available", "Checked just now", "Status On track", "Connect calendar"]);
    expect(strip.querySelector(".kit-sq")?.getAttribute("data-tone")).toBe("ok");
    expect(strip.querySelector("b")?.textContent).toBe("On track");
    expect(screen.getByRole("button", { name: "Connect calendar" }).className).toContain("btn");
  });

  it("drops empty items; an empty strip draws nothing", () => {
    const { container } = render(<StatusStrip items={[null, false, undefined]} />);
    expect(container.innerHTML).toBe("");
  });

  it("the lamp square is aria-hidden: the word carries the meaning", () => {
    const { container } = render(<StatusStrip items={[{ lamp: "fail", text: "ROOM · NOT READ" }]} />);
    expect(container.querySelector(".kit-sq")?.getAttribute("aria-hidden")).toBe("true");
    expect(container.textContent).toBe("ROOM · NOT READ");
  });
});
