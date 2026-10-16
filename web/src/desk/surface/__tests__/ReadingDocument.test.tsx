import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
const opened = vi.hoisted(() => vi.fn());
vi.mock("../../openObject", () => ({ refOpener: (ref: string) => ref === "action:held-17" ? () => opened(ref) : null }));
import { ReadingDocument } from "../ReadingDocument";
import { Material } from "../Material";
import { AgentWords } from "../../components/AgentWords";

afterEach(() => { cleanup(); opened.mockReset(); });

const DOCUMENT = "## Plan\n\nRead **the source**.\n\n- First\n  - Second\n    - Third\n\n| Source | State |\n| --- | --- |\n| [Held task](action:held-17) | Waiting |\n\n```python\n  if ready:\n    ship()\n```\n\n[Guide](https://example.com/guide) and [Plan](/repo/docs/plan.md)";

describe("shared reading document", () => {
  it.each(["material", "agent"])("%s uses semantic document blocks and original code", (host) => {
    const { container } = render(host === "material" ? <Material>{DOCUMENT}</Material> : <AgentWords text={DOCUMENT} />);
    expect(container.querySelector("h2")?.textContent?.trim()).toBe("Plan");
    expect(container.querySelector("ul > li > ul > li > ul > li")?.textContent).toBe("Third");
    expect([...container.querySelectorAll("th")].map((cell) => cell.textContent)).toEqual(["Source", "State"]);
    expect(container.querySelector("pre code")?.textContent).toBe("  if ready:\n    ship()");
    expect(container.querySelectorAll('.surface-scroll-hint[data-axis="x"]')).toHaveLength(2);
    expect(container.querySelectorAll('.reading-scroll[tabindex="0"]')).toHaveLength(2);
    const button = container.querySelector("button")!;
    expect(button.className).toContain("btn");
    fireEvent.click(button);
    expect(opened).toHaveBeenCalledWith("action:held-17");
    const guide = container.querySelector("a")!;
    expect(guide.textContent).toBe("Guide");
    expect(guide.getAttribute("href")).toBe("https://example.com/guide");
    expect(container.querySelector(".reading-inert")?.textContent).toBe("Plan /repo/docs/plan.md");
  });

  it("shows HTML and unsupported destinations as text and never loads images", () => {
    const { container } = render(<ReadingDocument>{'<img src="https://example.com/image">\n\n![Diagram](https://example.com/diagram.png)\n\n[Bad](javascript:alert(1)) [Mail](mailto:a@example.com)'}</ReadingDocument>);
    expect(container.querySelector("img,script,a,button")).toBeNull();
    expect(container.textContent).toContain('<img src="https://example.com/image">');
    expect(container.textContent).toContain("[Diagram]");
    expect(container.textContent).toContain("Bad javascript:alert(1)");
    expect(container.textContent).toContain("Mail mailto:a@example.com");
  });

  it.each(["material", "agent"])("%s renders task inline content and keeps static markers", (host) => {
    const source = "- [ ] **Provide the PRs to review** — You — no deadline stated\n- [x] Read [Guide](https://example.com/guide) and `review.md`";
    const { container } = render(host === "material" ? <Material>{source}</Material> : <AgentWords text={source} />);
    const items = container.querySelectorAll("ul > li");
    expect(items).toHaveLength(2);
    expect(items[0].textContent).toBe("[ ] Provide the PRs to review — You — no deadline stated");
    expect(items[0].querySelector("strong")?.textContent).toBe("Provide the PRs to review");
    expect(items[1].textContent).toBe("[x] Read Guide and review.md");
    expect(items[1].querySelector("a")?.getAttribute("href")).toBe("https://example.com/guide");
    expect(items[1].querySelector("code")?.textContent).toBe("review.md");
    expect(container.textContent).not.toContain("**");
    expect(container.querySelector("input")).toBeNull();
  });

  it("compact summaries keep their ask and never create link controls", () => {
    const { container } = render(<AgentWords compact text={`${DOCUMENT}\n\nMay I open [Held task](action:held-17)?`} />);
    expect(container.querySelector("p,table,pre,button,a,h2")).toBeNull();
    expect(container.textContent).toBe("May I open Held task action:held-17?");
  });
});
